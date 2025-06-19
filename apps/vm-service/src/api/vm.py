"""VM management API endpoints."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_

from core.auth import get_current_active_user, require_permissions
from core.logging import get_logger
from models.base import DatabaseSession
from models.user import User
from models.virtual_machine import VirtualMachine, VMStatus
from models.server import Server
from schemas.vm import (
    VMCreate, VMUpdate, VMResize, VMConfigUpdate, VMResponse, VMListResponse,
    VMOperationResponse, VMConfig, MessageResponse, ErrorResponse, VMListFilters,
    ServerInfo, VMResources, VMNetwork
)
from virtualization.exceptions import VMNotFoundError, VMOperationError, VMStateError

try:
    from virtualization.vm_operations import VMOperations
    vm_ops = VMOperations()
except ImportError as e:
    logger.warning(f"VM operations not available: {e}")
    vm_ops = None

logger = get_logger("vm_api")
router = APIRouter()

# Initialize VM operations (graceful handling of missing libvirt)


def check_vm_ops_available():
    """Check if VM operations are available."""
    if vm_ops is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="VM operations are not available - libvirt not configured"
        )


def get_db() -> Session:
    """Get database session."""
    return DatabaseSession.get_session()


def vm_to_response(vm: VirtualMachine) -> VMResponse:
    """Convert VirtualMachine model to response schema."""
    return VMResponse(
        id=vm.id,
        name=vm.name,
        uuid=vm.uuid,
        status=vm.status,
        server=ServerInfo(id=vm.server.id, hostname=vm.server.hostname),
        resources=VMResources(
            cpu_cores=vm.cpu_cores,
            memory_mb=vm.memory_mb,
            disk_gb=vm.disk_gb
        ),
        network=VMNetwork(
            ip_address=vm.ip_address,
            mac_address=None  # TODO: Get from libvirt
        ),
        os_type=vm.os_type,
        os_version=vm.os_version,
        vnc_port=vm.vnc_port,
        created_at=vm.created_at,
        updated_at=vm.updated_at
    )


# VM Management Endpoints

@router.get("/vms", response_model=VMListResponse)
@require_permissions(["read"])
async def list_vms(
    filters: VMListFilters = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all VMs with filtering and pagination."""
    try:
        # Build query
        query = db.query(VirtualMachine).options(joinedload(VirtualMachine.server))
        
        # Apply filters
        if filters.status:
            query = query.filter(VirtualMachine.status == filters.status)
        if filters.server_id:
            query = query.filter(VirtualMachine.server_id == filters.server_id)
        if filters.os_type:
            query = query.filter(VirtualMachine.os_type == filters.os_type)
        if filters.search:
            query = query.filter(VirtualMachine.name.ilike(f"%{filters.search}%"))
        
        # Apply pagination
        total = query.count()
        offset = (filters.page - 1) * filters.per_page
        vms = query.offset(offset).limit(filters.per_page).all()
        
        # Convert to response format
        vm_responses = [vm_to_response(vm) for vm in vms]
        
        total_pages = (total + filters.per_page - 1) // filters.per_page
        
        return VMListResponse(
            vms=vm_responses,
            total=total,
            page=filters.page,
            per_page=filters.per_page,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Error listing VMs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve VMs"
        )


@router.get("/vms/{vm_id}", response_model=VMResponse)
@require_permissions(["read"])
async def get_vm(
    vm_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get VM details by ID."""
    vm = db.query(VirtualMachine).options(joinedload(VirtualMachine.server)).filter(
        VirtualMachine.id == vm_id
    ).first()
    
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VM with ID {vm_id} not found"
        )
    
    return vm_to_response(vm)


@router.post("/vms", response_model=VMResponse, status_code=status.HTTP_201_CREATED)
@require_permissions(["write"])
async def create_vm(
    vm_data: VMCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new VM."""
    try:
        # Verify server exists
        server = db.query(Server).filter(Server.id == vm_data.server_id).first()
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server with ID {vm_data.server_id} not found"
            )
        
        # Generate UUID for new VM
        vm_uuid = str(uuid.uuid4())
        
        # Create VM in database
        vm = VirtualMachine(
            name=vm_data.name,
            uuid=vm_uuid,
            status=VMStatus.STOPPED,
            server_id=vm_data.server_id,
            cpu_cores=vm_data.cpu_cores,
            memory_mb=vm_data.memory_mb,
            disk_gb=vm_data.disk_gb,
            os_type=vm_data.os_type,
            os_version=vm_data.os_version,
            created_by=current_user.id
        )
        
        db.add(vm)
        db.commit()
        db.refresh(vm)
        
        # Create VM using libvirt
        try:
            check_vm_ops_available()
                
            create_result = await vm_ops.create_vm(
                name=vm_data.name,
                uuid=vm_uuid,
                cpu_cores=vm_data.cpu_cores,
                memory_mb=vm_data.memory_mb,
                disk_gb=vm_data.disk_gb,
                os_type=vm_data.os_type.value,
                os_version=vm_data.os_version,
                network=vm_data.network_config.bridge_name or "default"
            )
            
            logger.info(f"VM '{vm_data.name}' created successfully: {create_result}")
            
        except Exception as e:
            # If libvirt creation fails, clean up database entry
            db.delete(vm)
            db.commit()
            logger.error(f"Failed to create VM in libvirt: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create VM: {str(e)}"
            )
        
        # Reload VM with server relationship
        vm = db.query(VirtualMachine).options(joinedload(VirtualMachine.server)).filter(
            VirtualMachine.id == vm.id
        ).first()
        
        return vm_to_response(vm)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating VM: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create VM"
        )


