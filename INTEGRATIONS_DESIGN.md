# AI Corp Integrations System

## Vision

A simple, extensible integrations layer that connects AI Corp to external services. Anyone can connect their accounts in minutes. Developers can add new connectors easily.

**Design Principles:**
1. **Simple to connect** - OAuth or API key, that's it
2. **Categorized, not overwhelming** - Grouped by purpose
3. **Consistent interface** - All connectors work the same way
4. **Secure by default** - Credentials encrypted, never logged
5. **Graceful degradation** - Missing credentials = feature disabled, not error

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          INTEGRATIONS SYSTEM                                     │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         USER LAYER                                       │   │
│  │                                                                         │   │
│  │   "Connect YouTube"  →  OAuth flow  →  Credentials stored securely     │   │
│  │   "Connect OpenAI"   →  Paste API key  →  Validated and stored         │   │
│  │                                                                         │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                           │
│  ┌─────────────────────────────────┼───────────────────────────────────────┐   │
│  │                         CONNECTOR LAYER                                  │   │
│  │                                 │                                       │   │
│  │   ┌──────────────┐  ┌──────────┴──────────┐  ┌──────────────┐          │   │
│  │   │ AI Services  │  │  Social Platforms   │  │   Storage    │          │   │
│  │   ├──────────────┤  ├─────────────────────┤  ├──────────────┤          │   │
│  │   │ • OpenAI     │  │ • YouTube           │  │ • Cloudinary │          │   │
│  │   │ • Anthropic  │  │ • Instagram         │  │ • S3         │          │   │
│  │   │ • ElevenLabs │  │ • TikTok            │  │ • Google     │          │   │
│  │   │ • Replicate  │  │ • Twitter/X         │  │   Drive      │          │   │
│  │   └──────────────┘  │ • LinkedIn          │  └──────────────┘          │   │
│  │                     │ • Facebook          │                            │   │
│  │   ┌──────────────┐  └─────────────────────┘  ┌──────────────┐          │   │
│  │   │    Video     │                           │     Data     │          │   │
│  │   ├──────────────┤                           ├──────────────┤          │   │
│  │   │ • HeyGen     │                           │ • Airtable   │          │   │
│  │   │ • Runway     │                           │ • Sheets     │          │   │
│  │   │ • Synthesia  │                           │ • Notion     │          │   │
│  │   └──────────────┘                           └──────────────┘          │   │
│  │                                                                         │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                           │
│  ┌─────────────────────────────────┼───────────────────────────────────────┐   │
│  │                         FOUNDATION LAYER                                 │   │
│  │                                 │                                       │   │
│  │   ┌──────────────┐  ┌──────────┴──────────┐  ┌──────────────┐          │   │
│  │   │ Credential   │  │  Connector          │  │   Action     │          │   │
│  │   │ Vault        │  │  Registry           │  │   Executor   │          │   │
│  │   └──────────────┘  └─────────────────────┘  └──────────────┘          │   │
│  │                                                                         │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Connector Categories

### 🤖 AI Services
Generate text, images, audio, and more.

| Connector | Auth Type | Actions |
|-----------|-----------|---------|
| **OpenAI** | API Key | `generate_text`, `generate_image`, `transcribe`, `embed` |
| **Anthropic** | API Key | `generate_text`, `analyze` |
| **ElevenLabs** | API Key | `generate_speech`, `clone_voice` |
| **Replicate** | API Key | `run_model` (Flux, SD, Whisper, etc.) |
| **Perplexity** | API Key | `search`, `research` |

### 📺 Video Generation
Create videos with AI.

| Connector | Auth Type | Actions |
|-----------|-----------|---------|
| **HeyGen** | API Key | `create_avatar_video`, `list_avatars` |
| **Synthesia** | API Key | `create_avatar_video`, `list_avatars` |
| **Runway** | API Key | `generate_video`, `extend_video` |
| **Pika** | API Key | `generate_video` |
| **Captions** | API Key | `add_captions`, `translate` |

### 📱 Social Platforms
Publish and manage content.

| Connector | Auth Type | Actions |
|-----------|-----------|---------|
| **YouTube** | OAuth | `upload_video`, `upload_short`, `get_analytics`, `get_comments` |
| **Instagram** | OAuth | `upload_post`, `upload_reel`, `upload_story`, `get_insights` |
| **TikTok** | OAuth | `upload_video`, `get_analytics` |
| **Twitter/X** | OAuth | `post_tweet`, `post_thread`, `get_mentions` |
| **LinkedIn** | OAuth | `post_update`, `post_article` |
| **Facebook** | OAuth | `post_update`, `upload_reel` |
| **Threads** | OAuth | `post_thread` |
| **Pinterest** | OAuth | `create_pin` |
| **Bluesky** | App Password | `post` |

