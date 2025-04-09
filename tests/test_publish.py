"""
Test module for publish.py
Tests website publishing to Supabase storage and database.
"""
import pytest
import os
from pathlib import Path
from datetime import datetime
from ..publish import SitePublisher

# Test data
TEST_USER_ID = "test_user_123"
TEST_HTML = """
<!DOCTYPE html>
<html>
<head><title>Test Page</title></head>
<body>
    <h1>Test Content</h1>
    <p>This is a test page.</p>
</body>
</html>
"""

@pytest.fixture
async def publisher():
    """Fixture to create SitePublisher instance"""
    return SitePublisher()

@pytest.fixture
def test_site(tmp_path):
    """Fixture to create test site files"""
    site_dir = tmp_path / "test_site"
    site_dir.mkdir()
    
    # Create test files
    (site_dir / "index.html").write_text(TEST_HTML)
    
    # Create static directory
    static_dir = site_dir / "static"
    static_dir.mkdir()
    
    # Add CSS file
    (static_dir / "style.css").write_text("body { color: black; }")
    
    # Add JS file
    (static_dir / "script.js").write_text("console.log('test');")
    
    return site_dir

@pytest.mark.asyncio
async def test_publish_to_storage(publisher, test_site):
    """Test publishing files to Supabase storage"""
    # Publish site
    result = await publisher.publish_to_storage(
        str(test_site / "index.html"),
        TEST_USER_ID
    )
    
    # Verify result
    assert result is not None
    assert 'storage_path' in result
    assert 'public_url' in result
    assert not result.get('is_preview', False)
    
    # Check paths
    assert TEST_USER_ID in result['storage_path']
    assert result['public_url'].startswith('http')

@pytest.mark.asyncio
async def test_publish_preview_to_storage(publisher, test_site):
    """Test publishing preview files to Supabase storage"""
    # Publish preview
    result = await publisher.publish_to_storage(
        str(test_site / "index.html"),
        TEST_USER_ID,
        is_preview=True
    )
    
    # Verify result
    assert result is not None
    assert 'storage_path' in result
    assert 'public_url' in result
    assert result['is_preview']
    
    # Check paths
    assert 'previews' in result['storage_path'].lower()
    assert result['public_url'].startswith('http')

@pytest.mark.asyncio
async def test_publish_to_database(publisher, test_site):
    """Test publishing to website_versions table"""
    # Publish version
    version_name = "Test Version"
    result = await publisher.publish_to_database(
        str(test_site / "index.html"),
        TEST_USER_ID,
        version_name=version_name
    )
    
    # Verify result
    assert result is not None
    assert result['user_id'] == TEST_USER_ID
    assert result['version_name'] == version_name
    assert result['is_active']
    assert not result.get('is_preview', False)
    
    # Verify content
    assert 'content' in result
    assert 'Test Content' in result['content']

@pytest.mark.asyncio
async def test_publish_preview_to_database(publisher, test_site):
    """Test publishing preview to website_versions table"""
    # Publish preview version
    result = await publisher.publish_to_database(
        str(test_site / "index.html"),
        TEST_USER_ID,
        is_preview=True
    )
    
    # Verify result
    assert result is not None
    assert result['user_id'] == TEST_USER_ID
    assert result['is_preview']
    assert not result['is_active']

@pytest.mark.asyncio
async def test_activate_version(publisher):
    """Test version activation"""
    # First publish a version
    version_result = await publisher.publish_to_database(
        str(test_site / "index.html"),
        TEST_USER_ID
    )
    version_id = version_result['id']
    
    # Activate version
    await publisher.activate_version(version_id, TEST_USER_ID)
    
    # Get versions to verify
    versions = await publisher.get_site_versions(TEST_USER_ID)
    active_versions = [v for v in versions if v['is_active']]
    
    # Verify only one active version
    assert len(active_versions) == 1
    assert active_versions[0]['id'] == version_id

@pytest.mark.asyncio
async def test_get_site_versions(publisher, test_site):
    """Test retrieving version history"""
    # Create multiple versions
    version_names = ["Version 1", "Version 2", "Version 3"]
    for name in version_names:
        await publisher.publish_to_database(
            str(test_site / "index.html"),
            TEST_USER_ID,
            version_name=name
        )
    
    # Get versions
    versions = await publisher.get_site_versions(TEST_USER_ID)
    
    # Verify versions
    assert len(versions) >= len(version_names)
    assert all(v['user_id'] == TEST_USER_ID for v in versions)
    assert all(isinstance(v['created_at'], str) for v in versions)
    
    # Verify order (newest first)
    dates = [datetime.fromisoformat(v['created_at']) for v in versions]
    assert all(dates[i] >= dates[i+1] for i in range(len(dates)-1))

@pytest.mark.asyncio
async def test_error_handling(publisher):
    """Test error handling in publisher"""
    # Test with non-existent file
    with pytest.raises(Exception):
        await publisher.publish_to_storage(
            "nonexistent/file.html",
            TEST_USER_ID
        )
    
    # Test with invalid user ID
    with pytest.raises(Exception):
        await publisher.publish_to_database(
            str(test_site / "index.html"),
            None
        )
    
    # Test activating non-existent version
    with pytest.raises(Exception):
        await publisher.activate_version(
            "nonexistent-version",
            TEST_USER_ID
        )

if __name__ == '__main__':
    pytest.main(['-v', __file__])
