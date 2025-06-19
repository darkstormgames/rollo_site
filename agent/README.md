# VM Agent Service

A lightweight Python agent service that runs on remote Ubuntu/Debian servers to facilitate VM management operations and monitoring. The agent communicates securely with the main backend service and provides local libvirt operations.

## Features

- **Auto-registration** with main backend service
- **Heartbeat mechanism** for health monitoring
- **VM operations** via local libvirt (start, stop, restart, pause, resume, delete)
- **System and VM metrics** collection and reporting
- **Secure communication** with HTTPS and JWT authentication
- **Retry logic** with exponential backoff for network failures
- **Systemd integration** for reliable service management
- **Comprehensive logging** and error handling

## Architecture

### Core Components

1. **Agent Service** (`vm_agent.py`) - Main service orchestrating all operations
2. **Configuration Management** (`config.py`) - Environment-based configuration
3. **API Client** (`api_client.py`) - Secure communication with backend
4. **Metrics Collector** (`metrics.py`) - System and VM metrics collection
5. **VM Operations** (`operations.py`) - Local libvirt interface
6. **Systemd Service** - Service management and auto-start

### Communication Protocol

- HTTPS with optional mutual TLS authentication
- JWT token-based authorization
- Automatic token refresh
- Retry logic with exponential backoff
- Heartbeat mechanism for health monitoring

## Installation

### Automated Installation

```bash
# Download and run the installation script
sudo ./install.sh
```

The installation script will:
- Install system dependencies (Python 3, libvirt, etc.)
- Create VM agent user and directories
- Install Python dependencies in virtual environment
- Create systemd service
- Configure logging and log rotation
- Generate SSL certificates for testing

### Manual Installation

1. **Install system dependencies:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv python3-dev \
                 pkg-config libvirt-dev libvirt-daemon-system \
                 libvirt-clients qemu-kvm
```

2. **Create agent user and directories:**
```bash
sudo useradd --system --shell /bin/false --home-dir /opt/vm-agent \
             --create-home vm-agent
sudo usermod -a -G libvirt vm-agent
sudo mkdir -p /var/log/vm-agent /etc/vm-agent /var/lib/vm-agent
```

3. **Install agent:**
```bash
sudo cp *.py /opt/vm-agent/
sudo cp requirements.txt /opt/vm-agent/
sudo python3 -m venv /opt/vm-agent/venv
sudo /opt/vm-agent/venv/bin/pip install -r /opt/vm-agent/requirements.txt
```

4. **Install systemd service:**
```bash
sudo cp systemd/vm-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
```

## Configuration

Configuration is managed through environment variables or the configuration file `/etc/vm-agent/agent.env`.

### Required Configuration

```bash
# Backend server URL
AGENT_BACKEND_URL=https://your-backend-server.com

# Libvirt connection URI  
AGENT_LIBVIRT_URI=qemu:///system
```

### Optional Configuration

```bash
# Agent identification
AGENT_ID=auto-generated
AGENT_NAME=vm-agent

# Security
AGENT_TOKEN=your-agent-token
AGENT_SSL_VERIFY=true
AGENT_SSL_CERT_PATH=/etc/vm-agent/ssl/agent-cert.pem
AGENT_SSL_KEY_PATH=/etc/vm-agent/ssl/agent-key.pem

# Monitoring intervals (seconds)
AGENT_METRICS_INTERVAL=60
AGENT_HEARTBEAT_INTERVAL=30

# Network settings
AGENT_API_TIMEOUT=30
AGENT_RETRY_ATTEMPTS=3
AGENT_RETRY_BACKOFF=2.0

# Logging
AGENT_LOG_LEVEL=INFO
AGENT_LOG_FILE=/var/log/vm-agent/agent.log

# Features
AGENT_AUTO_REGISTER=true
AGENT_UPDATE_CHECK_INTERVAL=3600
```

## Usage

### Starting the Service

```bash
# Enable auto-start
sudo systemctl enable vm-agent

