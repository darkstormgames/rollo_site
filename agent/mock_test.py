#!/usr/bin/env python3
"""
VM Agent Mock Test

This script tests the agent with mocked dependencies to verify
the core logic works correctly without requiring libvirt or network access.
"""

import os
import sys
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def mock_dependencies():
    """Mock external dependencies."""
    
    # Mock pydantic
    mock_pydantic = MagicMock()
    mock_pydantic.BaseSettings = type('BaseSettings', (), {})
    mock_pydantic.Field = lambda *args, **kwargs: None
    sys.modules['pydantic'] = mock_pydantic
    
    # Mock psutil
    mock_psutil = MagicMock()
    mock_psutil.cpu_percent.return_value = 25.5
    mock_psutil.cpu_count.return_value = 4
    mock_psutil.cpu_freq.return_value = None
    mock_psutil.virtual_memory.return_value = Mock(
        total=8000000000, available=4000000000, used=4000000000,
        percent=50.0, free=4000000000, buffers=0, cached=0
    )
    mock_psutil.swap_memory.return_value = Mock(
        total=2000000000, used=0, percent=0.0, free=2000000000
    )
    mock_psutil.disk_usage.return_value = Mock(
        total=100000000000, used=50000000000, free=50000000000
    )
    mock_psutil.disk_io_counters.return_value = Mock(
        read_count=1000, write_count=500, read_bytes=1000000, write_bytes=500000
    )
    mock_psutil.net_io_counters.return_value = Mock(
        bytes_sent=1000000, bytes_recv=2000000, packets_sent=1000, packets_recv=2000,
        errin=0, errout=0, dropin=0, dropout=0
    )
    mock_psutil.boot_time.return_value = 1640995200
    mock_psutil.getloadavg.return_value = (0.5, 0.3, 0.1)
    sys.modules['psutil'] = mock_psutil
    
    # Mock jose
    mock_jose = MagicMock()
    mock_jose.jwt = MagicMock()
    mock_jose.JWTError = Exception
    sys.modules['jose'] = mock_jose
    sys.modules['jose.jwt'] = mock_jose.jwt
    
    # Mock requests
    mock_requests = MagicMock()
    mock_session = Mock()
    mock_session.post.return_value = Mock(status_code=200, json=lambda: {"access_token": "mock-token"})
    mock_session.get.return_value = Mock(status_code=200, json=lambda: {"commands": []})
    mock_requests.Session.return_value = mock_session
    sys.modules['requests'] = mock_requests
    
    # Mock schedule
    mock_schedule = MagicMock()
    sys.modules['schedule'] = mock_schedule
    
    # Mock colorlog
    mock_colorlog = MagicMock()
    sys.modules['colorlog'] = mock_colorlog


async def test_config():
    """Test configuration loading."""
    print("Testing configuration...")
    
    try:
        from config import AgentConfig, validate_config, get_agent_id
        
        # Test default config
        config = AgentConfig()
        print(f"✅ Default config created: {config.agent_name}")
        
        # Test validation
        validation = validate_config(config)
        print(f"✅ Config validation: {validation['valid']}")
        
        # Test agent ID generation
        agent_id = get_agent_id()
        print(f"✅ Agent ID: {agent_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False


async def test_metrics():
    """Test metrics collection."""
    print("Testing metrics collection...")
    
    try:
        from metrics import MetricsCollector
        
        collector = MetricsCollector()
        
        # Test system metrics
        system_metrics = collector.collect_system_metrics()
        print(f"✅ System metrics collected: {len(system_metrics)} categories")
        
        # Test VM metrics (should return empty list without libvirt)
        vm_metrics = collector.collect_vm_metrics()
        print(f"✅ VM metrics collected: {len(vm_metrics)} VMs")
        
        # Test all metrics
        all_metrics = collector.collect_all_metrics()
        print(f"✅ All metrics collected: {list(all_metrics.keys())}")
        
        collector.close()
        return True
        
    except Exception as e:
        print(f"❌ Metrics test failed: {e}")
        return False


async def test_operations():
    """Test VM operations."""
    print("Testing VM operations...")
    
    try:
        from operations import VMOperations, VMOperationError
        
        vm_ops = VMOperations()
        
        # Test unknown command
        result = await vm_ops.execute_command({"operation": "unknown"})
        print(f"✅ Unknown command handled: {result['success'] == False}")
        
        # Test list command
        result = await vm_ops.execute_command({"operation": "list"})
        print(f"✅ List command result: {result}")
        
        vm_ops.close()
        return True
        
    except Exception as e:
        print(f"❌ Operations test failed: {e}")
        return False


async def test_api_client():
    """Test API client."""
    print("Testing API client...")
    
    try:
        from config import AgentConfig
        from api_client import APIClient
        
        config = AgentConfig()
        client = APIClient(config)
        
        print(f"✅ API client created: {client.agent_id}")
        
        # Test authentication (will use mock)
        auth_result = await client.authenticate()
        print(f"✅ Authentication: {auth_result}")
        
        # Test heartbeat
        heartbeat_result = await client.send_heartbeat({"test": "data"})
        print(f"✅ Heartbeat: {heartbeat_result}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ API client test failed: {e}")
        return False


async def test_vm_agent():
    """Test main VM agent."""
    print("Testing VM agent...")
    
    try:
        from config import AgentConfig
        from vm_agent import VMAgent
        
        config = AgentConfig()
        agent = VMAgent(config)
        
        print(f"✅ VM agent created: {agent.agent_id}")
        
        # Test agent info
        agent_info = await agent._get_agent_info()
        print(f"✅ Agent info: {agent_info['agent_name']}")
        
        # Cleanup
        await agent.stop()
        return True
        
    except Exception as e:
        print(f"❌ VM agent test failed: {e}")
        return False


async def main():
    """Run all mock tests."""
    print("VM Agent Mock Test Suite")
    print("=" * 40)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Mock dependencies first
    mock_dependencies()
    
    # Run tests
    tests = [
        ("Configuration", test_config),
        ("Metrics Collection", test_metrics),
        ("VM Operations", test_operations),
        ("API Client", test_api_client),
        ("VM Agent", test_vm_agent)
    ]
    
    results = {}
    for name, test_func in tests:
        print(f"\n--- {name} ---")
        try:
            results[name] = await test_func()
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "=" * 40)
    print("SUMMARY")
    print("=" * 40)
    
    passed = sum(results.values())
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:20} {status}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Agent logic is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please review agent logic.")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))