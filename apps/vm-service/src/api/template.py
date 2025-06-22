"""VM template management API endpoints."""

import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from core.auth import get_current_active_user, require_permissions
from core.logging import get_logger
from models.base import DatabaseSession
from models.user import User
from models.vm_template import VMTemplate
from models.virtual_machine import VirtualMachine, VMStatus
import uuid
from schemas.template import (
    TemplateCreate, TemplateUpdate, TemplateResponse, TemplateListResponse,
    TemplateListFilters, PREDEFINED_TEMPLATES, TemplateType, TemplateDeployRequest, TemplateDeployResponse
)
from schemas.resources import VMResources
from core.resource_validator import ResourceValidator

logger = get_logger("template_api")
router = APIRouter()


def get_db() -> Session:
    """Get database session."""
    db_gen = DatabaseSession.get_session()
    db = next(db_gen)
    try:
        yield db
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


def template_to_response(template: VMTemplate) -> TemplateResponse:
    """Convert VMTemplate model to response schema."""
    # Parse resource configuration if available
    resources = None
    if template.resource_config:
        try:
            resource_data = json.loads(template.resource_config)
            resources = VMResources(**resource_data)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Invalid resource config for template {template.id}: {e}")
    
    # Fallback to basic configuration
    if not resources:
        from schemas.resources import CPUConfig, MemoryConfig, DiskConfig, NetworkConfig
        resources = VMResources(
            cpu=CPUConfig(cores=template.cpu_cores),
            memory=MemoryConfig(size_mb=template.memory_mb),
            disks=[DiskConfig(
                name="main",
                size_gb=template.disk_gb,
                format="qcow2",
                bootable=True
            )],
            network=[NetworkConfig(
                name="default",
                type="nat"
            )]
        )
    
    # Parse tags
    tags = []
    if template.tags:
        try:
            tags = json.loads(template.tags)
        except json.JSONDecodeError:
            tags = []
    
    # Parse packages
    packages = []
    if template.packages:
        try:
            packages = json.loads(template.packages)
        except json.JSONDecodeError:
            packages = []
    
    # Parse startup scripts
    startup_scripts = []
    if template.startup_scripts:
        try:
            startup_scripts = json.loads(template.startup_scripts)
        except json.JSONDecodeError:
            startup_scripts = []
    
    # Parse network config
    network_config = None
    if template.network_config:
        try:
            network_config = json.loads(template.network_config)
        except json.JSONDecodeError:
            network_config = None
    
    # Parse security hardening
    security_hardening = None
    if template.security_hardening:
        try:
            security_hardening = json.loads(template.security_hardening)
        except json.JSONDecodeError:
            security_hardening = None
    
    return TemplateResponse(
        id=template.id,
        name=template.name,
        description=template.description,
        type=TemplateType(template.type),
        os_type=template.os_type,
        os_version=template.os_version,
        resources=resources,
        base_image_path=template.base_image_path,
        tags=tags,
        public=template.public,
        created_by=template.created_by,
        created_at=template.created_at,
        version=template.version,
        packages=packages,
        cloud_init_config=template.cloud_init_config,
        image_source=template.image_source,
        image_checksum=template.image_checksum,
        image_format=template.image_format or "qcow2",
        startup_scripts=startup_scripts,
        network_config=network_config,
        security_hardening=security_hardening
    )


