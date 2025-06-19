# Enhanced VM Template System API Documentation

## Overview

The enhanced VM template system provides comprehensive functionality for creating, managing, and deploying virtual machines from predefined configurations and OS images. This system supports:

- **OS Templates**: Ubuntu, Debian, CentOS, Windows variants
- **Application Templates**: LAMP stack, Docker host, Kubernetes node, etc.
- **Resource Templates**: Development, Production, High-performance configurations
- **Image Management**: Upload, import, and manage OS images
- **Template Deployment**: Deploy VMs from templates with customization
- **Cloud-init Support**: Automated VM configuration on first boot

## Template Types

### Resource-Based Templates
- `small` - Small VM (1 CPU, 2GB RAM, 20GB disk)
- `medium` - Medium VM (2 CPUs, 4GB RAM, 40GB disk)
- `large` - Large VM (4 CPUs, 8GB RAM, 80GB disk)
- `custom` - Custom configuration

### OS Templates
- `ubuntu-20-04` - Ubuntu 20.04 LTS
- `ubuntu-22-04` - Ubuntu 22.04 LTS
- `ubuntu-24-04` - Ubuntu 24.04 LTS
- `debian-11` - Debian 11
- `debian-12` - Debian 12
- `centos-stream-8` - CentOS Stream 8
- `centos-stream-9` - CentOS Stream 9
- `windows-server-2012` - Windows Server 2012
- `windows-server-2016` - Windows Server 2016
- `windows-7` - Windows 7
- `windows-8-1` - Windows 8.1
- `windows-10` - Windows 10
- `windows-11` - Windows 11

### Application Templates
- `lamp-stack` - LAMP stack (Apache, MySQL, PHP)
- `docker-host` - Docker host with Docker CE
- `kubernetes-node` - Kubernetes node
- `database-server` - Database server
- `web-server` - Web server

### Resource Profile Templates
- `development` - Development environment (light resources)
- `production` - Production environment (balanced resources)
- `high-performance` - High-performance environment (max resources)

## API Endpoints

### Template Management

#### List Templates
```http
GET /api/templates
```

**Query Parameters:**
- `type` - Filter by template type
- `os_type` - Filter by OS type (linux, windows, bsd, other)
- `public` - Filter by public templates (true/false)
- `created_by` - Filter by creator user ID
- `page` - Page number (default: 1)
- `per_page` - Items per page (default: 20, max: 100)
- `search` - Search in template names
- `tags` - Filter by tags (array)

**Response:**
```json
{
  "templates": [
    {
      "id": 1,
      "name": "LAMP Stack Ubuntu 22.04",
      "description": "LAMP stack with Apache, MySQL, PHP on Ubuntu 22.04",
      "type": "lamp-stack",
      "os_type": "linux",
      "os_version": "22.04",
      "resources": {
        "cpu": {"cores": 2, "sockets": 1, "threads": 1},
        "memory": {"size_mb": 4096, "hugepages": false, "balloon": true},
        "disks": [{"name": "main", "size_gb": 60.0, "format": "qcow2", "bootable": true}],
        "network": [{"name": "default", "type": "nat"}]
      },
      "base_image_path": "/var/lib/libvirt/images/ubuntu-22.04.qcow2",
      "tags": ["lamp", "web-server", "apache", "mysql", "php"],
      "public": true,
      "created_by": 1,
      "created_at": "2024-06-19T18:30:00Z",
      "version": 1,
      "packages": ["apache2", "mysql-server", "php", "libapache2-mod-php", "php-mysql"],
      "cloud_init_config": "#cloud-config\npackages:\n  - apache2\n  - mysql-server\n...",
      "image_source": "https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img",
      "image_checksum": "sha256:...",
      "image_format": "qcow2",
      "startup_scripts": [],
      "network_config": {"bridge": "br0", "type": "dhcp"},
      "security_hardening": {"firewall": true, "fail2ban": true}
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 20,
  "total_pages": 1
}
```

#### Get Template Details
```http
GET /api/templates/{template_id}
```

**Response:** Single template object (same structure as in list)

#### Create Template
```http
POST /api/templates
```

**Request Body:**
```json
{
  "name": "My Custom Template",
  "description": "Custom template for development",
  "type": "custom",
  "os_type": "linux",
  "os_version": "22.04",
  "resources": {
    "cpu": {"cores": 2, "sockets": 1, "threads": 1},
    "memory": {"size_mb": 4096, "hugepages": false, "balloon": true},
    "disks": [{"name": "main", "size_gb": 40.0, "format": "qcow2", "bootable": true}],
    "network": [{"name": "default", "type": "nat"}]
  },
  "base_image_path": "/var/lib/libvirt/images/ubuntu-22.04.qcow2",
  "tags": ["development", "custom"],
  "public": false,
  "packages": ["git", "curl", "vim", "htop"],
  "cloud_init_config": "#cloud-config\npackages:\n  - git\n  - curl",
  "image_source": "https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img",
  "image_checksum": "sha256:abcdef...",
  "image_format": "qcow2",
  "startup_scripts": ["/opt/startup.sh"],
  "network_config": {"bridge": "br0", "ip": "192.168.1.100"},
  "security_hardening": {"firewall": true, "selinux": "enforcing"}
}
```

