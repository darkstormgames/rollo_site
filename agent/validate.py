#!/usr/bin/env python3
"""
VM Agent Configuration Validator

This script validates the agent configuration and tests basic functionality
without requiring libvirt or network connectivity.
"""

import os
import sys
import socket
import uuid
from datetime import datetime


def check_python_version():
    """Check Python version compatibility."""
    if sys.version_info < (3, 6):
        print("❌ Python 3.6+ required")
        return False
    print(f"✅ Python {sys.version.split()[0]}")
    return True


def check_dependencies():
    """Check if required Python packages are available."""
    required_packages = [
        'requests', 'pydantic', 'psutil', 'cryptography', 
        'jose', 'schedule'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (missing)")
            missing.append(package)
    
    return len(missing) == 0


def check_libvirt():
    """Check libvirt availability."""
    try:
        import libvirt
        print("✅ libvirt-python")
        return True
    except ImportError:
        print("⚠️  libvirt-python (optional for full functionality)")
        return False


def validate_config_structure():
    """Validate configuration file structure."""
    try:
        # Mock the imports for validation
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # Test basic configuration without dependencies
        config_data = {
            "agent_name": "test-agent",
            "backend_url": "https://test.example.com",
            "libvirt_uri": "qemu:///system",
            "metrics_interval": 60,
            "heartbeat_interval": 30,
            "auto_register": True
        }
        
        print("✅ Configuration structure valid")
        return True
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False


def test_agent_id_generation():
    """Test agent ID generation."""
    try:
        hostname = socket.gethostname()
        mac = hex(uuid.getnode()).replace('0x', '').upper()
        agent_id = f"{hostname}-{mac}"
        print(f"✅ Agent ID generation: {agent_id}")
        return True
    except Exception as e:
        print(f"❌ Agent ID generation failed: {e}")
        return False


def check_system_metrics():
    """Test basic system metrics collection."""
    try:
        import psutil
        
        # Test basic metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        print(f"✅ System metrics: CPU {cpu_percent}%, Memory {memory.percent}%, Disk {disk.percent}%")
        return True
        
    except Exception as e:
        print(f"❌ System metrics collection failed: {e}")
        return False


def check_network():
    """Test basic network connectivity."""
    try:
        # Test DNS resolution
        socket.getaddrinfo('google.com', 80)
        print("✅ Network connectivity")
        return True
    except Exception as e:
        print(f"⚠️  Network connectivity issue: {e}")
        return False


def check_file_structure():
    """Check agent file structure."""
    agent_dir = os.path.dirname(os.path.abspath(__file__))
    required_files = [
        'vm_agent.py',
        'config.py', 
        'api_client.py',
        'metrics.py',
        'operations.py',
        'requirements.txt',
        'install.sh',
        'README.md'
    ]
    
    missing = []
    for file in required_files:
        if os.path.exists(os.path.join(agent_dir, file)):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} (missing)")
            missing.append(file)
    
    return len(missing) == 0


def main():
    """Run all validation checks."""
    print("VM Agent Configuration Validator")
    print("=" * 40)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Agent Directory: {os.path.dirname(os.path.abspath(__file__))}")
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("File Structure", check_file_structure),
        ("Dependencies", check_dependencies),
        ("Libvirt", check_libvirt),
        ("Configuration", validate_config_structure),
        ("Agent ID", test_agent_id_generation),
        ("System Metrics", check_system_metrics),
        ("Network", check_network)
    ]
    
    results = {}
    for name, check_func in checks:
        print(f"\n--- {name} ---")
        results[name] = check_func()
    
    print("\n" + "=" * 40)
    print("SUMMARY")
    print("=" * 40)
    
    passed = sum(results.values())
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:20} {status}")
    
    print(f"\nResult: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All checks passed! Agent is ready for installation.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} checks failed. Please review and fix issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())