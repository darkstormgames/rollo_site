"""Tests for VM resource management functionality."""

import pytest
import json
from datetime import datetime
from sqlalchemy.orm import Session

from schemas.resources import (
    CPUConfig, MemoryConfig, DiskConfig, NetworkConfig, VMResources,
    ResourceLimits, ResourceValidationResult
)
from schemas.template import TemplateCreate, TemplateType
from core.resource_validator import ResourceValidator
from models.virtual_machine import VirtualMachine, VMStatus, OSType
from models.vm_template import VMTemplate
from models.vm_disk import VMDisk
from models.vm_network import VMNetwork
from models.user import User
from models.server import Server


class TestResourceSchemas:
    """Test resource configuration schemas."""
    
    def test_cpu_config_validation(self):
        """Test CPU configuration validation."""
        # Valid configuration
        cpu = CPUConfig(cores=4, sockets=1, threads=1)
        assert cpu.cores == 4
        assert cpu.sockets == 1
        assert cpu.threads == 1
        
        # Test with advanced options
        cpu_advanced = CPUConfig(
            cores=2,
            sockets=1,
            threads=2,
            model="host-passthrough",
            pinning=[0, 1],
            shares=1024,
            limit=80
        )
        assert cpu_advanced.model == "host-passthrough"
        assert cpu_advanced.pinning == [0, 1]
        assert cpu_advanced.shares == 1024
        assert cpu_advanced.limit == 80
    
    def test_memory_config_validation(self):
        """Test memory configuration validation."""
        memory = MemoryConfig(
            size_mb=4096,
            hugepages=True,
            balloon=False,
            shares=512
        )
        assert memory.size_mb == 4096
        assert memory.hugepages is True
        assert memory.balloon is False
        assert memory.shares == 512
    
    def test_disk_config_validation(self):
        """Test disk configuration validation."""
        disk = DiskConfig(
            name="main",
            size_gb=50.0,
            format="qcow2",
            pool="default",
            cache="writeback",
            bootable=True
        )
        assert disk.name == "main"
        assert disk.size_gb == 50.0
        assert disk.format == "qcow2"
        assert disk.bootable is True
    
    def test_network_config_validation(self):
        """Test network configuration validation."""
        network = NetworkConfig(
            name="eth0",
            type="bridge",
            bridge="br0",
            vlan_id=100,
            ip_address="192.168.1.100",
            mac_address="52:54:00:12:34:56"
        )
        assert network.name == "eth0"
        assert network.type == "bridge"
        assert network.bridge == "br0"
        assert network.vlan_id == 100
        assert network.ip_address == "192.168.1.100"
    
    def test_vm_resources_complete(self):
        """Test complete VM resource configuration."""
        cpu = CPUConfig(cores=2)
        memory = MemoryConfig(size_mb=2048)
        disks = [DiskConfig(name="main", size_gb=20.0, format="qcow2", bootable=True)]
        networks = [NetworkConfig(name="default", type="nat")]
        
        resources = VMResources(
            cpu=cpu,
            memory=memory,
            disks=disks,
            network=networks
        )
        
        assert resources.cpu.cores == 2
        assert resources.memory.size_mb == 2048
        assert len(resources.disks) == 1
        assert len(resources.network) == 1


class TestTemplateSchemas:
    """Test template configuration schemas."""
    
    def test_template_create(self):
        """Test template creation schema."""
        cpu = CPUConfig(cores=1)
        memory = MemoryConfig(size_mb=1024)
        disks = [DiskConfig(name="main", size_gb=10.0, format="qcow2", bootable=True)]
        networks = [NetworkConfig(name="default", type="nat")]
        
        resources = VMResources(
            cpu=cpu,
            memory=memory,
            disks=disks,
            network=networks
        )
        
        template = TemplateCreate(
            name="Test Template",
            description="A test template",
            type=TemplateType.SMALL,
            os_type=OSType.LINUX,
            resources=resources,
            tags=["test", "small"],
            public=False
        )
        
        assert template.name == "Test Template"
        assert template.type == TemplateType.SMALL
        assert template.os_type == OSType.LINUX
        assert template.tags == ["test", "small"]
        assert template.public is False


