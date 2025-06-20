"""VM management API endpoints."""

import uuid
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_

from core.auth import get_current_active_user, require_permissions
from core.logging import get_logger
from core.exceptions import (
    ServerNotFoundException, VMOperationException, ResourceAllocationException
)
from models.base import DatabaseSession
from models.user import User
from models.virtual_machine import VirtualMachine, VMStatus
from models.server import Server
from models.vm_disk import VMDisk
from models.vm_network import VMNetwork
from schemas.vm import (
    VMCreate, VMUpdate, VMResize, VMConfigUpdate, VMResponse, VMListResponse,
    VMOperationResponse, VMConfig, MessageResponse, ErrorResponse, VMListFilters,
    ServerInfo, VMResources, VMNetwork
)
from schemas.resources import (
    ResourceLimits, ResizeRequest, HotAddRequest, DiskConfig, NetworkConfig,
    ResourceValidationResult
)
from core.resource_validator import ResourceValidator

logger = get_logger("vm_api")

try:
    from virtualization.exceptions import VMNotFoundError, VMOperationError, VMStateError
except ImportError as e:
    logger.warning(f"Virtualization exceptions not available: {e}")
    # Define stub exceptions
    class VMNotFoundError(Exception):
        pass
    class VMOperationError(Exception):
        pass
    class VMStateError(Exception):
        pass

try:
    from virtualization.vm_operations import VMOperations
    vm_ops = VMOperations()
