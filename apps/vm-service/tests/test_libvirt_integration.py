"""Unit tests for libvirt integration with mock libvirt."""

import pytest
import asyncio
import uuid
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

# Add src to path for imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from virtualization.libvirt_manager import LibvirtManager
from virtualization.vm_operations import VMOperations
from virtualization.resource_manager import ResourceManager
from virtualization.monitoring import VMMonitoring
from virtualization.templates import XMLTemplateGenerator
from virtualization.exceptions import (
    LibvirtConnectionError,
    VMNotFoundError,
    VMOperationError,
    ResourceAllocationError,
    TemplateGenerationError
)


class MockLibvirtDomain:
    """Mock libvirt domain object."""
    
    def __init__(self, name="test-vm", uuid_str="12345678-1234-1234-1234-123456789012", 
                 state=1, info=None):
        self._name = name
        self._uuid = uuid_str
        self._state = state
        self._info = info or [1, 2048000, 2048000, 2, 1000000000]  # state, max_mem, mem, vcpus, cpu_time
        self._xml = f"""
        <domain type="kvm">
          <name>{name}</name>
          <uuid>{uuid_str}</uuid>
          <memory unit="KiB">2048000</memory>
          <vcpu>2</vcpu>
          <devices>
            <disk type="file" device="disk">
              <source file="/var/lib/libvirt/images/{name}.qcow2"/>
              <target dev="vda" bus="virtio"/>
            </disk>
            <interface type="network">
              <source network="default"/>
              <target dev="vnet0"/>
            </interface>
          </devices>
        </domain>
        """
    
    def name(self):
        return self._name
    
    def UUIDString(self):
        return self._uuid
    
    def state(self):
        return (self._state, 0)
    
    def info(self):
        return self._info
    
    def XMLDesc(self, flags):
        return self._xml
    
    def create(self):
        return 0
    
    def destroy(self):
        return 0
    
    def shutdown(self):
        return 0
    
    def undefine(self):
        return 0
    
    def setMaxMemory(self, memory):
        return 0
    
    def setMemory(self, memory):
        return 0
    
    def setVcpus(self, vcpus):
        return 0
    
    def setVcpusFlags(self, vcpus, flags):
        return 0
    
    def maxMemory(self):
        return self._info[1]
    
    def isActive(self):
        return self._state == 1
    
    def getCPUStats(self, total):
        return [{'cpu_time': 1000000000, 'user_time': 500000000, 'system_time': 300000000}]
    
    def memoryStats(self):
        return {'total': 2048000, 'available': 1024000, 'used': 1024000}
    
    def blockStats(self, device):
        return (100, 1024000, 50, 512000, 0)
    
    def interfaceStats(self, device):
        return (1024000, 100, 0, 0, 512000, 50, 0, 0)
    
    def setSchedulerParameters(self, params):
        return 0
    
    def setMemoryParameters(self, params):
        return 0


class MockLibvirtConnection:
    """Mock libvirt connection object."""
    
    def __init__(self):
        self.domains = {}
    
    def getHostname(self):
        return "test-host"
    
    def getURI(self):
        return "qemu:///system"
    
    def getType(self):
        return "QEMU"
    
    def getLibVersion(self):
        return 8000000
    
    def getVersion(self):
        return 6002000
    
    def getInfo(self):
        return ["x86_64", 16777216, 8, 2400, 1, 2, 4, 2]
    
    def listDomainsID(self):
        return [1, 2]
    
    def listAllDomains(self):
        return list(self.domains.values())
    
    def lookupByName(self, name):
        for domain in self.domains.values():
            if domain.name() == name:
                return domain
        # Create a proper libvirt error mock that mimics the actual libvirt module
        class MockLibvirtError(Exception):
            def __init__(self, message):
                super().__init__(message)
                self.message = message
            def get_error_code(self):
                return 42
        raise MockLibvirtError("Domain not found")
    
    def lookupByUUIDString(self, uuid_str):
        if uuid_str in self.domains:
            return self.domains[uuid_str]
        # Create a proper libvirt error mock that mimics the actual libvirt module
        class MockLibvirtError(Exception):
            def __init__(self, message):
                super().__init__(message)
                self.message = message
            def get_error_code(self):
                return 42
        raise MockLibvirtError("Domain not found")
    
    def lookupByID(self, domain_id):
        return list(self.domains.values())[0] if self.domains else None
    
    def defineXML(self, xml):
        # Parse name and UUID from XML for mock
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml)
        name = root.find('name').text
        uuid_str = root.find('uuid').text
        
        domain = MockLibvirtDomain(name, uuid_str)
        self.domains[uuid_str] = domain
        return domain
    
    def getCPUStats(self, cpu):
        return {'user': 1000, 'system': 500, 'idle': 8500}
    
    def getMemoryStats(self, cell):
        return {'total': 16777216, 'free': 8388608}
    
    def close(self):
        pass
    
    def domainEventRegisterAny(self, domain, event_id, callback, opaque):
        return 0