### 💾 Storage
Store and manage files.

| Connector | Auth Type | Actions |
|-----------|-----------|---------|
| **Cloudinary** | API Key | `upload`, `transform`, `delete` |
| **AWS S3** | API Key | `upload`, `download`, `list`, `delete` |
| **Google Drive** | OAuth | `upload`, `download`, `list`, `share` |
| **Dropbox** | OAuth | `upload`, `download`, `list` |

### 📊 Data
Connect to databases and spreadsheets.

| Connector | Auth Type | Actions |
|-----------|-----------|---------|
| **Airtable** | API Key | `list_records`, `create_record`, `update_record` |
| **Google Sheets** | OAuth | `read_range`, `write_range`, `append_row` |
| **Notion** | API Key | `query_database`, `create_page`, `update_page` |

### 💬 Communication
Send notifications and messages.

| Connector | Auth Type | Actions |
|-----------|-----------|---------|
| **Telegram** | Bot Token | `send_message`, `send_photo`, `send_video` |
| **Discord** | Webhook/Bot | `send_message`, `send_embed` |
| **Slack** | OAuth/Webhook | `send_message`, `upload_file` |
| **Email (SMTP)** | Credentials | `send_email` |

### 📧 Personal (for Personal Edition)
Connect personal accounts.

| Connector | Auth Type | Actions |
|-----------|-----------|---------|
| **Gmail** | OAuth | `list_emails`, `send_email`, `get_email` |
| **Google Calendar** | OAuth | `list_events`, `create_event` |
| **iMessage** | Local | `list_messages`, `send_message` |
| **Contacts** | Local/OAuth | `list_contacts`, `search` |

---

## Simple Connection Flow

### For API Key Services

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   1. User: "ai-corp connect openai"                        │
│                                                             │
│   2. System: "Enter your OpenAI API key:"                  │
│              "You can find this at platform.openai.com"    │
│                                                             │
│   3. User: sk-xxxxxxxxxxxxx                                │
│                                                             │
│   4. System: ✓ Validating...                               │
│              ✓ Connected! OpenAI ready to use.             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### For OAuth Services

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   1. User: "ai-corp connect youtube"                       │
│                                                             │
│   2. System: Opening browser for YouTube authorization...  │
│              [Browser opens Google OAuth]                  │
│                                                             │
│   3. User: [Clicks "Allow" in browser]                     │
│                                                             │
│   4. System: ✓ Connected! YouTube ready to use.            │
│              - Channel: @YourChannel                       │
│              - Permissions: Upload, Analytics              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## BaseConnector Interface

```python
# src/integrations/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from enum import Enum

class AuthType(Enum):
    API_KEY = "api_key"
    OAUTH = "oauth"
    CREDENTIALS = "credentials"  # username/password
    TOKEN = "token"              # bot token, app password
    LOCAL = "local"              # local system access

@dataclass
class ConnectorInfo:
    """Metadata about a connector"""
    id: str                      # e.g., "openai"
    name: str                    # e.g., "OpenAI"
    category: str                # e.g., "ai"
    description: str
    auth_type: AuthType
    auth_help: str               # Instructions for getting credentials
    website: str
    icon: str                    # Emoji or icon path
    actions: List[str]           # Available actions

@dataclass
class ActionResult:
    """Result from executing an action"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict] = None  # Rate limits, usage, etc.

class BaseConnector(ABC):
    """Base class for all connectors"""

    @classmethod
    @abstractmethod
    def info(cls) -> ConnectorInfo:
        """Return connector metadata"""
        pass

    @abstractmethod
    def validate_credentials(self, credentials: Dict[str, str]) -> bool:
        """Validate credentials are correct"""
        pass

    @abstractmethod
    def execute(self, action: str, params: Dict[str, Any]) -> ActionResult:
        """Execute an action"""
        pass

    def get_actions(self) -> List[str]:
        """Get available actions"""
        return self.info().actions

    def supports_action(self, action: str) -> bool:
        """Check if action is supported"""
        return action in self.get_actions()
```

## Example Connector: OpenAI

