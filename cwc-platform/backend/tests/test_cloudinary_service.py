"""
Tests for Cloudinary service.
"""
import pytest
from unittest.mock import patch, MagicMock
from app.services.cloudinary_service import CloudinaryService


class TestCloudinaryServiceStubMode:
    """Tests for Cloudinary service in stub mode (no credentials)."""

    @pytest.fixture
    def stub_service(self):
        """Create a service in stub mode."""
        with patch("app.services.cloudinary_service.get_settings") as mock_settings:
            mock_settings.return_value.cloudinary_cloud_name = None
            mock_settings.return_value.cloudinary_api_key = None
            mock_settings.return_value.cloudinary_api_secret = None
            service = CloudinaryService()
            assert not service.is_configured
            return service

    def test_stub_mode_not_configured(self, stub_service):
        """Test service correctly identifies stub mode."""
        assert not stub_service.is_configured

    def test_upload_video_stub(self, stub_service):
        """Test video upload in stub mode returns mock data."""
        result = stub_service.upload_video(
            file_data=b"fake video data",
            filename="test.mp4",
            folder="testimonials",
        )
        assert "stub.cloudinary.com" in result["url"]
        assert result["duration"] == 60
        assert "thumbnail_url" in result

    def test_delete_video_stub(self, stub_service):
        """Test video deletion in stub mode returns True."""
        result = stub_service.delete_video("testimonials/test123")
        assert result is True

    def test_get_video_url_stub(self, stub_service):
        """Test get video URL in stub mode."""
        url = stub_service.get_video_url("testimonials/test123")
        assert "stub.cloudinary.com" in url

    def test_get_video_url_with_dimensions_stub(self, stub_service):
        """Test get video URL with dimensions in stub mode."""
        url = stub_service.get_video_url(
            "testimonials/test123",
            width=640,
            height=480,
        )
        assert "stub.cloudinary.com" in url

    def test_get_thumbnail_url_stub(self, stub_service):
        """Test thumbnail URL in stub mode."""
        url = stub_service.get_thumbnail_url("testimonials/test123")
        assert "stub.cloudinary.com" in url
        assert ".jpg" in url

    def test_generate_upload_signature_stub(self, stub_service):
        """Test upload signature in stub mode."""
        result = stub_service.generate_upload_signature()
        assert result["signature"] == "stub_signature"
        assert result["cloud_name"] == "stub"


class TestCloudinaryServiceConfigured:
    """Tests for Cloudinary service with credentials configured."""

    @pytest.fixture
    def configured_service(self):
        """Create a service with credentials."""
        with patch("app.services.cloudinary_service.get_settings") as mock_settings:
            mock_settings.return_value.cloudinary_cloud_name = "test-cloud"
            mock_settings.return_value.cloudinary_api_key = "test-key"
            mock_settings.return_value.cloudinary_api_secret = "test-secret"
            with patch("app.services.cloudinary_service.cloudinary"):
                service = CloudinaryService()
                assert service.is_configured
                return service

    def test_configured_mode(self, configured_service):
        """Test service correctly identifies configured mode."""
        assert configured_service.is_configured
        assert configured_service.cloud_name == "test-cloud"

    @patch("cloudinary.uploader.upload")
    def test_upload_video_success(self, mock_upload, configured_service):
        """Test successful video upload."""
        mock_upload.return_value = {
            "secure_url": "https://cloudinary.com/video.mp4",
            "public_id": "testimonials/video123",
            "duration": 45.5,
            "format": "mp4",
            "width": 1920,
            "height": 1080,
            "eager": [{"secure_url": "https://cloudinary.com/thumb.jpg"}],
        }

        result = configured_service.upload_video(
            file_data=b"video data",
            filename="test.mp4",
        )

        assert result["url"] == "https://cloudinary.com/video.mp4"
        assert result["duration"] == 45
        assert result["thumbnail_url"] == "https://cloudinary.com/thumb.jpg"

    @patch("cloudinary.uploader.upload")
    def test_upload_video_no_thumbnail(self, mock_upload, configured_service):
        """Test upload when no thumbnail generated."""
        mock_upload.return_value = {
            "secure_url": "https://cloudinary.com/video.mp4",
            "public_id": "testimonials/video123",
            "duration": 30,
            "eager": [],
        }

        result = configured_service.upload_video(
            file_data=b"video data",
            filename="test.mp4",
        )

        assert result["thumbnail_url"] is None

    @patch("cloudinary.uploader.upload")
    def test_upload_video_error(self, mock_upload, configured_service):
        """Test upload error handling."""
        mock_upload.side_effect = Exception("Upload failed")

        with pytest.raises(Exception, match="Upload failed"):
            configured_service.upload_video(
                file_data=b"video data",
                filename="test.mp4",
            )

    @patch("cloudinary.uploader.destroy")
    def test_delete_video_success(self, mock_destroy, configured_service):
        """Test successful video deletion."""
        mock_destroy.return_value = {"result": "ok"}

        result = configured_service.delete_video("testimonials/video123")

        assert result is True
        mock_destroy.assert_called_once_with(
            "testimonials/video123",
            resource_type="video",
        )

    @patch("cloudinary.uploader.destroy")
    def test_delete_video_not_found(self, mock_destroy, configured_service):
        """Test deletion of non-existent video."""
        mock_destroy.return_value = {"result": "not found"}

        result = configured_service.delete_video("testimonials/nonexistent")

        assert result is False

    @patch("cloudinary.uploader.destroy")
    def test_delete_video_error(self, mock_destroy, configured_service):
        """Test deletion error handling."""
        mock_destroy.side_effect = Exception("Delete failed")

        result = configured_service.delete_video("testimonials/video123")

        assert result is False

    @patch("cloudinary.utils.cloudinary_url")
    def test_get_video_url(self, mock_url, configured_service):
        """Test getting video URL."""
        mock_url.return_value = ("https://cloudinary.com/video.mp4", {})

        url = configured_service.get_video_url("testimonials/video123")

        assert url == "https://cloudinary.com/video.mp4"

    @patch("cloudinary.utils.cloudinary_url")
    def test_get_video_url_with_dimensions(self, mock_url, configured_service):
        """Test getting video URL with resize."""
        mock_url.return_value = ("https://cloudinary.com/video_640x480.mp4", {})

        url = configured_service.get_video_url(
            "testimonials/video123",
            width=640,
            height=480,
        )

        assert "640x480" in url

    @patch("cloudinary.utils.cloudinary_url")
    def test_get_thumbnail_url(self, mock_url, configured_service):
        """Test getting thumbnail URL."""
        mock_url.return_value = ("https://cloudinary.com/thumb.jpg", {})

        url = configured_service.get_thumbnail_url(
            "testimonials/video123",
            width=400,
            height=225,
        )

        assert url == "https://cloudinary.com/thumb.jpg"

    @patch("cloudinary.utils.api_sign_request")
    def test_generate_upload_signature(self, mock_sign, configured_service):
        """Test generating upload signature."""
        mock_sign.return_value = "generated_signature"

        result = configured_service.generate_upload_signature(
            folder="custom_folder",
        )

        assert result["signature"] == "generated_signature"
        assert result["cloud_name"] == "test-cloud"
        assert result["folder"] == "custom_folder"
        assert "timestamp" in result