except ImportError as e:
    logger.warning(f"VM operations not available: {e}")
    vm_ops = None

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
            raise ServerNotFoundException(
                server_id=str(vm_data.server_id),
                details={"requested_server_id": vm_data.server_id}
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
            raise VMOperationException(
                operation="create",
                vm_name=vm_data.name,
                reason=str(e),
                details={
                    "libvirt_error": str(e),
                    "vm_uuid": vm_uuid,
                    "server_id": vm_data.server_id
                }
            )
        
        # Reload VM with server relationship
        vm = db.query(VirtualMachine).options(joinedload(VirtualMachine.server)).filter(
            VirtualMachine.id == vm.id
        ).first()
        
        return vm_to_response(vm)
        
    except (ServerNotFoundException, VMOperationException, ResourceAllocationException):
        # Re-raise our custom exceptions to be handled by global handler
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating VM: {e}")
        raise VMOperationException(
            operation="create",
            vm_name=vm_data.name,
            reason="An unexpected error occurred",
            details={"original_error": str(e)}
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


# Resource Management Endpoints

@router.get("/vm/resource-limits", response_model=ResourceLimits)
@require_permissions(["read"])
async def get_resource_limits(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get system resource limits and availability."""
    try:
        validator = ResourceValidator(db)
        limits = validator.get_system_limits()
        return limits
    except Exception as e:
        logger.error(f"Error getting resource limits: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve resource limits"
        )


@router.put("/vm/{vm_id}/resources", response_model=VMOperationResponse)
@require_permissions(["write"])
async def update_vm_resources(
    vm_id: int,
    resize_data: ResizeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update VM resource configuration with validation."""
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VM with ID {vm_id} not found"
        )
    
    try:
        # Validate resources if not validation-only mode
        validator = ResourceValidator(db)
        
        # Build complete resource configuration for validation
        from schemas.resources import VMResources, CPUConfig, MemoryConfig
        
        current_cpu = CPUConfig(
            cores=vm.cpu_cores,
            sockets=vm.cpu_sockets,
            threads=vm.cpu_threads,
            model=vm.cpu_model,
            shares=vm.cpu_shares,
            limit=vm.cpu_limit
        )
        
        current_memory = MemoryConfig(
            size_mb=vm.memory_mb,
            hugepages=vm.memory_hugepages,
            balloon=vm.memory_balloon,
            shares=vm.memory_shares
        )
        
        # Get current disks and networks
        current_disks = []
        for disk in vm.disks:
            current_disks.append(DiskConfig(
                name=disk.name,
                size_gb=disk.size_gb,
                format=disk.format,
                pool=disk.pool,
                bootable=disk.bootable
            ))
        
        current_networks = []
        for network in vm.networks:
            current_networks.append(NetworkConfig(
                name=network.name,
                type=network.type,
                bridge=network.bridge,
                vlan_id=network.vlan_id,
                ip_address=network.ip_address,
                mac_address=network.mac_address
            ))
        
        # Use new configuration if provided, otherwise keep current
        new_cpu = resize_data.cpu if resize_data.cpu else current_cpu
        new_memory = resize_data.memory if resize_data.memory else current_memory
        new_disks = resize_data.disks if resize_data.disks else current_disks
        new_networks = resize_data.network if resize_data.network else current_networks
        
        new_resources = VMResources(
            cpu=new_cpu,
            memory=new_memory,
            disks=new_disks,
            network=new_networks
        )
        
        validation_result = validator.validate_vm_resources(new_resources)
        
        if not validation_result.valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid resource configuration: {', '.join(validation_result.errors)}"
            )
        
        # If validation-only mode, return result without applying changes
        if resize_data.validate_only:
            return VMOperationResponse(
                id=vm.id,
                name=vm.name,
                operation="validate-resources",
                status="success",
                message="Resource configuration is valid",
                details={
                    "validation": {
                        "valid": validation_result.valid,
                        "warnings": validation_result.warnings
                    }
                }
            )
        
        # Check if VM needs to be stopped for certain changes
        requires_stop = False
        if resize_data.cpu and (
            resize_data.cpu.cores != vm.cpu_cores or
            resize_data.cpu.sockets != vm.cpu_sockets or
            resize_data.cpu.threads != vm.cpu_threads
        ):
            requires_stop = True
        
        if resize_data.memory and resize_data.memory.size_mb != vm.memory_mb:
            requires_stop = True
        
        if requires_stop and vm.status == VMStatus.RUNNING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="VM must be stopped to modify CPU cores, sockets, threads, or memory size"
            )
        
        # Apply changes
        changes = {}
        
        if resize_data.cpu:
            vm.cpu_cores = resize_data.cpu.cores
            vm.cpu_sockets = resize_data.cpu.sockets
            vm.cpu_threads = resize_data.cpu.threads
            vm.cpu_model = resize_data.cpu.model
            vm.cpu_pinning = json.dumps(resize_data.cpu.pinning) if resize_data.cpu.pinning else None
            vm.cpu_shares = resize_data.cpu.shares
            vm.cpu_limit = resize_data.cpu.limit
            vm.numa_nodes = json.dumps(resize_data.cpu.numa_nodes) if resize_data.cpu.numa_nodes else None
            changes["cpu"] = resize_data.cpu.model_dump()
        
        if resize_data.memory:
            vm.memory_mb = resize_data.memory.size_mb
            vm.memory_hugepages = resize_data.memory.hugepages
            vm.memory_balloon = resize_data.memory.balloon
            vm.memory_shares = resize_data.memory.shares
            vm.memory_numa_nodes = json.dumps(resize_data.memory.numa_nodes) if resize_data.memory.numa_nodes else None
            changes["memory"] = resize_data.memory.model_dump()
        
        # Handle disk changes
        if resize_data.disks:
            # For now, we'll handle basic disk updates
            # More complex operations (add/remove) should use dedicated endpoints
            changes["disks"] = [disk.model_dump() for disk in resize_data.disks]
        
        # Handle network changes
        if resize_data.network:
            changes["networks"] = [net.model_dump() for net in resize_data.network]
        
        db.commit()
        
        logger.info(f"VM '{vm.name}' resources updated successfully")
        
        return VMOperationResponse(
            id=vm.id,
            name=vm.name,
            operation="update-resources",
            status="success",
            message="VM resources updated successfully",
            details={
                "changes": changes,
                "warnings": validation_result.warnings
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating VM resources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update VM resources"
        )


@router.post("/vm/{vm_id}/disks", response_model=VMOperationResponse)
@require_permissions(["write"])
async def add_vm_disk(
    vm_id: int,
    disk_config: DiskConfig,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add a new disk to VM."""
    vm = db.query(VirtualMachine).options(joinedload(VirtualMachine.disks)).filter(
        VirtualMachine.id == vm_id
    ).first()
    
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VM with ID {vm_id} not found"
        )
    
    try:
        # Check if disk name already exists for this VM
        existing_disk = db.query(VMDisk).filter(
            VMDisk.vm_id == vm_id,
            VMDisk.name == disk_config.name
        ).first()
        
        if existing_disk:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Disk with name '{disk_config.name}' already exists for this VM"
            )
        
        # Validate disk configuration
        validator = ResourceValidator(db)
        current_disks = [DiskConfig(
            name=disk.name,
            size_gb=disk.size_gb,
            format=disk.format,
            pool=disk.pool,
            bootable=disk.bootable
        ) for disk in vm.disks]
        current_disks.append(disk_config)
        
        validation_result = validator.validate_disk_config(current_disks)
        
        if not validation_result.valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid disk configuration: {', '.join(validation_result.errors)}"
            )
        
        # Create new disk
        new_disk = VMDisk(
            vm_id=vm_id,
            name=disk_config.name,
            size_gb=disk_config.size_gb,
            format=disk_config.format.value,
            pool=disk_config.pool or "default",
            path=disk_config.path,
            cache=disk_config.cache,
            discard=disk_config.discard,
            readonly=disk_config.readonly,
            bootable=disk_config.bootable
        )
        
        db.add(new_disk)
        db.commit()
        db.refresh(new_disk)
        
        logger.info(f"Disk '{disk_config.name}' added to VM '{vm.name}'")
        
        return VMOperationResponse(
            id=vm.id,
            name=vm.name,
            operation="add-disk",
            status="success",
            message=f"Disk '{disk_config.name}' added successfully",
            details={
                "disk": {
                    "id": new_disk.id,
                    "name": new_disk.name,
                    "size_gb": new_disk.size_gb,
                    "format": new_disk.format,
                    "path": new_disk.full_path
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding disk to VM: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add disk to VM"
        )


@router.delete("/vm/{vm_id}/disks/{disk_id}", response_model=VMOperationResponse)
@require_permissions(["write"])
async def remove_vm_disk(
    vm_id: int,
    disk_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove a disk from VM."""
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VM with ID {vm_id} not found"
        )
    
    disk = db.query(VMDisk).filter(
        VMDisk.id == disk_id,
        VMDisk.vm_id == vm_id
    ).first()
    
    if not disk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disk with ID {disk_id} not found for VM {vm_id}"
        )
    
    try:
        # Check if this is a bootable disk
        if disk.bootable:
            # Check if there are other bootable disks
            other_bootable = db.query(VMDisk).filter(
                VMDisk.vm_id == vm_id,
                VMDisk.id != disk_id,
                VMDisk.bootable == True
            ).first()
            
            if not other_bootable:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot remove the only bootable disk from VM"
                )
        
        disk_name = disk.name
        db.delete(disk)
        db.commit()
        
        logger.info(f"Disk '{disk_name}' removed from VM '{vm.name}'")
        
        return VMOperationResponse(
            id=vm.id,
            name=vm.name,
            operation="remove-disk",
            status="success",
            message=f"Disk '{disk_name}' removed successfully",
            details={
                "removed_disk": {
                    "id": disk_id,
                    "name": disk_name
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing disk from VM: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove disk from VM"
        )