"""VM monitoring and metrics collection."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
import libvirt
import json

from .libvirt_manager import LibvirtManager
from .exceptions import LibvirtConnectionError, VMNotFoundError
from models.virtual_machine import VMStatus


logger = logging.getLogger(__name__)


class VMMonitoring:
    """Monitor VM status, events, and collect metrics."""
    
    def __init__(self, libvirt_manager: LibvirtManager = None):
        """Initialize VM monitoring.
        
        Args:
            libvirt_manager: LibvirtManager instance.
        """
        self.manager = libvirt_manager or LibvirtManager()
        self._event_callbacks: Dict[str, List[Callable]] = {}
        self._monitoring_active = False
        self._event_loop_task: Optional[asyncio.Task] = None
    
    async def get_vm_metrics(self, name: str = None, uuid: str = None) -> Dict[str, Any]:
        """Get comprehensive metrics for a VM.
        
        Args:
            name: VM name.
            uuid: VM UUID.
            
        Returns:
            Dict with VM metrics.
        """
        try:
            # Get domain
            if uuid:
                domain = self.manager.get_domain_by_uuid(uuid)
                vm_name = domain.name()
            else:
                domain = self.manager.get_domain_by_name(name)
                vm_name = name
            
            # Get basic info
            info = domain.info()
            state = info[0]
            
            metrics = {
                'name': vm_name,
                'uuid': domain.UUIDString(),
                'state': state,
                'max_memory_kb': info[1],
                'current_memory_kb': info[2],
                'vcpus': info[3],
                'cpu_time_ns': info[4],
                'timestamp': datetime.now().isoformat(),
                'uptime_seconds': None,
                'cpu_stats': {},
                'memory_stats': {},
                'disk_stats': {},
                'network_stats': {},
                'performance_metrics': {}
            }
            
            # Only collect detailed stats if VM is running
            if state == libvirt.VIR_DOMAIN_RUNNING:
                try:
                    # Get uptime
                    metrics['uptime_seconds'] = await self._get_vm_uptime(domain)
                    
                    # CPU statistics
                    cpu_stats = domain.getCPUStats(True)
                    metrics['cpu_stats'] = self._process_cpu_stats(cpu_stats)
                    
                    # Memory statistics
                    memory_stats = domain.memoryStats()
                    metrics['memory_stats'] = self._process_memory_stats(memory_stats)
                    
                    # Disk I/O statistics
                    disk_stats = await self._get_disk_stats(domain)
                    metrics['disk_stats'] = disk_stats
                    
                    # Network I/O statistics
                    network_stats = await self._get_network_stats(domain)
                    metrics['network_stats'] = network_stats
                    
                    # Calculate performance metrics
                    metrics['performance_metrics'] = self._calculate_performance_metrics(metrics)
                    
                except libvirt.libvirtError as e:
                    logger.warning(f"Failed to collect some metrics for VM '{vm_name}': {e}")
            
            return metrics
            
        except (VMNotFoundError):
            raise
        except libvirt.libvirtError as e:
            error_msg = f"Failed to get VM metrics: {e}"
            logger.error(error_msg)
            raise LibvirtConnectionError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error getting VM metrics: {e}"
            logger.error(error_msg)
            raise LibvirtConnectionError(error_msg)
    
    async def get_all_vm_metrics(self) -> List[Dict[str, Any]]:
        """Get metrics for all VMs.
        
        Returns:
            List of VM metrics dictionaries.
        """
        try:
            async with self.manager.get_connection() as conn:
                domains = conn.listAllDomains()
                
                metrics_list = []
                for domain in domains:
                    try:
                        vm_metrics = await self.get_vm_metrics(name=domain.name())
                        metrics_list.append(vm_metrics)
                    except Exception as e:
                        logger.warning(f"Failed to get metrics for VM '{domain.name()}': {e}")
                        # Add basic info even if detailed metrics fail
                        try:
                            info = domain.info()
                            metrics_list.append({
                                'name': domain.name(),
                                'uuid': domain.UUIDString(),
                                'state': info[0],
                                'error': str(e),
                                'timestamp': datetime.now().isoformat()
                            })
                        except:
                            pass
                
                return metrics_list
                
        except libvirt.libvirtError as e:
            raise LibvirtConnectionError(f"Failed to get all VM metrics: {e}")
    
    async def get_host_metrics(self) -> Dict[str, Any]:
        """Get host system metrics.
        
        Returns:
            Dict with host metrics.
        """
        try:
            async with self.manager.get_connection() as conn:
                # Get basic node info
                node_info = conn.getInfo()
                
                # Get host statistics
                host_stats = {}
                try:
                    cpu_stats = conn.getCPUStats(libvirt.VIR_NODE_CPU_STATS_ALL_CPUS)
                    host_stats['cpu'] = cpu_stats
                except:
                    pass
                
                try:
                    memory_stats = conn.getMemoryStats(libvirt.VIR_NODE_MEMORY_STATS_ALL_CELLS)
                    host_stats['memory'] = memory_stats
                except:
                    pass
                
                # Get VM counts
                all_domains = conn.listAllDomains()
                active_domains = [d for d in all_domains if d.isActive()]
                
                return {
                    'hostname': conn.getHostname(),
                    'architecture': node_info[0],
                    'total_memory_kb': node_info[1],
                    'total_cpus': node_info[2],
                    'cpu_mhz': node_info[3],
                    'numa_nodes': node_info[4],
                    'cpu_sockets': node_info[5],
                    'cores_per_socket': node_info[6],
                    'threads_per_core': node_info[7],
                    'active_vms': len(active_domains),
                    'total_vms': len(all_domains),
                    'hypervisor_type': conn.getType(),
                    'libvirt_version': conn.getLibVersion(),
                    'hypervisor_version': conn.getVersion(),
                    'host_stats': host_stats,
                    'timestamp': datetime.now().isoformat()
                }
                
        except libvirt.libvirtError as e:
            raise LibvirtConnectionError(f"Failed to get host metrics: {e}")
    
    async def monitor_vm_events(self, callback: Callable[[str, Dict[str, Any]], None]):
        """Monitor VM events and call callback function.
        
        Args:
            callback: Function to call when events occur.
                     Signature: callback(event_type: str, event_data: Dict[str, Any])
        """
        try:
            async with self.manager.get_connection() as conn:
                # Register for domain events
                def domain_event_callback(conn, domain, event, detail, opaque):
                    """Handle domain lifecycle events."""
                    try:
                        event_data = {
                            'domain_name': domain.name(),
                            'domain_uuid': domain.UUIDString(),
                            'event': event,
                            'detail': detail,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        # Convert event codes to readable strings
                        event_types = {
                            libvirt.VIR_DOMAIN_EVENT_DEFINED: 'defined',
                            libvirt.VIR_DOMAIN_EVENT_UNDEFINED: 'undefined',
                            libvirt.VIR_DOMAIN_EVENT_STARTED: 'started',
                            libvirt.VIR_DOMAIN_EVENT_SUSPENDED: 'suspended',
                            libvirt.VIR_DOMAIN_EVENT_RESUMED: 'resumed',
                            libvirt.VIR_DOMAIN_EVENT_STOPPED: 'stopped',
                            libvirt.VIR_DOMAIN_EVENT_SHUTDOWN: 'shutdown',
                            libvirt.VIR_DOMAIN_EVENT_PMSUSPENDED: 'pmsuspended',
                            libvirt.VIR_DOMAIN_EVENT_CRASHED: 'crashed'
                        }
                        
                        event_type = event_types.get(event, f'unknown_{event}')
                        event_data['event_type'] = event_type
                        
                        # Call the callback
                        asyncio.create_task(self._async_callback_wrapper(callback, event_type, event_data))
                        
                    except Exception as e:
                        logger.error(f"Error in domain event callback: {e}")
                
                # Register the callback
                conn.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE,
                                          domain_event_callback, None)
                
                logger.info("VM event monitoring started")
                
                # Keep the connection alive and process events
                while self._monitoring_active:
                    libvirt.virEventRunDefaultImpl()
                    await asyncio.sleep(0.1)
                    
        except libvirt.libvirtError as e:
            logger.error(f"Failed to monitor VM events: {e}")
            raise LibvirtConnectionError(f"Event monitoring failed: {e}")
    
    async def start_monitoring(self, event_callback: Callable = None):
        """Start background monitoring.
        
        Args:
            event_callback: Optional callback for events.
        """
        if self._monitoring_active:
            logger.warning("Monitoring is already active")
            return
        
        self._monitoring_active = True
        
        if event_callback:
            self._event_loop_task = asyncio.create_task(
                self.monitor_vm_events(event_callback)
            )
        
        logger.info("VM monitoring started")
    
    async def stop_monitoring(self):
        """Stop background monitoring."""
        self._monitoring_active = False
        
        if self._event_loop_task:
            self._event_loop_task.cancel()
            try:
                await self._event_loop_task
            except asyncio.CancelledError:
                pass
        
        logger.info("VM monitoring stopped")
    
    async def get_vm_performance_history(self, name: str = None, uuid: str = None,
                                        duration_minutes: int = 60) -> Dict[str, Any]:
        """Get performance history for a VM (simulated - would need time series DB).
        
        Args:
            name: VM name.
            uuid: VM UUID.
            duration_minutes: Duration in minutes to look back.
            
        Returns:
            Dict with performance history data.
        """
        # This is a placeholder implementation
        # In a real system, you would query a time series database
        current_metrics = await self.get_vm_metrics(name=name, uuid=uuid)
        
        return {
            'vm_name': current_metrics['name'],
            'vm_uuid': current_metrics['uuid'],
            'duration_minutes': duration_minutes,
            'current_metrics': current_metrics,
            'historical_data': {
                'note': 'Historical data requires time series database integration',
                'suggestion': 'Use InfluxDB, Prometheus, or similar for historical metrics'
            }
        }
    
    def _process_cpu_stats(self, cpu_stats: List[Dict]) -> Dict[str, Any]:
        """Process raw CPU statistics.
        
        Args:
            cpu_stats: Raw CPU stats from libvirt.
            
        Returns:
            Processed CPU statistics.
        """
        if not cpu_stats:
            return {}
        
        # Calculate totals
        total_time = 0
        user_time = 0
        system_time = 0
        
        for cpu_stat in cpu_stats:
            if 'cpu_time' in cpu_stat:
                total_time += cpu_stat['cpu_time']
            if 'user_time' in cpu_stat:
                user_time += cpu_stat['user_time']
            if 'system_time' in cpu_stat:
                system_time += cpu_stat['system_time']
        
        return {
            'total_time_ns': total_time,
            'user_time_ns': user_time,
            'system_time_ns': system_time,
            'vcpu_count': len(cpu_stats),
            'per_vcpu_stats': cpu_stats
        }
    
    def _process_memory_stats(self, memory_stats: Dict) -> Dict[str, Any]:
        """Process raw memory statistics.
        
        Args:
            memory_stats: Raw memory stats from libvirt.
            
        Returns:
            Processed memory statistics.
        """
        processed = memory_stats.copy()
        
        # Calculate usage percentages if we have the data
        if 'available' in memory_stats and 'total' in memory_stats:
            used = memory_stats['total'] - memory_stats['available']
            processed['used_kb'] = used
            processed['usage_percent'] = (used / memory_stats['total']) * 100
        
        return processed
    
    async def _get_disk_stats(self, domain: libvirt.virDomain) -> Dict[str, Any]:
        """Get disk I/O statistics for a domain.
        
        Args:
            domain: Libvirt domain object.
            
        Returns:
            Disk statistics.
        """
        disk_stats = {}
        
        try:
            # Parse XML to get disk devices
            xml_desc = domain.XMLDesc(0)
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_desc)
            
            for disk in root.findall('.//disk'):
                target = disk.find('target')
                if target is not None:
                    dev = target.get('dev')
                    if dev:
                        try:
                            stats = domain.blockStats(dev)
                            disk_stats[dev] = {
                                'read_requests': stats[0],
                                'read_bytes': stats[1],
                                'write_requests': stats[2],
                                'write_bytes': stats[3],
                                'errors': stats[4] if len(stats) > 4 else 0
                            }
                        except libvirt.libvirtError:
                            # Device might not exist or be accessible
                            pass
        except Exception as e:
            logger.warning(f"Failed to get disk stats: {e}")
        
        return disk_stats
    
    async def _get_network_stats(self, domain: libvirt.virDomain) -> Dict[str, Any]:
        """Get network I/O statistics for a domain.
        
        Args:
            domain: Libvirt domain object.
            
        Returns:
            Network statistics.
        """
        network_stats = {}
        
        try:
            # Parse XML to get network interfaces
            xml_desc = domain.XMLDesc(0)
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_desc)
            
            for interface in root.findall('.//interface'):
                target = interface.find('target')
                if target is not None:
                    dev = target.get('dev')
                    if dev:
                        try:
                            stats = domain.interfaceStats(dev)
                            network_stats[dev] = {
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
                            # Interface might not exist or be accessible
                            pass
        except Exception as e:
            logger.warning(f"Failed to get network stats: {e}")
        
        return network_stats
    
    async def _get_vm_uptime(self, domain: libvirt.virDomain) -> Optional[int]:
        """Get VM uptime in seconds.
        
        Args:
            domain: Libvirt domain object.
            
        Returns:
            Uptime in seconds or None if unavailable.
        """
        try:
            # This is an approximation - libvirt doesn't provide exact uptime
            # In a real implementation, you might track start times separately
            info = domain.info()
            cpu_time_ns = info[4]
            vcpus = info[3]
            
            # Rough estimate: assume average 10% CPU usage
            if vcpus > 0:
                estimated_uptime = cpu_time_ns / (vcpus * 1000000000 * 0.1)
                return int(estimated_uptime)
        except:
            pass
        
        return None
    
    def _calculate_performance_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate derived performance metrics.
        
        Args:
            metrics: Raw metrics data.
            
        Returns:
            Calculated performance metrics.
        """
        performance = {}
        
        # Memory utilization
        if metrics['current_memory_kb'] > 0 and metrics['max_memory_kb'] > 0:
            performance['memory_utilization_percent'] = (
                metrics['current_memory_kb'] / metrics['max_memory_kb']
            ) * 100
        
        # CPU utilization (simplified)
        if 'cpu_stats' in metrics and metrics['cpu_stats']:
            # This would need baseline measurements for accurate calculation
            performance['cpu_utilization_note'] = 'Requires baseline measurements'
        
        # Disk I/O rates
        total_read_bytes = 0
        total_write_bytes = 0
        for dev_stats in metrics.get('disk_stats', {}).values():
            total_read_bytes += dev_stats.get('read_bytes', 0)
            total_write_bytes += dev_stats.get('write_bytes', 0)
        
        performance['total_disk_read_bytes'] = total_read_bytes
        performance['total_disk_write_bytes'] = total_write_bytes
        
        # Network I/O rates
        total_rx_bytes = 0
        total_tx_bytes = 0
        for dev_stats in metrics.get('network_stats', {}).values():
            total_rx_bytes += dev_stats.get('rx_bytes', 0)
            total_tx_bytes += dev_stats.get('tx_bytes', 0)
        
        performance['total_network_rx_bytes'] = total_rx_bytes
        performance['total_network_tx_bytes'] = total_tx_bytes
        
        return performance
    
    async def _async_callback_wrapper(self, callback: Callable, *args):
        """Wrapper to handle async callback execution."""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args)
            else:
                callback(*args)
        except Exception as e:
            logger.error(f"Error in event callback: {e}")


# Global instance
vm_monitoring = VMMonitoring()