"""
Builder module for generating static HTML files from templates.
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
from .validation import validate_content, clean_content, ValidationResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BuildError(Exception):
    """Custom exception for build errors."""
    def __init__(self, message: str, validation_result: Optional[ValidationResult] = None):
        super().__init__(message)
        self.validation_result = validation_result

class SiteBuilder:
    """Handles HTML generation using Jinja2 templates."""

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize Jinja2 environment and set up directories.
        
        Args:
            output_dir: Optional custom output directory path
        """
        # Set up template directory
        self.template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Set up output directory
        self.output_base = Path(output_dir) if output_dir else Path(__file__).parent / "output"
        self.output_base.mkdir(parents=True, exist_ok=True)
        
        # Set up asset directories
        self.static_dir = Path(__file__).parent / "static"
        self.static_dir.mkdir(exist_ok=True)
        
        # Add custom filters
        self.env.filters['format_date'] = self._format_date
        self.env.filters['truncate_words'] = self._truncate_words
        self.env.filters['style_color'] = self._style_color
        self.env.filters['style_font'] = self._style_font
        
    def _format_date(self, date_str: str) -> str:
        """Format ISO date string to human-readable format."""
        try:
            date = datetime.fromisoformat(date_str)
            return date.strftime("%B %d, %Y")
        except (ValueError, TypeError):
            return date_str
            
    def _truncate_words(self, text: str, length: int = 50) -> str:
        """Truncate text to specified word length."""
        if not text:
            return ""
        words = text.split()
        if len(words) <= length:
            return text
        return ' '.join(words[:length]) + '...'
        
    def _style_color(self, key: str, style_data: Dict[str, Any]) -> str:
        """Get color value from style profile."""
        colors = style_data.get('colors', {})
        return colors.get(key, {}).get('value', '#000000')
        
    def _style_font(self, key: str, style_data: Dict[str, Any]) -> str:
        """Get font settings from style profile."""
        typography = style_data.get('typography', {})
        return typography.get(key, {}).get('family', 'system-ui')
        
    def _prepare_page_context(self, content: Dict[str, Any], page_title: str = None, 
                            page_description: str = None) -> Dict[str, Any]:
        """Prepare common context data for all pages."""
        style = content.get('style', {})
        images = content.get('images', {})
        
        return {
            'site_title': content.get('bio', {}).get('name', 'Personal Brand'),
            'page_title': page_title,
            'page_description': page_description,
            'current_year': datetime.now().year,
            'style': style,
            'logo': images.get('logo', {'url': '', 'alt': ''}),
            'metadata': content.get('metadata', {}),
            'navigation': [
                {'title': 'Home', 'url': '/'},
                {'title': 'About', 'url': '/about.html'},
                {'title': 'Blog', 'url': '/blog/'},
                {'title': 'Videos', 'url': '/videos.html'},
                {'title': 'My Story', 'url': '/story.html'}
            ]
        }
        
    def build_site(self, user_id: str, content: Dict[str, Any]) -> Path:
        """
        Build a complete website for a user.
        
        Args:
            user_id: User's unique identifier
            content: Dictionary containing all website content
            
        Returns:
            Path to the generated site directory
            
        Raises:
            BuildError: If content validation fails or build process errors
        """
        try:
            # Validate content
            validation_result = validate_content(content)
            
            # Log warnings
            for warning in validation_result.warnings:
                logger.warning(f"Content warning for user {user_id}: {warning}")
            
            # Stop if validation failed
            if not validation_result.is_valid:
                error_msg = "\n".join(validation_result.errors)
                raise BuildError(
                    f"Content validation failed for user {user_id}:\n{error_msg}",
                    validation_result
                )
            
            # Clean and sort content
            content = clean_content(content)
            
            # Create user's site directory
            user_site_dir = self.output_base / user_id
            user_site_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy static files
            self._copy_static_files(user_site_dir)
            
            # Generate all pages
            site_pages = self.generate_site(content)
            
            # Write pages to files
            for path, html_content in site_pages.items():
                file_path = user_site_dir / path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(html_content, encoding='utf-8')
            
            # Generate style.css from user's style profile
            self._generate_css(
                content.get('style', {}),
                user_site_dir / "static" / "css" / "custom.css"
            )
            
            logger.info(f"Successfully built site for user {user_id}")
            return user_site_dir
            
        except BuildError:
            raise
        except Exception as e:
            raise BuildError(f"Failed to build site: {str(e)}")

    def _copy_static_files(self, user_site_dir: Path) -> None:
        """Copy static files to user's site directory."""
        static_dir = user_site_dir / "static"
        static_dir.mkdir(exist_ok=True)
        
        if self.static_dir.exists():
            shutil.copytree(self.static_dir, static_dir, dirs_exist_ok=True)

    def _generate_css(self, style_data: Dict[str, Any], output_path: Path) -> None:
        """Generate custom CSS from user's style profile."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        css_template = self.env.get_template('style.css')
        css_content = css_template.render(style=style_data)
        
        output_path.write_text(css_content, encoding='utf-8')
        
    def generate_site(self, content: Dict[str, Any]) -> Dict[str, str]:
        """Generate all HTML pages for the website."""
        site_pages = {}
        
        # Homepage
        homepage_context = {
            **self._prepare_page_context(
                content,
                page_title='Welcome',
                page_description=content.get('bio', {}).get('summary', '')
            ),
            'bio': content.get('bio', {}),
            'banner': content.get('images', {}).get('banner', {'url': '', 'alt': ''}),
            'headshot': content.get('images', {}).get('headshot', {'url': '', 'alt': ''}),
            'latest_blogs': content.get('blogs', [])[:3],
            'featured_videos': content.get('videos', [])[:2],
            'story_preview': content.get('story_chunks', [])[:1]
        }
        site_pages['index.html'] = self.render_template('home.html', homepage_context)
        
        # About Page
        about_context = {
            **self._prepare_page_context(
                content,
                page_title='About Me',
                page_description=content.get('bio', {}).get('headline', '')
            ),
            'bio': content.get('bio', {}),
            'headshot': content.get('images', {}).get('headshot', {'url': '', 'alt': ''}),
            'values': content.get('values', []),
            'social_links': content.get('social_links', [])
        }
        site_pages['about.html'] = self.render_template('about.html', about_context)
        
        # Blog Section
        blog_context = {
            **self._prepare_page_context(
                content,
                page_title='Blog',
                page_description='Latest thoughts and insights'
            ),
            'posts': content.get('blogs', [])
        }
        site_pages['blog/index.html'] = self.render_template('blog_section.html', blog_context)
        
        # Individual Blog Posts
        for post in content.get('blogs', []):
            post_context = {
                **self._prepare_page_context(
                    content,
                    page_title=post.get('title', ''),
                    page_description=post.get('excerpt', '')
                ),
                'post': post,
                'author': content.get('bio', {}).get('name', ''),
                'author_image': content.get('images', {}).get('headshot', {'url': '', 'alt': ''})
            }
            slug = post.get('slug', '')
            if slug:
                site_pages[f'blog/{slug}.html'] = self.render_template(
                    'blog_post.html', post_context
                )
        
        # Video Gallery
        video_context = {
            **self._prepare_page_context(
                content,
                page_title='Videos',
                page_description='Watch my latest content'
            ),
            'videos': content.get('videos', [])
        }
        site_pages['videos.html'] = self.render_template('video_gallery.html', video_context)
        
        # Story Page
        story_context = {
            **self._prepare_page_context(
                content,
                page_title='My Story',
                page_description='Journey, experiences, and values that shape who I am'
            ),
            'story_chunks': content.get('story_chunks', []),
            'values': content.get('values', []),
            'social_links': content.get('social_links', []),
            'bio': content.get('bio', {})
        }
        site_pages['story.html'] = self.render_template('story_section.html', story_context)
        
        return site_pages
        
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render a single template with given context."""
        template = self.env.get_template(template_name)
        return template.render(**context)
