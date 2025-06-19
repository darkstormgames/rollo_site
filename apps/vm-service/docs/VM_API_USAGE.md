# VM Lifecycle API Endpoints

This document provides examples of how to use the newly implemented VM lifecycle API endpoints.

## Authentication

All endpoints require authentication using a Bearer token:

```bash
Authorization: Bearer <your-access-token>
```

## VM Management Endpoints

### List VMs
```bash
GET /api/vms?page=1&per_page=20&status=running&search=web-server
```

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 20, max: 100)
- `status` (optional): Filter by status (running, stopped, paused, etc.)
- `server_id` (optional): Filter by server ID
- `os_type` (optional): Filter by OS type (linux, windows, etc.)
- `search` (optional): Search in VM names

**Response:**
```json
{
  "vms": [
    {
      "id": 1,
      "name": "web-server-01",
      "uuid": "12345678-1234-1234-1234-123456789012",
      "status": "running",
      "server": {
        "id": 1,
        "hostname": "host1.example.com"
      },
      "resources": {
        "cpu_cores": 2,
        "memory_mb": 2048,
        "disk_gb": 20.0
      },
      "network": {
        "ip_address": "192.168.1.100",
        "mac_address": null
      },
      "os_type": "linux",
      "os_version": "Ubuntu 22.04",
      "vnc_port": 5901,
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 20,
  "total_pages": 1
}
```

### Get VM Details
```bash
GET /api/vms/1
```

**Response:** Single VM object (same structure as in list)

### Create VM
```bash
POST /api/vms
Content-Type: application/json

{
  "name": "my-new-vm",
  "server_id": 1,
  "cpu_cores": 2,
  "memory_mb": 2048,
  "disk_gb": 20.0,
  "os_type": "linux",
  "os_version": "Ubuntu 22.04",
  "network_config": {
    "type": "nat"
  }
}
```

**Response:** VM object with HTTP 201 Created

### Update VM
```bash
PUT /api/vms/1
Content-Type: application/json

{
  "name": "renamed-vm",
  "cpu_cores": 4,
  "memory_mb": 4096
}
```

### Delete VM
```bash
DELETE /api/vms/1?delete_disks=true
```

**Response:**
```json
{
  "message": "VM 'my-vm' deleted successfully",
  "detail": "Deleted disks: ['/path/to/disk.qcow2']"
}
```

## VM Operations Endpoints

### Start VM
```bash
POST /api/vms/1/start
```

**Response:**
```json
{
  "id": 1,
  "name": "my-vm",
  "operation": "start",
  "status": "success",
  "message": "VM started successfully",
  "details": {
    "name": "my-vm",
    "status": "started"
  }
}
```

### Stop VM (Graceful)
```bash
POST /api/vms/1/stop
```

### Force Stop VM
```bash
POST /api/vms/1/force-stop
```

### Restart VM
```bash
POST /api/vms/1/restart?force=false
```

### Reset VM (Hard Reset)
```bash
POST /api/vms/1/reset
```

## VM Configuration Endpoints

### Get VM Configuration
```bash
GET /api/vms/1/config
```

**Response:**
```json
{
  "id": 1,
  "name": "my-vm",
  "uuid": "12345678-1234-1234-1234-123456789012",
  "cpu_cores": 2,
  "memory_mb": 2048,
  "disk_gb": 20.0,
  "os_type": "linux",
  "os_version": "Ubuntu 22.04",
  "vnc_enabled": true,
  "vnc_port": 5901,
  "network_config": {
    "type": "nat",
    "bridge_name": null
  },
  "xml_config": null
}
```

### Update VM Configuration
```bash
PUT /api/vms/1/config
Content-Type: application/json

{
  "cpu_cores": 4,
  "memory_mb": 4096,
  "vnc_enabled": true
}
```

### Resize VM Resources
```bash
POST /api/vms/1/resize
Content-Type: application/json

{
  "cpu_cores": 4,
  "memory_mb": 8192,
  "disk_gb": 40.0
}
```

**Note:** VM must be stopped before resizing.

## Error Responses

All endpoints return appropriate HTTP status codes and error messages:

### 400 Bad Request
```json
{
  "detail": "VM must be stopped before resizing"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found
```json
{
  "detail": "VM with ID 999 not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to create VM: Disk creation failed"
}
```

### 503 Service Unavailable
```json
{
  "detail": "VM operations are not available - libvirt not configured"
}
```

## Required Permissions

- **Read Operations** (GET): Require `read` permission
- **Write Operations** (POST, PUT, DELETE): Require `write` permission

The permissions are enforced using the existing authentication and authorization system.