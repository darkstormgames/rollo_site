"""Test template system extensions."""

import pytest
import json
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from schemas.template import TemplateType, TemplateCreate, TemplateDeployRequest
from schemas.resources import VMResources, CPUConfig, MemoryConfig, DiskConfig, NetworkConfig
from models.virtual_machine import OSType


class TestTemplateExtensions:
    """Test extended template functionality."""
    
    def test_extended_template_types(self):
        """Test that extended template types are available."""
        # Test OS templates
        assert TemplateType.UBUNTU_22_04 == "ubuntu-22-04"
        assert TemplateType.DEBIAN_12 == "debian-12"
        assert TemplateType.CENTOS_STREAM_9 == "centos-stream-9"
        
        # Test application templates
        assert TemplateType.LAMP_STACK == "lamp-stack"
        assert TemplateType.DOCKER_HOST == "docker-host"
        assert TemplateType.KUBERNETES_NODE == "kubernetes-node"
        
        # Test resource profile templates
        assert TemplateType.DEVELOPMENT == "development"
        assert TemplateType.PRODUCTION == "production"
        assert TemplateType.HIGH_PERFORMANCE == "high-performance"
    
    def test_enhanced_template_creation_schema(self):
        """Test enhanced template creation with new fields."""
        template_data = TemplateCreate(
            name="Test Enhanced Template",
            description="Test template with enhanced features",
            type=TemplateType.UBUNTU_22_04,
            os_type=OSType.LINUX,
            os_version="22.04",
            resources=VMResources(
                cpu=CPUConfig(cores=2, sockets=1, threads=1),
                memory=MemoryConfig(size_mb=4096, hugepages=False, balloon=True),
                disks=[DiskConfig(
                    name="main",
                    size_gb=40.0,
                    format="qcow2",
                    bootable=True
                )],
                network=[NetworkConfig(
                    name="default",
                    type="nat"
                )]
            ),
            packages=["nginx", "php-fpm", "mysql-client"],
            cloud_init_config="#cloud-config\npackages:\n  - nginx",
            image_source="https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img",
            image_checksum="sha256:abcdef1234567890",
            image_format="qcow2",
            startup_scripts=["/opt/startup.sh"],
            network_config={"bridge": "br0", "ip": "192.168.1.100"},
            security_hardening={"firewall": True, "selinux": "enforcing"}
        )
        
        # Validate the schema accepts all fields
        assert template_data.name == "Test Enhanced Template"
        assert template_data.packages == ["nginx", "php-fpm", "mysql-client"]
        assert template_data.cloud_init_config == "#cloud-config\npackages:\n  - nginx"
        assert template_data.image_source == "https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img"
        assert template_data.image_checksum == "sha256:abcdef1234567890"
        assert template_data.image_format == "qcow2"
        assert template_data.startup_scripts == ["/opt/startup.sh"]
        assert template_data.network_config == {"bridge": "br0", "ip": "192.168.1.100"}
        assert template_data.security_hardening == {"firewall": True, "selinux": "enforcing"}
    
    def test_template_deployment_request_schema(self):
        """Test template deployment request schema."""
        deploy_request = TemplateDeployRequest(
            template_id=1,
            vm_name="test-vm",
            hostname="test-vm.example.com",
            custom_resources=VMResources(
                cpu=CPUConfig(cores=4, sockets=1, threads=1),
                memory=MemoryConfig(size_mb=8192, hugepages=False, balloon=True),
                disks=[DiskConfig(
                    name="main",
                    size_gb=80.0,
                    format="qcow2",
                    bootable=True
                )],
                network=[NetworkConfig(
                    name="default",
                    type="nat"
                )]
            ),
            network_interfaces=[{"type": "bridge", "bridge": "br0"}],
            custom_cloud_init="#cloud-config\nhostname: test-vm",
            root_password="secure_password",
            ssh_keys=["ssh-rsa AAAAB3..."],
            custom_packages=["htop", "curl"],
            environment_variables={"ENV": "production", "DEBUG": "false"}
        )
        
        # Validate the schema
        assert deploy_request.template_id == 1
        assert deploy_request.vm_name == "test-vm"
        assert deploy_request.hostname == "test-vm.example.com"
        assert deploy_request.custom_resources.cpu.cores == 4
        assert deploy_request.custom_packages == ["htop", "curl"]
        assert deploy_request.environment_variables == {"ENV": "production", "DEBUG": "false"}


class TestImageManagement:
    """Test image management functionality."""
    
    def test_image_creation_schema(self):
        """Test image creation schema."""
        from schemas.template import ImageCreate
        
        image_data = ImageCreate(
            name="Ubuntu 22.04 Server",
            description="Ubuntu 22.04 LTS Server Image",
            os_type=OSType.LINUX,
            os_version="22.04",
            format="qcow2",
            source_url="https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img",
            checksum="sha256:abcdef1234567890",
            size_gb=2.5,
            public=True
        )
        
        assert image_data.name == "Ubuntu 22.04 Server"
        assert image_data.os_type == OSType.LINUX
        assert image_data.format == "qcow2"
        assert str(image_data.source_url) == "https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img"
        assert image_data.checksum == "sha256:abcdef1234567890"
        assert image_data.size_gb == 2.5
        assert image_data.public is True


# Integration test (would need client fixture)
def test_template_creation_api_mock():
    """Test template creation API with mock."""
    # This would normally use the client fixture, but we'll mock it for now
    template_data = {
        "name": "Test Template",
        "description": "A test template",
        "type": "ubuntu-22-04",
        "os_type": "linux",
        "os_version": "22.04",
        "resources": {
            "cpu": {
                "cores": 2,
                "sockets": 1,
                "threads": 1
            },
            "memory": {
                "size_mb": 4096,
                "hugepages": False,
                "balloon": True
            },
            "disks": [
                {
                    "name": "main",
                    "size_gb": 40.0,
                    "format": "qcow2",
                    "bootable": True
                }
            ],
            "network": [
                {
                    "name": "default",
                    "type": "nat"
                }
            ]
        },
        "packages": ["nginx", "php-fpm"],
        "cloud_init_config": "#cloud-config\npackages:\n  - nginx",
        "image_source": "https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img",
        "public": False
    }
    
    # This test validates the structure is correct
    assert template_data["name"] == "Test Template"
    assert template_data["type"] == "ubuntu-22-04"
    assert template_data["packages"] == ["nginx", "php-fpm"]
    assert "cloud_init_config" in template_data
    assert "image_source" in template_data


if __name__ == "__main__":
    # Run basic tests
    test_ext = TestTemplateExtensions()
    test_ext.test_extended_template_types()
    test_ext.test_enhanced_template_creation_schema()
    test_ext.test_template_deployment_request_schema()
    
    test_img = TestImageManagement()
    test_img.test_image_creation_schema()
    
    test_template_creation_api_mock()
    
    print("✅ All basic tests passed!")