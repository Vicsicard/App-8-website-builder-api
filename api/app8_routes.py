"""
FastAPI routes for App 8 - Personal Brand Website Builder.
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, List, Optional
from pydantic import BaseModel
import logging

from .fetch_content import ContentFetcher
from .builder import WebsiteBuilder
from .publish import Publisher
from .constants import WEBSITE_STATUS
from .utils import validate_user_input

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1", tags=["website-builder"])

class BuildRequest(BaseModel):
    """Request model for site building."""
    user_id: str = Field(..., description="User's unique identifier")
    preview: bool = Field(False, description="If true, creates a preview build")

class BuildResponse(BaseModel):
    """Response model for site building."""
    status: str = Field(..., description="Build status: success, error, or in_progress")
    url: str = Field(None, description="URL of the published site")
    build_id: str = Field(None, description="Unique identifier for the build")
    message: str = Field(None, description="Error or status message")

async def _build_site_async(
    user_id: str,
    preview: bool = False,
    background_tasks: BackgroundTasks = None
) -> Dict[str, Any]:
    """
    Asynchronously build and publish a site.
    
    Args:
        user_id: User's unique identifier
        preview: If true, creates a preview build
        background_tasks: FastAPI background tasks
        
    Returns:
        Dictionary with build status and URL
        
    Raises:
        HTTPException: If build fails
    """
    try:
        # Initialize components
        content_fetcher = ContentFetcher()
        if not content_fetcher.is_ready():
            raise HTTPException(
                status_code=503,
                detail="Service not fully configured. Check Supabase settings."
            )
        site_builder = WebsiteBuilder()
        publisher = Publisher()
        
        # Fetch content
        logger.info(f"Fetching content for user {user_id}")
        content = await content_fetcher.fetch_all_content(user_id)
        
        # Validate content
        validation_result = validate_user_input(content)
        if not validation_result.is_valid:
            error_msg = "\n".join(validation_result.errors)
            raise HTTPException(
                status_code=400,
                detail=f"Content validation failed:\n{error_msg}"
            )
        
        # Log any warnings
        for warning in validation_result.warnings:
            logger.warning(f"Content warning for user {user_id}: {warning}")
        
        # Build site
        logger.info(f"Building site for user {user_id}")
        build_dir = site_builder.build_site(user_id, content)
        
        # Publish site
        logger.info(f"Publishing site for user {user_id}")
        if preview:
            url = await publisher.publish_preview(user_id, build_dir)
            build_type = "preview"
        else:
            url = await publisher.publish_production(user_id, build_dir)
            build_type = "production"
        
        logger.info(f"Successfully published {build_type} site for user {user_id}")
        return {
            "status": "success",
            "url": url,
            "build_id": f"{user_id}_{build_type}",
            "message": f"Successfully published {build_type} site"
        }
        
    except HTTPException as e:
        logger.error(f"Build error for user {user_id}: {str(e)}")
        raise e
        
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to build site: {str(e)}"
        )

@router.post("/build-site", response_model=BuildResponse)
async def build_site(
    request: BuildRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Build and publish a personal brand website.
    
    Args:
        request: Build request containing user_id and preview flag
        background_tasks: FastAPI background tasks
        
    Returns:
        Dictionary with build status and URL
    """
    return await _build_site_async(
        request.user_id,
        request.preview,
        background_tasks
    )

@router.get("/build-status/{build_id}", response_model=BuildResponse)
async def get_build_status(build_id: str) -> Dict[str, Any]:
    """
    Get the status of a site build.
    
    Args:
        build_id: Unique identifier for the build
        
    Returns:
        Dictionary with build status and URL if complete
    """
    try:
        # Parse build ID
        user_id, build_type = build_id.split("_")
        
        # Get status from publisher
        publisher = Publisher()
        status = await publisher.get_build_status(user_id, build_type)
        
        return {
            "status": status["status"],
            "url": status.get("url"),
            "build_id": build_id,
            "message": status.get("message")
        }
        
    except Exception as e:
        logger.error(f"Failed to get build status for {build_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get build status: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Health check endpoint that also reports Supabase connection status"""
    content_fetcher = ContentFetcher()
    status = {
        "status": "healthy",
        "service": "website-builder-api",
        "supabase_connection": "ready" if content_fetcher.is_ready() else "not configured"
    }
    return status
