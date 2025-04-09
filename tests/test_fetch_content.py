"""
Test module for fetch_content.py
Verifies content fetching functionality from Supabase.
"""
import asyncio
import pytest
from ..fetch_content import ContentFetcher

# Test user ID for running tests
TEST_USER_ID = "test_user_123"

@pytest.fixture
async def content_fetcher():
    """Fixture to create ContentFetcher instance"""
    return ContentFetcher()

@pytest.mark.asyncio
async def test_fetch_bio(content_fetcher):
    """Test fetching user bio"""
    bio = await content_fetcher.fetch_bio(TEST_USER_ID)
    assert bio is not None
    assert 'name' in bio
    assert 'summary' in bio

@pytest.mark.asyncio
async def test_fetch_blogs(content_fetcher):
    """Test fetching approved blog posts"""
    blogs = await content_fetcher.fetch_approved_blogs(TEST_USER_ID)
    assert isinstance(blogs, list)
    if blogs:
        assert all('title' in blog for blog in blogs)
        assert all('content' in blog for blog in blogs)
        assert all('status' in blog for blog in blogs)
        assert all(blog['status'] == 'approved' for blog in blogs)

@pytest.mark.asyncio
async def test_fetch_videos(content_fetcher):
    """Test fetching approved videos"""
    videos = await content_fetcher.fetch_approved_videos(TEST_USER_ID)
    assert isinstance(videos, list)
    if videos:
        assert all('title' in video for video in videos)
        assert all('url' in video for video in videos)
        assert all('status' in video for video in videos)
        assert all(video['status'] == 'approved' for video in videos)

@pytest.mark.asyncio
async def test_fetch_social_proof(content_fetcher):
    """Test fetching social proof content"""
    social_proof = await content_fetcher.fetch_social_proof(TEST_USER_ID)
    assert 'testimonials' in social_proof
    assert 'media_mentions' in social_proof
    assert isinstance(social_proof['testimonials'], list)
    assert isinstance(social_proof['media_mentions'], list)

@pytest.mark.asyncio
async def test_fetch_visuals(content_fetcher):
    """Test fetching visual assets"""
    visuals = await content_fetcher.fetch_visuals(TEST_USER_ID)
    assert isinstance(visuals, dict)
    # Check if URLs are properly formatted
    if visuals:
        assert all(isinstance(url, str) and url.startswith('http') for url in visuals.values())

@pytest.mark.asyncio
async def test_fetch_all_content(content_fetcher):
    """Test fetching all content types"""
    all_content = await content_fetcher.fetch_all_content(TEST_USER_ID)
    
    # Check structure
    assert 'bio' in all_content
    assert 'blogs' in all_content
    assert 'videos' in all_content
    assert 'testimonials' in all_content
    assert 'media_mentions' in all_content
    assert 'images' in all_content
    assert 'metadata' in all_content
    
    # Check metadata
    assert 'generated_at' in all_content['metadata']
    assert 'content_count' in all_content['metadata']
    
    # Verify content counts match actual content
    counts = all_content['metadata']['content_count']
    assert len(all_content['blogs']) == counts['blogs']
    assert len(all_content['videos']) == counts['videos']
    assert len(all_content['testimonials']) == counts['testimonials']
    assert len(all_content['media_mentions']) == counts['media_mentions']

if __name__ == '__main__':
    pytest.main(['-v', __file__])
