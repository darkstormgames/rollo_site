"""Example integration of WebSocket events into VM operations."""

from websocket.events import event_broadcaster
from models.vm import VM, VMStatus
from models.server import Server, ServerStatus
import asyncio
from datetime import datetime


async def create_vm_with_events(vm_data: dict, server_id: int):
    """Example VM creation with progress and event broadcasting."""
    operation_id = f"vm-create-{vm_data['name']}-{datetime.utcnow().timestamp()}"
    
    try:
        # Start operation
        await event_broadcaster.broadcast_progress_update(
            operation_id=operation_id,
            operation_type="vm_creation",
            progress_percent=0,
            status="starting",
            message="Initializing VM creation..."
        )
        
        # Step 1: Allocate resources (20%)
        await asyncio.sleep(1)  # Simulate work
        await event_broadcaster.broadcast_progress_update(
            operation_id=operation_id,
            operation_type="vm_creation",
            progress_percent=20,
            status="in_progress",
            message="Allocating system resources..."
        )
        
        # Step 2: Create VM definition (40%)
        vm = VM(
            name=vm_data['name'],
            uuid=vm_data.get('uuid'),
            status=VMStatus.STOPPED,
            server_id=server_id,
            cpu_cores=vm_data.get('cpu_cores', 1),
            memory_mb=vm_data.get('memory_mb', 512)
        )
        # Save to database...
        
        await event_broadcaster.broadcast_progress_update(
            operation_id=operation_id,
            operation_type="vm_creation", 
            progress_percent=40,
            status="in_progress",
            message="Creating VM definition..."
        )
        
        # Broadcast VM created event
        await event_broadcaster.broadcast_vm_created({
            "id": vm.id,
            "name": vm.name,
            "uuid": vm.uuid,
            "status": vm.status.value,
            "server_id": vm.server_id
        })
        
        # Step 3: Install OS (80%)
        await asyncio.sleep(2)  # Simulate OS installation
        await event_broadcaster.broadcast_progress_update(
            operation_id=operation_id,
            operation_type="vm_creation",
            progress_percent=80,
            status="in_progress", 
            message="Installing operating system..."
        )
        
        # Step 4: Start VM (100%)
        vm.status = VMStatus.RUNNING
        # Update in database...
        
        await event_broadcaster.broadcast_progress_update(
            operation_id=operation_id,
            operation_type="vm_creation",
            progress_percent=100,
            status="completed",
            message="VM created successfully"
        )
        
        # Broadcast status change
        await event_broadcaster.broadcast_vm_status_change(
            vm_id=vm.id,
            vm_name=vm.name,
            old_status="stopped",
            new_status="running"
        )
        
        return vm
        
    except Exception as e:
        # Broadcast failure
        await event_broadcaster.broadcast_progress_update(
            operation_id=operation_id,
            operation_type="vm_creation",
            progress_percent=0,
            status="failed",
            message=f"VM creation failed: {str(e)}"
        )
        
        # Broadcast alert
        await event_broadcaster.broadcast_alert(
            alert_id=f"vm-create-error-{datetime.utcnow().timestamp()}",
            alert_type="operation_failure",
            severity="error",
            title="VM Creation Failed",
            message=f"Failed to create VM '{vm_data['name']}': {str(e)}",
            entity_type="server",
            entity_id=server_id
        )
        
        raise


async def update_vm_status_with_events(vm_id: int, new_status: VMStatus):
    """Update VM status and broadcast events."""
    # Get VM from database
    vm = get_vm_by_id(vm_id)  # Implement this function
    if not vm:
        return False
    
    old_status = vm.status
    vm.status = new_status
    # Update in database...
    
    # Broadcast status change
    await event_broadcaster.broadcast_vm_status_change(
        vm_id=vm.id,
        vm_name=vm.name,
        old_status=old_status.value,
        new_status=new_status.value
    )
    
    # Send alert for critical status changes
    if new_status == VMStatus.ERROR:
        await event_broadcaster.broadcast_alert(
            alert_id=f"vm-error-{vm.id}-{datetime.utcnow().timestamp()}",
            alert_type="vm_error",
            severity="error",
            title="VM Error State",
            message=f"VM '{vm.name}' has entered error state",
            entity_type="vm",
            entity_id=vm.id
        )
    
    return True