```python
# src/integrations/ai/openai.py

from openai import OpenAI
from ..base import BaseConnector, ConnectorInfo, AuthType, ActionResult

class OpenAIConnector(BaseConnector):
    """OpenAI connector for GPT, DALL-E, Whisper"""

    @classmethod
    def info(cls) -> ConnectorInfo:
        return ConnectorInfo(
            id="openai",
            name="OpenAI",
            category="ai",
            description="GPT-4, DALL-E, Whisper, and more",
            auth_type=AuthType.API_KEY,
            auth_help="Get your API key at https://platform.openai.com/api-keys",
            website="https://openai.com",
            icon="🤖",
            actions=[
                "generate_text",
                "generate_image",
                "transcribe",
                "embed",
                "moderate"
            ]
        )

    def __init__(self, credentials: Dict[str, str]):
        self.client = OpenAI(api_key=credentials["api_key"])

    def validate_credentials(self, credentials: Dict[str, str]) -> bool:
        try:
            client = OpenAI(api_key=credentials["api_key"])
            # Make a minimal API call to verify
            client.models.list()
            return True
        except Exception:
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> ActionResult:
        try:
            if action == "generate_text":
                return self._generate_text(params)
            elif action == "generate_image":
                return self._generate_image(params)
            elif action == "transcribe":
                return self._transcribe(params)
            else:
                return ActionResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ActionResult(success=False, error=str(e))

    def _generate_text(self, params: Dict) -> ActionResult:
        response = self.client.chat.completions.create(
            model=params.get("model", "gpt-4"),
            messages=params["messages"],
            max_tokens=params.get("max_tokens", 1000)
        )
        return ActionResult(
            success=True,
            data=response.choices[0].message.content,
            metadata={
                "usage": response.usage.model_dump(),
                "model": response.model
            }
        )

    def _generate_image(self, params: Dict) -> ActionResult:
        response = self.client.images.generate(
            model=params.get("model", "dall-e-3"),
            prompt=params["prompt"],
            size=params.get("size", "1024x1024"),
            n=params.get("n", 1)
        )
        return ActionResult(
            success=True,
            data=[img.url for img in response.data]
        )

    def _transcribe(self, params: Dict) -> ActionResult:
        with open(params["file_path"], "rb") as f:
            response = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )
        return ActionResult(success=True, data=response.text)
```

## Example Connector: YouTube (OAuth)

```python
# src/integrations/social/youtube.py

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from ..base import BaseConnector, ConnectorInfo, AuthType, ActionResult

class YouTubeConnector(BaseConnector):
    """YouTube connector for uploading and analytics"""

    SCOPES = [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.readonly",
        "https://www.googleapis.com/auth/yt-analytics.readonly"
    ]

    @classmethod
    def info(cls) -> ConnectorInfo:
        return ConnectorInfo(
            id="youtube",
            name="YouTube",
            category="social",
            description="Upload videos and shorts, view analytics",
            auth_type=AuthType.OAUTH,
            auth_help="Connect your YouTube channel via Google",
            website="https://youtube.com",
            icon="📺",
            actions=[
                "upload_video",
                "upload_short",
                "get_analytics",
                "get_comments",
                "list_videos"
            ]
        )

    def __init__(self, credentials: Dict[str, str]):
        creds = Credentials(
            token=credentials["access_token"],
            refresh_token=credentials.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"]
        )
        self.youtube = build("youtube", "v3", credentials=creds)

    def execute(self, action: str, params: Dict[str, Any]) -> ActionResult:
        if action == "upload_video":
            return self._upload_video(params)
        elif action == "upload_short":
            return self._upload_short(params)
        # ... other actions

    def _upload_video(self, params: Dict) -> ActionResult:
        body = {
            "snippet": {
                "title": params["title"],
                "description": params.get("description", ""),
                "tags": params.get("tags", []),
                "categoryId": params.get("category_id", "22")
            },
            "status": {
                "privacyStatus": params.get("privacy", "private"),
                "selfDeclaredMadeForKids": False
            }
        }

        media = MediaFileUpload(
            params["file_path"],
            mimetype="video/*",
            resumable=True
        )

        request = self.youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        response = request.execute()

        return ActionResult(
            success=True,
            data={
                "video_id": response["id"],
                "url": f"https://youtube.com/watch?v={response['id']}"
            }
        )
```

---

## Credential Vault

Secure storage for credentials, encrypted at rest.

