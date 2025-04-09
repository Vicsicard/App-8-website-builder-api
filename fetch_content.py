"""
Module: fetch_content
Purpose: Retrieve all approved personal brand content from Supabase
for use in App 8 website builder.
"""

# ✅ STEP 1: IMPORTS
import os
import asyncio
from supabase import create_client, Client
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv
import logging
from .validation import validate_story_chunk, validate_value, validate_social_link, sort_by_order_index

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ STEP 2: SUPABASE INITIALIZATION
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing required Supabase environment variables")

class ContentFetchError(Exception):
    """Custom exception for content fetching errors."""
    def __init__(self, message: str, table: str, details: Any = None):
        self.table = table
        self.details = details
        super().__init__(f"Error fetching {table}: {message}")

class ContentFetcher:
    """Handles fetching and validating content from Supabase."""
    
    def __init__(self):
        """Initialize Supabase client connection."""
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
    async def _fetch_table_data(self, table: str, user_id: str, select_fields: str, 
                              status_field: str = 'status', status_value: str = 'approved', 
                              order_by: str = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Generic method to fetch data from any table with common filtering.
        
        Args:
            table: Table name to query
            select_fields: Fields to select
            user_id: User ID to filter by
            status_field: Name of the status field
            status_value: Value to filter status by
            order_by: Optional field to order results by
            
        Returns:
            Tuple of (data list, error message if any)
        """
        try:
            query = self.client.table(table)\
                .select(select_fields)\
                .eq('user_id', user_id)\
                .eq(status_field, status_value)
                
            if order_by:
                query = query.order(order_by, desc=True)
                
            response = await query.execute()
            return response.data, None
            
        except Exception as e:
            error_msg = f"Failed to fetch {table}: {str(e)}"
            return [], error_msg
            
    async def fetch_approved_blogs(self, user_id: str) -> List[Dict[str, Any]]:
        """Fetch approved blog posts for a user."""
        data, error = await self._fetch_table_data(
            'blogs',
            user_id,
            'title, slug, content, tags, published_at, excerpt, thumbnail, status',
            order_by='published_at'
        )
        if error:
            raise ContentFetchError(error, "blogs")
        return data
        
    async def fetch_approved_videos(self, user_id: str) -> List[Dict[str, Any]]:
        """Fetch approved video content for a user."""
        data, error = await self._fetch_table_data(
            'videos',
            user_id,
            'title, url, type, thumbnail, description, tags, status',
            order_by='created_at'
        )
        if error:
            raise ContentFetchError(error, "videos")
        return data
        
    async def fetch_bio(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch the user's approved professional bio."""
        data, error = await self._fetch_table_data(
            'bios',
            user_id,
            'content, headline, summary, expertise, name',
            status_field='is_final',
            status_value=True
        )
        if error:
            raise ContentFetchError(error, "bio")
        return data[0] if data else None
        
    async def fetch_visuals(self, user_id: str) -> Dict[str, Dict[str, str]]:
        """Fetch approved images and visual assets."""
        data, error = await self._fetch_table_data(
            'images',
            user_id,
            'type, url, alt_text, status'
        )
        if error:
            raise ContentFetchError(error, "visuals")
            
        # Organize by type with alt text
        return {
            img['type']: {
                'url': img['url'],
                'alt': img.get('alt_text', '')
            } for img in data if img['type'] in ['banner', 'headshot', 'logo']
        }
        
    async def fetch_style_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch the user's style profile containing brand colors, typography, and voice."""
        data, error = await self._fetch_table_data(
            'style_profiles',
            user_id,
            'colors, typography, voice, themes',
            status_field='is_active',
            status_value=True
        )
        if error:
            raise ContentFetchError(error, "style_profile")
        return data[0] if data else None
        
    async def fetch_story_chunks(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Fetch and validate story chunks.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            List of validated and sorted story chunks
        """
        data = await self._fetch_table_data('story_chunks', user_id, '*')
        
        valid_chunks = []
        for i, chunk in enumerate(data):
            result = validate_story_chunk(chunk, i)
            if result.is_valid:
                valid_chunks.append(chunk)
            else:
                logger.warning(
                    f"Skipping invalid story chunk for user {user_id}:\n" +
                    "\n".join(result.errors)
                )
                for warning in result.warnings:
                    logger.warning(f"Story chunk warning: {warning}")
        
        return sort_by_order_index(valid_chunks)

    async def fetch_values(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Fetch and validate values.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            List of validated and sorted values
        """
        data = await self._fetch_table_data('values', user_id, '*')
        
        valid_values = []
        for i, value in enumerate(data):
            result = validate_value(value, i)
            if result.is_valid:
                valid_values.append(value)
            else:
                logger.warning(
                    f"Skipping invalid value for user {user_id}:\n" +
                    "\n".join(result.errors)
                )
                for warning in result.warnings:
                    logger.warning(f"Value warning: {warning}")
        
        return sort_by_order_index(valid_values)

    async def fetch_social_links(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Fetch and validate social links.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            List of validated social links
        """
        data = await self._fetch_table_data('social_links', user_id, '*')
        
        valid_links = []
        for i, link in enumerate(data):
            result = validate_social_link(link, i)
            if result.is_valid:
                valid_links.append(link)
            else:
                logger.warning(
                    f"Skipping invalid social link for user {user_id}:\n" +
                    "\n".join(result.errors)
                )
                for warning in result.warnings:
                    logger.warning(f"Social link warning: {warning}")
        
        return valid_links

    async def fetch_all_content(self, user_id: str) -> Dict[str, Any]:
        """
        Fetch all approved content for a user's website.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            Dictionary containing all website content structured for HTML generation
            
        Raises:
            ContentFetchError: If there's an error fetching any content type
        """
        errors = []
        content = {}
        
        try:
            # Create tasks for all content fetching
            tasks = [
                ('bio', self.fetch_bio(user_id)),
                ('blogs', self.fetch_approved_blogs(user_id)),
                ('videos', self.fetch_approved_videos(user_id)),
                ('images', self.fetch_visuals(user_id)),
                ('style', self.fetch_style_profile(user_id)),
                ('story_chunks', self.fetch_story_chunks(user_id)),
                ('values', self.fetch_values(user_id)),
                ('social_links', self.fetch_social_links(user_id))
            ]
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)
            
            # Process results and collect any errors
            for (key, _), result in zip(tasks, results):
                if isinstance(result, Exception):
                    errors.append(f"{key}: {str(result)}")
                else:
                    content[key] = result
            
            # If we have any errors, raise them
            if errors:
                raise ContentFetchError(
                    "Multiple errors occurred while fetching content",
                    "multiple_tables",
                    errors
                )
            
            # Add metadata
            content['metadata'] = {
                'generated_at': datetime.now().isoformat(),
                'content_count': {
                    'blogs': len(content.get('blogs', [])),
                    'videos': len(content.get('videos', [])),
                    'story_chunks': len(content.get('story_chunks', []))
                }
            }
            
            return content
            
        except Exception as e:
            raise ContentFetchError(str(e), "all_content", errors if errors else None)
