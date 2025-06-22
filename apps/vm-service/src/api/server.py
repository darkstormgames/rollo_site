"""Server management API endpoints."""

import uuid
import subprocess
import socket
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
import ipaddress
import time

from core.auth import get_current_active_user, require_permissions
from core.logging import get_logger
from models.base import DatabaseSession
from models.user import User
from models.server import Server, ServerStatus
from schemas.server import (
    ServerRegistrationRequest, ServerUpdate, ServerResponse, ServerListResponse,
    ServerDiscoverRequest, ServerDiscoverResponse, ServerStatusResponse,
    ServerMetricsResponse, ServerHealthCheckResponse, ServerOperationResponse,
    ServerListFilters, MessageResponse, ErrorResponse
)

logger = get_logger("server_api")
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


def validate_auth_token(token: str) -> bool:
    """Validate authentication token for server registration.
    
    In a production system, this would validate against a secure token store.
    For now, we'll use a simple validation.
    """
    # TODO: Implement proper token validation
    return len(token) >= 32


def ping_server(ip_address: str, port: int = 22, timeout: int = 5) -> bool:
    """Check if server is reachable."""
    try:
        sock = socket.create_connection((ip_address, port), timeout)
        sock.close()
        return True
    except (socket.timeout, socket.error, OSError):
        return False


def scan_subnet(subnet: str, port: int = 22, timeout: int = 5) -> List[str]:
    """Scan subnet for reachable servers."""
    try:
        network = ipaddress.ip_network(subnet, strict=False)
        reachable_hosts = []
        
        for ip in network.hosts():
            if ping_server(str(ip), port, timeout):
                reachable_hosts.append(str(ip))
                
        return reachable_hosts
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid subnet format: {e}"
        )


