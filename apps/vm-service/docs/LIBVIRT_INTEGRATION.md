# Libvirt Integration for VM Management

This module provides comprehensive KVM/QEMU virtual machine management through libvirt API integration.

## Overview

The libvirt integration consists of several core components:

- **LibvirtManager**: Connection management and health checks
- **VMOperations**: VM lifecycle operations (create, start, stop, delete, clone)
- **ResourceManager**: CPU/memory allocation and resource limits
- **VMMonitoring**: Real-time metrics and event monitoring
- **XMLTemplateGenerator**: Flexible XML template generation for VM configurations

## Quick Start

### Basic VM Operations

```python
from virtualization import LibvirtManager, VMOperations

# Initialize managers
libvirt_manager = LibvirtManager()
vm_ops = VMOperations(libvirt_manager)

# Create a new VM
vm_result = await vm_ops.create_vm(
    name="test-vm",
    uuid="12345678-1234-1234-1234-123456789012",
    cpu_cores=2,
    memory_mb=2048,
    disk_gb=20.0,
    os_type="linux"
)

# Start the VM
start_result = await vm_ops.start_vm(name="test-vm")

# Get VM status
status = await vm_ops.get_vm_status(name="test-vm")

# Stop the VM
stop_result = await vm_ops.stop_vm(name="test-vm")
```

### Resource Management

```python
from virtualization import ResourceManager

resource_manager = ResourceManager(libvirt_manager)

# Check available resources
resources = await resource_manager.get_available_resources()

# Validate resource allocation
valid, message = await resource_manager.validate_resource_allocation(
    cpu_cores=4, 
    memory_mb=8192
)

# Update VM resources
update_result = await resource_manager.update_vm_resources(
    name="test-vm",
    cpu_cores=4,
    memory_mb=8192,
    live_update=True
)
```

### Monitoring and Metrics

```python
from virtualization import VMMonitoring

monitoring = VMMonitoring(libvirt_manager)

# Get VM metrics
metrics = await monitoring.get_vm_metrics(name="test-vm")

# Get host metrics
host_metrics = await monitoring.get_host_metrics()

# Monitor VM events
async def vm_event_handler(event_type, event_data):
    print(f"VM Event: {event_type} - {event_data}")

await monitoring.start_monitoring(vm_event_handler)
```

### XML Template Generation

```python
from virtualization import XMLTemplateGenerator

xml_gen = XMLTemplateGenerator()

# Generate VM XML
vm_xml = xml_gen.generate_vm_xml(
    name="example-vm",
    cpu_cores=2,
    memory_mb=4096,
    disks=[{
        'path': '/var/lib/libvirt/images/example-vm.qcow2',
        'target': 'vda'
    }],
    network_interfaces=[{
        'network': 'default'
    }]
)

# Generate from template
template = {
    'name': 'template-vm',
    'cpu_cores': 2,
    'memory_mb': 2048
}

overrides = {'memory_mb': 4096}
custom_xml = xml_gen.create_vm_from_template(template, overrides)
```

## Configuration

Set the following environment variables:

```bash
# Libvirt connection URI
LIBVIRT_URI=qemu:///system

# VM storage path
VM_STORAGE_PATH=/var/lib/libvirt/images
```

## Error Handling

The module provides comprehensive error handling with custom exceptions:

- `LibvirtConnectionError`: Connection issues
- `VMNotFoundError`: VM doesn't exist
- `VMOperationError`: VM operation failures
- `ResourceAllocationError`: Resource allocation problems
- `TemplateGenerationError`: XML template errors

```python
from virtualization.exceptions import VMNotFoundError, VMOperationError

try:
    await vm_ops.start_vm(name="nonexistent-vm")
except VMNotFoundError:
    print("VM not found")
except VMOperationError as e:
    print(f"VM operation failed: {e}")
```

## Health Checks

```python
# Check libvirt connectivity
health = await libvirt_manager.health_check()

if health['status'] == 'healthy':
    print(f"Connected to {health['hostname']}")
    print(f"Active VMs: {health['active_domains']}")
else:
    print(f"Health check failed: {health['error']}")
```

## Testing

The module includes comprehensive unit tests with mock libvirt integration:

```bash
# Run all libvirt integration tests
pytest tests/test_libvirt_integration.py -v

# Run specific test class
pytest tests/test_libvirt_integration.py::TestVMOperations -v
```

## Integration with FastAPI

The libvirt modules can be easily integrated with FastAPI endpoints:

```python
from fastapi import APIRouter, HTTPException
from virtualization import vm_operations

router = APIRouter()

@router.post("/vms/{vm_name}/start")
async def start_vm(vm_name: str):
    try:
        result = await vm_operations.start_vm(name=vm_name)
        return result
    except VMNotFoundError:
        raise HTTPException(status_code=404, detail="VM not found")
    except VMOperationError as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Performance Considerations

- Connection pooling reduces overhead for multiple operations
- Async operations prevent blocking
- Resource validation prevents system overcommit
- Event monitoring provides real-time updates
- XML template caching improves performance

## Security

- Proper error handling prevents information leakage
- Resource limits prevent resource exhaustion
- Connection management includes timeout handling
- Input validation for all XML template generation

## Future Enhancements

- Integration with time series databases for historical metrics
- Advanced networking configuration (bridges, VLANs)
- GPU passthrough support
- Live migration between hosts
- Backup and snapshot management
- Integration with cloud-init for VM provisioning