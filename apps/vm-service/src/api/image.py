"""Image management API endpoints."""

import json
import os
import hashlib
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from core.auth import get_current_active_user, require_permissions
from core.logging import get_logger
from core.config import settings
from models.base import DatabaseSession
from models.user import User
from models.os_image import OSImage, ImageStatus
from schemas.template import (
    ImageCreate, ImageResponse, ImageListResponse
)

logger = get_logger("image_api")
router = APIRouter()


def get_db() -> Session:
    """Get database session."""
    return DatabaseSession.get_session()


def image_to_response(image: OSImage) -> ImageResponse:
    """Convert OSImage model to response schema."""
    return ImageResponse(
        id=image.id,
        name=image.name,
        description=image.description,
        os_type=image.os_type,
        os_version=image.os_version,
        format=image.format,
        file_path=image.file_path,
        source_url=image.source_url,
        checksum=image.checksum,
        size_gb=image.size_gb,
        status=image.status,
        public=image.public,
        created_by=image.created_by,
        created_at=image.created_at,
        updated_at=image.updated_at
    )


@router.get("/images", response_model=ImageListResponse)
@require_permissions(["read"])
async def list_images(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in image names"),
    os_type: Optional[str] = Query(None, description="Filter by OS type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    public: Optional[bool] = Query(None, description="Filter by public images"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List OS images with filtering and pagination."""
    try:
        # Build query - include public images and user's own images
        query = db.query(OSImage).filter(
            or_(
                OSImage.public == True,
                OSImage.created_by == current_user.id
            )
        )
        
        # Apply filters
        if search:
            query = query.filter(OSImage.name.ilike(f"%{search}%"))
        if os_type:
            query = query.filter(OSImage.os_type == os_type)
        if status:
            query = query.filter(OSImage.status == status)
        if public is not None:
            query = query.filter(OSImage.public == public)
        
        # Apply pagination
        total = query.count()
        offset = (page - 1) * per_page
        images = query.offset(offset).limit(per_page).all()
        
        # Convert to response format
        image_responses = [image_to_response(image) for image in images]
        
        total_pages = (total + per_page - 1) // per_page
        
        return ImageListResponse(
            images=image_responses,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Error listing images: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve images"
        )


@router.get("/images/{image_id}", response_model=ImageResponse)
@require_permissions(["read"])
async def get_image(
    image_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get image details by ID."""
    image = db.query(OSImage).filter(
        OSImage.id == image_id,
        or_(
            OSImage.public == True,
            OSImage.created_by == current_user.id
        )
    ).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with ID {image_id} not found"
        )
    
    return image_to_response(image)


@router.post("/images", response_model=ImageResponse, status_code=status.HTTP_201_CREATED)
@require_permissions(["write"])
async def create_image(
    image_data: ImageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new OS image entry."""
    try:
        # Check if image name already exists
        existing = db.query(OSImage).filter(OSImage.name == image_data.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image with name '{image_data.name}' already exists"
            )
        
        # Create image entry
        image = OSImage(
            name=image_data.name,
            description=image_data.description,
            os_type=image_data.os_type.value,
            os_version=image_data.os_version,
            format=image_data.format,
            source_url=str(image_data.source_url) if image_data.source_url else None,
            checksum=image_data.checksum,
            size_gb=image_data.size_gb,
            status=ImageStatus.UPLOADING if not image_data.source_url else ImageStatus.IMPORTING,
            public=image_data.public,
            created_by=current_user.id
        )
        
        db.add(image)
        db.commit()
        db.refresh(image)
        
        logger.info(f"Image '{image_data.name}' created successfully by user {current_user.id}")
        
        return image_to_response(image)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create image"
        )


@router.post("/images/upload", response_model=ImageResponse)
@require_permissions(["write"])
async def upload_image(
    file: UploadFile = File(...),
    name: str = Query(..., description="Image name"),
    description: Optional[str] = Query(None, description="Image description"),
    os_type: str = Query(..., description="Operating system type"),
    os_version: Optional[str] = Query(None, description="OS version"),
    public: bool = Query(False, description="Whether image is public"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload an OS image file."""
    try:
        # Check if image name already exists
        existing = db.query(OSImage).filter(OSImage.name == name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image with name '{name}' already exists"
            )
        
        # Validate file type
        if not file.filename or not file.filename.endswith(('.qcow2', '.raw', '.vmdk', '.img')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Supported formats: qcow2, raw, vmdk, img"
            )
        
        # Determine format from filename
        format_ext = file.filename.split('.')[-1]
        if format_ext == 'img':
            format_ext = 'raw'
        
        # Create images directory if it doesn't exist
        images_dir = os.path.join(settings.vm_storage_path, "images")
        os.makedirs(images_dir, exist_ok=True)
        
        # Generate unique filename
        file_path = os.path.join(images_dir, f"{name}_{current_user.id}.{format_ext}")
        
        # Create image entry first
        image = OSImage(
            name=name,
            description=description,
            os_type=os_type,
            os_version=os_version,
            format=format_ext,
            file_path=file_path,
            status=ImageStatus.UPLOADING,
            public=public,
            created_by=current_user.id
        )
        
        db.add(image)
        db.commit()
        db.refresh(image)
        
        # Save file and calculate checksum
        sha256_hash = hashlib.sha256()
        total_size = 0
        
        try:
            with open(file_path, "wb") as buffer:
                while chunk := await file.read(8192):  # Read in 8KB chunks
                    buffer.write(chunk)
                    sha256_hash.update(chunk)
                    total_size += len(chunk)
            
            # Update image with file info
            image.checksum = sha256_hash.hexdigest()
            image.size_gb = total_size / (1024 * 1024 * 1024)  # Convert to GB
            image.status = ImageStatus.AVAILABLE
            
            db.commit()
            db.refresh(image)
            
            logger.info(f"Image '{name}' uploaded successfully by user {current_user.id}")
            
            return image_to_response(image)
            
        except Exception as e:
            # Clean up file if upload failed
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Update status to error
            image.status = ImageStatus.ERROR
            image.error_message = str(e)
            db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload image: {str(e)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload image"
        )


@router.delete("/images/{image_id}")
@require_permissions(["write"])
async def delete_image(
    image_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an image."""
    image = db.query(OSImage).filter(
        OSImage.id == image_id,
        OSImage.created_by == current_user.id  # Only creator can delete
    ).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with ID {image_id} not found or access denied"
        )
    
    try:
        image_name = image.name
        file_path = image.file_path
        
        # Mark as deleted first
        image.status = ImageStatus.DELETED
        db.commit()
        
        # Remove file if it exists
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        
        # Actually delete from database
        db.delete(image)
        db.commit()
        
        logger.info(f"Image '{image_name}' deleted by user {current_user.id}")
        
        return {"message": f"Image '{image_name}' deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete image"
        )