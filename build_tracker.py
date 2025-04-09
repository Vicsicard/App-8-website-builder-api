"""
Module for tracking website build status in Supabase.
"""
import os
from enum import Enum
from datetime import datetime
from typing import Dict, Any, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing required Supabase environment variables")

class BuildStatus(str, Enum):
    """Enum for build status values."""
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    ERROR = "error"

class BuildTracker:
    """Handles tracking of website build status in Supabase."""
    
    def __init__(self):
        """Initialize Supabase client."""
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
    async def create_build(self, user_id: str) -> Dict[str, Any]:
        """
        Create a new build record in queued state.
        
        Args:
            user_id: ID of the user requesting the build
            
        Returns:
            Dict containing build record details
        """
        data = {
            'user_id': user_id,
            'status': BuildStatus.QUEUED,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        response = await self.client.table('website_builds')\
            .insert(data)\
            .execute()
            
        return response.data[0]
        
    async def update_status(
        self,
        build_id: str,
        status: BuildStatus,
        preview_url: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update the status of a build.
        
        Args:
            build_id: ID of the build to update
            status: New status
            preview_url: Optional URL of the preview site
            error_message: Optional error message if status is ERROR
            
        Returns:
            Dict containing updated build record
        """
        data = {
            'status': status,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        if preview_url:
            data['preview_url'] = preview_url
            
        if error_message and status == BuildStatus.ERROR:
            data['error_message'] = error_message
            
        response = await self.client.table('website_builds')\
            .update(data)\
            .eq('id', build_id)\
            .execute()
            
        return response.data[0]
        
    async def get_build_status(self, build_id: str) -> Dict[str, Any]:
        """
        Get the current status of a build.
        
        Args:
            build_id: ID of the build to check
            
        Returns:
            Dict containing build record details
        """
        response = await self.client.table('website_builds')\
            .select('*')\
            .eq('id', build_id)\
            .execute()
            
        return response.data[0] if response.data else None
        
    async def get_latest_build(self, user_id: str) -> Dict[str, Any]:
        """
        Get the most recent build for a user.
        
        Args:
            user_id: User ID to check
            
        Returns:
            Dict containing build record details
        """
        response = await self.client.table('website_builds')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .limit(1)\
            .execute()
            
        return response.data[0] if response.data else None
