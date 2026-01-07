"""
Anthropic Connector - Claude models for text generation and analysis.

Supports:
- Text generation with Claude models
- Multi-turn conversations
- Vision (image analysis)
"""

from typing import Dict, Any, List
import logging

from ..base import (
    BaseConnector,
    ConnectorInfo,
    ConnectorCategory,
    AuthType,
    ActionResult,
    ActionDefinition,
    ActionParam
)

logger = logging.getLogger(__name__)


class AnthropicConnector(BaseConnector):
    """
    Anthropic connector for Claude models.

    Actions:
    - generate_text: Generate text with Claude
    - analyze_image: Analyze images with Claude's vision
    """

    @classmethod
    def info(cls) -> ConnectorInfo:
        return ConnectorInfo(
            id="anthropic",
            name="Anthropic",
            category=ConnectorCategory.AI,
            description="Claude models for text generation and analysis",
            auth_type=AuthType.API_KEY,
            auth_help="Get your API key at https://console.anthropic.com/",
            website="https://anthropic.com",
            icon="🧠",
            actions=[
                "generate_text",
                "analyze_image",
                "count_tokens"
            ],
            required_credentials=["api_key"]
        )

    def __init__(self, credentials: Dict[str, str]):
        super().__init__(credentials)
        self._client = None

    def _get_client(self):
        """Lazy-load Anthropic client."""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(
                    api_key=self._credentials["api_key"]
                )
            except ImportError:
                raise ImportError("anthropic package required: pip install anthropic")
        return self._client

    def validate_credentials(self) -> bool:
        """Validate by making a minimal API call."""
        try:
            client = self._get_client()
            # Make a minimal API call to verify credentials
            client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "hi"}]
            )
            return True
        except Exception as e:
            logger.error(f"Anthropic credential validation failed: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> ActionResult:
        """Execute an Anthropic action."""
        try:
            if action == "generate_text":
                return self._generate_text(params)
            elif action == "analyze_image":
                return self._analyze_image(params)
            elif action == "count_tokens":
                return self._count_tokens(params)
            else:
                return ActionResult(success=False, error=f"Unknown action: {action}")
        except ImportError as e:
            return ActionResult(success=False, error=str(e))
        except Exception as e:
            logger.error(f"Anthropic action failed: {e}")
            return ActionResult(success=False, error=str(e))

    def _generate_text(self, params: Dict) -> ActionResult:
        """Generate text with Claude."""
        client = self._get_client()

        messages = params.get("messages", [])
        if isinstance(params.get("prompt"), str):
            # Simple prompt mode
            messages = [{"role": "user", "content": params["prompt"]}]

        response = client.messages.create(
            model=params.get("model", "claude-sonnet-4-20250514"),
            max_tokens=params.get("max_tokens", 1024),
            messages=messages,
            system=params.get("system"),
            temperature=params.get("temperature", 1.0),
            top_p=params.get("top_p"),
            stop_sequences=params.get("stop_sequences")
        )

        # Extract text content
        text_content = ""
        for block in response.content:
            if block.type == "text":
                text_content += block.text

        return ActionResult(
            success=True,
            data=text_content,
            metadata={
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                },
                "model": response.model,
                "stop_reason": response.stop_reason
            }
        )

    def _analyze_image(self, params: Dict) -> ActionResult:
        """Analyze an image with Claude's vision."""
        client = self._get_client()
        import base64

        # Support both URL and file path
        image_content = None
        if "image_url" in params:
            image_content = {
                "type": "image",
                "source": {
                    "type": "url",
                    "url": params["image_url"]
                }
            }
        elif "image_path" in params:
            # Read and encode file
            with open(params["image_path"], "rb") as f:
                image_data = base64.standard_b64encode(f.read()).decode("utf-8")

            # Detect media type
            path = params["image_path"].lower()
            if path.endswith(".png"):
                media_type = "image/png"
            elif path.endswith(".gif"):
                media_type = "image/gif"
            elif path.endswith(".webp"):
                media_type = "image/webp"
            else:
                media_type = "image/jpeg"

            image_content = {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": image_data
                }
            }
        else:
            return ActionResult(success=False, error="image_url or image_path required")

        messages = [{
            "role": "user",
            "content": [
                image_content,
                {
                    "type": "text",
                    "text": params.get("prompt", "Describe this image in detail.")
                }
            ]
        }]

        response = client.messages.create(
            model=params.get("model", "claude-sonnet-4-20250514"),
            max_tokens=params.get("max_tokens", 1024),
            messages=messages
        )

        text_content = ""
        for block in response.content:
            if block.type == "text":
                text_content += block.text

        return ActionResult(
            success=True,
            data=text_content,
            metadata={
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                },
                "model": response.model
            }
        )

    def _count_tokens(self, params: Dict) -> ActionResult:
        """Count tokens in text."""
        client = self._get_client()

        response = client.messages.count_tokens(
            model=params.get("model", "claude-sonnet-4-20250514"),
            messages=[{"role": "user", "content": params["text"]}]
        )

        return ActionResult(
            success=True,
            data={"input_tokens": response.input_tokens}
        )

    def get_action_definitions(self) -> List[ActionDefinition]:
        """Return detailed action definitions."""
        return [
            ActionDefinition(
                id="generate_text",
                name="Generate Text",
                description="Generate text using Claude models",
                params=[
                    ActionParam("prompt", "string", "Text prompt (or use messages)", required=False),
                    ActionParam("messages", "array", "Chat messages array", required=False),
                    ActionParam("system", "string", "System prompt", required=False),
                    ActionParam("model", "string", "Model to use", required=False, default="claude-sonnet-4-20250514",
                              options=["claude-opus-4-20250514", "claude-sonnet-4-20250514", "claude-3-haiku-20240307"]),
                    ActionParam("max_tokens", "number", "Maximum tokens", required=False, default=1024),
                    ActionParam("temperature", "number", "Creativity (0-1)", required=False, default=1.0),
                ],
                returns="Generated text string"
            ),
            ActionDefinition(
                id="analyze_image",
                name="Analyze Image",
                description="Analyze an image using Claude's vision capabilities",
                params=[
                    ActionParam("image_url", "string", "URL of image to analyze", required=False),
                    ActionParam("image_path", "file", "Path to local image file", required=False),
                    ActionParam("prompt", "string", "Analysis prompt", required=False, default="Describe this image in detail."),
                    ActionParam("model", "string", "Model to use", required=False, default="claude-sonnet-4-20250514"),
                ],
                returns="Analysis text"
            ),
            ActionDefinition(
                id="count_tokens",
                name="Count Tokens",
                description="Count tokens in text for the specified model",
                params=[
                    ActionParam("text", "string", "Text to count tokens for", required=True),
                    ActionParam("model", "string", "Model to use", required=False, default="claude-sonnet-4-20250514"),
                ],
                returns="Token count object"
            ),
        ]
