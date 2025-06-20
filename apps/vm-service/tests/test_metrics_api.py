"""Tests for metrics API endpoints."""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import app
from models.base import DatabaseSession
from models.server import Server, ServerStatus
from models.virtual_machine import VirtualMachine, VMStatus, OSType
from models.server_metrics import ServerMetrics
from models.vm_metrics import VMMetrics
from models.user import User


client = TestClient(app)


@pytest.fixture
def db_session():
    """Get database session for tests."""
    return DatabaseSession.get_session()


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_server(db_session: Session, test_user: User):
    """Create a test server."""
    server = Server(
        hostname="test-server",
        ip_address="192.168.1.100",
        port=22,
        status=ServerStatus.ONLINE,
        user_id=test_user.id,
        os_version="Ubuntu 22.04",
        cpu_cores=4,
        memory_gb=8.0,
        disk_gb=100.0
    )
    db_session.add(server)
    db_session.commit()
    db_session.refresh(server)
    return server


@pytest.fixture
def test_vm(db_session: Session, test_server: Server):
    """Create a test VM."""
    vm = VirtualMachine(
        name="test-vm",
        uuid="12345678-1234-1234-1234-123456789012",
        status=VMStatus.RUNNING,
        server_id=test_server.id,
        cpu_cores=2,
        memory_mb=2048,
        disk_gb=20.0,
        os_type=OSType.LINUX,
        os_version="Ubuntu 20.04"
    )
    db_session.add(vm)
    db_session.commit()
    db_session.refresh(vm)
    return vm


@pytest.fixture
def server_metrics_data(db_session: Session, test_server: Server):
    """Create test server metrics data."""
    metrics = []
    base_time = datetime.now() - timedelta(hours=1)
    
    for i in range(10):
        timestamp = base_time + timedelta(minutes=i * 5)
        
        # CPU usage metric
        cpu_metric = ServerMetrics(
            server_id=test_server.id,
            metric_name="cpu_usage",
            metric_value=50.0 + i * 5,  # Increasing CPU usage
            metric_unit="percent",
            timestamp=timestamp
        )
        metrics.append(cpu_metric)
        
        # Memory usage metric
        memory_metric = ServerMetrics(
            server_id=test_server.id,
            metric_name="memory_usage",
            metric_value=60.0 + i * 2,  # Increasing memory usage
            metric_unit="percent",
            timestamp=timestamp
        )
        metrics.append(memory_metric)
    
    db_session.add_all(metrics)
    db_session.commit()
    return metrics


@pytest.fixture
def vm_metrics_data(db_session: Session, test_vm: VirtualMachine):
    """Create test VM metrics data."""
    metrics = []
    base_time = datetime.now() - timedelta(hours=1)
    
    for i in range(10):
        timestamp = base_time + timedelta(minutes=i * 5)
        
        # CPU usage metric
        cpu_metric = VMMetrics(
            vm_id=test_vm.id,
            metric_name="cpu_usage",
            metric_value=30.0 + i * 3,  # Increasing CPU usage
            metric_unit="percent",
            timestamp=timestamp
        )
        metrics.append(cpu_metric)
        
        # Memory usage metric
        memory_metric = VMMetrics(
            vm_id=test_vm.id,
            metric_name="memory_usage",
            metric_value=40.0 + i * 2,  # Increasing memory usage
            metric_unit="percent",
            timestamp=timestamp
        )
        metrics.append(memory_metric)
    
    db_session.add_all(metrics)
    db_session.commit()
    return metrics


