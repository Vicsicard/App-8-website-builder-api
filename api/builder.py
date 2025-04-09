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

class WebsiteBuilder:
    """Website builder class for generating static HTML files."""
    def __init__(self):
        self.template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )

    async def build_site(self, content: Dict[str, Any], build_type: str = 'draft') -> Dict[str, Any]:
        """Build the website using the provided content."""
        try:
            # Validate content
            validation_result = validate_content(content)
            if not validation_result.is_valid:
                raise BuildError("Content validation failed", validation_result)

            # Clean content
            cleaned_content = clean_content(content)

            # Build site
            template = self.env.get_template('base.html')
            html = template.render(content=cleaned_content)

            # Save to file
            output_dir = os.path.join(os.path.dirname(__file__), '..', 'build', build_type)
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, 'index.html')
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)

            return {
                "status": "success",
                "message": f"Site built successfully at {output_file}",
                "path": output_file
            }

        except Exception as e:
            logger.error(f"Build error: {str(e)}")
            raise BuildError(f"Failed to build site: {str(e)}")