async def update_vm_metrics_with_events(vm_id: int, metrics: dict):
    """Update VM metrics and broadcast if significant changes."""
    vm = get_vm_by_id(vm_id)
    if not vm:
        return
    
    # Always broadcast metrics for real-time monitoring
    await event_broadcaster.broadcast_vm_metrics(
        vm_id=vm.id,
        vm_name=vm.name,
        metrics=metrics
    )
    
    # Check for alerts
    cpu_usage = metrics.get('cpu_usage_percent', 0)
    memory_usage = metrics.get('memory_usage_percent', 0)
    
    if cpu_usage > 90:
        await event_broadcaster.broadcast_alert(
            alert_id=f"vm-cpu-high-{vm.id}-{datetime.utcnow().timestamp()}",
            alert_type="resource_warning",
            severity="warning",
            title="High CPU Usage",
            message=f"VM '{vm.name}' CPU usage is {cpu_usage}%",
            entity_type="vm",
            entity_id=vm.id
        )
    
    if memory_usage > 95:
        await event_broadcaster.broadcast_alert(
            alert_id=f"vm-memory-high-{vm.id}-{datetime.utcnow().timestamp()}",
            alert_type="resource_critical",
            severity="critical", 
            title="Critical Memory Usage",
            message=f"VM '{vm.name}' memory usage is {memory_usage}%",
            entity_type="vm",
            entity_id=vm.id
        )


async def delete_vm_with_events(vm_id: int):
    """Delete VM with progress tracking and events."""
    vm = get_vm_by_id(vm_id)
    if not vm:
        return False
    
    operation_id = f"vm-delete-{vm.id}-{datetime.utcnow().timestamp()}"
    
    try:
        # Start deletion
        await event_broadcaster.broadcast_progress_update(
            operation_id=operation_id,
            operation_type="vm_deletion",
            progress_percent=0,
            status="starting",
            message="Starting VM deletion..."
        )
        
        # Stop VM if running
        if vm.status == VMStatus.RUNNING:
            await event_broadcaster.broadcast_progress_update(
                operation_id=operation_id,
                operation_type="vm_deletion",
                progress_percent=25,
                status="in_progress",
                message="Stopping VM..."
            )
            
            vm.status = VMStatus.STOPPED
            await event_broadcaster.broadcast_vm_status_change(
                vm_id=vm.id,
                vm_name=vm.name,
                old_status="running",
                new_status="stopped"
            )
        
        # Delete VM resources
        await event_broadcaster.broadcast_progress_update(
            operation_id=operation_id,
            operation_type="vm_deletion",
            progress_percent=75,
            status="in_progress",
            message="Deleting VM resources..."
        )
        
        # Remove from database
        # delete_vm_from_db(vm.id)
        
        await event_broadcaster.broadcast_progress_update(
            operation_id=operation_id,
            operation_type="vm_deletion",
            progress_percent=100,
            status="completed",
            message="VM deleted successfully"
        )
        
        # Broadcast deletion event
        await event_broadcaster.broadcast_vm_deleted(
            vm_id=vm.id,
            vm_name=vm.name
        )
        
        return True
        
    except Exception as e:
        await event_broadcaster.broadcast_progress_update(
            operation_id=operation_id,
            operation_type="vm_deletion",
            progress_percent=0,
            status="failed",
            message=f"VM deletion failed: {str(e)}"
        )
        
        await event_broadcaster.broadcast_alert(
            alert_id=f"vm-delete-error-{vm.id}-{datetime.utcnow().timestamp()}",
            alert_type="operation_failure",
            severity="error", 
            title="VM Deletion Failed",
            message=f"Failed to delete VM '{vm.name}': {str(e)}",
            entity_type="vm",
            entity_id=vm.id
        )
        
        return False


# Server event examples