class TestMetricsAPI:
    """Test metrics API endpoints."""
    
    def test_get_server_metrics(self, test_server: Server, server_metrics_data):
        """Test getting server metrics."""
        # This test would need proper authentication setup
        # For now, we'll test the basic endpoint structure
        response = client.get(f"/api/metrics/servers/{test_server.id}")
        
        # Without proper auth, we expect 401 or 403
        assert response.status_code in [401, 403]
    
    def test_get_vm_metrics(self, test_vm: VirtualMachine, vm_metrics_data):
        """Test getting VM metrics."""
        response = client.get(f"/api/metrics/vms/{test_vm.id}")
        
        # Without proper auth, we expect 401 or 403
        assert response.status_code in [401, 403]
    
    def test_get_server_historical_metrics(self, test_server: Server, server_metrics_data):
        """Test getting server historical metrics."""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=2)
        
        response = client.get(
            f"/api/metrics/servers/{test_server.id}/history",
            params={
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "interval": "5m",
                "aggregation": "avg"
            }
        )
        
        # Without proper auth, we expect 401 or 403
        assert response.status_code in [401, 403]
    
    def test_get_vm_historical_metrics(self, test_vm: VirtualMachine, vm_metrics_data):
        """Test getting VM historical metrics."""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=2)
        
        response = client.get(
            f"/api/metrics/vms/{test_vm.id}/history",
            params={
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "interval": "5m",
                "aggregation": "avg"
            }
        )
        
        # Without proper auth, we expect 401 or 403
        assert response.status_code in [401, 403]
    
    def test_custom_metrics_query(self):
        """Test custom metrics query endpoint."""
        query_data = {
            "entity_type": "server",
            "metrics": ["cpu", "memory"],
            "start": (datetime.now() - timedelta(hours=1)).isoformat(),
            "end": datetime.now().isoformat(),
            "interval": "5m",
            "aggregation": "avg"
        }
        
        response = client.post("/api/metrics/query", json=query_data)
        
        # Without proper auth, we expect 401 or 403
        assert response.status_code in [401, 403]
    
    def test_get_alerts(self):
        """Test getting alerts."""
        response = client.get("/api/metrics/alerts")
        
        # Without proper auth, we expect 401 or 403
        assert response.status_code in [401, 403]
    
    def test_get_metrics_collection_status(self, test_server: Server):
        """Test getting metrics collection status."""
        response = client.get(f"/api/metrics/status/server/{test_server.id}")
        
        # Without proper auth, we expect 401 or 403
        assert response.status_code in [401, 403]
    
    def test_record_server_metric(self, test_server: Server):
        """Test recording a server metric."""
        response = client.post(
            f"/api/metrics/servers/{test_server.id}/record",
            params={
                "metric_name": "cpu_usage",
                "value": 75.5,
                "unit": "percent"
            }
        )
        
        # Without proper auth, we expect 401 or 403
        assert response.status_code in [401, 403]
    
    def test_record_vm_metric(self, test_vm: VirtualMachine):
        """Test recording a VM metric."""
        response = client.post(
            f"/api/metrics/vms/{test_vm.id}/record",
            params={
                "metric_name": "memory_usage",
                "value": 85.2,
                "unit": "percent"
            }
        )
        
        # Without proper auth, we expect 401 or 403
        assert response.status_code in [401, 403]


class TestMetricsService:
    """Test metrics service functionality."""
    
    def test_server_metrics_model(self, db_session: Session, test_server: Server):
        """Test ServerMetrics model functionality."""
        metric = ServerMetrics.record_metric(
            server_id=test_server.id,
            metric_name="cpu_usage",
            metric_value=75.5,
            metric_unit="percent"
        )
        
        assert metric.server_id == test_server.id
        assert metric.metric_name == "cpu_usage"
        assert metric.metric_value == 75.5
        assert metric.metric_unit == "percent"
        assert metric.formatted_value == "75.5 percent"
    
    def test_vm_metrics_model(self, db_session: Session, test_vm: VirtualMachine):
        """Test VMMetrics model functionality."""
        metric = VMMetrics.record_metric(
            vm_id=test_vm.id,
            metric_name="memory_usage",
            metric_value=85.2,
            metric_unit="percent"
        )
        
        assert metric.vm_id == test_vm.id
        assert metric.metric_name == "memory_usage"
        assert metric.metric_value == 85.2
        assert metric.metric_unit == "percent"
        assert metric.formatted_value == "85.2 percent"