**Response:** Created template object

#### Update Template
```http
PUT /api/templates/{template_id}
```

**Request Body:** Partial template object (same fields as create, all optional)

**Response:** Updated template object

#### Delete Template
```http
DELETE /api/templates/{template_id}
```

**Response:**
```json
{
  "message": "Template 'My Custom Template' deleted successfully"
}
```

#### Get Predefined Templates
```http
GET /api/templates/predefined
```

**Response:** Array of predefined template objects

#### Deploy VM from Template
```http
POST /api/templates/{template_id}/deploy
```

**Request Body:**
```json
{
  "template_id": 1,
  "vm_name": "my-lamp-server",
  "hostname": "lamp.example.com",
  "custom_resources": {
    "cpu": {"cores": 4, "sockets": 1, "threads": 1},
    "memory": {"size_mb": 8192, "hugepages": false, "balloon": true},
    "disks": [{"name": "main", "size_gb": 100.0, "format": "qcow2", "bootable": true}],
    "network": [{"name": "default", "type": "nat"}]
  },
  "network_interfaces": [{"type": "bridge", "bridge": "br0"}],
  "custom_cloud_init": "#cloud-config\nhostname: lamp-server",
  "root_password": "secure_password",
  "ssh_keys": ["ssh-rsa AAAAB3NzaC1yc2EAAAA..."],
  "custom_packages": ["htop", "curl", "wget"],
  "environment_variables": {"ENV": "production", "DEBUG": "false"}
}
```

**Response:**
```json
{
  "vm_id": 123,
  "vm_name": "my-lamp-server",
  "vm_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "status": "created",
  "message": "VM 'my-lamp-server' successfully deployed from template 'LAMP Stack Ubuntu 22.04'",
  "template_used": {
    // Full template object that was used
  }
}
```

#### Get Template Versions
```http
GET /api/templates/{template_id}/versions
```

**Response:**
```json
{
  "template_id": 1,
  "current_version": 2,
  "versions": [
    {
      "version": 1,
      "created_at": "2024-06-19T18:30:00Z",
      "created_by": 1,
      "changes": "Initial version",
      "template_data": {
        // Template configuration at this version
      }
    },
    {
      "version": 2,
      "created_at": "2024-06-19T19:15:00Z",
      "created_by": 1,
      "changes": "Updated packages and security settings",
      "template_data": {
        // Template configuration at this version
      }
    }
  ]
}
```

### Image Management

#### List Images
```http
GET /api/images
```

**Query Parameters:**
- `page` - Page number (default: 1)
- `per_page` - Items per page (default: 20, max: 100)
- `search` - Search in image names
- `os_type` - Filter by OS type
- `status` - Filter by status (uploading, importing, available, error, deleted)
- `public` - Filter by public images (true/false)

**Response:**
```json
{
  "images": [
    {
      "id": 1,
      "name": "Ubuntu 22.04 LTS",
      "description": "Ubuntu 22.04 LTS Server Cloud Image",
      "os_type": "linux",
      "os_version": "22.04",
      "format": "qcow2",
      "file_path": "/var/lib/libvirt/images/ubuntu-22.04.qcow2",
      "source_url": "https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img",
      "checksum": "sha256:abcdef1234567890...",
      "size_gb": 2.5,
      "status": "available",
      "public": true,
      "created_by": 1,
      "created_at": "2024-06-19T18:30:00Z",
      "updated_at": "2024-06-19T18:30:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 20,
  "total_pages": 1
}
```

#### Get Image Details
```http
GET /api/images/{image_id}
```

**Response:** Single image object (same structure as in list)

#### Create Image Entry
```http
POST /api/images
```

**Request Body:**
```json
{
  "name": "CentOS 9 Stream",
  "description": "CentOS 9 Stream Cloud Image",
  "os_type": "linux",
  "os_version": "9",
  "format": "qcow2",
  "source_url": "https://cloud.centos.org/centos/9-stream/x86_64/images/CentOS-Stream-GenericCloud-9-latest.x86_64.qcow2",
  "checksum": "sha256:fedcba0987654321...",
  "size_gb": 3.0,
  "public": true
}
```

**Response:** Created image object

#### Upload Image File
```http
POST /api/images/upload
```

