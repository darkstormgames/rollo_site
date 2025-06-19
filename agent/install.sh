#!/bin/bash
#
# VM Agent Installation Script for Ubuntu/Debian
#
# This script installs the VM Agent service on Ubuntu/Debian systems
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
AGENT_USER="vm-agent"
AGENT_HOME="/opt/vm-agent"
LOG_DIR="/var/log/vm-agent"
CONFIG_DIR="/etc/vm-agent"
DATA_DIR="/var/lib/vm-agent"

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root"
        exit 1
    fi
}

check_os() {
    if [[ ! -f /etc/debian_version ]]; then
        print_error "This script is designed for Ubuntu/Debian systems"
        exit 1
    fi
    
    print_status "Detected Debian-based system"
}

install_dependencies() {
    print_status "Installing system dependencies..."
    
    # Update package list
    apt-get update -q
    
    # Install required packages
    apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        pkg-config \
        libvirt-dev \
        libvirt-daemon-system \
        libvirt-clients \
        qemu-kvm \
        curl \
        wget \
        systemd
    
    # Enable and start libvirt
    systemctl enable libvirtd
    systemctl start libvirtd
    
    print_status "System dependencies installed"
}

create_user() {
    print_status "Creating VM Agent user..."
    
    # Create system user
    if ! id "$AGENT_USER" &>/dev/null; then
        useradd --system --shell /bin/false --home-dir "$AGENT_HOME" \
                --create-home --comment "VM Agent Service" "$AGENT_USER"
        print_status "Created user: $AGENT_USER"
    else
        print_status "User $AGENT_USER already exists"
    fi
    
    # Add user to libvirt group
    usermod -a -G libvirt "$AGENT_USER"
}

create_directories() {
    print_status "Creating directories..."
    
    # Create directories
    mkdir -p "$AGENT_HOME"
    mkdir -p "$LOG_DIR"
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$DATA_DIR"
    
    # Set permissions
    chown -R "$AGENT_USER:$AGENT_USER" "$AGENT_HOME"
    chown -R "$AGENT_USER:$AGENT_USER" "$LOG_DIR"
    chown -R root:root "$CONFIG_DIR"
    chown -R "$AGENT_USER:$AGENT_USER" "$DATA_DIR"
    
    chmod 755 "$AGENT_HOME"
    chmod 755 "$LOG_DIR"
    chmod 750 "$CONFIG_DIR"
    chmod 755 "$DATA_DIR"
}