@router.post("/servers/register", response_model=ServerResponse)
async def register_server(
    registration_data: ServerRegistrationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Register a new server."""
    logger.info(f"Server registration attempt from {registration_data.ip_address}")
    
    # Validate auth token
    if not validate_auth_token(registration_data.auth_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    
    # Check if server already exists
    existing_server = db.query(Server).filter(
        or_(
            Server.hostname == registration_data.hostname,
            Server.ip_address == registration_data.ip_address
        )
    ).first()
    
    if existing_server:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Server with this hostname or IP address already exists"
        )
    
    # Create new server
    server = Server(
        hostname=registration_data.hostname,
        ip_address=registration_data.ip_address,
        status=ServerStatus.ONLINE,
        os_version=registration_data.system_info.os_version,
        cpu_cores=registration_data.system_info.cpu_cores,
        memory_gb=registration_data.system_info.memory_gb,
        disk_gb=registration_data.system_info.disk_gb,
        agent_version=registration_data.agent_version,
        last_heartbeat=datetime.now(timezone.utc),
        user_id=current_user.id
    )
    
    db.add(server)
    db.commit()
    db.refresh(server)
    
    logger.info(f"Server registered successfully: {server.hostname} ({server.ip_address})")
    return server


@router.get("/servers", response_model=ServerListResponse)
async def list_servers(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[ServerStatus] = Query(None, description="Filter by status"),
    hostname: Optional[str] = Query(None, description="Filter by hostname"),
    agent_version: Optional[str] = Query(None, description="Filter by agent version"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all servers with filtering and pagination."""
    query = db.query(Server).options(joinedload(Server.virtual_machines))
    
    # Apply filters
    if status:
        query = query.filter(Server.status == status)
    if hostname:
        query = query.filter(Server.hostname.ilike(f"%{hostname}%"))
    if agent_version:
        query = query.filter(Server.agent_version == agent_version)
    print(f"Current user: {current_user}")
    # Only show servers owned by current user (unless admin)
    # TODO: Add admin role check
    query = query.filter(Server.user_id == current_user["id"])
    
    # Count total
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * per_page
    servers = query.offset(offset).limit(per_page).all()
    
    total_pages = (total + per_page - 1) // per_page
    
    return ServerListResponse(
        servers=servers,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.get("/servers/{server_id}", response_model=ServerResponse)
async def get_server(
    server_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get server details."""
    server = db.query(Server).options(joinedload(Server.virtual_machines)).filter(
        and_(
            Server.id == server_id,
            Server.user_id == current_user.id
        )
    ).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    return server


@router.put("/servers/{server_id}", response_model=ServerResponse)
async def update_server(
    server_id: int,
    update_data: ServerUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update server information."""
    server = db.query(Server).filter(
        and_(
            Server.id == server_id,
            Server.user_id == current_user.id
        )
    ).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    # Check for hostname/IP conflicts if being updated
    if update_data.hostname or update_data.ip_address:
        conflict_query = db.query(Server).filter(Server.id != server_id)
        
        if update_data.hostname:
            conflict_query = conflict_query.filter(Server.hostname == update_data.hostname)
        if update_data.ip_address:
            conflict_query = conflict_query.filter(Server.ip_address == update_data.ip_address)
            
        if conflict_query.first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Server with this hostname or IP address already exists"
            )
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(server, field, value)
    
    server.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(server)
    
    logger.info(f"Server updated: {server.hostname}")
    return server


@router.delete("/servers/{server_id}", response_model=MessageResponse)
async def delete_server(
    server_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove server."""
    server = db.query(Server).filter(
        and_(
            Server.id == server_id,
            Server.user_id == current_user.id
        )
    ).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    # Check if server has VMs
    if server.virtual_machines:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete server with active VMs"
        )
    
    hostname = server.hostname
    db.delete(server)
    db.commit()
    
    logger.info(f"Server deleted: {hostname}")
    return MessageResponse(message=f"Server {hostname} deleted successfully")


@router.post("/servers/discover", response_model=ServerDiscoverResponse)
async def discover_servers(
    discover_data: ServerDiscoverRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Discover servers on network."""
    logger.info(f"Server discovery requested for subnet: {discover_data.subnet}")
    
    start_time = time.time()
    try:
        discovered_ips = scan_subnet(
            discover_data.subnet, 
            discover_data.port, 
            discover_data.timeout
        )
        scan_duration = time.time() - start_time
        
        logger.info(f"Discovery completed: {len(discovered_ips)} servers found in {scan_duration:.2f}s")
        
        return ServerDiscoverResponse(
            discovered_servers=discovered_ips,
            scan_duration=scan_duration,
            total_found=len(discovered_ips)
        )
    except Exception as e:
        logger.error(f"Server discovery failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Discovery failed: {str(e)}"
        )


@router.post("/servers/{server_id}/verify", response_model=ServerOperationResponse)
async def verify_server_connectivity(
    server_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Verify server connectivity."""
    server = db.query(Server).filter(
        and_(
            Server.id == server_id,
            Server.user_id == current_user.id
        )
    ).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    # Test connectivity
    is_reachable = ping_server(server.ip_address, server.port)
    
    # Update server status based on connectivity
    if is_reachable:
        if server.status == ServerStatus.OFFLINE:
            server.status = ServerStatus.ONLINE
        operation_status = "success"
        message = "Server is reachable"
    else:
        server.status = ServerStatus.OFFLINE
        operation_status = "failed"
        message = "Server is not reachable"
    
    server.updated_at = datetime.now(timezone.utc)
    db.commit()
    
    logger.info(f"Server verification: {server.hostname} - {message}")
    
    return ServerOperationResponse(
        id=server.id,
        hostname=server.hostname,
        operation="verify_connectivity",
        status=operation_status,
        message=message,
        timestamp=datetime.now(timezone.utc)
    )


@router.get("/servers/{server_id}/status", response_model=ServerStatusResponse)
async def get_server_status(
    server_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current server status."""
    server = db.query(Server).filter(
        and_(
            Server.id == server_id,
            Server.user_id == current_user.id
        )
    ).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    # Check if server is reachable
    is_reachable = ping_server(server.ip_address, server.port)
    
    # Calculate uptime if server is online
    uptime_seconds = None
    if server.last_heartbeat:
        uptime_seconds = int((datetime.now(timezone.utc) - server.last_heartbeat).total_seconds())
    
    return ServerStatusResponse(
        id=server.id,
        hostname=server.hostname,
        ip_address=server.ip_address,
        status=server.status,
        last_heartbeat=server.last_heartbeat,
        agent_version=server.agent_version,
        uptime_seconds=uptime_seconds,
        is_reachable=is_reachable
    )


@router.get("/servers/{server_id}/metrics", response_model=ServerMetricsResponse)
async def get_server_metrics(
    server_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get server metrics."""
    server = db.query(Server).filter(
        and_(
            Server.id == server_id,
            Server.user_id == current_user.id
        )
    ).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    # In a real implementation, this would fetch actual metrics from the server
    # For now, return mock data based on server specs
    return ServerMetricsResponse(
        id=server.id,
        hostname=server.hostname,
        timestamp=datetime.now(timezone.utc),
        cpu_usage_percent=None,  # Would be fetched from monitoring agent
        memory_usage_percent=None,
        memory_used_gb=None,
        memory_total_gb=server.memory_gb,
        disk_usage_percent=None,
        disk_used_gb=None,
        disk_total_gb=server.disk_gb,
        network_rx_bytes=None,
        network_tx_bytes=None,
        load_average=None
    )


@router.post("/servers/{server_id}/health-check", response_model=ServerHealthCheckResponse)
async def manual_health_check(
    server_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Perform manual health check."""
    server = db.query(Server).filter(
        and_(
            Server.id == server_id,
            Server.user_id == current_user.id
        )
    ).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    # Perform health checks
    checks = {
        "connectivity": "healthy" if ping_server(server.ip_address, server.port) else "unhealthy",
        "agent": "unknown",  # Would check agent health in real implementation
        "disk_space": "unknown",  # Would check disk usage
        "memory": "unknown",  # Would check memory usage
        "cpu": "unknown",  # Would check CPU usage
    }
    
    # Determine overall health
    unhealthy_checks = [k for k, v in checks.items() if v == "unhealthy"]
    if unhealthy_checks:
        overall_health = "critical"
    elif any(v == "unknown" for v in checks.values()):
        overall_health = "warning"
    else:
        overall_health = "healthy"
    
    # Update server status based on health
    if overall_health == "critical":
        server.status = ServerStatus.ERROR
    elif checks["connectivity"] == "healthy":
        server.status = ServerStatus.ONLINE
    
    server.updated_at = datetime.now(timezone.utc)
    db.commit()
    
    logger.info(f"Health check completed for {server.hostname}: {overall_health}")
    
    return ServerHealthCheckResponse(
        id=server.id,
        hostname=server.hostname,
        status=server.status,
        timestamp=datetime.now(timezone.utc),
        checks=checks,
        overall_health=overall_health
    )