async def register_server_with_events(server_data: dict):
    """Register new server with events."""
    server = Server(
        hostname=server_data['hostname'],
        ip_address=server_data['ip_address'],
        status=ServerStatus.ONLINE,
        # ... other fields
    )
    # Save to database...
    
    await event_broadcaster.broadcast_server_registered({
        "id": server.id,
        "hostname": server.hostname,
        "ip_address": server.ip_address,
        "status": server.status.value
    })
    
    return server


async def update_server_metrics_with_events(server_id: int, metrics: dict):
    """Update server metrics and check for alerts."""
    server = get_server_by_id(server_id)
    if not server:
        return
    
    await event_broadcaster.broadcast_server_metrics(
        server_id=server.id,
        hostname=server.hostname,
        metrics=metrics
    )
    
    # Check for server-level alerts
    cpu_usage = metrics.get('cpu_usage_percent', 0)
    memory_usage = metrics.get('memory_usage_percent', 0)
    disk_usage = metrics.get('disk_usage_percent', 0)
    load_average = metrics.get('load_average', 0)
    
    if cpu_usage > 85:
        await event_broadcaster.broadcast_alert(
            alert_id=f"server-cpu-high-{server.id}-{datetime.utcnow().timestamp()}",
            alert_type="resource_warning",
            severity="warning",
            title="High Server CPU Usage",
            message=f"Server '{server.hostname}' CPU usage is {cpu_usage}%",
            entity_type="server",
            entity_id=server.id
        )
    
    if disk_usage > 90:
        await event_broadcaster.broadcast_alert(
            alert_id=f"server-disk-high-{server.id}-{datetime.utcnow().timestamp()}",
            alert_type="resource_critical",
            severity="critical",
            title="Critical Disk Usage",
            message=f"Server '{server.hostname}' disk usage is {disk_usage}%",
            entity_type="server",
            entity_id=server.id
        )


# Utility functions for integration

def get_vm_by_id(vm_id: int) -> VM:
    """Get VM by ID - implement with your database access."""
    # This would be implemented with your actual database access
    pass


def get_server_by_id(server_id: int) -> Server:
    """Get server by ID - implement with your database access."""
    # This would be implemented with your actual database access
    pass


# Background task example for periodic metrics collection

async def collect_metrics_periodically():
    """Background task to collect and broadcast metrics."""
    while True:
        try:
            # Collect VM metrics
            vms = get_all_vms()  # Implement this
            for vm in vms:
                if vm.status == VMStatus.RUNNING:
                    metrics = collect_vm_metrics(vm.id)  # Implement this
                    await update_vm_metrics_with_events(vm.id, metrics)
            
            # Collect server metrics
            servers = get_all_servers()  # Implement this
            for server in servers:
                if server.status == ServerStatus.ONLINE:
                    metrics = collect_server_metrics(server.id)  # Implement this
                    await update_server_metrics_with_events(server.id, metrics)
            
            # Wait 5 seconds before next collection
            await asyncio.sleep(5)
            
        except Exception as e:
            print(f"Error collecting metrics: {e}")
            await asyncio.sleep(30)  # Wait longer on error


def get_all_vms():
    """Get all VMs - implement with your database access."""
    pass


def get_all_servers():
    """Get all servers - implement with your database access."""
    pass


def collect_vm_metrics(vm_id: int) -> dict:
    """Collect VM metrics - implement with your virtualization platform."""
    # This would integrate with libvirt or your virtualization platform
    return {
        'cpu_usage_percent': 45.2,
        'memory_usage_percent': 60.1,
        'memory_used_mb': 512,
        'network_rx_bytes': 1048576,
        'network_tx_bytes': 524288,
        'disk_read_bytes': 2097152,
        'disk_write_bytes': 1048576
    }


def collect_server_metrics(server_id: int) -> dict:
    """Collect server metrics - implement with your monitoring system."""
    # This would integrate with your server monitoring system
    return {
        'cpu_usage_percent': 35.8,
        'memory_usage_percent': 70.2,
        'memory_used_gb': 14.1,
        'memory_total_gb': 20.0,
        'disk_usage_percent': 45.0,
        'disk_used_gb': 180.0,
        'disk_total_gb': 400.0,
        'network_rx_bytes': 10485760,
        'network_tx_bytes': 5242880,
        'load_average': 1.8
    }