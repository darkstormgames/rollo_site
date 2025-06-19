# VM Resource Management Implementation

This document provides a comprehensive overview of the VM resource allocation and configuration management features implemented for the rollo_site VM service.

## Overview

The implementation extends the existing VM management system with advanced resource allocation, configuration templates, and comprehensive validation. All changes were made with minimal disruption to existing functionality.

## Key Features Implemented

### 1. Enhanced Resource Models

#### CPU Management
- **Core allocation**: Support for 1-32 cores per VM
- **Socket/Thread configuration**: Configurable sockets (1-4) and threads per core (1-2)
- **CPU pinning**: Pin specific cores to physical CPU cores
- **CPU shares and limits**: Relative priority and percentage limits
- **NUMA topology**: NUMA node assignment for performance optimization
- **CPU model selection**: Support for host-passthrough and other models

#### Memory Management
- **RAM allocation**: Flexible memory allocation in MB (512MB-64GB)
- **Memory ballooning**: Dynamic memory adjustment support
- **Huge pages**: Large page support for performance
- **Memory overcommit**: Configurable overcommit ratios (0.5-2.0)
- **NUMA memory binding**: Memory allocation to specific NUMA nodes
- **Memory shares**: Relative memory priority

#### Storage Management
- **Multiple disk support**: Support for multiple disks per VM
- **Disk formats**: qcow2, raw, and vmdk format support
- **Storage pools**: Configurable storage pool assignment
- **Performance tuning**: Cache modes, discard/TRIM support
- **Bootable disk management**: Proper boot order and bootable disk tracking
- **Individual disk operations**: Add/remove disks dynamically

#### Network Configuration
- **Multiple interfaces**: Support for up to 5 network interfaces per VM
- **Network types**: NAT, bridge, and VLAN support
- **VLAN support**: VLAN ID configuration (1-4094)
- **IP address management**: Static IP configuration
- **MAC address control**: Custom MAC address assignment
- **Bandwidth limiting**: Configurable bandwidth limits

### 2. Template System

#### Predefined Templates
- **Small VM**: 1 CPU, 2GB RAM, 20GB disk
- **Medium VM**: 2 CPU, 4GB RAM, 40GB disk
- **Large VM**: 4 CPU, 8GB RAM, 80GB disk
- **Custom**: User-defined configurations

#### Template Features
- **Template versioning**: Version tracking for template changes
- **Public/Private sharing**: Templates can be shared or kept private
- **Tag system**: Categorization and filtering support
- **Resource validation**: Templates validated before creation
- **JSON configuration**: Flexible resource storage format

### 3. Resource Validation System

#### Validation Features
- **System limit checking**: Validates against host resource availability
- **Cross-validation**: Ensures resource configurations are compatible
- **Host resource tracking**: Monitors current allocation vs. available resources
- **Validation warnings**: Non-blocking warnings for optimization suggestions
- **Pre-validation**: Validate configurations before applying changes

#### Resource Limits
- **CPU limits**: Based on physical CPU availability
- **Memory limits**: Based on system RAM with safety margins
- **Disk limits**: Based on available storage space
- **Network limits**: Maximum interfaces and configuration validation

### 4. API Endpoints

#### Template Management
- `GET /api/templates` - List templates with filtering and pagination
- `POST /api/templates` - Create new template with validation
- `PUT /api/templates/{id}` - Update template (version incremented)
- `DELETE /api/templates/{id}` - Delete template (creator only)
- `GET /api/templates/predefined` - Get predefined template configurations

#### Resource Management
- `GET /api/vm/resource-limits` - Get system resource limits and availability
- `PUT /api/vm/{vm_id}/resources` - Update VM resources with validation
- `POST /api/vm/{vm_id}/resize` - Resize VM resources (legacy endpoint)

#### Disk Management
- `POST /api/vm/{vm_id}/disks` - Add new disk to VM
- `DELETE /api/vm/{vm_id}/disks/{disk_id}` - Remove disk from VM

## Database Schema Changes

### Enhanced VirtualMachine Model
```python
# Advanced CPU fields
cpu_sockets: int = 1
cpu_threads: int = 1
cpu_model: str = None
cpu_pinning: str = None  # JSON array
cpu_shares: int = None
cpu_limit: int = None
numa_nodes: str = None  # JSON array

# Advanced memory fields
memory_hugepages: bool = False
memory_balloon: bool = True
memory_shares: int = None
memory_numa_nodes: str = None  # JSON array
```

