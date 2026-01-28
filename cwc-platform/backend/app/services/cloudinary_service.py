"""
Cloudinary service for video testimonial uploads.
Handles video uploads, transformations, and deletion.
"""
import logging
from typing import Optional, Dict, Any
import cloudinary
import cloudinary.uploader
import cloudinary.api
from app.config import get_settings

logger = logging.getLogger(__name__)


class CloudinaryService:
    """
    Service for managing video uploads to Cloudinary.

    Uses Cloudinary when credentials are provided, otherwise operates in stub mode.
    """

    def __init__(self):
        settings = get_settings()
        self.cloud_name = settings.cloudinary_cloud_name
        self.api_key = settings.cloudinary_api_key
        self.api_secret = settings.cloudinary_api_secret
        self.is_configured = bool(self.cloud_name and self.api_key and self.api_secret)

        if self.is_configured:
            cloudinary.config(
                cloud_name=self.cloud_name,
                api_key=self.api_key,
                api_secret=self.api_secret,
                secure=True
            )
            logger.info("Cloudinary service initialized")
        else:
            logger.info("Cloudinary service running in stub mode (no credentials)")

    def upload_video(
        self,
        file_data: bytes,
        filename: str,
        folder: str = "testimonials",
    ) -> Dict[str, Any]:
        """
        Upload a video to Cloudinary.

        Args:
            file_data: Video file bytes
            filename: Original filename
            folder: Cloudinary folder to upload to

        Returns:
            Dict with url, public_id, duration, thumbnail_url
        """
        if not self.is_configured:
            logger.info(f"STUB: Would upload video {filename} to Cloudinary")
            return {
                "url": f"https://stub.cloudinary.com/{folder}/{filename}",
                "public_id": f"{folder}/stub_{filename}",
                "duration": 60,
                "thumbnail_url": f"https://stub.cloudinary.com/{folder}/{filename}.jpg",
                "format": "mp4",
                "width": 1280,
                "height": 720,
            }

        try:
            result = cloudinary.uploader.upload(
                file_data,
                resource_type="video",
                folder=folder,
                eager=[
                    # Generate thumbnail at 1 second
                    {"format": "jpg", "start_offset": "1"},
                ],
                eager_async=False,
                # Video optimizations
                quality="auto",
                fetch_format="auto",
            )

            # Extract thumbnail URL from eager transformations
            thumbnail_url = None
            if result.get("eager") and len(result["eager"]) > 0:
                thumbnail_url = result["eager"][0].get("secure_url")

            return {
                "url": result.get("secure_url"),
                "public_id": result.get("public_id"),
                "duration": int(result.get("duration", 0)),
                "thumbnail_url": thumbnail_url,
                "format": result.get("format"),
                "width": result.get("width"),
                "height": result.get("height"),
            }
        except Exception as e:
            logger.error(f"Failed to upload video to Cloudinary: {e}")
            raise

    def delete_video(self, public_id: str) -> bool:
        """
        Delete a video from Cloudinary.

        Args:
            public_id: The Cloudinary public ID of the video

        Returns:
            True if deleted successfully
        """
        if not self.is_configured:
            logger.info(f"STUB: Would delete video {public_id} from Cloudinary")
            return True

        try:
            result = cloudinary.uploader.destroy(public_id, resource_type="video")
            return result.get("result") == "ok"
        except Exception as e:
            logger.error(f"Failed to delete video from Cloudinary: {e}")
            return False

    def get_video_url(
        self,
        public_id: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        quality: str = "auto",
    ) -> str:
        """
        Get an optimized video URL with transformations.

        Args:
            public_id: The Cloudinary public ID
            width: Optional width resize
            height: Optional height resize
            quality: Quality setting (auto, best, good, eco, low)

        Returns:
            Transformed video URL
        """
        if not self.is_configured:
            return f"https://stub.cloudinary.com/{public_id}"

        transformations = [{"quality": quality}]

        if width or height:
            resize = {"crop": "limit"}
            if width:
                resize["width"] = width
            if height:
                resize["height"] = height
            transformations.insert(0, resize)

        url, _ = cloudinary.utils.cloudinary_url(
            public_id,
            resource_type="video",
            transformation=transformations,
            secure=True,
        )
        return url

    def get_thumbnail_url(
        self,
        public_id: str,
        width: int = 400,
        height: int = 225,
        start_offset: str = "1",
    ) -> str:
        """
        Get a thumbnail image URL for a video.

        Args:
            public_id: The Cloudinary public ID of the video
            width: Thumbnail width
            height: Thumbnail height
            start_offset: Time offset in seconds for the thumbnail frame

        Returns:
            Thumbnail image URL
        """
        if not self.is_configured:
            return f"https://stub.cloudinary.com/{public_id}.jpg"

        url, _ = cloudinary.utils.cloudinary_url(
            public_id,
            resource_type="video",
            format="jpg",
            transformation=[
                {"width": width, "height": height, "crop": "fill"},
                {"start_offset": start_offset},
            ],
            secure=True,
        )
        return url

    def generate_upload_signature(
        self,
        folder: str = "testimonials",
        max_file_size: int = 104857600,  # 100MB
    ) -> Dict[str, Any]:
        """
        Generate a signed upload preset for direct browser uploads.

        Args:
            folder: Cloudinary folder
            max_file_size: Maximum file size in bytes

        Returns:
            Dict with signature, timestamp, and upload parameters
        """
        if not self.is_configured:
            return {
                "signature": "stub_signature",
                "timestamp": 0,
                "cloud_name": "stub",
                "api_key": "stub",
                "folder": folder,
            }

        import time
        timestamp = int(time.time())

        params = {
            "folder": folder,
            "timestamp": timestamp,
            "resource_type": "video",
        }

        signature = cloudinary.utils.api_sign_request(params, self.api_secret)

        return {
            "signature": signature,
            "timestamp": timestamp,
            "cloud_name": self.cloud_name,
            "api_key": self.api_key,
            "folder": folder,
        }


# Singleton instance for easy access
cloudinary_service = CloudinaryService()