@pytest.fixture
def mock_libvirt():
    """Mock libvirt module."""
    with patch('virtualization.libvirt_manager.libvirt') as mock_lib:
        # Setup mock constants
        mock_lib.VIR_ERR_NO_DOMAIN = 42
        mock_lib.VIR_DOMAIN_RUNNING = 1
        mock_lib.VIR_DOMAIN_SHUTOFF = 5
        mock_lib.VIR_DOMAIN_SHUTDOWN = 4
        mock_lib.VIR_DOMAIN_PAUSED = 3
        mock_lib.VIR_NODE_CPU_STATS_ALL_CPUS = -1
        mock_lib.VIR_NODE_MEMORY_STATS_ALL_CELLS = -1
        mock_lib.VIR_DOMAIN_VCPU_CONFIG = 2
        mock_lib.VIR_DOMAIN_EVENT_ID_LIFECYCLE = 0
        
        # Mock error class
        class MockLibvirtError(Exception):
            def __init__(self, message):
                super().__init__(message)
                self.message = message
            def get_error_code(self):
                return 42
        
        mock_lib.libvirtError = MockLibvirtError
        
        # Mock connection
        mock_conn = MockLibvirtConnection()
        mock_lib.open.return_value = mock_conn
        mock_lib.registerErrorHandler = Mock()
        mock_lib.virEventRunDefaultImpl = Mock()
        
        yield mock_lib, mock_conn


@pytest.fixture
def libvirt_manager(mock_libvirt):
    """LibvirtManager instance with mocked libvirt."""
    mock_lib, mock_conn = mock_libvirt
    manager = LibvirtManager("test:///default")
    return manager


@pytest.fixture
def vm_operations(libvirt_manager):
    """VMOperations instance."""
    return VMOperations(libvirt_manager)


@pytest.fixture
def resource_manager(libvirt_manager):
    """ResourceManager instance."""
    return ResourceManager(libvirt_manager)


@pytest.fixture
def vm_monitoring(libvirt_manager):
    """VMMonitoring instance."""
    return VMMonitoring(libvirt_manager)


@pytest.fixture
def xml_generator():
    """XMLTemplateGenerator instance."""
    return XMLTemplateGenerator()


class TestLibvirtManager:
    """Test LibvirtManager class."""
    
    def test_init(self, libvirt_manager):
        """Test LibvirtManager initialization."""
        assert libvirt_manager.uri == "test:///default"
        assert libvirt_manager._connection is None
    
    def test_connect(self, libvirt_manager, mock_libvirt):
        """Test connection establishment."""
        mock_lib, mock_conn = mock_libvirt
        
        connection = libvirt_manager.connect()
        assert connection is not None
        assert libvirt_manager._connection is not None
    
    def test_disconnect(self, libvirt_manager, mock_libvirt):
        """Test connection cleanup."""
        mock_lib, mock_conn = mock_libvirt
        
        libvirt_manager.connect()
        libvirt_manager.disconnect()
        assert libvirt_manager._connection is None
    
    def test_get_domain_by_name_success(self, libvirt_manager, mock_libvirt):
        """Test successful domain lookup by name."""
        mock_lib, mock_conn = mock_libvirt
        
        # Add a domain to the mock connection
        test_domain = MockLibvirtDomain("test-vm")
        mock_conn.domains["12345678-1234-1234-1234-123456789012"] = test_domain
        
        domain = libvirt_manager.get_domain_by_name("test-vm")
        assert domain.name() == "test-vm"
    
    def test_get_domain_by_name_not_found(self, libvirt_manager, mock_libvirt):
        """Test domain lookup by name when not found."""
        mock_lib, mock_conn = mock_libvirt
        
        with pytest.raises(VMNotFoundError):
            libvirt_manager.get_domain_by_name("nonexistent-vm")
    
    def test_get_hypervisor_info(self, libvirt_manager, mock_libvirt):
        """Test getting hypervisor information."""
        mock_lib, mock_conn = mock_libvirt
        
        info = libvirt_manager.get_hypervisor_info()
        assert info['hostname'] == "test-host"
        assert info['hypervisor_type'] == "QEMU"
        assert 'cpus' in info  # Updated field name
        assert 'memory_size_kb' in info
    
    @pytest.mark.asyncio
    async def test_health_check(self, libvirt_manager, mock_libvirt):
        """Test health check functionality."""
        mock_lib, mock_conn = mock_libvirt
        
        health = await libvirt_manager.health_check()
        assert health['status'] == 'healthy'
        assert health['hostname'] == 'test-host'