# Start the service
sudo systemctl start vm-agent

# Check status
sudo systemctl status vm-agent
```

### Monitoring

```bash
# View logs
sudo journalctl -u vm-agent -f

# View log file
sudo tail -f /var/log/vm-agent/agent.log

# Check agent status
curl -k https://backend-server/api/agent/status
```

### Manual Execution

```bash
# Run in foreground for testing
cd /opt/vm-agent
sudo -u vm-agent ./venv/bin/python vm_agent.py
```

## API Operations

The agent responds to the following operations from the backend:

### VM Operations
- `start` - Start a VM
- `stop` - Stop a VM (gracefully or forced)
- `restart` - Restart a VM
- `pause` - Pause a VM
- `resume` - Resume a paused VM
- `delete` - Delete a VM
- `list` - List all VMs
- `info` - Get VM information
- `snapshot` - Create VM snapshot

### Monitoring Operations
- `health_check` - Check libvirt connectivity
- `collect_metrics` - Collect system and VM metrics
- `agent_info` - Get comprehensive agent information

## Metrics Collected

### System Metrics
- CPU usage, frequency, core count
- Memory usage (RAM and swap)
- Disk usage and I/O statistics
- Network I/O statistics
- System uptime and load average

### VM Metrics
- VM state and basic information
- CPU time and statistics
- Memory usage and statistics
- Network interface statistics
- Disk I/O statistics
- VM uptime

## Security

### Authentication
- JWT token-based authentication
- Automatic token refresh
- Agent registration with unique ID

### Communication Security
- HTTPS with SSL/TLS encryption
- Optional mutual TLS authentication
- Certificate validation
- Secure credential storage

### System Security
- Runs as dedicated system user
- Limited file system access
- Resource limits via systemd
- No new privileges flag

## Troubleshooting

### Common Issues

1. **Agent fails to start:**
   - Check libvirt daemon is running: `systemctl status libvirtd`
   - Verify Python dependencies: `/opt/vm-agent/venv/bin/pip list`
   - Check configuration: `/etc/vm-agent/agent.env`

2. **Connection to backend fails:**
   - Verify backend URL is accessible
   - Check SSL certificate validation
   - Verify authentication token
   - Check firewall rules

3. **Libvirt operations fail:**
   - Ensure user is in libvirt group: `groups vm-agent`
   - Check libvirt permissions: `virsh -c qemu:///system list`
   - Verify QEMU/KVM is properly installed

### Log Levels

- `DEBUG` - Detailed debugging information
- `INFO` - General operational messages
- `WARNING` - Warning conditions
- `ERROR` - Error conditions
- `CRITICAL` - Critical errors

### Health Checks

The agent performs automatic health checks:
- Libvirt connectivity
- Backend communication
- System resource availability

## Dependencies

### System Requirements
- Ubuntu 18.04+ or Debian 10+
- Python 3.6+
- libvirt daemon
- QEMU/KVM virtualization

### Python Dependencies
- requests - HTTP client
- pydantic - Data validation
- psutil - System metrics
- libvirt-python - VM operations
- python-jose - JWT handling
- cryptography - Security utilities
- schedule - Task scheduling

## Development

### Running Tests

```bash
cd /opt/vm-agent
./venv/bin/python -m pytest tests/
```

### Configuration Validation

```bash
# Test configuration
./venv/bin/python -c "from config import load_config, validate_config; print(validate_config(load_config()))"
```

### Manual Testing

```bash
# Test libvirt connection
./venv/bin/python -c "from operations import VMOperations; print(VMOperations().health_check())"

# Test metrics collection
./venv/bin/python -c "from metrics import MetricsCollector; print(MetricsCollector().collect_system_metrics())"
```

## License

This project is licensed under the ISC License - see the main project license for details.

## Support

For issues and support:
1. Check the logs: `/var/log/vm-agent/agent.log`
2. Verify configuration: `/etc/vm-agent/agent.env`
3. Test connectivity to backend service
4. Check system dependencies and permissions