@router.put("/vms/{vm_id}", response_model=VMResponse)
@require_permissions(["write"])
async def update_vm(
    vm_id: int,
    vm_data: VMUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update VM configuration."""
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VM with ID {vm_id} not found"
        )
    
    # Update provided fields
    update_data = vm_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vm, field, value)
    
    db.commit()
    db.refresh(vm)
    
    # Reload with server relationship
    vm = db.query(VirtualMachine).options(joinedload(VirtualMachine.server)).filter(
        VirtualMachine.id == vm_id
    ).first()
    
    return vm_to_response(vm)


@router.delete("/vms/{vm_id}", response_model=MessageResponse)
@require_permissions(["write"])
async def delete_vm(
    vm_id: int,
    delete_disks: bool = Query(True, description="Delete associated disk files"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete VM."""
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VM with ID {vm_id} not found"
        )
    
    try:
        # Delete VM using libvirt
        check_vm_ops_available()
            
        delete_result = await vm_ops.delete_vm(
            name=vm.name,
            delete_disks=delete_disks
        )
        
        # Delete from database
        db.delete(vm)
        db.commit()
        
        logger.info(f"VM '{vm.name}' deleted successfully: {delete_result}")
        
        return MessageResponse(
            message=f"VM '{vm.name}' deleted successfully",
            detail=f"Deleted disks: {delete_result.get('deleted_disks', [])}"
        )
        
    except VMNotFoundError:
        # VM not found in libvirt, but exists in database - clean up database
        db.delete(vm)
        db.commit()
        logger.warning(f"VM '{vm.name}' not found in libvirt, removed from database")
        return MessageResponse(message=f"VM '{vm.name}' deleted from database")
        
    except Exception as e:
        logger.error(f"Error deleting VM: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete VM: {str(e)}"
        )


# VM Operations Endpoints

@router.post("/vms/{vm_id}/start", response_model=VMOperationResponse)
@require_permissions(["write"])
async def start_vm(
    vm_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Start VM."""
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VM with ID {vm_id} not found"
        )
    
    try:
        check_vm_ops_available()
        result = await vm_ops.start_vm(name=vm.name)
        
        # Update VM status in database
        vm.status = VMStatus.RUNNING
        db.commit()
        
        logger.info(f"VM '{vm.name}' started successfully")
        
        return VMOperationResponse(
            id=vm.id,
            name=vm.name,
            operation="start",
            status="success",
            message="VM started successfully",
            details=result
        )
        
    except VMNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VM '{vm.name}' not found in libvirt"
        )
    except VMOperationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/vms/{vm_id}/stop", response_model=VMOperationResponse)
@require_permissions(["write"])
async def stop_vm(
    vm_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Stop VM gracefully."""
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VM with ID {vm_id} not found"
        )
    
    try:
        check_vm_ops_available()
        result = await vm_ops.stop_vm(name=vm.name, force=False)
        
        # Update VM status in database
        vm.status = VMStatus.STOPPED
        db.commit()
        
        logger.info(f"VM '{vm.name}' stopped successfully")
        
        return VMOperationResponse(
            id=vm.id,
            name=vm.name,
            operation="stop",
            status="success",
            message="VM stopped successfully",
            details=result
        )
        
    except VMNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VM '{vm.name}' not found in libvirt"
        )
    except VMOperationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/vms/{vm_id}/force-stop", response_model=VMOperationResponse)
@require_permissions(["write"])
async def force_stop_vm(
    vm_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Force stop VM."""
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VM with ID {vm_id} not found"
        )
    
    try:
        check_vm_ops_available()
        result = await vm_ops.stop_vm(name=vm.name, force=True)
        
        # Update VM status in database
        vm.status = VMStatus.STOPPED
        db.commit()
        
        logger.info(f"VM '{vm.name}' force stopped successfully")
        
        return VMOperationResponse(
            id=vm.id,
            name=vm.name,
            operation="force-stop",
            status="success",
            message="VM force stopped successfully",
            details=result
        )
        
    except VMNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VM '{vm.name}' not found in libvirt"
        )
    except VMOperationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/vms/{vm_id}/restart", response_model=VMOperationResponse)
@require_permissions(["write"])
async def restart_vm(
    vm_id: int,
    force: bool = Query(False, description="Force restart"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Restart VM."""
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VM with ID {vm_id} not found"
        )
    
    try:
        check_vm_ops_available()
        result = await vm_ops.restart_vm(name=vm.name, force=force)
        
        # Update VM status in database
        vm.status = VMStatus.RUNNING
        db.commit()
        
        logger.info(f"VM '{vm.name}' restarted successfully")
        
        return VMOperationResponse(
            id=vm.id,
            name=vm.name,
            operation="restart",
            status="success",
            message="VM restarted successfully",
            details=result
        )
        
    except VMNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VM '{vm.name}' not found in libvirt"
        )
    except VMOperationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/vms/{vm_id}/reset", response_model=VMOperationResponse)
