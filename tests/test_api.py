"""
Tests for the FastAPI endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
from ..api.main import app
from ..validation import ValidationResult

# Create test client
client = TestClient(app)

# Mock data
MOCK_USER_ID = "test123"
MOCK_CONTENT = {
    "bio": {
        "name": "Test User",
        "summary": "Test summary"
    },
    "images": {
        "profile": {"url": "https://example.com/profile.jpg"},
        "background": {"url": "https://example.com/bg.jpg"}
    },
    "story_chunks": [
        {
            "title": "Test Story",
            "content": "Test content",
            "order_index": 0
        }
    ],
    "values": [
        {
            "title": "Test Value",
            "description": "Test description",
            "order_index": 0
        }
    ],
    "social_links": [
        {
            "platform": "twitter",
            "url": "https://twitter.com/test"
        }
    ]
}

@pytest.fixture
def mock_content_fetcher():
    """Mock content fetcher for testing."""
    with patch("app_8_website_builder.api.app8_routes.ContentFetcher") as mock:
        fetcher = AsyncMock()
        fetcher.fetch_all_content.return_value = MOCK_CONTENT
        mock.return_value = fetcher
        yield mock

@pytest.fixture
def mock_site_builder():
    """Mock site builder for testing."""
    with patch("app_8_website_builder.api.app8_routes.SiteBuilder") as mock:
        builder = MagicMock()
        builder.build_site.return_value = Path("/tmp/test_site")
        mock.return_value = builder
        yield mock

@pytest.fixture
def mock_publisher():
    """Mock publisher for testing."""
    with patch("app_8_website_builder.api.app8_routes.Publisher") as mock:
        publisher = AsyncMock()
        publisher.publish_production.return_value = "https://example.com/site"
        publisher.publish_preview.return_value = "https://preview.example.com/site"
        mock.return_value = publisher
        yield mock

@pytest.fixture
def mock_validation():
    """Mock content validation for testing."""
    with patch("app_8_website_builder.api.app8_routes.validate_content") as mock:
        mock.return_value = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[]
        )
        yield mock

@pytest.mark.asyncio
async def test_build_site_success(
    mock_content_fetcher,
    mock_site_builder,
    mock_publisher,
    mock_validation
):
    """Test successful site build."""
    # Test production build
    response = client.post("/app8/build-site", json={
        "user_id": MOCK_USER_ID,
        "preview": False
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["url"] == "https://example.com/site"
    assert data["build_id"] == f"{MOCK_USER_ID}_production"
    
    # Verify mocks were called correctly
    mock_content_fetcher.return_value.fetch_all_content.assert_called_once_with(MOCK_USER_ID)
    mock_site_builder.return_value.build_site.assert_called_once()
    mock_publisher.return_value.publish_production.assert_called_once()

@pytest.mark.asyncio
async def test_build_site_preview(
    mock_content_fetcher,
    mock_site_builder,
    mock_publisher,
    mock_validation
):
    """Test preview site build."""
    response = client.post("/app8/build-site", json={
        "user_id": MOCK_USER_ID,
        "preview": True
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["url"] == "https://preview.example.com/site"
    assert data["build_id"] == f"{MOCK_USER_ID}_preview"
    
    mock_publisher.return_value.publish_preview.assert_called_once()

@pytest.mark.asyncio
async def test_build_site_validation_error(
    mock_content_fetcher,
    mock_validation
):
    """Test build with invalid content."""
    # Mock validation failure
    mock_validation.return_value = ValidationResult(
        is_valid=False,
        errors=["Missing required field"],
        warnings=[]
    )
    
    response = client.post("/app8/build-site", json={
        "user_id": MOCK_USER_ID
    })
    assert response.status_code == 400
    data = response.json()
    assert "Missing required field" in data["detail"]

@pytest.mark.asyncio
async def test_build_status():
    """Test build status endpoint."""
    build_id = f"{MOCK_USER_ID}_production"
    
    with patch("app_8_website_builder.api.app8_routes.Publisher") as mock:
        publisher = AsyncMock()
        publisher.get_build_status.return_value = {
            "status": "complete",
            "url": "https://example.com/site",
            "message": "Build complete"
        }
        mock.return_value = publisher
        
        response = client.get(f"/app8/build-status/{build_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "complete"
        assert data["url"] == "https://example.com/site"
        assert data["build_id"] == build_id

@pytest.mark.asyncio
async def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Website Builder API"
    assert data["status"] == "healthy"