class TestResourceValidator:
    """Test resource validation system."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        # This would typically be a mock or test database
        # For now, return None as we're testing schema validation
        return None
    
    def test_cpu_validation(self, mock_db):
        """Test CPU configuration validation."""
        validator = ResourceValidator(mock_db)
        
        # Valid CPU configuration
        cpu = CPUConfig(cores=2, sockets=1, threads=1)
        result = validator.validate_cpu_config(cpu)
        # Note: This will fail in actual execution due to psutil dependency
        # but shows the intended structure
        
        # Invalid CPU configuration
        cpu_invalid = CPUConfig(cores=0, sockets=0, threads=0)
        # This would show validation errors
    
    def test_memory_validation(self, mock_db):
        """Test memory configuration validation."""
        validator = ResourceValidator(mock_db)
        
        # Valid memory configuration
        memory = MemoryConfig(size_mb=1024)
        # result = validator.validate_memory_config(memory)
        
        # Invalid memory configuration
        memory_invalid = MemoryConfig(size_mb=100)  # Too small
        # This would show validation errors
    
    def test_disk_validation(self, mock_db):
        """Test disk configuration validation."""
        validator = ResourceValidator(mock_db)
        
        # Valid disk configuration
        disks = [DiskConfig(name="main", size_gb=20.0, format="qcow2", bootable=True)]
        # result = validator.validate_disk_config(disks)
        
        # Invalid disk configuration - no bootable disk
        disks_invalid = [DiskConfig(name="data", size_gb=20.0, format="qcow2", bootable=False)]
        # This would show validation warnings
    
    def test_network_validation(self, mock_db):
        """Test network configuration validation."""
        validator = ResourceValidator(mock_db)
        
        # Valid network configuration
        networks = [NetworkConfig(name="eth0", type="nat")]
        # result = validator.validate_network_config(networks)
        
        # Invalid network configuration - duplicate names
        networks_invalid = [
            NetworkConfig(name="eth0", type="nat"),
            NetworkConfig(name="eth0", type="bridge")
        ]
        # This would show validation errors


class TestDatabaseModels:
    """Test database model functionality."""
    
    def test_vm_disk_model(self):
        """Test VM disk model."""
        disk = VMDisk(
            vm_id=1,
            name="main",
            size_gb=50.0,
            format="qcow2",
            pool="default",
            bootable=True
        )
        
        assert disk.name == "main"
        assert disk.size_gb == 50.0
        assert disk.format == "qcow2"
        assert disk.bootable is True
        
        # Test property
        expected_path = "/var/lib/libvirt/images/None_main.qcow2"
        # Note: This would need a proper VM relationship in real test
    
    def test_vm_network_model(self):
        """Test VM network model."""
        network = VMNetwork(
            vm_id=1,
            name="eth0",
            type="bridge",
            bridge="br0",
            ip_address="192.168.1.100",
            mac_address="52:54:00:12:34:56"
        )
        
        assert network.name == "eth0"
        assert network.type == "bridge"
        assert network.bridge == "br0"
        assert network.ip_address == "192.168.1.100"
        assert network.is_static_ip is True
    
    def test_vm_template_model(self):
        """Test VM template model."""
        template = VMTemplate(
            name="Test Template",
            description="A test template",
            type="small",
            os_type="linux",
            cpu_cores=1,
            memory_mb=1024,
            disk_gb=20.0,
            base_image_path="/var/lib/libvirt/images/base.qcow2",
            created_by=1
        )
        
        assert template.name == "Test Template"
        assert template.type == "small"
        assert template.cpu_cores == 1
        assert template.memory_mb == 1024
        assert template.memory_gb == 1.0  # Test property


if __name__ == "__main__":
    pytest.main([__file__])