```python
# src/integrations/vault.py

from cryptography.fernet import Fernet
from pathlib import Path
import json
import os

class CredentialVault:
    """Secure credential storage"""

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.vault_path.mkdir(parents=True, exist_ok=True)
        self._key = self._get_or_create_key()
        self._fernet = Fernet(self._key)

    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key"""
        key_path = self.vault_path / ".key"
        if key_path.exists():
            return key_path.read_bytes()
        else:
            key = Fernet.generate_key()
            key_path.write_bytes(key)
            os.chmod(key_path, 0o600)  # Owner read/write only
            return key

    def store(self, connector_id: str, credentials: Dict[str, str]) -> None:
        """Store credentials for a connector"""
        encrypted = self._fernet.encrypt(json.dumps(credentials).encode())
        cred_path = self.vault_path / f"{connector_id}.enc"
        cred_path.write_bytes(encrypted)
        os.chmod(cred_path, 0o600)

    def retrieve(self, connector_id: str) -> Optional[Dict[str, str]]:
        """Retrieve credentials for a connector"""
        cred_path = self.vault_path / f"{connector_id}.enc"
        if not cred_path.exists():
            return None
        encrypted = cred_path.read_bytes()
        decrypted = self._fernet.decrypt(encrypted)
        return json.loads(decrypted)

    def delete(self, connector_id: str) -> bool:
        """Delete credentials for a connector"""
        cred_path = self.vault_path / f"{connector_id}.enc"
        if cred_path.exists():
            cred_path.unlink()
            return True
        return False

    def list_connected(self) -> List[str]:
        """List all connected services"""
        return [p.stem for p in self.vault_path.glob("*.enc")]
```

---

## Connector Registry

Discover and manage connectors.

```python
# src/integrations/registry.py

from typing import Dict, List, Type, Optional
from .base import BaseConnector, ConnectorInfo
from .vault import CredentialVault

class ConnectorRegistry:
    """Registry of available connectors"""

    def __init__(self, vault: CredentialVault):
        self._connectors: Dict[str, Type[BaseConnector]] = {}
        self._vault = vault
        self._instances: Dict[str, BaseConnector] = {}

    def register(self, connector_class: Type[BaseConnector]) -> None:
        """Register a connector"""
        info = connector_class.info()
        self._connectors[info.id] = connector_class

    def list_all(self) -> List[ConnectorInfo]:
        """List all available connectors"""
        return [cls.info() for cls in self._connectors.values()]

    def list_by_category(self, category: str) -> List[ConnectorInfo]:
        """List connectors in a category"""
        return [
            cls.info() for cls in self._connectors.values()
            if cls.info().category == category
        ]

    def list_connected(self) -> List[ConnectorInfo]:
        """List connectors with stored credentials"""
        connected_ids = self._vault.list_connected()
        return [
            cls.info() for cls in self._connectors.values()
            if cls.info().id in connected_ids
        ]

    def get(self, connector_id: str) -> Optional[BaseConnector]:
        """Get a connector instance (with credentials loaded)"""
        if connector_id in self._instances:
            return self._instances[connector_id]

        if connector_id not in self._connectors:
            return None

        credentials = self._vault.retrieve(connector_id)
        if not credentials:
            return None

        connector = self._connectors[connector_id](credentials)
        self._instances[connector_id] = connector
        return connector

    def connect(self, connector_id: str, credentials: Dict[str, str]) -> bool:
        """Connect a service with credentials"""
        if connector_id not in self._connectors:
            return False

        connector_class = self._connectors[connector_id]
        connector = connector_class(credentials)

        if not connector.validate_credentials(credentials):
            return False

        self._vault.store(connector_id, credentials)
        self._instances[connector_id] = connector
        return True

    def disconnect(self, connector_id: str) -> bool:
        """Disconnect a service"""
        if connector_id in self._instances:
            del self._instances[connector_id]
        return self._vault.delete(connector_id)
```

---

## CLI Commands

```bash
# List all available connectors
ai-corp integrations list
ai-corp integrations list --category ai
ai-corp integrations list --connected

# Connect a service
ai-corp connect openai
ai-corp connect youtube

# Disconnect a service
ai-corp disconnect openai

# Test a connection
ai-corp integrations test openai

# Execute an action
ai-corp integrations run openai generate_text --prompt "Hello"
```

**Example Output:**

