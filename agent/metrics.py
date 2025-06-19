"""System and VM metrics collection."""

import time
import psutil
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import libvirt
    LIBVIRT_AVAILABLE = True
except ImportError:
    LIBVIRT_AVAILABLE = False
    logger.warning("libvirt not available - VM metrics will be limited")


class MetricsCollector:
    """Collect system and VM metrics."""
    
    def __init__(self, libvirt_uri: str = "qemu:///system"):
        """Initialize metrics collector."""
        self.libvirt_uri = libvirt_uri
        self._libvirt_conn = None
        self._last_network_stats = {}
        self._last_disk_stats = {}
        
    def _get_libvirt_connection(self):
        """Get or create libvirt connection."""
        if not LIBVIRT_AVAILABLE:
            return None
            
        try:
            if self._libvirt_conn is None or not self._is_connection_alive():
                self._libvirt_conn = libvirt.open(self.libvirt_uri)
            return self._libvirt_conn
        except Exception as e:
            logger.error(f"Failed to connect to libvirt: {e}")
            return None
    
    def _is_connection_alive(self) -> bool:
        """Check if libvirt connection is alive."""
        if not self._libvirt_conn:
            return False
        try:
            self._libvirt_conn.getVersion()
            return True
        except:
            return False
    
    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system-level metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk metrics
            disk_usage = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            # Network metrics
            network_io = psutil.net_io_counters()
            
            # Load average (Unix-like systems)
            load_avg = None
            try:
                load_avg = psutil.getloadavg()
            except AttributeError:
                # Not available on Windows
                pass
            
            # Boot time
            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time
            
            system_metrics = {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "frequency": {
                        "current": cpu_freq.current if cpu_freq else None,
                        "min": cpu_freq.min if cpu_freq else None,
                        "max": cpu_freq.max if cpu_freq else None
                    }
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "percent": memory.percent,
                    "free": memory.free,
                    "buffers": getattr(memory, 'buffers', 0),
                    "cached": getattr(memory, 'cached', 0)
                },
                "swap": {
                    "total": swap.total,
                    "used": swap.used,
                    "percent": swap.percent,
                    "free": swap.free
                },
                "disk": {
                    "total": disk_usage.total,
                    "used": disk_usage.used,
                    "free": disk_usage.free,
                    "percent": (disk_usage.used / disk_usage.total) * 100,
                    "io": {
                        "read_count": disk_io.read_count if disk_io else 0,
                        "write_count": disk_io.write_count if disk_io else 0,
                        "read_bytes": disk_io.read_bytes if disk_io else 0,
                        "write_bytes": disk_io.write_bytes if disk_io else 0
                    }
                },
                "network": {
                    "bytes_sent": network_io.bytes_sent if network_io else 0,
                    "bytes_recv": network_io.bytes_recv if network_io else 0,
                    "packets_sent": network_io.packets_sent if network_io else 0,
                    "packets_recv": network_io.packets_recv if network_io else 0,
                    "errin": network_io.errin if network_io else 0,
                    "errout": network_io.errout if network_io else 0,
                    "dropin": network_io.dropin if network_io else 0,
                    "dropout": network_io.dropout if network_io else 0
                },
                "system": {
                    "uptime": uptime,
                    "boot_time": boot_time,
                    "load_average": load_avg
                }
            }
            
            return system_metrics
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return {}
    
    def collect_vm_metrics(self) -> List[Dict[str, Any]]:
        """Collect VM-specific metrics."""
        vm_metrics = []
        
        if not LIBVIRT_AVAILABLE:
            logger.warning("libvirt not available - returning empty VM metrics")
            return vm_metrics
        
        conn = self._get_libvirt_connection()
        if not conn:
            logger.error("Could not connect to libvirt")
            return vm_metrics
        
        try:
            # Get all domains (VMs)
            domains = conn.listAllDomains()
            
            for domain in domains:
                try:
                    vm_metric = self._collect_single_vm_metrics(domain)
                    if vm_metric:
                        vm_metrics.append(vm_metric)
                except Exception as e:
                    logger.error(f"Failed to collect metrics for VM {domain.name()}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to list domains: {e}")
            
        return vm_metrics
    
    def _collect_single_vm_metrics(self, domain) -> Optional[Dict[str, Any]]:
        """Collect metrics for a single VM."""
        try:
            # Basic VM info
            vm_name = domain.name()
            vm_uuid = domain.UUIDString()
            state = domain.state()[0]
            
            # VM info
            info = domain.info()
            
            vm_metric = {
                "name": vm_name,
                "uuid": vm_uuid,
                "state": self._get_state_name(state),
                "timestamp": datetime.now().isoformat(),
                "max_memory": info[1] * 1024,  # Convert from KB to bytes
                "memory": info[2] * 1024,      # Convert from KB to bytes
                "vcpus": info[3],
                "cpu_time": info[4]
            }
            
            # Only collect detailed stats if VM is running
            if state == libvirt.VIR_DOMAIN_RUNNING:
                try:
                    # CPU statistics
                    cpu_stats = domain.getCPUStats(True)
                    vm_metric["cpu_stats"] = cpu_stats
                    
                    # Memory statistics
                    try:
                        memory_stats = domain.memoryStats()
                        vm_metric["memory_stats"] = memory_stats
                    except Exception:
                        pass  # Some VMs might not support memory stats
                    
                    # Network interface statistics
                    try:
                        network_stats = self._get_vm_network_stats(domain)
                        vm_metric["network_stats"] = network_stats
                    except Exception:
                        pass
                    
                    # Disk statistics
                    try:
                        disk_stats = self._get_vm_disk_stats(domain)
                        vm_metric["disk_stats"] = disk_stats
                    except Exception:
                        pass
                        
                except Exception as e:
                    logger.warning(f"Could not collect detailed stats for {vm_name}: {e}")
            
            return vm_metric
            
        except Exception as e:
            logger.error(f"Failed to collect VM metrics: {e}")
            return None
    
    def _get_vm_network_stats(self, domain) -> Dict[str, Any]:
        """Get network statistics for a VM."""
        network_stats = {}
        
        try:
            # Get network interfaces from domain XML
            xml_desc = domain.XMLDesc(0)
            # This is a simplified approach - in practice you'd parse the XML
            # to get actual interface names
            
            # Try common interface names
            for interface in ['vnet0', 'vnet1', 'vnet2', 'tap0', 'tap1']:
                try:
                    stats = domain.interfaceStats(interface)
                    network_stats[interface] = {
                        'rx_bytes': stats[0],
                        'rx_packets': stats[1],
                        'rx_errors': stats[2],
                        'rx_drops': stats[3],
                        'tx_bytes': stats[4],
                        'tx_packets': stats[5],
                        'tx_errors': stats[6],
                        'tx_drops': stats[7]
                    }
                except libvirt.libvirtError:
                    # Interface doesn't exist
                    continue
                    
        except Exception as e:
            logger.warning(f"Failed to get network stats: {e}")
            
        return network_stats
    
    def _get_vm_disk_stats(self, domain) -> Dict[str, Any]:
        """Get disk statistics for a VM."""
        disk_stats = {}
        
        try:
            # Get block devices from domain XML
            xml_desc = domain.XMLDesc(0)
            # This is a simplified approach - in practice you'd parse the XML
            # to get actual device names
            
            # Try common disk device names
            for device in ['vda', 'vdb', 'sda', 'sdb', 'hda', 'hdb']:
                try:
                    stats = domain.blockStats(device)
                    disk_stats[device] = {
                        'read_requests': stats[0],
                        'read_bytes': stats[1],
                        'write_requests': stats[2],
                        'write_bytes': stats[3],
                        'errors': stats[4] if len(stats) > 4 else 0
                    }
                except libvirt.libvirtError:
                    # Device doesn't exist
                    continue
                    
        except Exception as e:
            logger.warning(f"Failed to get disk stats: {e}")
            
        return disk_stats
    
    def _get_state_name(self, state: int) -> str:
        """Convert libvirt state code to readable name."""
        state_names = {
            libvirt.VIR_DOMAIN_NOSTATE: "no_state",
            libvirt.VIR_DOMAIN_RUNNING: "running",
            libvirt.VIR_DOMAIN_BLOCKED: "blocked",
            libvirt.VIR_DOMAIN_PAUSED: "paused",
            libvirt.VIR_DOMAIN_SHUTDOWN: "shutdown",
            libvirt.VIR_DOMAIN_SHUTOFF: "shutoff",
            libvirt.VIR_DOMAIN_CRASHED: "crashed",
            libvirt.VIR_DOMAIN_PMSUSPENDED: "pmsuspended"
        }
        return state_names.get(state, f"unknown_{state}")
    
    def collect_all_metrics(self) -> Dict[str, Any]:
        """Collect both system and VM metrics."""
        return {
            "system": self.collect_system_metrics(),
            "vms": self.collect_vm_metrics(),
            "collector_info": {
                "libvirt_available": LIBVIRT_AVAILABLE,
                "libvirt_uri": self.libvirt_uri,
                "collection_time": datetime.now().isoformat()
            }
        }
    
    def close(self):
        """Close libvirt connection."""
        if self._libvirt_conn:
            try:
                self._libvirt_conn.close()
            except:
                pass
            self._libvirt_conn = None