**Request:** Multipart form data
- `file` - Image file (qcow2, raw, vmdk, img)
- `name` - Image name
- `description` - Image description (optional)
- `os_type` - Operating system type
- `os_version` - OS version (optional)
- `public` - Whether image is public (default: false)

**Response:** Created image object with calculated checksum and size

#### Delete Image
```http
DELETE /api/images/{image_id}
```

**Response:**
```json
{
  "message": "Image 'Ubuntu 22.04 LTS' deleted successfully"
}
```

## Template Structure Example

Here's a complete example of an enhanced template structure:

```yaml
template:
  id: "ubuntu-22-04-web"
  name: "Ubuntu 22.04 Web Server"
  description: "Ubuntu with nginx pre-installed"
  type: "web-server"
  os:
    type: "linux"
    distro: "ubuntu"
    version: "22.04"
  image:
    source: "https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img"
    checksum: "sha256:abcdef1234567890..."
    format: "qcow2"
  resources:
    cpu:
      cores: 2
      sockets: 1
      threads: 1
    memory:
      size_mb: 4096
      hugepages: false
      balloon: true
    disks:
      - name: "main"
        size_gb: 40
        format: "qcow2"
        bootable: true
    network:
      - name: "default"
        type: "nat"
  packages:
    - nginx
    - php-fpm
    - mysql-client
  cloud_init:
    user_data: |
      #cloud-config
      packages:
        - nginx
        - php-fpm
      runcmd:
        - systemctl enable nginx
        - systemctl start nginx
  startup_scripts:
    - "/opt/configure-web-server.sh"
  network_config:
    bridge: "br0"
    type: "dhcp"
  security_hardening:
    firewall: true
    fail2ban: true
    ssh_key_only: true
  tags:
    - web-server
    - nginx
    - php
  version: 1
  public: true
```

## Authentication & Permissions

All endpoints require authentication. The following permissions are required:

- **read**: Required for GET operations (listing and viewing templates/images)
- **write**: Required for POST and PUT operations (creating and updating templates/images)
- **delete**: Required for DELETE operations

Users can only:
- View public templates/images and their own private ones
- Modify templates/images they created
- Deploy from any template they can view

## Error Handling

The API returns standard HTTP status codes:

- **200**: Success
- **201**: Created (for POST operations)
- **400**: Bad Request (validation errors)
- **401**: Unauthorized (authentication required)
- **403**: Forbidden (insufficient permissions)
- **404**: Not Found
- **500**: Internal Server Error

Error responses include details:
```json
{
  "detail": "Template with name 'My Template' already exists"
}
```

## Rate Limiting

API endpoints are rate-limited to prevent abuse:
- **General endpoints**: 60 requests per minute
- **Authentication endpoints**: 5 requests per minute

## Cloud-init Integration

The template system supports cloud-init for automated VM configuration. You can include:

- Package installation
- User creation
- SSH key setup
- Service configuration
- Custom scripts

Example cloud-init configuration:
```yaml
#cloud-config
packages:
  - docker.io
  - docker-compose
users:
  - name: devuser
    groups: docker
    sudo: ALL=(ALL) NOPASSWD:ALL
    ssh_authorized_keys:
      - ssh-rsa AAAAB3NzaC1yc2EAAAA...
runcmd:
  - systemctl enable docker
  - systemctl start docker
```

## Template Marketplace

Templates can be marked as public to share with other users. Public templates appear in the marketplace and can be:

- Searched and filtered
- Deployed by any user
- Used as base for creating custom templates
- Rated and reviewed (future feature)

## Deployment Workflow

1. **Select Template**: Choose from predefined or custom templates
2. **Customize Resources**: Override CPU, memory, disk, network settings
3. **Configure Network**: Set up network interfaces and IP addressing
4. **Set Credentials**: Configure root password and SSH keys
5. **Customize Software**: Add additional packages beyond template defaults
6. **Review Configuration**: Verify all settings before deployment
7. **Deploy VM**: Create and start the virtual machine
8. **Post-deployment**: Cloud-init runs to configure the VM

## Best Practices

### Template Creation
- Use descriptive names and detailed descriptions
- Include comprehensive package lists
- Test cloud-init configurations before publishing
- Tag templates appropriately for discoverability
- Document any manual configuration steps

### Image Management
- Verify checksums for downloaded images
- Keep images up to date with security patches
- Use consistent naming conventions
- Compress images to save storage space

### Deployment
- Always review resource allocations
- Use strong passwords and SSH keys
- Consider network security requirements
- Monitor VM resources after deployment
- Keep cloud-init logs for troubleshooting

### Security
- Regularly update base images
- Enable security hardening options
- Use firewall rules and fail2ban
- Limit network exposure
- Implement proper access controls