class TestVMOperations:
    """Test VMOperations class."""
    
    @pytest.mark.asyncio
    async def test_create_vm(self, vm_operations, mock_libvirt):
        """Test VM creation."""
        mock_lib, mock_conn = mock_libvirt
        
        with patch('virtualization.vm_operations.VMOperations._create_disk_image') as mock_disk:
            mock_disk.return_value = "/var/lib/libvirt/images/test-vm.qcow2"
            
            # Make lookupByName return None for non-existent VM (allowing creation)
            original_lookup = mock_conn.lookupByName
            def lookup_with_creation_check(name):
                if name == "test-vm":
                    # For the creation check, simulate VM doesn't exist initially
                    class MockLibvirtError(Exception):
                        def get_error_code(self):
                            return 42
                    raise MockLibvirtError("Domain not found")
                return original_lookup(name)
            
            mock_conn.lookupByName = lookup_with_creation_check
            
            result = await vm_operations.create_vm(
                name="test-vm",
                uuid="12345678-1234-1234-1234-123456789012",
                cpu_cores=2,
                memory_mb=2048,
                disk_gb=20.0
            )
            
            assert result['name'] == "test-vm"
            assert result['status'] == "created"
            assert 'disk_path' in result
    
    @pytest.mark.asyncio
    async def test_start_vm(self, vm_operations, mock_libvirt):
        """Test VM start operation."""
        mock_lib, mock_conn = mock_libvirt
        
        # Add a domain to the mock connection
        test_domain = MockLibvirtDomain("test-vm", state=5)  # SHUTOFF state
        mock_conn.domains["12345678-1234-1234-1234-123456789012"] = test_domain
        
        result = await vm_operations.start_vm(name="test-vm")
        assert result['name'] == "test-vm"
        assert result['status'] == "started"
    
    @pytest.mark.asyncio
    async def test_stop_vm(self, vm_operations, mock_libvirt):
        """Test VM stop operation."""
        mock_lib, mock_conn = mock_libvirt
        
        # Add a running domain to the mock connection
        test_domain = MockLibvirtDomain("test-vm", state=1)  # RUNNING state
        mock_conn.domains["12345678-1234-1234-1234-123456789012"] = test_domain
        
        result = await vm_operations.stop_vm(name="test-vm")
        assert result['name'] == "test-vm"
        assert result['status'] == "shutdown"
    
    @pytest.mark.asyncio
    async def test_get_vm_status(self, vm_operations, mock_libvirt):
        """Test getting VM status."""
        mock_lib, mock_conn = mock_libvirt
        
        # Add a domain to the mock connection
        test_domain = MockLibvirtDomain("test-vm")
        mock_conn.domains["12345678-1234-1234-1234-123456789012"] = test_domain
        
        status = await vm_operations.get_vm_status(name="test-vm")
        assert status['name'] == "test-vm"
        assert 'status' in status
        assert 'uuid' in status


class TestResourceManager:
    """Test ResourceManager class."""
    
    @pytest.mark.asyncio
    async def test_get_host_resources(self, resource_manager, mock_libvirt):
        """Test getting host resources."""
        mock_lib, mock_conn = mock_libvirt
        
        resources = await resource_manager.get_host_resources()
        assert 'total_memory_kb' in resources
        assert 'total_cpus' in resources
        assert resources['architecture'] == 'x86_64'
    
    @pytest.mark.asyncio
    async def test_get_allocated_resources(self, resource_manager, mock_libvirt):
        """Test getting allocated resources."""
        mock_lib, mock_conn = mock_libvirt
        
        # Add some domains
        test_domain1 = MockLibvirtDomain("vm1")
        test_domain2 = MockLibvirtDomain("vm2")
        mock_conn.domains["uuid1"] = test_domain1
        mock_conn.domains["uuid2"] = test_domain2
        
        resources = await resource_manager.get_allocated_resources()
        assert 'total_memory_kb' in resources
        assert 'total_vcpus' in resources
        assert 'total_vms' in resources
    
    @pytest.mark.asyncio
    async def test_validate_resource_allocation(self, resource_manager, mock_libvirt):
        """Test resource allocation validation."""
        mock_lib, mock_conn = mock_libvirt
        
        # Test valid allocation
        valid, message = await resource_manager.validate_resource_allocation(2, 1024)
        assert valid == True
        
        # Test invalid allocation (too much memory)
        valid, message = await resource_manager.validate_resource_allocation(2, 20000000)
        assert valid == False
        assert "memory" in message.lower()