@router.get("/templates", response_model=TemplateListResponse)
@require_permissions(["read"])
async def list_templates(
    filters: TemplateListFilters = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List VM templates with filtering and pagination."""
    try:
        # Build query - include public templates and user's own templates
        query = db.query(VMTemplate).filter(
            or_(
                VMTemplate.public == True,
                VMTemplate.created_by == current_user.id
            )
        )
        
        # Apply filters
        if filters.type:
            query = query.filter(VMTemplate.type == filters.type.value)
        if filters.os_type:
            query = query.filter(VMTemplate.os_type == filters.os_type.value)
        if filters.public is not None:
            query = query.filter(VMTemplate.public == filters.public)
        if filters.created_by:
            query = query.filter(VMTemplate.created_by == filters.created_by)
        if filters.search:
            query = query.filter(VMTemplate.name.ilike(f"%{filters.search}%"))
        if filters.tags:
            # Simple tag filtering - check if any of the requested tags exist in the template tags
            for tag in filters.tags:
                query = query.filter(VMTemplate.tags.ilike(f"%{tag}%"))
        
        # Apply pagination
        total = query.count()
        offset = (filters.page - 1) * filters.per_page
        templates = query.offset(offset).limit(filters.per_page).all()
        
        # Convert to response format
        template_responses = [template_to_response(template) for template in templates]
        
        total_pages = (total + filters.per_page - 1) // filters.per_page
        
        return TemplateListResponse(
            templates=template_responses,
            total=total,
            page=filters.page,
            per_page=filters.per_page,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve templates"
        )


@router.get("/templates/{template_id}", response_model=TemplateResponse)
@require_permissions(["read"])
async def get_template(
    template_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get template details by ID."""
    template = db.query(VMTemplate).filter(
        VMTemplate.id == template_id,
        or_(
            VMTemplate.public == True,
            VMTemplate.created_by == current_user.id
        )
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with ID {template_id} not found"
        )
    
    return template_to_response(template)


@router.post("/templates", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
@require_permissions(["write"])
async def create_template(
    template_data: TemplateCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new VM template."""
    try:
        # Validate resource configuration
        validator = ResourceValidator(db)
        validation_result = validator.validate_vm_resources(template_data.resources)
        
        if not validation_result.valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid resource configuration: {', '.join(validation_result.errors)}"
            )
        
        # Check if template name already exists
        existing = db.query(VMTemplate).filter(VMTemplate.name == template_data.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Template with name '{template_data.name}' already exists"
            )
        
        # Serialize resources, tags, and new fields
        resource_config = template_data.resources.model_dump()
        tags_json = json.dumps(template_data.tags) if template_data.tags else None
        packages_json = json.dumps(template_data.packages) if template_data.packages else None
        startup_scripts_json = json.dumps(template_data.startup_scripts) if template_data.startup_scripts else None
        network_config_json = json.dumps(template_data.network_config) if template_data.network_config else None
        security_hardening_json = json.dumps(template_data.security_hardening) if template_data.security_hardening else None
        
        # Create template
        template = VMTemplate(
            name=template_data.name,
            description=template_data.description,
            type=template_data.type.value,
            os_type=template_data.os_type.value,
            os_version=template_data.os_version,
            cpu_cores=template_data.resources.cpu.cores,
            memory_mb=template_data.resources.memory.size_mb,
            disk_gb=template_data.resources.disks[0].size_gb if template_data.resources.disks else 20.0,
            resource_config=json.dumps(resource_config),
            base_image_path=template_data.base_image_path or "/var/lib/libvirt/images/base.qcow2",
            tags=tags_json,
            public=template_data.public,
            created_by=current_user.id,
            # New fields
            packages=packages_json,
            cloud_init_config=template_data.cloud_init_config,
            image_source=template_data.image_source,
            image_checksum=template_data.image_checksum,
            image_format=template_data.image_format or "qcow2",
            startup_scripts=startup_scripts_json,
            network_config=network_config_json,
            security_hardening=security_hardening_json
        )
        
        db.add(template)
        db.commit()
        db.refresh(template)
        
        logger.info(f"Template '{template_data.name}' created successfully by user {current_user.id}")
        
        return template_to_response(template)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create template"
        )


@router.put("/templates/{template_id}", response_model=TemplateResponse)
@require_permissions(["write"])
async def update_template(
    template_id: int,
    template_data: TemplateUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update template configuration."""
    template = db.query(VMTemplate).filter(
        VMTemplate.id == template_id,
        VMTemplate.created_by == current_user.id  # Only creator can update
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with ID {template_id} not found or access denied"
        )
    
    try:
        # Validate resources if provided
        if template_data.resources:
            validator = ResourceValidator(db)
            validation_result = validator.validate_vm_resources(template_data.resources)
            
            if not validation_result.valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid resource configuration: {', '.join(validation_result.errors)}"
                )
        
        # Update provided fields
        update_data = template_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if field == "resources" and value:
                # Update resource configuration
                template.resource_config = json.dumps(value.model_dump())
                template.cpu_cores = value.cpu.cores
                template.memory_mb = value.memory.size_mb
                template.disk_gb = value.disks[0].size_gb if value.disks else template.disk_gb
            elif field == "tags" and value is not None:
                template.tags = json.dumps(value)
            elif field in ["packages", "startup_scripts", "network_config", "security_hardening"] and value is not None:
                # Handle JSON fields
                setattr(template, field, json.dumps(value))
            elif field not in ["resources", "tags", "packages", "startup_scripts", "network_config", "security_hardening"]:
                setattr(template, field, value)
        
        # Increment version
        template.version += 1
        
        db.commit()
        db.refresh(template)
        
        logger.info(f"Template '{template.name}' updated by user {current_user.id}")
        
        return template_to_response(template)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update template"
        )


@router.delete("/templates/{template_id}")
@require_permissions(["write"])
async def delete_template(
    template_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a template."""
    template = db.query(VMTemplate).filter(
        VMTemplate.id == template_id,
        VMTemplate.created_by == current_user.id  # Only creator can delete
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with ID {template_id} not found or access denied"
        )
    
    try:
        template_name = template.name
        db.delete(template)
        db.commit()
        
        logger.info(f"Template '{template_name}' deleted by user {current_user.id}")
        
        return {"message": f"Template '{template_name}' deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete template"
        )


@router.get("/templates/predefined", response_model=List[TemplateResponse])
async def get_predefined_templates():
    """Get predefined template configurations."""
    responses = []
    
    for template_type, config in PREDEFINED_TEMPLATES.items():
        responses.append(TemplateResponse(
            id=0,  # Predefined templates don't have DB IDs
            name=config.name,
            description=config.description,
            type=config.type,
            os_type=config.os_type,
            os_version=None,
            resources=config.resources,
            base_image_path="/var/lib/libvirt/images/base.qcow2",
            tags=[],
            public=True,
            created_by=0,
            created_at=datetime.now(),
            version=1
        ))
    
    return responses


@router.post("/templates/{template_id}/deploy", response_model=TemplateDeployResponse)
@require_permissions(["write"])
async def deploy_template(
    template_id: int,
    deploy_request: TemplateDeployRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Deploy a VM from a template."""
    try:
        # Get the template
        template = db.query(VMTemplate).filter(
            VMTemplate.id == template_id,
            or_(
                VMTemplate.public == True,
                VMTemplate.created_by == current_user.id
            )
        ).first()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template with ID {template_id} not found"
            )
        
        # Check if VM name already exists
        existing_vm = db.query(VirtualMachine).filter(VirtualMachine.name == deploy_request.vm_name).first()
        if existing_vm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"VM with name '{deploy_request.vm_name}' already exists"
            )
        
        # Use custom resources if provided, otherwise use template resources
        if deploy_request.custom_resources:
            validator = ResourceValidator(db)
            validation_result = validator.validate_vm_resources(deploy_request.custom_resources)
            
            if not validation_result.valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid custom resource configuration: {', '.join(validation_result.errors)}"
                )
            
            cpu_cores = deploy_request.custom_resources.cpu.cores
            memory_mb = deploy_request.custom_resources.memory.size_mb
            disk_gb = deploy_request.custom_resources.disks[0].size_gb if deploy_request.custom_resources.disks else template.disk_gb
        else:
            cpu_cores = template.cpu_cores
            memory_mb = template.memory_mb
            disk_gb = template.disk_gb
        
        # Generate VM UUID
        vm_uuid = str(uuid.uuid4())
        
        # Create VM record
        vm = VirtualMachine(
            name=deploy_request.vm_name,
            uuid=vm_uuid,
            status=VMStatus.STOPPED,
            server_id=1,  # Default server - this should be configurable
            cpu_cores=cpu_cores,
            memory_mb=memory_mb,
            disk_gb=disk_gb,
            os_type=template.os_type,
            os_version=template.os_version,
            created_by=current_user.id
        )
        
        db.add(vm)
        db.commit()
        db.refresh(vm)
        
        # Build cloud-init configuration if needed
        cloud_init_config = deploy_request.custom_cloud_init or template.cloud_init_config
        
        # Build deployment configuration
        deployment_config = {
            "vm_name": deploy_request.vm_name,
            "vm_uuid": vm_uuid,
            "cpu_cores": cpu_cores,
            "memory_mb": memory_mb,
            "disk_gb": disk_gb,
            "os_type": template.os_type,
            "os_version": template.os_version,
            "base_image_path": template.base_image_path,
            "cloud_init_config": cloud_init_config,
            "hostname": deploy_request.hostname or deploy_request.vm_name,
            "packages": template.get_packages_list() + (deploy_request.custom_packages or []),
            "startup_scripts": template.get_startup_scripts_list(),
            "network_config": template.get_network_config_dict(),
            "security_hardening": template.get_security_hardening_dict(),
            "root_password": deploy_request.root_password,
            "ssh_keys": deploy_request.ssh_keys or [],
            "environment_variables": deploy_request.environment_variables or {}
        }
        
        # Here you would normally trigger the actual VM creation
        # For now, we'll just mark it as created
        logger.info(f"VM '{deploy_request.vm_name}' deployed from template '{template.name}' by user {current_user.id}")
        logger.debug(f"Deployment config: {deployment_config}")
        
        # Return response
        return TemplateDeployResponse(
            vm_id=vm.id,
            vm_name=vm.name,
            vm_uuid=vm.uuid,
            status="created",
            message=f"VM '{deploy_request.vm_name}' successfully deployed from template '{template.name}'",
            template_used=template_to_response(template)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deploying template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deploy template"
        )


@router.get("/templates/{template_id}/versions", response_model=dict)
@require_permissions(["read"])
async def get_template_versions(
    template_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get template version history."""
    template = db.query(VMTemplate).filter(
        VMTemplate.id == template_id,
        or_(
            VMTemplate.public == True,
            VMTemplate.created_by == current_user.id
        )
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with ID {template_id} not found"
        )
    
    # Parse version history
    version_history = []
    if template.version_history:
        try:
            version_history = json.loads(template.version_history)
        except json.JSONDecodeError:
            version_history = []
    
    return {
        "template_id": template.id,
        "current_version": template.version,
        "versions": version_history
    }