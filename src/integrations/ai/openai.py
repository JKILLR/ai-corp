"""
OpenAI Connector - GPT, DALL-E, Whisper, and more.

Supports:
- Text generation (GPT-4, GPT-4o, etc.)
- Image generation (DALL-E 3)
- Speech-to-text (Whisper)
- Text embeddings
- Content moderation
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


class OpenAIConnector(BaseConnector):
    """
    OpenAI connector for GPT, DALL-E, Whisper.

    Actions:
    - generate_text: Generate text with GPT models
    - generate_image: Generate images with DALL-E
    - transcribe: Transcribe audio with Whisper
    - embed: Generate text embeddings
    - moderate: Check content for policy violations
    """

    @classmethod
    def info(cls) -> ConnectorInfo:
        return ConnectorInfo(
            id="openai",
            name="OpenAI",
            category=ConnectorCategory.AI,
            description="GPT-4, DALL-E 3, Whisper, and more",
            auth_type=AuthType.API_KEY,
            auth_help="Get your API key at https://platform.openai.com/api-keys",
            website="https://openai.com",
            icon="🤖",
            actions=[
                "generate_text",
                "generate_image",
                "transcribe",
                "embed",
                "moderate",
                "list_models"
            ],
            required_credentials=["api_key"],
            optional_credentials=["organization_id", "project_id"]
        )

    def __init__(self, credentials: Dict[str, str]):
        super().__init__(credentials)
        self._client = None

    def _get_client(self):
        """Lazy-load OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self._credentials["api_key"],
                    organization=self._credentials.get("organization_id"),
                    project=self._credentials.get("project_id")
                )
            except ImportError:
                raise ImportError("openai package required: pip install openai")
        return self._client

    def validate_credentials(self) -> bool:
        """Validate by listing models."""
        try:
            client = self._get_client()
            # Make a minimal API call to verify
            list(client.models.list())
            return True
        except Exception as e:
            logger.error(f"OpenAI credential validation failed: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> ActionResult:
        """Execute an OpenAI action."""
        try:
            if action == "generate_text":
                return self._generate_text(params)
            elif action == "generate_image":
                return self._generate_image(params)
            elif action == "transcribe":
                return self._transcribe(params)
            elif action == "embed":
                return self._embed(params)
            elif action == "moderate":
                return self._moderate(params)
            elif action == "list_models":
                return self._list_models()
            else:
                return ActionResult(success=False, error=f"Unknown action: {action}")
        except ImportError as e:
            return ActionResult(success=False, error=str(e))
        except Exception as e:
            logger.error(f"OpenAI action failed: {e}")
            return ActionResult(success=False, error=str(e))

    def _generate_text(self, params: Dict) -> ActionResult:
        """Generate text with GPT."""
        client = self._get_client()

        messages = params.get("messages", [])
        if isinstance(params.get("prompt"), str):
            # Simple prompt mode
            messages = [{"role": "user", "content": params["prompt"]}]

        response = client.chat.completions.create(
            model=params.get("model", "gpt-4o"),
            messages=messages,
            max_tokens=params.get("max_tokens", 1000),
            temperature=params.get("temperature", 0.7),
            top_p=params.get("top_p"),
            stream=False
        )

        return ActionResult(
            success=True,
            data=response.choices[0].message.content,
            metadata={
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason
            }
        )

    def _generate_image(self, params: Dict) -> ActionResult:
        """Generate image with DALL-E."""
        client = self._get_client()

        response = client.images.generate(
            model=params.get("model", "dall-e-3"),
            prompt=params["prompt"],
            size=params.get("size", "1024x1024"),
            quality=params.get("quality", "standard"),
            n=params.get("n", 1),
            response_format=params.get("response_format", "url")
        )

        return ActionResult(
            success=True,
            data=[img.url for img in response.data],
            metadata={
                "revised_prompt": response.data[0].revised_prompt if hasattr(response.data[0], 'revised_prompt') else None
            }
        )

    def _transcribe(self, params: Dict) -> ActionResult:
        """Transcribe audio with Whisper."""
        client = self._get_client()

        file_path = params.get("file_path")
        if not file_path:
            return ActionResult(success=False, error="file_path required")

        with open(file_path, "rb") as f:
            response = client.audio.transcriptions.create(
                model=params.get("model", "whisper-1"),
                file=f,
                language=params.get("language"),
                response_format=params.get("response_format", "text")
            )

        return ActionResult(
            success=True,
            data=response.text if hasattr(response, 'text') else response
        )

    def _embed(self, params: Dict) -> ActionResult:
        """Generate embeddings."""
        client = self._get_client()

        response = client.embeddings.create(
            model=params.get("model", "text-embedding-3-small"),
            input=params["input"],
            encoding_format=params.get("encoding_format", "float")
        )

        return ActionResult(
            success=True,
            data=[e.embedding for e in response.data],
            metadata={
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "model": response.model
            }
        )

    def _moderate(self, params: Dict) -> ActionResult:
        """Check content for policy violations."""
        client = self._get_client()

        response = client.moderations.create(
            model=params.get("model", "omni-moderation-latest"),
            input=params["input"]
        )

        result = response.results[0]
        return ActionResult(
            success=True,
            data={
                "flagged": result.flagged,
                "categories": {k: v for k, v in result.categories.model_dump().items()},
                "category_scores": {k: v for k, v in result.category_scores.model_dump().items()}
            }
        )

    def _list_models(self) -> ActionResult:
        """List available models."""
        client = self._get_client()

        models = list(client.models.list())
        return ActionResult(
            success=True,
            data=[{"id": m.id, "owned_by": m.owned_by} for m in models]
        )

    def get_action_definitions(self) -> List[ActionDefinition]:
        """Return detailed action definitions."""
        return [
            ActionDefinition(
                id="generate_text",
                name="Generate Text",
                description="Generate text using GPT models",
                params=[
                    ActionParam("prompt", "string", "Text prompt (or use messages)", required=False),
                    ActionParam("messages", "array", "Chat messages array", required=False),
                    ActionParam("model", "string", "Model to use", required=False, default="gpt-4o"),
                    ActionParam("max_tokens", "number", "Maximum tokens", required=False, default=1000),
                    ActionParam("temperature", "number", "Creativity (0-2)", required=False, default=0.7),
                ],
                returns="Generated text string"
            ),
            ActionDefinition(
                id="generate_image",
                name="Generate Image",
                description="Generate images using DALL-E",
                params=[
                    ActionParam("prompt", "string", "Image description", required=True),
                    ActionParam("model", "string", "Model to use", required=False, default="dall-e-3"),
                    ActionParam("size", "string", "Image size", required=False, default="1024x1024",
                              options=["1024x1024", "1792x1024", "1024x1792"]),
                    ActionParam("quality", "string", "Quality level", required=False, default="standard",
                              options=["standard", "hd"]),
                ],
                returns="Array of image URLs"
            ),
            ActionDefinition(
                id="transcribe",
                name="Transcribe Audio",
                description="Transcribe audio to text using Whisper",
                params=[
                    ActionParam("file_path", "file", "Path to audio file", required=True),
                    ActionParam("language", "string", "Language code (e.g., 'en')", required=False),
                ],
                returns="Transcribed text"
            ),
            ActionDefinition(
                id="embed",
                name="Create Embeddings",
                description="Generate vector embeddings for text",
                params=[
                    ActionParam("input", "string", "Text to embed", required=True),
                    ActionParam("model", "string", "Model to use", required=False, default="text-embedding-3-small"),
                ],
                returns="Array of embedding vectors"
            ),
            ActionDefinition(
                id="moderate",
                name="Moderate Content",
                description="Check content for policy violations",
                params=[
                    ActionParam("input", "string", "Content to moderate", required=True),
                ],
                returns="Moderation results with flagged categories"
            ),
        ]
