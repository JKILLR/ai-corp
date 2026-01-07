"""
YouTube Connector - Upload videos, manage channel, view analytics.

Supports:
- Video and Shorts upload
- Analytics retrieval
- Comment management
- Playlist management
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


class YouTubeConnector(BaseConnector):
    """
    YouTube connector for video upload and management.

    Requires OAuth credentials with appropriate scopes.

    Actions:
    - upload_video: Upload a video to YouTube
    - upload_short: Upload a YouTube Short
    - get_analytics: Get channel analytics
    - get_comments: Get comments on a video
    - list_videos: List channel videos
    - create_playlist: Create a new playlist
    """

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
            category=ConnectorCategory.SOCIAL,
            description="Upload videos and shorts, view analytics",
            auth_type=AuthType.OAUTH,
            auth_help="Connect your YouTube channel via Google OAuth",
            website="https://youtube.com",
            icon="📺",
            actions=[
                "upload_video",
                "upload_short",
                "get_analytics",
                "get_comments",
                "list_videos",
                "create_playlist",
                "get_channel_info"
            ],
            required_credentials=["access_token", "refresh_token", "client_id", "client_secret"],
            optional_credentials=["channel_id"]
        )

    def __init__(self, credentials: Dict[str, str]):
        super().__init__(credentials)
        self._youtube = None
        self._analytics = None

    def _get_youtube_client(self):
        """Lazy-load YouTube API client."""
        if self._youtube is None:
            try:
                from google.oauth2.credentials import Credentials
                from googleapiclient.discovery import build

                creds = Credentials(
                    token=self._credentials["access_token"],
                    refresh_token=self._credentials.get("refresh_token"),
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=self._credentials["client_id"],
                    client_secret=self._credentials["client_secret"]
                )
                self._youtube = build("youtube", "v3", credentials=creds)
            except ImportError:
                raise ImportError(
                    "google-api-python-client required: "
                    "pip install google-api-python-client google-auth"
                )
        return self._youtube

    def _get_analytics_client(self):
        """Lazy-load YouTube Analytics API client."""
        if self._analytics is None:
            try:
                from google.oauth2.credentials import Credentials
                from googleapiclient.discovery import build

                creds = Credentials(
                    token=self._credentials["access_token"],
                    refresh_token=self._credentials.get("refresh_token"),
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=self._credentials["client_id"],
                    client_secret=self._credentials["client_secret"]
                )
                self._analytics = build("youtubeAnalytics", "v2", credentials=creds)
            except ImportError:
                raise ImportError(
                    "google-api-python-client required: "
                    "pip install google-api-python-client google-auth"
                )
        return self._analytics

    def validate_credentials(self) -> bool:
        """Validate by getting channel info."""
        try:
            youtube = self._get_youtube_client()
            response = youtube.channels().list(
                part="snippet",
                mine=True
            ).execute()
            return len(response.get("items", [])) > 0
        except Exception as e:
            logger.error(f"YouTube credential validation failed: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> ActionResult:
        """Execute a YouTube action."""
        try:
            if action == "upload_video":
                return self._upload_video(params, is_short=False)
            elif action == "upload_short":
                return self._upload_video(params, is_short=True)
            elif action == "get_analytics":
                return self._get_analytics(params)
            elif action == "get_comments":
                return self._get_comments(params)
            elif action == "list_videos":
                return self._list_videos(params)
            elif action == "create_playlist":
                return self._create_playlist(params)
            elif action == "get_channel_info":
                return self._get_channel_info()
            else:
                return ActionResult(success=False, error=f"Unknown action: {action}")
        except ImportError as e:
            return ActionResult(success=False, error=str(e))
        except Exception as e:
            logger.error(f"YouTube action failed: {e}")
            return ActionResult(success=False, error=str(e))

    def _upload_video(self, params: Dict, is_short: bool = False) -> ActionResult:
        """Upload a video to YouTube."""
        from googleapiclient.http import MediaFileUpload

        youtube = self._get_youtube_client()

        # Build request body
        body = {
            "snippet": {
                "title": params["title"],
                "description": params.get("description", ""),
                "tags": params.get("tags", []),
                "categoryId": params.get("category_id", "22")  # 22 = People & Blogs
            },
            "status": {
                "privacyStatus": params.get("privacy", "private"),
                "selfDeclaredMadeForKids": params.get("made_for_kids", False)
            }
        }

        # For Shorts, add to Shorts shelf
        if is_short:
            body["snippet"]["description"] = "#Shorts " + body["snippet"].get("description", "")

        # Upload file
        media = MediaFileUpload(
            params["file_path"],
            mimetype="video/*",
            resumable=True,
            chunksize=1024 * 1024  # 1MB chunks
        )

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        response = request.execute()

        return ActionResult(
            success=True,
            data={
                "video_id": response["id"],
                "url": f"https://youtube.com/watch?v={response['id']}",
                "title": response["snippet"]["title"]
            },
            metadata={
                "upload_status": response.get("status", {}).get("uploadStatus")
            }
        )

    def _get_analytics(self, params: Dict) -> ActionResult:
        """Get channel analytics."""
        analytics = self._get_analytics_client()

        response = analytics.reports().query(
            ids="channel==MINE",
            startDate=params.get("start_date", "2020-01-01"),
            endDate=params.get("end_date", "2099-12-31"),
            metrics=params.get("metrics", "views,likes,subscribersGained"),
            dimensions=params.get("dimensions", "day"),
            sort=params.get("sort", "-views"),
            maxResults=params.get("max_results", 100)
        ).execute()

        return ActionResult(
            success=True,
            data={
                "column_headers": response.get("columnHeaders", []),
                "rows": response.get("rows", [])
            }
        )

    def _get_comments(self, params: Dict) -> ActionResult:
        """Get comments on a video."""
        youtube = self._get_youtube_client()

        response = youtube.commentThreads().list(
            part="snippet,replies",
            videoId=params["video_id"],
            maxResults=params.get("max_results", 50),
            order=params.get("order", "relevance")
        ).execute()

        comments = []
        for item in response.get("items", []):
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "id": item["id"],
                "author": snippet["authorDisplayName"],
                "text": snippet["textDisplay"],
                "likes": snippet["likeCount"],
                "published_at": snippet["publishedAt"],
                "reply_count": item["snippet"]["totalReplyCount"]
            })

        return ActionResult(
            success=True,
            data=comments,
            metadata={
                "total_results": response.get("pageInfo", {}).get("totalResults"),
                "next_page_token": response.get("nextPageToken")
            }
        )

    def _list_videos(self, params: Dict) -> ActionResult:
        """List channel videos."""
        youtube = self._get_youtube_client()

        response = youtube.search().list(
            part="snippet",
            forMine=True,
            type="video",
            maxResults=params.get("max_results", 25),
            order=params.get("order", "date")
        ).execute()

        videos = []
        for item in response.get("items", []):
            videos.append({
                "video_id": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "description": item["snippet"]["description"],
                "published_at": item["snippet"]["publishedAt"],
                "thumbnail": item["snippet"]["thumbnails"]["default"]["url"]
            })

        return ActionResult(
            success=True,
            data=videos,
            metadata={
                "total_results": response.get("pageInfo", {}).get("totalResults"),
                "next_page_token": response.get("nextPageToken")
            }
        )

    def _create_playlist(self, params: Dict) -> ActionResult:
        """Create a new playlist."""
        youtube = self._get_youtube_client()

        response = youtube.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": params["title"],
                    "description": params.get("description", "")
                },
                "status": {
                    "privacyStatus": params.get("privacy", "private")
                }
            }
        ).execute()

        return ActionResult(
            success=True,
            data={
                "playlist_id": response["id"],
                "title": response["snippet"]["title"],
                "url": f"https://youtube.com/playlist?list={response['id']}"
            }
        )

    def _get_channel_info(self) -> ActionResult:
        """Get channel information."""
        youtube = self._get_youtube_client()

        response = youtube.channels().list(
            part="snippet,statistics",
            mine=True
        ).execute()

        if not response.get("items"):
            return ActionResult(success=False, error="No channel found")

        channel = response["items"][0]
        return ActionResult(
            success=True,
            data={
                "channel_id": channel["id"],
                "title": channel["snippet"]["title"],
                "description": channel["snippet"]["description"],
                "subscriber_count": channel["statistics"]["subscriberCount"],
                "video_count": channel["statistics"]["videoCount"],
                "view_count": channel["statistics"]["viewCount"],
                "thumbnail": channel["snippet"]["thumbnails"]["default"]["url"]
            }
        )

    def get_action_definitions(self) -> List[ActionDefinition]:
        """Return detailed action definitions."""
        return [
            ActionDefinition(
                id="upload_video",
                name="Upload Video",
                description="Upload a video to YouTube",
                params=[
                    ActionParam("file_path", "file", "Path to video file", required=True),
                    ActionParam("title", "string", "Video title", required=True),
                    ActionParam("description", "string", "Video description", required=False),
                    ActionParam("tags", "array", "Video tags", required=False),
                    ActionParam("privacy", "string", "Privacy setting", required=False, default="private",
                              options=["public", "private", "unlisted"]),
                ],
                returns="Video ID and URL"
            ),
            ActionDefinition(
                id="upload_short",
                name="Upload Short",
                description="Upload a YouTube Short (vertical video < 60s)",
                params=[
                    ActionParam("file_path", "file", "Path to video file", required=True),
                    ActionParam("title", "string", "Short title", required=True),
                    ActionParam("description", "string", "Short description", required=False),
                ],
                returns="Video ID and URL"
            ),
            ActionDefinition(
                id="get_analytics",
                name="Get Analytics",
                description="Get channel analytics data",
                params=[
                    ActionParam("start_date", "string", "Start date (YYYY-MM-DD)", required=False),
                    ActionParam("end_date", "string", "End date (YYYY-MM-DD)", required=False),
                    ActionParam("metrics", "string", "Metrics to retrieve", required=False,
                              default="views,likes,subscribersGained"),
                ],
                returns="Analytics data with rows and columns"
            ),
        ]