### Enhanced VMTemplate Model
```python
type: str = "custom"  # small, medium, large, custom
version: int = 1
resource_config: str = None  # JSON configuration
tags: str = None  # JSON array
public: bool = False
updated_at: datetime
```

### New VMDisk Model
```python
vm_id: int  # Foreign key
name: str
device_name: str = None
size_gb: float
format: str = "qcow2"
pool: str = "default"
path: str = None
cache: str = "writeback"
discard: bool = False
readonly: bool = False
bootable: bool = False
boot_order: int = None
status: str = "created"
```

### New VMNetwork Model
```python
vm_id: int  # Foreign key
name: str
device_name: str = None
type: str = "nat"
bridge: str = None
vlan_id: int = None
ip_address: str = None
netmask: str = None
gateway: str = None
mac_address: str = None  # Unique
bandwidth_limit: int = None
status: str = "configured"
```

## File Structure

### New Files Added
```
src/schemas/resources.py         # Resource configuration schemas
src/schemas/template.py          # Template management schemas
src/models/vm_disk.py           # Disk management model
src/models/vm_network.py        # Network interface model
src/core/resource_validator.py  # Resource validation system
src/api/template.py             # Template management API
tests/test_vm_resources.py      # Resource management tests
tests/test_vm_api_integration.py # API integration tests
```

### Modified Files
```
src/models/virtual_machine.py   # Added advanced resource fields
src/models/vm_template.py       # Enhanced with versioning
src/api/vm.py                   # Added resource management endpoints
src/app.py                      # Integrated template router
src/models/__init__.py          # Added new model exports
```

## Usage Examples

### Creating a Template
```python
POST /api/templates
{
    "name": "Development VM",
    "description": "Standard development environment",
    "type": "custom",
    "os_type": "linux",
    "resources": {
        "cpu": {
            "cores": 2,
            "sockets": 1,
            "threads": 1,
            "model": "host-passthrough"
        },
        "memory": {
            "size_mb": 4096,
            "hugepages": false,
            "balloon": true
        },
        "disks": [
            {
                "name": "main",
                "size_gb": 50.0,
                "format": "qcow2",
                "bootable": true
            }
        ],
        "network": [
            {
                "name": "default",
                "type": "nat"
            }
        ]
    },
    "tags": ["development", "linux"],
    "public": false
}
```

### Updating VM Resources
```python
PUT /api/vm/1/resources
{
    "cpu": {
        "cores": 4,
        "pinning": [0, 1, 2, 3],
        "shares": 1024
    },
    "memory": {
        "size_mb": 8192,
        "hugepages": true
    },
    "validate_only": false
}
```

### Adding a Disk
```python
POST /api/vm/1/disks
{
    "name": "data",
    "size_gb": 100.0,
    "format": "qcow2",
    "pool": "storage",
    "cache": "writeback",
    "discard": true
}
```

## Validation Rules

### Resource Constraints
- CPU cores: 1-32 per VM
- Memory: 512MB-64GB per VM
- Disks: 1GB-2TB per disk, max 10 disks per VM
- Networks: Max 5 interfaces per VM
- Total allocation cannot exceed host resources

### Template Constraints
- Template names must be unique
- Only template creators can modify templates
- Public templates visible to all users
- Resource configurations must pass validation

### System Limits
- Based on actual host resources using psutil
- Safety margins applied (80% memory, 90% disk)
- Real-time availability checking
- Current allocation tracking

## Migration Requirements

The database migration `001_vm_resources.py` adds:
- Advanced CPU/memory columns to virtual_machines table
- Enhanced template fields to vm_templates table
- New vm_disks table for disk management
- New vm_networks table for network management

## Testing

Comprehensive test suite includes:
- Schema validation tests
- Resource validation logic tests
- API endpoint integration tests
- Database model tests
- Template system tests

## Performance Considerations

- JSON storage for complex configurations allows flexibility
- Indexed columns for efficient querying
- Cascade deletion for cleanup
- Lazy loading for relationships
- Validation caching where appropriate

## Security Considerations

- Permission-based access control
- Resource limit enforcement
- Template ownership validation
- MAC address uniqueness
- IP address validation

## Future Enhancements

The modular design supports future additions:
- Hot-add/hot-remove operations
- Resource monitoring endpoints
- Advanced networking features
- Storage snapshot management
- Performance metrics collection