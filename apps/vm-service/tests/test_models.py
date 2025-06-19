"""Test database models functionality."""

import pytest
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

# Add src to path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from models import User, Role, Server, VirtualMachine, VMTemplate, AuditLog, ServerMetrics, VMSnapshot
from models.server import ServerStatus
from models.virtual_machine import VMStatus, OSType


def test_user_model(db_session: Session):
    """Test User model creation and relationships."""
    user = User(
        username="testuser",
        email="test@example.com", 
        password_hash="hashed_password",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    assert user.id is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.is_active is True
    assert user.created_at is not None
    assert user.updated_at is not None


def test_role_model(db_session: Session):
    """Test Role model creation and permissions."""
    role = Role(
        name="test_role",
        permissions={"test.read": True, "test.write": False}
    )
    db_session.add(role)
    db_session.commit()
    
    assert role.id is not None
    assert role.name == "test_role"
    assert role.has_permission("test.read") is True
    assert role.has_permission("test.write") is False
    assert role.has_permission("nonexistent") is False
    
    # Test permission management
    role.add_permission("new.permission")
    assert role.has_permission("new.permission") is True
    
    role.remove_permission("test.read")
    assert role.has_permission("test.read") is False


def test_user_role_relationship(db_session: Session):
    """Test many-to-many relationship between users and roles."""
    user = User(username="testuser", email="test@example.com", password_hash="hash")
    role = Role(name="test_role", permissions={"test": True})
    
    user.roles.append(role)
    
    db_session.add(user)
    db_session.add(role)
    db_session.commit()
    
    assert len(user.roles) == 1
    assert user.roles[0].name == "test_role"
    assert len(role.users) == 1
    assert role.users[0].username == "testuser"


def test_server_model(db_session: Session):
    """Test Server model creation."""
    user = User(username="owner", email="owner@example.com", password_hash="hash")
    db_session.add(user)
    db_session.commit()
    
    server = Server(
        hostname="test-server",
        ip_address="192.168.1.100",
        port=22,
        status=ServerStatus.ONLINE,
        os_version="Ubuntu 22.04",
        cpu_cores=4,
        memory_gb=16.0,
        disk_gb=500.0,
        user_id=user.id
    )
    db_session.add(server)
    db_session.commit()
    
    assert server.id is not None
    assert server.hostname == "test-server"
    assert server.is_online is True
    assert server.vm_count == 0
    assert server.owner.username == "owner"


def test_virtual_machine_model(db_session: Session):
    """Test VirtualMachine model creation."""
    user = User(username="creator", email="creator@example.com", password_hash="hash")
    db_session.add(user)
    db_session.commit()
    
    server = Server(
        hostname="vm-host",
        ip_address="192.168.1.101", 
        port=22,
        status=ServerStatus.ONLINE,
        user_id=user.id
    )
    db_session.add(server)
    db_session.commit()
    
    vm = VirtualMachine(
        name="test-vm",
        uuid=str(uuid.uuid4()),
        status=VMStatus.RUNNING,
        server_id=server.id,
        cpu_cores=2,
        memory_mb=2048,
        disk_gb=50.0,
        os_type=OSType.LINUX,
        os_version="Ubuntu 22.04",
        created_by=user.id
    )
    db_session.add(vm)
    db_session.commit()
    
    assert vm.id is not None
    assert vm.is_running is True
    assert vm.memory_gb == 2.0
    assert vm.server.hostname == "vm-host"
    assert vm.created_by_user.username == "creator"


def test_vm_template_model(db_session: Session):
    """Test VMTemplate model creation."""
    user = User(username="template_creator", email="creator@example.com", password_hash="hash")
    db_session.add(user)
    db_session.commit()
    
    template = VMTemplate(
        name="ubuntu-basic",
        description="Basic Ubuntu template",
        os_type="linux",
        os_version="Ubuntu 22.04",
        cpu_cores=1,
        memory_mb=1024,
        disk_gb=20.0,
        base_image_path="/images/ubuntu-22.04.qcow2",
        created_by=user.id
    )
    db_session.add(template)
    db_session.commit()
    
    assert template.id is not None
    assert template.memory_gb == 1.0
    vm_dict = template.to_vm_dict()
    assert vm_dict["cpu_cores"] == 1
    assert vm_dict["memory_mb"] == 1024


def test_audit_log_model(db_session: Session):
    """Test AuditLog model creation."""
    user = User(username="auditor", email="auditor@example.com", password_hash="hash")
    db_session.add(user)
    db_session.commit()
    
    log = AuditLog.log_action(
        action="vm.create",
        resource_type="vm",
        user_id=user.id,
        resource_id=123,
        description="Created new VM",
        extra_data={"vm_name": "test-vm"},
        ip_address="192.168.1.50"
    )
    db_session.add(log)
    db_session.commit()
    
    assert log.id is not None
    assert log.action == "vm.create"
    assert log.user.username == "auditor"
    assert log.extra_data["vm_name"] == "test-vm"


def test_server_metrics_model(db_session: Session):
    """Test ServerMetrics model creation."""
    user = User(username="metrics_user", email="metrics@example.com", password_hash="hash")
    db_session.add(user)
    db_session.commit()
    
    server = Server(hostname="metrics-server", ip_address="192.168.1.102", port=22, user_id=user.id)
    db_session.add(server)
    db_session.commit()
    
    metric = ServerMetrics.record_metric(
        server_id=server.id,
        metric_name="cpu_usage", 
        metric_value=75.5,
        metric_unit="percent"
    )
    db_session.add(metric)
    db_session.commit()
    
    assert metric.id is not None
    assert metric.formatted_value == "75.5 percent"
    assert metric.server.hostname == "metrics-server"


def test_vm_snapshot_model(db_session: Session):
    """Test VMSnapshot model creation."""
    user = User(username="snapshot_user", email="snapshot@example.com", password_hash="hash")
    db_session.add(user)
    db_session.commit()
    
    server = Server(hostname="snapshot-server", ip_address="192.168.1.103", port=22, user_id=user.id)
    db_session.add(server)
    db_session.commit()
    
    vm = VirtualMachine(
        name="snapshot-vm",
        uuid=str(uuid.uuid4()),
        server_id=server.id,
        cpu_cores=1,
        memory_mb=1024,
        disk_gb=20.0,
        created_by=user.id
    )
    db_session.add(vm)
    db_session.commit()
    
    snapshot = VMSnapshot(
        vm_id=vm.id,
        name="initial-snapshot",
        description="Initial system state",
        snapshot_path="/snapshots/vm1_initial.qcow2",
        size_mb=512.0,
        is_active=True
    )
    db_session.add(snapshot)
    db_session.commit()
    
    assert snapshot.id is not None
    assert snapshot.size_gb == 0.5
    assert snapshot.formatted_size == "512.0 MB"
    assert snapshot.virtual_machine.name == "snapshot-vm"
    
    snapshot.mark_inactive()
    assert snapshot.is_active is False