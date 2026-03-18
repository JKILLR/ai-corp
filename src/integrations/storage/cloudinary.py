"""
Cloudinary Connector - Media storage, transformation, and delivery.

Supports:
- Image/video upload
- On-the-fly transformations
- Asset management
- Delivery optimization
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


class CloudinaryConnector(BaseConnector):
    """
    Cloudinary connector for media management.

    Actions:
    - upload: Upload an image or video
    - transform: Get transformed URL for an asset
    - delete: Delete an asset
    - list_assets: List assets in account
    - get_asset: Get asset details
    """

    @classmethod
    def info(cls) -> ConnectorInfo:
        return ConnectorInfo(
            id="cloudinary",
            name="Cloudinary",
            category=ConnectorCategory.STORAGE,
            description="Media storage, transformation, and delivery",
            auth_type=AuthType.API_KEY,
            auth_help="Get credentials from Cloudinary Dashboard → Settings → API Keys",
            website="https://cloudinary.com",
            icon="☁️",
            actions=[
                "upload",
                "transform",
                "delete",
                "list_assets",
                "get_asset",
                "create_folder"
            ],
            required_credentials=["cloud_name", "api_key", "api_secret"]
        )

    def __init__(self, credentials: Dict[str, str]):
        super().__init__(credentials)
        self._configured = False

    def _configure(self):
        """Configure Cloudinary SDK."""
        if not self._configured:
            try:
                import cloudinary
                cloudinary.config(
                    cloud_name=self._credentials["cloud_name"],
                    api_key=self._credentials["api_key"],
                    api_secret=self._credentials["api_secret"],
                    secure=True
                )
                self._configured = True
            except ImportError:
                raise ImportError("cloudinary package required: pip install cloudinary")

    def validate_credentials(self) -> bool:
        """Validate by getting account usage."""
        try:
            self._configure()
            import cloudinary.api
            cloudinary.api.usage()
            return True
        except Exception as e:
            logger.error(f"Cloudinary credential validation failed: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> ActionResult:
        """Execute a Cloudinary action."""
        try:
            self._configure()

            if action == "upload":
                return self._upload(params)
            elif action == "transform":
                return self._transform(params)
            elif action == "delete":
                return self._delete(params)
            elif action == "list_assets":
                return self._list_assets(params)
            elif action == "get_asset":
                return self._get_asset(params)
            elif action == "create_folder":
                return self._create_folder(params)
            else:
                return ActionResult(success=False, error=f"Unknown action: {action}")
        except ImportError as e:
            return ActionResult(success=False, error=str(e))
        except Exception as e:
            logger.error(f"Cloudinary action failed: {e}")
            return ActionResult(success=False, error=str(e))

    def _upload(self, params: Dict) -> ActionResult:
        """Upload a file to Cloudinary."""
        import cloudinary.uploader

        # Determine resource type
        file_path = params.get("file_path") or params.get("url")
        resource_type = params.get("resource_type", "auto")

        upload_params = {
            "resource_type": resource_type,
            "folder": params.get("folder"),
            "public_id": params.get("public_id"),
            "overwrite": params.get("overwrite", True),
            "tags": params.get("tags", []),
        }

        # Add transformation if specified
        if params.get("transformation"):
            upload_params["transformation"] = params["transformation"]

        # Remove None values
        upload_params = {k: v for k, v in upload_params.items() if v is not None}

        result = cloudinary.uploader.upload(file_path, **upload_params)

        return ActionResult(
            success=True,
            data={
                "public_id": result["public_id"],
                "url": result["secure_url"],
                "resource_type": result["resource_type"],
                "format": result["format"],
                "width": result.get("width"),
                "height": result.get("height"),
                "bytes": result["bytes"]
            },
            metadata={
                "asset_id": result["asset_id"],
                "version": result["version"]
            }
        )

    def _transform(self, params: Dict) -> ActionResult:
        """Get a transformed URL for an asset."""
        import cloudinary

        public_id = params["public_id"]
        transformation = params.get("transformation", {})
        resource_type = params.get("resource_type", "image")

        # Build transformation
        url = cloudinary.CloudinaryImage(public_id).build_url(
            transformation=transformation,
            resource_type=resource_type,
            secure=True
        )

        return ActionResult(
            success=True,
            data={"url": url}
        )

    def _delete(self, params: Dict) -> ActionResult:
        """Delete an asset."""
        import cloudinary.uploader

        result = cloudinary.uploader.destroy(
            params["public_id"],
            resource_type=params.get("resource_type", "image")
        )

        return ActionResult(
            success=result["result"] == "ok",
            data={"result": result["result"]}
        )

    def _list_assets(self, params: Dict) -> ActionResult:
        """List assets in account."""
        import cloudinary.api

        result = cloudinary.api.resources(
            type=params.get("type", "upload"),
            resource_type=params.get("resource_type", "image"),
            prefix=params.get("prefix"),
            max_results=params.get("max_results", 50),
            next_cursor=params.get("next_cursor")
        )

        assets = []
        for resource in result.get("resources", []):
            assets.append({
                "public_id": resource["public_id"],
                "url": resource["secure_url"],
                "format": resource["format"],
                "resource_type": resource["resource_type"],
                "created_at": resource["created_at"],
                "bytes": resource["bytes"]
            })

        return ActionResult(
            success=True,
            data=assets,
            metadata={
                "next_cursor": result.get("next_cursor"),
                "rate_limit_remaining": result.get("rate_limit_remaining")
            }
        )

    def _get_asset(self, params: Dict) -> ActionResult:
        """Get details for a specific asset."""
        import cloudinary.api

        result = cloudinary.api.resource(
            params["public_id"],
            resource_type=params.get("resource_type", "image")
        )

        return ActionResult(
            success=True,
            data={
                "public_id": result["public_id"],
                "url": result["secure_url"],
                "format": result["format"],
                "resource_type": result["resource_type"],
                "created_at": result["created_at"],
                "bytes": result["bytes"],
                "width": result.get("width"),
                "height": result.get("height"),
                "tags": result.get("tags", []),
                "metadata": result.get("metadata", {})
            }
        )

    def _create_folder(self, params: Dict) -> ActionResult:
        """Create a folder."""
        import cloudinary.api

        result = cloudinary.api.create_folder(params["folder_path"])

        return ActionResult(
            success=result.get("success", False),
            data={"path": result.get("path")}
        )

    def get_action_definitions(self) -> List[ActionDefinition]:
        """Return detailed action definitions."""
        return [
            ActionDefinition(
                id="upload",
                name="Upload",
                description="Upload an image or video to Cloudinary",
                params=[
                    ActionParam("file_path", "file", "Path to local file", required=False),
                    ActionParam("url", "string", "URL of file to upload", required=False),
                    ActionParam("folder", "string", "Destination folder", required=False),
                    ActionParam("public_id", "string", "Custom public ID", required=False),
                    ActionParam("resource_type", "string", "Type of resource", required=False, default="auto",
                              options=["auto", "image", "video", "raw"]),
                    ActionParam("tags", "array", "Tags for the asset", required=False),
                ],
                returns="Upload result with URL and metadata"
            ),
            ActionDefinition(
                id="transform",
                name="Transform",
                description="Get a transformed URL for an asset",
                params=[
                    ActionParam("public_id", "string", "Asset public ID", required=True),
                    ActionParam("transformation", "object", "Transformation options", required=False),
                    ActionParam("resource_type", "string", "Type of resource", required=False, default="image"),
                ],
                returns="Transformed URL",
                example={
                    "public_id": "sample",
                    "transformation": {"width": 300, "height": 300, "crop": "fill"}
                }
            ),
            ActionDefinition(
                id="delete",
                name="Delete",
                description="Delete an asset from Cloudinary",
                params=[
                    ActionParam("public_id", "string", "Asset public ID", required=True),
                    ActionParam("resource_type", "string", "Type of resource", required=False, default="image"),
                ],
                returns="Deletion result"
            ),
        ]
