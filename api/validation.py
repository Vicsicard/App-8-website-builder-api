"""
Validation module for content data structures.
Provides validation functions and logging for content integrity.
"""
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from urllib.parse import urlparse
from .constants import DEFAULT_SOCIAL_ICONS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of content validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]

def validate_story_chunk(chunk: Dict[str, Any], index: int) -> ValidationResult:
    """
    Validate a single story chunk.
    
    Args:
        chunk: Story chunk data
        index: Position in the list for better error messages
        
    Returns:
        ValidationResult with validation status and messages
    """
    errors = []
    warnings = []
    
    # Required fields
    if not chunk.get('title'):
        errors.append(f"Story chunk {index}: Missing title")
    
    if not chunk.get('content'):
        errors.append(f"Story chunk {index}: Missing content")
    
    if 'order_index' not in chunk:
        errors.append(f"Story chunk {index}: Missing order_index")
    
    # Optional fields
    if chunk.get('image'):
        try:
            result = urlparse(chunk['image'])
            if not all([result.scheme, result.netloc]):
                warnings.append(f"Story chunk {index}: Invalid image URL format")
        except Exception:
            warnings.append(f"Story chunk {index}: Invalid image URL")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )

def validate_value(value: Dict[str, Any], index: int) -> ValidationResult:
    """
    Validate a single value object.
    
    Args:
        value: Value data
        index: Position in the list for better error messages
        
    Returns:
        ValidationResult with validation status and messages
    """
    errors = []
    warnings = []
    
    # Required fields
    if not value.get('title'):
        errors.append(f"Value {index}: Missing title")
    
    if not value.get('description'):
        errors.append(f"Value {index}: Missing description")
    
    if 'order_index' not in value:
        errors.append(f"Value {index}: Missing order_index")
    
    # Optional fields
    if value.get('icon') and not isinstance(value['icon'], str):
        warnings.append(f"Value {index}: Icon should be a string")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )

def validate_social_link(link: Dict[str, Any], index: int) -> ValidationResult:
    """
    Validate a single social link.
    
    Args:
        link: Social link data
        index: Position in the list for better error messages
        
    Returns:
        ValidationResult with validation status and messages
    """
    errors = []
    warnings = []
    
    # Required fields
    if not link.get('platform'):
        errors.append(f"Social link {index}: Missing platform")
    else:
        # Convert platform to lowercase for consistent matching
        link['platform'] = link['platform'].lower()
        
        # Add default icon if none provided
        if not link.get('icon'):
            default_icon = DEFAULT_SOCIAL_ICONS.get(
                link['platform'],
                DEFAULT_SOCIAL_ICONS['default']
            )
            link['icon'] = default_icon
            warnings.append(
                f"Social link {index}: Using default icon '{default_icon}' " +
                f"for platform '{link['platform']}'"
            )
    
    if not link.get('url'):
        errors.append(f"Social link {index}: Missing URL")
    else:
        try:
            result = urlparse(link['url'])
            if not all([result.scheme, result.netloc]):
                errors.append(f"Social link {index}: Invalid URL format")
        except Exception:
            errors.append(f"Social link {index}: Invalid URL")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )

def validate_content(content: Dict[str, Any]) -> ValidationResult:
    """
    Validate all content sections.
    
    Args:
        content: Complete content dictionary
        
    Returns:
        ValidationResult with validation status and messages
    """
    errors = []
    warnings = []
    
    # Validate story chunks
    story_chunks = content.get('story_chunks', [])
    if story_chunks:
        for i, chunk in enumerate(story_chunks):
            result = validate_story_chunk(chunk, i)
            errors.extend(result.errors)
            warnings.extend(result.warnings)
    
    # Validate values
    values = content.get('values', [])
    if values:
        for i, value in enumerate(values):
            result = validate_value(value, i)
            errors.extend(result.errors)
            warnings.extend(result.warnings)
    
    # Validate social links
    social_links = content.get('social_links', [])
    if social_links:
        for i, link in enumerate(social_links):
            result = validate_social_link(link, i)
            errors.extend(result.errors)
            warnings.extend(result.warnings)
    
    # Validate required content
    bio = content.get('bio', {})
    if not bio.get('name'):
        errors.append("Missing required bio.name")
    if not bio.get('summary'):
        errors.append("Missing required bio.summary")
    
    images = content.get('images', {})
    if not images.get('profile', {}).get('url'):
        errors.append("Missing required profile image URL")
    if not images.get('background', {}).get('url'):
        errors.append("Missing required background image URL")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )

def sort_by_order_index(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sort a list of items by order_index.
    
    Args:
        items: List of dictionaries containing order_index
        
    Returns:
        Sorted list
    """
    try:
        return sorted(items, key=lambda x: x.get('order_index', float('inf')))
    except Exception as e:
        logger.warning(f"Failed to sort items by order_index: {str(e)}")
        return items

def clean_content(content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean and sort content data.
    
    Args:
        content: Raw content dictionary
        
    Returns:
        Cleaned content dictionary with sorted lists
    """
    cleaned = content.copy()
    
    # Sort lists by order_index
    if 'story_chunks' in cleaned:
        cleaned['story_chunks'] = sort_by_order_index(cleaned['story_chunks'])
    
    if 'values' in cleaned:
        cleaned['values'] = sort_by_order_index(cleaned['values'])
    
    # Filter out invalid items
    if 'social_links' in cleaned:
        valid_links = []
        for link in cleaned['social_links']:
            if validate_social_link(link, -1).is_valid:
                valid_links.append(link)
            else:
                logger.warning(f"Skipping invalid social link: {link}")
        cleaned['social_links'] = valid_links
    
    return cleaned
