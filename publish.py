"""
Publisher module for saving the generated website to Supabase storage.
Handles versioning and deployment of the final site.
"""
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# ✅ STEP 1: SUPABASE INITIALIZATION
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing required Supabase environment variables")

class SitePublisher:
    def __init__(self):
        """Initialize Supabase client"""
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
    async def publish_to_storage(
        self, 
        site_path: str, 
        user_id: str,
        is_preview: bool = False
    ) -> Dict[str, str]:
        """
        Save the generated site to Supabase storage
        
        Args:
            site_path: Path to the generated index.html file
            user_id: User ID for organizing storage
            is_preview: If True, store in previews bucket
            
        Returns:
            Dict containing storage path and public URL
        """
        try:
            # Read all files in the site directory
            site_dir = Path(site_path).parent
            files_to_upload = []
            
            for file_path in site_dir.rglob('*'):
                if file_path.is_file():
                    rel_path = file_path.relative_to(site_dir)
                    with open(file_path, 'rb') as f:
                        files_to_upload.append((str(rel_path), f.read()))
            
            # Create storage paths
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            bucket = 'previews' if is_preview else 'websites'
            base_path = f"sites/{user_id}/{timestamp}"
            
            # Upload all files
            uploaded_files = []
            for rel_path, content in files_to_upload:
                storage_path = f"{base_path}/{rel_path}"
                
                # Determine content type
                content_type = 'text/html' if rel_path.endswith('.html') else \
                             'text/css' if rel_path.endswith('.css') else \
                             'application/javascript' if rel_path.endswith('.js') else \
                             'application/octet-stream'
                
                # Upload to Supabase Storage
                response = await self.client.storage\
                    .from_(bucket)\
                    .upload(
                        path=storage_path,
                        file=content,
                        file_options={"content-type": content_type}
                    )
                uploaded_files.append(response)
                
            # Get public URL for index.html
            index_path = f"{base_path}/index.html"
            public_url = self.client.storage\
                .from_(bucket)\
                .get_public_url(index_path)
                
            # Set CORS headers for preview bucket
            if is_preview:
                await self._set_cors_headers(bucket, index_path)
                
            return {
                'storage_path': index_path,
                'public_url': public_url,
                'is_preview': is_preview
            }
            
        except Exception as e:
            print(f"Error publishing to storage: {str(e)}")
            raise
            
    async def _set_cors_headers(self, bucket: str, path: str):
        """Set CORS headers for preview files."""
        try:
            # Update object metadata to allow CORS
            await self.client.storage\
                .from_(bucket)\
                .update(
                    path,
                    file_options={
                        "cache-control": "no-cache",
                        "content-type": "text/html",
                        "x-amz-acl": "public-read",
                        "x-amz-meta-access-control-allow-origin": "*",
                        "x-amz-meta-access-control-allow-methods": "GET, HEAD",
                        "x-amz-meta-access-control-max-age": "86400"
                    }
                )
        except Exception as e:
            print(f"Warning: Failed to set CORS headers: {str(e)}")
            
    async def publish_to_database(
        self, 
        site_path: str, 
        user_id: str,
        version_name: Optional[str] = None,
        is_preview: bool = False
    ) -> Dict[str, Any]:
        """
        Save the site content to the websites table with versioning
        
        Args:
            site_path: Path to the generated index.html file
            user_id: User ID for the website owner
            version_name: Optional name for this version
            is_preview: If True, mark as preview version
            
        Returns:
            Dict containing version details
        """
        try:
            # Read the HTML content
            with open(site_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
                
            # Create version metadata
            version_data = {
                'user_id': user_id,
                'content': html_content,
                'version_name': version_name or f"Version {datetime.now().isoformat()}",
                'created_at': datetime.now().isoformat(),
                'is_preview': is_preview,
                'is_active': not is_preview  # Only non-preview versions are active by default
            }
            
            # Save to database
            response = await self.client.table('website_versions')\
                .insert(version_data)\
                .execute()
                
            return response.data[0]
            
        except Exception as e:
            print(f"Error publishing to database: {str(e)}")
            raise
            
    async def activate_version(self, version_id: str, user_id: str) -> None:
        """
        Set a specific version as the active one
        
        Args:
            version_id: ID of the version to activate
            user_id: User ID for verification
        """
        try:
            # First, deactivate all versions for this user
            await self.client.table('website_versions')\
                .update({'is_active': False})\
                .eq('user_id', user_id)\
                .execute()
                
            # Then activate the specified version
            await self.client.table('website_versions')\
                .update({'is_active': True})\
                .eq('id', version_id)\
                .eq('user_id', user_id)\
                .execute()
                
        except Exception as e:
            print(f"Error activating version: {str(e)}")
            raise
            
    async def get_site_versions(self, user_id: str) -> list:
        """
        Retrieve version history for a user's site
        
        Args:
            user_id: User ID to get versions for
            
        Returns:
            List of version records
        """
        try:
            response = await self.client.table('website_versions')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .execute()
                
            return response.data
            
        except Exception as e:
            print(f"Error getting versions: {str(e)}")
            raise