install_agent() {
    print_status "Installing VM Agent..."
    
    # Copy agent files
    cp "$SCRIPT_DIR"/*.py "$AGENT_HOME/"
    cp "$SCRIPT_DIR/requirements.txt" "$AGENT_HOME/"
    
    # Create Python virtual environment
    python3 -m venv "$AGENT_HOME/venv"
    
    # Install Python dependencies
    "$AGENT_HOME/venv/bin/pip" install --upgrade pip
    "$AGENT_HOME/venv/bin/pip" install -r "$AGENT_HOME/requirements.txt"
    
    # Create wrapper script
    cat > "$AGENT_HOME/run_agent.sh" << 'EOF'
#!/bin/bash
cd /opt/vm-agent
exec ./venv/bin/python vm_agent.py
EOF
    
    chmod +x "$AGENT_HOME/run_agent.sh"
    
    # Set ownership
    chown -R "$AGENT_USER:$AGENT_USER" "$AGENT_HOME"
    
    print_status "VM Agent installed"
}

create_config() {
    print_status "Creating configuration..."
    
    # Create default configuration
    cat > "$CONFIG_DIR/agent.env" << EOF
# VM Agent Configuration
AGENT_BACKEND_URL=https://your-backend-server.com
AGENT_LIBVIRT_URI=qemu:///system
AGENT_LOG_LEVEL=INFO
AGENT_LOG_FILE=$LOG_DIR/agent.log
AGENT_METRICS_INTERVAL=60
AGENT_HEARTBEAT_INTERVAL=30
AGENT_AUTO_REGISTER=true
AGENT_SSL_VERIFY=true
EOF
    
    chmod 640 "$CONFIG_DIR/agent.env"
    chown root:"$AGENT_USER" "$CONFIG_DIR/agent.env"
    
    print_status "Configuration created at $CONFIG_DIR/agent.env"
    print_warning "Please edit $CONFIG_DIR/agent.env to configure your backend URL"
}

install_systemd_service() {
    print_status "Installing systemd service..."
    
    # Copy service file
    cp "$SCRIPT_DIR/systemd/vm-agent.service" /etc/systemd/system/
    
    # Update service file to use correct paths
    sed -i "s|/usr/bin/python3 /opt/vm-agent/vm_agent.py|$AGENT_HOME/run_agent.sh|g" /etc/systemd/system/vm-agent.service
    sed -i "s|/opt/vm-agent|$AGENT_HOME|g" /etc/systemd/system/vm-agent.service
    
    # Reload systemd
    systemctl daemon-reload
    
    print_status "Systemd service installed"
}

configure_logrotate() {
    print_status "Configuring log rotation..."
    
    cat > /etc/logrotate.d/vm-agent << EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $AGENT_USER $AGENT_USER
    postrotate
        systemctl reload vm-agent || true
    endscript
}
EOF
    
    print_status "Log rotation configured"
}

setup_firewall() {
    print_status "Checking firewall configuration..."
    
    # Check if ufw is installed and active
    if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
        print_warning "UFW firewall is active. You may need to allow outbound HTTPS traffic."
        print_warning "Run: ufw allow out 443/tcp"
    fi
    
    # Check if iptables rules might block outbound connections
    if iptables -L OUTPUT | grep -q "DROP\|REJECT"; then
        print_warning "Detected restrictive iptables rules. Ensure outbound HTTPS is allowed."
    fi
}

generate_ssl_cert() {
    print_status "Generating self-signed SSL certificate for testing..."
    
    SSL_DIR="$CONFIG_DIR/ssl"
    mkdir -p "$SSL_DIR"
    
    openssl req -x509 -newkey rsa:4096 -keyout "$SSL_DIR/agent-key.pem" \
                -out "$SSL_DIR/agent-cert.pem" -days 365 -nodes \
                -subj "/CN=$(hostname -f)"
    
    chmod 600 "$SSL_DIR/agent-key.pem"
    chmod 644 "$SSL_DIR/agent-cert.pem"
    chown -R root:"$AGENT_USER" "$SSL_DIR"
    
    print_status "SSL certificate generated at $SSL_DIR/"
}

show_next_steps() {
    print_status "Installation completed successfully!"
    echo
    echo "Next steps:"
    echo "1. Edit the configuration file: $CONFIG_DIR/agent.env"
    echo "   - Set AGENT_BACKEND_URL to your backend server URL"
    echo "   - Configure authentication tokens if needed"
    echo
    echo "2. Start the service:"
    echo "   systemctl enable vm-agent"
    echo "   systemctl start vm-agent"
    echo
    echo "3. Check service status:"
    echo "   systemctl status vm-agent"
    echo "   journalctl -u vm-agent -f"
    echo
    echo "4. View logs:"
    echo "   tail -f $LOG_DIR/agent.log"
    echo
    echo "Configuration file: $CONFIG_DIR/agent.env"
    echo "Service file: /etc/systemd/system/vm-agent.service"
    echo "Agent directory: $AGENT_HOME"
    echo "Log directory: $LOG_DIR"
}

# Main installation process
main() {
    print_status "Starting VM Agent installation..."
    
    check_root
    check_os
    install_dependencies
    create_user
    create_directories
    install_agent
    create_config
    install_systemd_service
    configure_logrotate
    setup_firewall
    generate_ssl_cert
    
    show_next_steps
}

# Run installation if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi