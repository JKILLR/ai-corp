"""
Telegram Connector - Send messages, photos, videos via Telegram Bot API.

Supports:
- Text messages
- Photos and videos
- Documents
- Polls
- Notifications
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


class TelegramConnector(BaseConnector):
    """
    Telegram connector for bot messaging.

    Uses the Telegram Bot API. Requires a bot token from @BotFather.

    Actions:
    - send_message: Send a text message
    - send_photo: Send a photo
    - send_video: Send a video
    - send_document: Send a document
    - send_poll: Send a poll
    - get_updates: Get recent updates/messages
    """

    BASE_URL = "https://api.telegram.org/bot"

    @classmethod
    def info(cls) -> ConnectorInfo:
        return ConnectorInfo(
            id="telegram",
            name="Telegram",
            category=ConnectorCategory.COMMUNICATION,
            description="Send messages and media via Telegram Bot",
            auth_type=AuthType.TOKEN,
            auth_help="Create a bot with @BotFather and get the bot token",
            website="https://telegram.org",
            icon="📨",
            actions=[
                "send_message",
                "send_photo",
                "send_video",
                "send_document",
                "send_poll",
                "get_updates",
                "get_me"
            ],
            required_credentials=["bot_token"],
            optional_credentials=["default_chat_id"]
        )

    def __init__(self, credentials: Dict[str, str]):
        super().__init__(credentials)
        self._base_url = f"{self.BASE_URL}{credentials['bot_token']}"

    def _make_request(self, method: str, params: Dict = None, files: Dict = None) -> Dict:
        """Make a request to Telegram Bot API."""
        import urllib.request
        import urllib.parse
        import json

        url = f"{self._base_url}/{method}"

        if files:
            # Multipart form data for file uploads
            import io
            boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
            body = io.BytesIO()

            for key, value in (params or {}).items():
                body.write(f"--{boundary}\r\n".encode())
                body.write(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode())
                body.write(f"{value}\r\n".encode())

            for key, file_path in files.items():
                filename = file_path.split("/")[-1]
                body.write(f"--{boundary}\r\n".encode())
                body.write(f'Content-Disposition: form-data; name="{key}"; filename="{filename}"\r\n'.encode())
                body.write(b"Content-Type: application/octet-stream\r\n\r\n")
                with open(file_path, "rb") as f:
                    body.write(f.read())
                body.write(b"\r\n")

            body.write(f"--{boundary}--\r\n".encode())

            req = urllib.request.Request(
                url,
                data=body.getvalue(),
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
            )
        else:
            # JSON request
            data = json.dumps(params or {}).encode()
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"}
            )

        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())

    def validate_credentials(self) -> bool:
        """Validate by calling getMe."""
        try:
            result = self._make_request("getMe")
            return result.get("ok", False)
        except Exception as e:
            logger.error(f"Telegram credential validation failed: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> ActionResult:
        """Execute a Telegram action."""
        try:
            if action == "send_message":
                return self._send_message(params)
            elif action == "send_photo":
                return self._send_photo(params)
            elif action == "send_video":
                return self._send_video(params)
            elif action == "send_document":
                return self._send_document(params)
            elif action == "send_poll":
                return self._send_poll(params)
            elif action == "get_updates":
                return self._get_updates(params)
            elif action == "get_me":
                return self._get_me()
            else:
                return ActionResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            logger.error(f"Telegram action failed: {e}")
            return ActionResult(success=False, error=str(e))

    def _get_chat_id(self, params: Dict) -> str:
        """Get chat ID from params or default."""
        return params.get("chat_id") or self._credentials.get("default_chat_id")

    def _send_message(self, params: Dict) -> ActionResult:
        """Send a text message."""
        chat_id = self._get_chat_id(params)
        if not chat_id:
            return ActionResult(success=False, error="chat_id required")

        request_params = {
            "chat_id": chat_id,
            "text": params["text"],
            "parse_mode": params.get("parse_mode", "HTML"),
            "disable_web_page_preview": params.get("disable_preview", False),
            "disable_notification": params.get("silent", False)
        }

        # Add reply markup if provided
        if params.get("reply_markup"):
            import json
            request_params["reply_markup"] = json.dumps(params["reply_markup"])

        result = self._make_request("sendMessage", request_params)

        if result.get("ok"):
            message = result["result"]
            return ActionResult(
                success=True,
                data={
                    "message_id": message["message_id"],
                    "chat_id": message["chat"]["id"],
                    "date": message["date"]
                }
            )
        else:
            return ActionResult(success=False, error=result.get("description"))

    def _send_photo(self, params: Dict) -> ActionResult:
        """Send a photo."""
        chat_id = self._get_chat_id(params)
        if not chat_id:
            return ActionResult(success=False, error="chat_id required")

        request_params = {
            "chat_id": chat_id,
            "caption": params.get("caption", ""),
            "parse_mode": params.get("parse_mode", "HTML")
        }

        files = None
        if "file_path" in params:
            files = {"photo": params["file_path"]}
        elif "url" in params:
            request_params["photo"] = params["url"]
        else:
            return ActionResult(success=False, error="file_path or url required")

        result = self._make_request("sendPhoto", request_params, files)

        if result.get("ok"):
            message = result["result"]
            return ActionResult(
                success=True,
                data={
                    "message_id": message["message_id"],
                    "chat_id": message["chat"]["id"]
                }
            )
        else:
            return ActionResult(success=False, error=result.get("description"))

    def _send_video(self, params: Dict) -> ActionResult:
        """Send a video."""
        chat_id = self._get_chat_id(params)
        if not chat_id:
            return ActionResult(success=False, error="chat_id required")

        request_params = {
            "chat_id": chat_id,
            "caption": params.get("caption", ""),
            "parse_mode": params.get("parse_mode", "HTML"),
            "supports_streaming": params.get("supports_streaming", True)
        }

        files = None
        if "file_path" in params:
            files = {"video": params["file_path"]}
        elif "url" in params:
            request_params["video"] = params["url"]
        else:
            return ActionResult(success=False, error="file_path or url required")

        result = self._make_request("sendVideo", request_params, files)

        if result.get("ok"):
            message = result["result"]
            return ActionResult(
                success=True,
                data={
                    "message_id": message["message_id"],
                    "chat_id": message["chat"]["id"]
                }
            )
        else:
            return ActionResult(success=False, error=result.get("description"))

    def _send_document(self, params: Dict) -> ActionResult:
        """Send a document."""
        chat_id = self._get_chat_id(params)
        if not chat_id:
            return ActionResult(success=False, error="chat_id required")

        request_params = {
            "chat_id": chat_id,
            "caption": params.get("caption", ""),
            "parse_mode": params.get("parse_mode", "HTML")
        }

        files = None
        if "file_path" in params:
            files = {"document": params["file_path"]}
        elif "url" in params:
            request_params["document"] = params["url"]
        else:
            return ActionResult(success=False, error="file_path or url required")

        result = self._make_request("sendDocument", request_params, files)

        if result.get("ok"):
            message = result["result"]
            return ActionResult(
                success=True,
                data={
                    "message_id": message["message_id"],
                    "chat_id": message["chat"]["id"]
                }
            )
        else:
            return ActionResult(success=False, error=result.get("description"))

    def _send_poll(self, params: Dict) -> ActionResult:
        """Send a poll."""
        chat_id = self._get_chat_id(params)
        if not chat_id:
            return ActionResult(success=False, error="chat_id required")

        import json
        request_params = {
            "chat_id": chat_id,
            "question": params["question"],
            "options": json.dumps(params["options"]),
            "is_anonymous": params.get("is_anonymous", True),
            "type": params.get("type", "regular"),
            "allows_multiple_answers": params.get("allows_multiple_answers", False)
        }

        result = self._make_request("sendPoll", request_params)

        if result.get("ok"):
            message = result["result"]
            return ActionResult(
                success=True,
                data={
                    "message_id": message["message_id"],
                    "poll_id": message["poll"]["id"],
                    "chat_id": message["chat"]["id"]
                }
            )
        else:
            return ActionResult(success=False, error=result.get("description"))

    def _get_updates(self, params: Dict) -> ActionResult:
        """Get recent updates/messages."""
        request_params = {
            "offset": params.get("offset"),
            "limit": params.get("limit", 100),
            "timeout": params.get("timeout", 0)
        }
        request_params = {k: v for k, v in request_params.items() if v is not None}

        result = self._make_request("getUpdates", request_params)

        if result.get("ok"):
            updates = []
            for update in result.get("result", []):
                update_data = {
                    "update_id": update["update_id"]
                }
                if "message" in update:
                    msg = update["message"]
                    update_data["message"] = {
                        "message_id": msg["message_id"],
                        "chat_id": msg["chat"]["id"],
                        "from": msg.get("from", {}).get("username"),
                        "text": msg.get("text"),
                        "date": msg["date"]
                    }
                updates.append(update_data)

            return ActionResult(success=True, data=updates)
        else:
            return ActionResult(success=False, error=result.get("description"))

    def _get_me(self) -> ActionResult:
        """Get bot information."""
        result = self._make_request("getMe")

        if result.get("ok"):
            bot = result["result"]
            return ActionResult(
                success=True,
                data={
                    "id": bot["id"],
                    "username": bot["username"],
                    "first_name": bot["first_name"],
                    "can_join_groups": bot.get("can_join_groups"),
                    "can_read_all_group_messages": bot.get("can_read_all_group_messages")
                }
            )
        else:
            return ActionResult(success=False, error=result.get("description"))

    def get_action_definitions(self) -> List[ActionDefinition]:
        """Return detailed action definitions."""
        return [
            ActionDefinition(
                id="send_message",
                name="Send Message",
                description="Send a text message to a chat",
                params=[
                    ActionParam("chat_id", "string", "Chat ID to send to", required=False),
                    ActionParam("text", "string", "Message text", required=True),
                    ActionParam("parse_mode", "string", "Parse mode", required=False, default="HTML",
                              options=["HTML", "Markdown", "MarkdownV2"]),
                    ActionParam("silent", "boolean", "Send silently", required=False, default=False),
                ],
                returns="Message ID and chat ID"
            ),
            ActionDefinition(
                id="send_photo",
                name="Send Photo",
                description="Send a photo to a chat",
                params=[
                    ActionParam("chat_id", "string", "Chat ID to send to", required=False),
                    ActionParam("file_path", "file", "Path to photo file", required=False),
                    ActionParam("url", "string", "URL of photo", required=False),
                    ActionParam("caption", "string", "Photo caption", required=False),
                ],
                returns="Message ID"
            ),
            ActionDefinition(
                id="send_video",
                name="Send Video",
                description="Send a video to a chat",
                params=[
                    ActionParam("chat_id", "string", "Chat ID to send to", required=False),
                    ActionParam("file_path", "file", "Path to video file", required=False),
                    ActionParam("url", "string", "URL of video", required=False),
                    ActionParam("caption", "string", "Video caption", required=False),
                ],
                returns="Message ID"
            ),
        ]
