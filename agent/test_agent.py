"""Tests for VM Agent components."""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

# Import agent modules
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import AgentConfig, load_config, validate_config, get_agent_id
from api_client import APIClient
from metrics import MetricsCollector
from operations import VMOperations, VMOperationError


class TestAgentConfig:
    """Test agent configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = AgentConfig()
        
        assert config.agent_name == "vm-agent"
        assert config.backend_url == "https://localhost:8000"
        assert config.libvirt_uri == "qemu:///system"
        assert config.metrics_interval == 60
        assert config.heartbeat_interval == 30
        assert config.auto_register is True
    
    def test_config_validation_valid(self):
        """Test valid configuration."""
        config = AgentConfig(
            backend_url="https://example.com",
            libvirt_uri="qemu:///system"
        )
        
        validation = validate_config(config)
        assert validation["valid"] is True
        assert len(validation["issues"]) == 0
    
    def test_config_validation_invalid(self):
        """Test invalid configuration."""
        config = AgentConfig(
            backend_url="",
            libvirt_uri=""
        )
        
        validation = validate_config(config)
        assert validation["valid"] is False
        assert len(validation["issues"]) > 0
    
    def test_get_agent_id(self):
        """Test agent ID generation."""
        agent_id = get_agent_id()
        assert agent_id is not None
        assert len(agent_id) > 0
        assert "-" in agent_id  # Should contain hostname-mac format


class TestAPIClient:
    """Test API client functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.config = AgentConfig(
            backend_url="https://test-backend.com",
            api_timeout=10
        )
        self.client = APIClient(self.config)
    
    def test_client_initialization(self):
        """Test client initialization."""
        assert self.client.config == self.config
        assert self.client.agent_id is not None
        assert self.client.session is not None
    
    @patch('requests.Session.post')
    async def test_authenticate_success(self, mock_post):
        """Test successful authentication."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test-token"
        }
        mock_post.return_value = mock_response
        
        result = await self.client.authenticate()
        assert result is True
        assert self.client.token == "test-token"
    
    @patch('requests.Session.post')
    async def test_authenticate_failure(self, mock_post):
        """Test authentication failure."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response
        
        result = await self.client.authenticate()
        assert result is False
        assert self.client.token is None
    
    def teardown_method(self):
        """Cleanup after tests."""
        self.client.close()


class TestMetricsCollector:
    """Test metrics collection."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.collector = MetricsCollector()
    
    def test_collect_system_metrics(self):
        """Test system metrics collection."""
        metrics = self.collector.collect_system_metrics()
        
        assert "timestamp" in metrics
        assert "cpu" in metrics
        assert "memory" in metrics
        assert "disk" in metrics
        assert "network" in metrics
        assert "system" in metrics
        
        # Check CPU metrics
        assert "percent" in metrics["cpu"]
        assert "count" in metrics["cpu"]
        
        # Check memory metrics
        assert "total" in metrics["memory"]
        assert "available" in metrics["memory"]
        assert "percent" in metrics["memory"]
    
    @patch('agent.metrics.LIBVIRT_AVAILABLE', False)
    def test_collect_vm_metrics_no_libvirt(self):
        """Test VM metrics collection without libvirt."""
        metrics = self.collector.collect_vm_metrics()
        assert metrics == []
    
    def test_collect_all_metrics(self):
        """Test collecting all metrics."""
        all_metrics = self.collector.collect_all_metrics()
        
        assert "system" in all_metrics
        assert "vms" in all_metrics
        assert "collector_info" in all_metrics
        
        collector_info = all_metrics["collector_info"]
        assert "libvirt_available" in collector_info
        assert "libvirt_uri" in collector_info
        assert "collection_time" in collector_info
    
    def teardown_method(self):
        """Cleanup after tests."""
        self.collector.close()


class TestVMOperations:
    """Test VM operations."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.vm_ops = VMOperations()
    
    @patch('agent.operations.LIBVIRT_AVAILABLE', False)
    async def test_list_vms_no_libvirt(self):
        """Test listing VMs without libvirt."""
        with pytest.raises(VMOperationError, match="libvirt not available"):
            await self.vm_ops.list_vms()
    
    @patch('agent.operations.LIBVIRT_AVAILABLE', False)
    def test_health_check_no_libvirt(self):
        """Test health check without libvirt."""
        with pytest.raises(VMOperationError, match="libvirt not available"):
            self.vm_ops.health_check()
    
    async def test_execute_unknown_command(self):
        """Test executing unknown command."""
        command = {
            "operation": "unknown_operation"
        }
        
        result = await self.vm_ops.execute_command(command)
        assert result["success"] is False
        assert "Unknown operation" in result["message"]
    
    async def test_execute_list_command(self):
        """Test executing list command."""
        command = {
            "operation": "list"
        }
        
        with patch.object(self.vm_ops, 'list_vms') as mock_list:
            mock_list.return_value = []
            result = await self.vm_ops.execute_command(command)
            assert result["success"] is True
            assert "vms" in result
    
    def teardown_method(self):
        """Cleanup after tests."""
        self.vm_ops.close()


class TestIntegration:
    """Integration tests."""
    
    def test_config_loading_from_env(self):
        """Test loading configuration from environment variables."""
        with patch.dict(os.environ, {
            'AGENT_BACKEND_URL': 'https://test.example.com',
            'AGENT_AGENT_NAME': 'test-agent',
            'AGENT_METRICS_INTERVAL': '120'
        }):
            config = load_config()
            assert config.backend_url == 'https://test.example.com'
            assert config.agent_name == 'test-agent'
            assert config.metrics_interval == 120
    
    def test_agent_components_integration(self):
        """Test that agent components work together."""
        config = AgentConfig()
        
        # Test that all components can be initialized
        api_client = APIClient(config)
        metrics_collector = MetricsCollector(config.libvirt_uri)
        vm_operations = VMOperations(config.libvirt_uri)
        
        # Test that components have expected interfaces
        assert hasattr(api_client, 'authenticate')
        assert hasattr(metrics_collector, 'collect_all_metrics')
        assert hasattr(vm_operations, 'health_check')
        
        # Cleanup
        api_client.close()
        metrics_collector.close()
        vm_operations.close()


# Run tests if script is executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])