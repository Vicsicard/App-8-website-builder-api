"""
Main FastAPI application for the website builder API.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .app8_routes import router as app8_router

# Create FastAPI app
app = FastAPI(
    title="App 8 Website Builder API",
    description="API for building and managing personal brand websites",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include App 8 routes
app.include_router(app8_router)

@app.get("/")
async def root():
    """Root endpoint returning API info."""
    return {
        "name": "Website Builder API",
        "version": "1.0.0",
        "status": "healthy"
    }

"""
FastAPI endpoint for App 8 - Personal Brand Website Builder.
Handles website build requests from App 5.
"""
from fastapi import HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import asyncio
from typing import Dict, Any, Optional
import logging
from pathlib import Path
from datetime import datetime

from ..fetch_content import ContentFetcher, ContentFetchError
from ..builder import SiteBuilder
from ..publish import SitePublisher
from ..build_tracker import BuildTracker, BuildStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BuildRequest(BaseModel):
    """Request model for site building."""
    user_id: str
    preview_only: bool = False

class BuildResponse(BaseModel):
    """Response model for site building."""
    build_id: str
    status: str
    preview_url: Optional[str] = None

class BuildStatusResponse(BaseModel):
    """Response model for build status."""
    build_id: str
    status: str
    preview_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None

@app.post("/build-site", response_model=BuildResponse)
async def build_site(request: BuildRequest) -> Dict[str, Any]:
    """
    Build and publish a personal brand website.
    
    Args:
        request: BuildRequest containing user_id and preview flag
        
    Returns:
        Dict containing build ID and initial status
    """
    try:
        # Create build record
        tracker = BuildTracker()
        build = await tracker.create_build(request.user_id)
        build_id = build['id']
        
        # Start build process in background task
        asyncio.create_task(
            process_build(build_id, request.user_id, request.preview_only)
        )
        
        return {
            "build_id": build_id,
            "status": BuildStatus.QUEUED
        }
        
    except Exception as e:
        logger.error(f"Failed to start build: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start build: {str(e)}"
        )

@app.get("/build-status/{build_id}", response_model=BuildStatusResponse)
async def get_build_status(build_id: str) -> Dict[str, Any]:
    """
    Get the current status of a build.
    
    Args:
        build_id: ID of the build to check
        
    Returns:
        Dict containing build status details
    """
    try:
        tracker = BuildTracker()
        status = await tracker.get_build_status(build_id)
        
        if not status:
            raise HTTPException(
                status_code=404,
                detail=f"Build {build_id} not found"
            )
            
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get build status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get build status: {str(e)}"
        )

@app.get("/preview/{build_id}", response_class=HTMLResponse)
async def get_preview_frame(
    build_id: str,
    height: int = Query(default=800, ge=100, le=4000)
) -> str:
    """
    Get an HTML iframe for previewing a build.
    
    Args:
        build_id: ID of the build to preview
        height: Height of the iframe in pixels
        
    Returns:
        HTML with iframe for preview
    """
    try:
        # Get build status
        tracker = BuildTracker()
        status = await tracker.get_build_status(build_id)
        
        if not status:
            raise HTTPException(
                status_code=404,
                detail=f"Build {build_id} not found"
            )
            
        if not status.get('preview_url'):
            raise HTTPException(
                status_code=400,
                detail="Preview URL not available"
            )
            
        # Return iframe HTML
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Website Preview</title>
            <style>
                body {{ margin: 0; padding: 0; }}
                iframe {{
                    width: 100%;
                    height: {height}px;
                    border: none;
                    margin: 0;
                    padding: 0;
                }}
            </style>
        </head>
        <body>
            <iframe
                src="{status['preview_url']}"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowfullscreen
            ></iframe>
        </body>
        </html>
        """
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get preview: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get preview: {str(e)}"
        )

async def process_build(build_id: str, user_id: str, preview_only: bool = False):
    """
    Process a website build in the background.
    
    Args:
        build_id: ID of the build to process
        user_id: ID of the user requesting the build
        preview_only: If True, only create preview version
    """
    tracker = BuildTracker()
    
    try:
        # Update status to in progress
        await tracker.update_status(build_id, BuildStatus.IN_PROGRESS)
        
        # Step 1: Fetch content
        logger.info(f"Fetching content for user {user_id}")
        content_fetcher = ContentFetcher()
        content = await content_fetcher.fetch_all_content(user_id)
        
        if not content.get('bio'):
            await tracker.update_status(
                build_id,
                BuildStatus.ERROR,
                error_message="User has no approved bio content"
            )
            return
            
        # Step 2: Build site
        logger.info("Building website from templates")
        builder = SiteBuilder()
        site_path = builder.build_site(user_id, content)
        
        # Step 3: Publish site
        logger.info("Publishing website")
        publisher = SitePublisher()
        
        # Save to storage as preview
        storage_result = await publisher.publish_to_storage(
            str(site_path / "index.html"),
            user_id,
            is_preview=True
        )
        
        # If not preview_only, also publish as regular version
        if not preview_only:
            # Save to storage as regular version
            await publisher.publish_to_storage(
                str(site_path / "index.html"),
                user_id,
                is_preview=False
            )
            
            # Save to database with version
            version_result = await publisher.publish_to_database(
                str(site_path / "index.html"),
                user_id,
                version_name=f"Build {content['metadata']['generated_at']}",
                is_preview=False
            )
            
            # Activate this version
            await publisher.activate_version(
                version_result['version_id'],
                user_id
            )
        
        # Update build status to complete with preview URL
        await tracker.update_status(
            build_id,
            BuildStatus.COMPLETE,
            preview_url=storage_result['public_url']
        )
        
    except Exception as e:
        logger.error(f"Build error: {str(e)}")
        await tracker.update_status(
            build_id,
            BuildStatus.ERROR,
            error_message=str(e)
        )

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "app-8-website-builder-api"}