```
$ ai-corp integrations list

🤖 AI SERVICES
  ├─ ✓ openai        OpenAI (GPT-4, DALL-E, Whisper)
  ├─ ✗ anthropic     Anthropic (Claude)
  ├─ ✗ elevenlabs    ElevenLabs (Voice generation)
  └─ ✗ replicate     Replicate (Run any model)

📺 VIDEO GENERATION
  ├─ ✗ heygen        HeyGen (Avatar videos)
  ├─ ✗ runway        Runway (AI video generation)
  └─ ✗ synthesia     Synthesia (Avatar videos)

📱 SOCIAL PLATFORMS
  ├─ ✓ youtube       YouTube (Upload, analytics)
  ├─ ✗ instagram     Instagram (Posts, reels)
  ├─ ✗ tiktok        TikTok (Upload, analytics)
  └─ ✗ twitter       Twitter/X (Posts, threads)

💾 STORAGE
  ├─ ✓ gdrive        Google Drive (Files)
  └─ ✗ cloudinary    Cloudinary (Media)

✓ = Connected    ✗ = Not connected
```

---

## Molecule Integration

Use connectors in molecule steps:

```yaml
# Example molecule using integrations
molecule:
  id: MOL-content-001
  name: "Create and Post Video"

  steps:
    - id: generate_script
      name: "Generate Script"
      type: integration
      connector: openai
      action: generate_text
      params:
        model: gpt-4
        messages:
          - role: system
            content: "You are a viral content writer"
          - role: user
            content: "Write a 60 second script about {{topic}}"
      output_as: script

    - id: generate_video
      name: "Create Avatar Video"
      type: integration
      connector: heygen
      action: create_avatar_video
      params:
        avatar_id: "{{avatar}}"
        script: "{{steps.generate_script.output}}"
      depends_on: [generate_script]
      output_as: video_url

    - id: upload
      name: "Upload to YouTube"
      type: integration
      connector: youtube
      action: upload_short
      params:
        file_url: "{{steps.generate_video.output}}"
        title: "{{title}}"
        description: "{{description}}"
      depends_on: [generate_video]
      gate: publish_review  # Human approves before upload
```

---

## Priority Connectors (Phase 1)

Start with the most valuable connectors:

| Priority | Connector | Why |
|----------|-----------|-----|
| P1 | **OpenAI** | Core AI generation |
| P1 | **Anthropic** | Claude for agents |
| P1 | **YouTube** | Primary publishing |
| P1 | **Cloudinary** | Media storage |
| P1 | **Telegram** | Notifications |
| P2 | Instagram | Social reach |
| P2 | TikTok | Social reach |
| P2 | HeyGen | Avatar videos |
| P2 | ElevenLabs | Voice generation |
| P3 | Twitter/X | Social |
| P3 | LinkedIn | Professional |
| P3 | Airtable | Data |
| P3 | Others | As needed |

---

## Content Factory Preset

```yaml
# presets/content-factory/manifest.yaml
preset:
  id: content-factory
  name: "AI Content Factory"
  description: "Automated content creation and publishing"

  required_integrations:
    - openai       # Content generation
    - cloudinary   # Media storage

  optional_integrations:
    - youtube      # Publishing
    - instagram    # Publishing
    - tiktok       # Publishing
    - heygen       # Avatar videos
    - elevenlabs   # Voice generation
    - telegram     # Notifications

  departments:
    - content_creation
    - publishing
    - analytics

  molecule_templates:
    - viral-clone
    - text-to-video
    - image-carousel
    - podcast-to-clips
```

---

## Security Considerations

1. **Encryption at rest** - All credentials encrypted with Fernet
2. **Key isolation** - Encryption key stored separately, owner-only permissions
3. **No logging** - Credentials never written to logs
4. **Token refresh** - OAuth tokens auto-refreshed
5. **Scope limiting** - Request minimum necessary OAuth scopes
6. **Revocation** - Easy disconnect removes all stored credentials

---

## Implementation Phases

| Phase | Focus | Deliverables |
|-------|-------|-------------|
| 1 | Foundation | BaseConnector, Registry, Vault, CLI |
| 2 | Core AI | OpenAI, Anthropic connectors |
| 3 | Publishing | YouTube, Cloudinary |
| 4 | Notifications | Telegram, Discord |
| 5 | Social | Instagram, TikTok, Twitter |
| 6 | Video Gen | HeyGen, ElevenLabs |
| 7 | Personal | Gmail, Calendar |

---

## Related Documents

- [PLATFORM_ARCHITECTURE.md](./PLATFORM_ARCHITECTURE.md) - Core Services handles auth
- [LEARNING_SYSTEM_DESIGN.md](./LEARNING_SYSTEM_DESIGN.md) - Learn from integration usage
- [BUSINESS_MODEL.md](./BUSINESS_MODEL.md) - Connectors as premium features?