@require_permissions(["write"])
async def reset_vm(
    vm_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Hard reset VM (equivalent to force restart)."""
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VM with ID {vm_id} not found"
        )
    
    try:
        check_vm_ops_available()
        result = await vm_ops.restart_vm(name=vm.name, force=True)
        
        # Update VM status in database
        vm.status = VMStatus.RUNNING
        db.commit()
        
        logger.info(f"VM '{vm.name}' reset successfully")
        
        return VMOperationResponse(
            id=vm.id,
            name=vm.name,
            operation="reset",
            status="success",
            message="VM reset successfully",
            details=result
        )
        
    except VMNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VM '{vm.name}' not found in libvirt"
        )
    except VMOperationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# VM Configuration Endpoints

@router.get("/vms/{vm_id}/config", response_model=VMConfig)
@require_permissions(["read"])
async def get_vm_config(
    vm_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get VM configuration."""
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VM with ID {vm_id} not found"
        )
    
    try:
        # Get VM status from libvirt (includes additional details)
        check_vm_ops_available()
        status_info = await vm_ops.get_vm_status(name=vm.name)
        
        return VMConfig(
            id=vm.id,
            name=vm.name,
            uuid=vm.uuid,
            cpu_cores=vm.cpu_cores,
            memory_mb=vm.memory_mb,
            disk_gb=vm.disk_gb,
            os_type=vm.os_type,
            os_version=vm.os_version,
            vnc_enabled=vm.vnc_port is not None,
            vnc_port=vm.vnc_port,
            network_config={
                "type": "nat",  # Default for now
                "bridge_name": None
            },
            xml_config=None  # Could be retrieved from libvirt if needed
        )
        
    except VMNotFoundError:
        # Return DB info even if not found in libvirt
        return VMConfig(
            id=vm.id,
            name=vm.name,
            uuid=vm.uuid,
            cpu_cores=vm.cpu_cores,
            memory_mb=vm.memory_mb,
            disk_gb=vm.disk_gb,
            os_type=vm.os_type,
            os_version=vm.os_version,
            vnc_enabled=vm.vnc_port is not None,
            vnc_port=vm.vnc_port,
            network_config={
                "type": "nat",
                "bridge_name": None
            }
        )


@router.put("/vms/{vm_id}/config", response_model=VMConfig)
@require_permissions(["write"])
async def update_vm_config(
    vm_id: int,
    config_data: VMConfigUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update VM configuration."""
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VM with ID {vm_id} not found"
        )
    
    # Update VM configuration in database
    update_data = config_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "vnc_enabled":
            # Handle VNC port assignment
            if value and not vm.vnc_port:
                # Assign a VNC port (simplified logic)
                vm.vnc_port = 5900 + vm.id
            elif not value:
                vm.vnc_port = None
        elif field != "network_config":  # Skip network_config for now
            setattr(vm, field, value)
    
    db.commit()
    db.refresh(vm)
    
    # Return updated config
    return VMConfig(
        id=vm.id,
        name=vm.name,
        uuid=vm.uuid,
        cpu_cores=vm.cpu_cores,
        memory_mb=vm.memory_mb,
        disk_gb=vm.disk_gb,
        os_type=vm.os_type,
        os_version=vm.os_version,
        vnc_enabled=vm.vnc_port is not None,
        vnc_port=vm.vnc_port,
        network_config={
            "type": "nat",
            "bridge_name": None
        }
    )


@router.post("/vms/{vm_id}/resize", response_model=VMOperationResponse)
@require_permissions(["write"])
async def resize_vm(
    vm_id: int,
    resize_data: VMResize,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Resize VM resources."""
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VM with ID {vm_id} not found"
        )
    
    # Check if VM is stopped (required for resize)
    if vm.status != VMStatus.STOPPED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="VM must be stopped before resizing"
        )
    
    # Update VM resources in database
    update_data = resize_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vm, field, value)
    
    db.commit()
    
    logger.info(f"VM '{vm.name}' resized successfully")
    
    return VMOperationResponse(
        id=vm.id,
        name=vm.name,
        operation="resize",
        status="success",
        message="VM resized successfully",
        details={
            "new_resources": {
                "cpu_cores": vm.cpu_cores,
                "memory_mb": vm.memory_mb,
                "disk_gb": vm.disk_gb
            }
        }
    )