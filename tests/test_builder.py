"""
Test module for builder.py
Tests website generation from templates.
"""
import pytest
from pathlib import Path
import shutil
import json
from ..builder import SiteBuilder

# Test data
MOCK_CONTENT = {
    'bio': {
        'name': 'Test User',
        'summary': 'Test bio summary',
        'title': 'Test Title',
        'social_links': {
            'twitter': 'https://twitter.com/test',
            'linkedin': 'https://linkedin.com/in/test'
        }
    },
    'blogs': [
        {
            'title': 'Test Blog 1',
            'content': 'Test blog content 1',
            'date': '2025-01-01',
            'slug': 'test-blog-1'
        }
    ],
    'videos': [
        {
            'title': 'Test Video 1',
            'url': 'https://youtube.com/test1',
            'thumbnail': 'https://img.youtube.com/test1.jpg',
            'description': 'Test video description'
        }
    ],
    'testimonials': [
        {
            'author': 'Test Author',
            'content': 'Test testimonial',
            'company': 'Test Co'
        }
    ],
    'media_mentions': [
        {
            'outlet': 'Test News',
            'title': 'Test Article',
            'url': 'https://testnews.com/article'
        }
    ],
    'images': {
        'profile': 'https://test.com/profile.jpg',
        'background': 'https://test.com/bg.jpg'
    },
    'metadata': {
        'generated_at': '2025-04-07T12:00:00Z',
        'content_count': {
            'blogs': 1,
            'videos': 1,
            'testimonials': 1,
            'media_mentions': 1
        }
    }
}

@pytest.fixture
def site_builder():
    """Fixture to create SiteBuilder instance"""
    return SiteBuilder()

@pytest.fixture
def output_dir(tmp_path):
    """Fixture to create temporary output directory"""
    return tmp_path / "test_site"

def test_init_site_builder(site_builder):
    """Test SiteBuilder initialization"""
    assert site_builder is not None
    assert hasattr(site_builder, 'build_site')
    assert hasattr(site_builder, 'template_dir')

def test_create_output_dir(site_builder, output_dir):
    """Test output directory creation"""
    site_builder._create_output_dir(output_dir)
    assert output_dir.exists()
    assert output_dir.is_dir()

def test_copy_static_files(site_builder, output_dir):
    """Test static file copying"""
    site_builder._create_output_dir(output_dir)
    site_builder._copy_static_files(output_dir)
    
    # Check if essential static files exist
    assert (output_dir / "static" / "style.css").exists()
    assert (output_dir / "static" / "js").exists()

def test_build_site(site_builder, output_dir):
    """Test full site building process"""
    test_user_id = "test_user_123"
    
    # Build the site
    site_path = site_builder.build_site(test_user_id, MOCK_CONTENT)
    
    # Verify directory structure
    assert site_path.exists()
    assert (site_path / "index.html").exists()
    assert (site_path / "static").exists()
    assert (site_path / "blog").exists()
    
    # Check index.html content
    with open(site_path / "index.html", "r", encoding="utf-8") as f:
        content = f.read()
        assert MOCK_CONTENT['bio']['name'] in content
        assert MOCK_CONTENT['bio']['summary'] in content
        assert MOCK_CONTENT['blogs'][0]['title'] in content
        assert MOCK_CONTENT['videos'][0]['title'] in content

def test_build_blog_pages(site_builder, output_dir):
    """Test blog page generation"""
    site_builder._create_output_dir(output_dir)
    blog_dir = output_dir / "blog"
    blog_dir.mkdir(exist_ok=True)
    
    # Build blog pages
    site_builder._build_blog_pages(MOCK_CONTENT['blogs'], blog_dir)
    
    # Check if blog pages were created
    blog_file = blog_dir / f"{MOCK_CONTENT['blogs'][0]['slug']}.html"
    assert blog_file.exists()
    
    # Verify blog content
    with open(blog_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert MOCK_CONTENT['blogs'][0]['title'] in content
        assert MOCK_CONTENT['blogs'][0]['content'] in content

def test_build_with_missing_content(site_builder, output_dir):
    """Test building with missing content sections"""
    incomplete_content = {
        'bio': MOCK_CONTENT['bio'],
        'blogs': [],
        'videos': [],
        'testimonials': [],
        'media_mentions': [],
        'images': {},
        'metadata': MOCK_CONTENT['metadata']
    }
    
    # Build should still work with minimal content
    site_path = site_builder.build_site("test_user_123", incomplete_content)
    assert site_path.exists()
    assert (site_path / "index.html").exists()

def test_build_with_invalid_content(site_builder):
    """Test building with invalid content"""
    invalid_content = {'bio': None}
    
    with pytest.raises(ValueError):
        site_builder.build_site("test_user_123", invalid_content)

def test_template_rendering(site_builder, output_dir):
    """Test template rendering with various content types"""
    site_builder._create_output_dir(output_dir)
    
    # Render home page
    index_path = output_dir / "index.html"
    site_builder._render_template(
        "home.html",
        index_path,
        content=MOCK_CONTENT
    )
    
    # Verify template rendering
    assert index_path.exists()
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()
        # Check template sections
        assert "<!DOCTYPE html>" in content
        assert "<title>" in content
        assert "navigation" in content.lower()
        assert "footer" in content.lower()

def test_cleanup(site_builder, output_dir):
    """Test cleanup of temporary files"""
    site_builder._create_output_dir(output_dir)
    temp_file = output_dir / "temp.txt"
    temp_file.write_text("test")
    
    # Clean up
    site_builder._cleanup(output_dir)
    assert not temp_file.exists()

if __name__ == '__main__':
    pytest.main(['-v', __file__])