class TestVMMonitoring:
    """Test VMMonitoring class."""
    
    @pytest.mark.asyncio
    async def test_get_vm_metrics(self, vm_monitoring, mock_libvirt):
        """Test getting VM metrics."""
        mock_lib, mock_conn = mock_libvirt
        
        # Add a running domain
        test_domain = MockLibvirtDomain("test-vm", state=1)  # RUNNING
        mock_conn.domains["12345678-1234-1234-1234-123456789012"] = test_domain
        
        metrics = await vm_monitoring.get_vm_metrics(name="test-vm")
        assert metrics['name'] == "test-vm"
        assert 'cpu_stats' in metrics
        assert 'memory_stats' in metrics
        assert 'timestamp' in metrics
    
    @pytest.mark.asyncio
    async def test_get_host_metrics(self, vm_monitoring, mock_libvirt):
        """Test getting host metrics."""
        mock_lib, mock_conn = mock_libvirt
        
        metrics = await vm_monitoring.get_host_metrics()
        assert metrics['hostname'] == "test-host"
        assert 'total_memory_kb' in metrics
        assert 'total_cpus' in metrics
        assert 'active_vms' in metrics
    
    @pytest.mark.asyncio
    async def test_get_all_vm_metrics(self, vm_monitoring, mock_libvirt):
        """Test getting metrics for all VMs."""
        mock_lib, mock_conn = mock_libvirt
        
        # Add some domains
        test_domain1 = MockLibvirtDomain("vm1")
        test_domain2 = MockLibvirtDomain("vm2")
        mock_conn.domains["uuid1"] = test_domain1
        mock_conn.domains["uuid2"] = test_domain2
        
        all_metrics = await vm_monitoring.get_all_vm_metrics()
        assert len(all_metrics) == 2
        assert all(isinstance(m, dict) for m in all_metrics)


class TestXMLTemplateGenerator:
    """Test XMLTemplateGenerator class."""
    
    def test_generate_vm_xml(self, xml_generator):
        """Test VM XML generation."""
        xml = xml_generator.generate_vm_xml(
            name="test-vm",
            cpu_cores=2,
            memory_mb=2048
        )
        
        assert "<name>test-vm</name>" in xml
        assert "<memory unit=\"MiB\">2048</memory>" in xml
        assert "<vcpu placement=\"static\">2</vcpu>" in xml
        
        # Validate XML structure
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml)
        assert root.tag == "domain"
        assert root.get("type") == "kvm"
    
    def test_generate_vm_xml_missing_name(self, xml_generator):
        """Test VM XML generation with missing required field."""
        with pytest.raises(TemplateGenerationError):
            xml_generator.generate_vm_xml(cpu_cores=2, memory_mb=2048)
    
    def test_generate_disk_xml(self, xml_generator):
        """Test disk XML generation."""
        xml = xml_generator.generate_disk_xml(
            path="/var/lib/libvirt/images/test.qcow2",
            target="vda"
        )
        
        assert "test.qcow2" in xml
        assert "vda" in xml
        assert "virtio" in xml
        
        # Validate XML structure
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml)
        assert root.tag == "disk"
    
    def test_generate_network_interface_xml(self, xml_generator):
        """Test network interface XML generation."""
        xml = xml_generator.generate_network_interface_xml(
            network="default",
            model="virtio"
        )
        
        assert "default" in xml
        assert "virtio" in xml
        
        # Validate XML structure
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml)
        assert root.tag == "interface"
    
    def test_create_vm_from_template(self, xml_generator):
        """Test creating VM XML from template."""
        template = {
            'name': 'template-vm',
            'cpu_cores': 4,
            'memory_mb': 4096
        }
        
        overrides = {
            'name': 'custom-vm',
            'memory_mb': 8192
        }
        
        xml = xml_generator.create_vm_from_template(template, overrides)
        
        assert "<name>custom-vm</name>" in xml
        assert "<memory unit=\"MiB\">8192</memory>" in xml
        assert "<vcpu placement=\"static\">4</vcpu>" in xml


class TestExceptions:
    """Test custom exceptions."""
    
    def test_libvirt_error(self):
        """Test base LibvirtError."""
        error = LibvirtConnectionError("Connection failed", error_code=1)
        assert str(error) == "Connection failed"
        assert error.error_code == 1
    
    def test_vm_not_found_error(self):
        """Test VMNotFoundError."""
        error = VMNotFoundError(vm_name="test-vm")
        assert "test-vm" in str(error)
        
        error = VMNotFoundError(vm_uuid="12345")
        assert "12345" in str(error)
    
    def test_vm_operation_error(self):
        """Test VMOperationError."""
        error = VMOperationError("start", "test-vm", "Failed to start")
        assert "start" in str(error)
        assert "test-vm" in str(error)
        assert "Failed to start" in str(error)
    
    def test_resource_allocation_error(self):
        """Test ResourceAllocationError."""
        error = ResourceAllocationError("memory", "8GB", "4GB")
        assert "memory" in str(error)
        assert "8GB" in str(error)
        assert "4GB" in str(error)
    
    def test_template_generation_error(self):
        """Test TemplateGenerationError."""
        error = TemplateGenerationError("vm", "Invalid template")
        assert "vm" in str(error)
        assert "Invalid template" in str(error)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])