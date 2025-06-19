"""Resource management for VM allocation and limits."""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
import libvirt

from .libvirt_manager import LibvirtManager
from .exceptions import (
    ResourceAllocationError,
    LibvirtConnectionError,
    VMNotFoundError
)


logger = logging.getLogger(__name__)


class ResourceManager:
    """Manage VM resource allocation and limits."""
    
    def __init__(self, libvirt_manager: LibvirtManager = None):
        """Initialize resource manager.
        
        Args:
            libvirt_manager: LibvirtManager instance.
        """
        self.manager = libvirt_manager or LibvirtManager()
    
    async def get_host_resources(self) -> Dict[str, Any]:
        """Get host system resource information.
        
        Returns:
            Dict with host resource details.
        """
        try:
            async with self.manager.get_connection() as conn:
                # Get node information
                node_info = conn.getInfo()
                
                # Get host statistics
                try:
                    stats = conn.getCPUStats(libvirt.VIR_NODE_CPU_STATS_ALL_CPUS)
                    memory_stats = conn.getMemoryStats(libvirt.VIR_NODE_MEMORY_STATS_ALL_CELLS)
                except libvirt.libvirtError:
                    # Fallback if detailed stats not available
                    stats = {}
                    memory_stats = {}
                
                return {
                    'architecture': node_info[0],
                    'total_memory_kb': node_info[1],
                    'total_cpus': node_info[2],
                    'cpu_mhz': node_info[3],
                    'numa_nodes': node_info[4],
                    'cpu_sockets': node_info[5],
                    'cores_per_socket': node_info[6],
                    'threads_per_core': node_info[7],
                    'cpu_stats': stats,
                    'memory_stats': memory_stats
                }
                
        except libvirt.libvirtError as e:
            raise LibvirtConnectionError(f"Failed to get host resources: {e}")
    
    async def get_available_resources(self) -> Dict[str, Any]:
        """Get available (unallocated) resources.
        
        Returns:
            Dict with available resource information.
        """
        try:
            # Get total host resources
            host_resources = await self.get_host_resources()
            
            # Get allocated resources from all VMs
            allocated_resources = await self.get_allocated_resources()
            
            # Calculate available resources
            total_memory_kb = host_resources['total_memory_kb']
            allocated_memory_kb = allocated_resources['total_memory_kb']
            available_memory_kb = total_memory_kb - allocated_memory_kb
            
            total_cpus = host_resources['total_cpus']
            allocated_cpus = allocated_resources['total_vcpus']
            available_cpus = total_cpus - allocated_cpus
            
            return {
                'total_memory_kb': total_memory_kb,
                'allocated_memory_kb': allocated_memory_kb,
                'available_memory_kb': max(0, available_memory_kb),
                'memory_usage_percent': (allocated_memory_kb / total_memory_kb) * 100 if total_memory_kb > 0 else 0,
                'total_cpus': total_cpus,
                'allocated_vcpus': allocated_cpus,
                'available_vcpus': max(0, available_cpus),
                'cpu_usage_percent': (allocated_cpus / total_cpus) * 100 if total_cpus > 0 else 0,
                'active_vms': allocated_resources['active_vms'],
                'total_vms': allocated_resources['total_vms']
            }
            
        except Exception as e:
            logger.error(f"Failed to get available resources: {e}")
            raise ResourceAllocationError('system', 'Failed to calculate available resources')
    
    async def get_allocated_resources(self) -> Dict[str, Any]:
        """Get currently allocated resources across all VMs.
        
        Returns:
            Dict with allocated resource information.
        """
        try:
            async with self.manager.get_connection() as conn:
                domains = conn.listAllDomains()
                
                total_memory_kb = 0
                total_vcpus = 0
                active_vms = 0
                vm_details = []
                
                for domain in domains:
                    try:
                        info = domain.info()
                        state = info[0]
                        max_memory_kb = info[1]
                        memory_kb = info[2]
                        num_vcpus = info[3]
                        
                        # Count towards total allocation
                        total_memory_kb += max_memory_kb
                        total_vcpus += num_vcpus
                        
                        if state == libvirt.VIR_DOMAIN_RUNNING:
                            active_vms += 1
                        
                        vm_details.append({
                            'name': domain.name(),
                            'uuid': domain.UUIDString(),
                            'state': state,
                            'max_memory_kb': max_memory_kb,
                            'current_memory_kb': memory_kb,
                            'vcpus': num_vcpus
                        })
                        
                    except libvirt.libvirtError as e:
                        logger.warning(f"Failed to get info for domain {domain.name()}: {e}")
                        continue
                
                return {
                    'total_memory_kb': total_memory_kb,
                    'total_vcpus': total_vcpus,
                    'active_vms': active_vms,
                    'total_vms': len(domains),
                    'vm_details': vm_details
                }
                
        except libvirt.libvirtError as e:
            raise LibvirtConnectionError(f"Failed to get allocated resources: {e}")
    
    async def validate_resource_allocation(self, cpu_cores: int, memory_mb: int) -> Tuple[bool, str]:
        """Validate if requested resources can be allocated.
        
        Args:
            cpu_cores: Requested CPU cores.
            memory_mb: Requested memory in MB.
            
        Returns:
            Tuple of (is_valid, error_message).
        """
        try:
            available = await self.get_available_resources()
            
            # Convert memory to KB for comparison
            memory_kb = memory_mb * 1024
            
            # Check memory
            if memory_kb > available['available_memory_kb']:
                return False, f"Insufficient memory: requested {memory_mb}MB, available {available['available_memory_kb'] // 1024}MB"
            
            # Check CPU cores (allow some overcommit)
            max_vcpu_ratio = 4  # Allow 4:1 vCPU to physical CPU ratio
            max_allowed_vcpus = available['total_cpus'] * max_vcpu_ratio
            
            if (available['allocated_vcpus'] + cpu_cores) > max_allowed_vcpus:
                return False, f"Insufficient CPU: requested {cpu_cores} cores, would exceed limit"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Failed to validate resource allocation: {e}")
            return False, f"Validation error: {e}"
    
    async def update_vm_resources(self, name: str = None, uuid: str = None,
                                 cpu_cores: int = None, memory_mb: int = None,
                                 live_update: bool = False) -> Dict[str, Any]:
        """Update VM resource allocation.
        
        Args:
            name: VM name.
            uuid: VM UUID.
            cpu_cores: New CPU core count.
            memory_mb: New memory in MB.
            live_update: Apply changes to running VM.
            
        Returns:
            Dict with update results.
        """
        try:
            # Get domain
            if uuid:
                domain = self.manager.get_domain_by_uuid(uuid)
                vm_name = domain.name()
            else:
                domain = self.manager.get_domain_by_name(name)
                vm_name = name
            
            # Get current configuration
            current_info = domain.info()
            current_max_memory_kb = current_info[1]
            current_vcpus = current_info[3]
            
            changes_made = []
            
            # Update memory if requested
            if memory_mb is not None:
                memory_kb = memory_mb * 1024
                
                # Validate allocation
                if memory_kb > current_max_memory_kb:
                    valid, error = await self.validate_resource_allocation(0, memory_mb - (current_max_memory_kb // 1024))
                    if not valid:
                        raise ResourceAllocationError('memory', error)
                
                # Set maximum memory (requires VM to be stopped)
                state, _ = domain.state()
                if state != libvirt.VIR_DOMAIN_SHUTOFF:
                    if not live_update:
                        raise ResourceAllocationError('memory', 'VM must be stopped to change maximum memory')
                else:
                    domain.setMaxMemory(memory_kb)
                    changes_made.append(f"Maximum memory set to {memory_mb}MB")
                
                # Set current memory (can be done live if VM is running and new value <= max)
                if memory_kb <= domain.maxMemory():
                    if live_update and state == libvirt.VIR_DOMAIN_RUNNING:
                        domain.setMemory(memory_kb)
                        changes_made.append(f"Current memory set to {memory_mb}MB (live)")
                    else:
                        domain.setMemory(memory_kb)
                        changes_made.append(f"Current memory set to {memory_mb}MB")
            
            # Update CPU cores if requested
            if cpu_cores is not None:
                # Validate allocation
                if cpu_cores > current_vcpus:
                    valid, error = await self.validate_resource_allocation(cpu_cores - current_vcpus, 0)
                    if not valid:
                        raise ResourceAllocationError('cpu', error)
                
                state, _ = domain.state()
                if state == libvirt.VIR_DOMAIN_RUNNING and live_update:
                    # Hot plug/unplug CPUs
                    try:
                        domain.setVcpus(cpu_cores)
                        changes_made.append(f"vCPUs set to {cpu_cores} (live)")
                    except libvirt.libvirtError as e:
                        # Fallback: modify configuration for next boot
                        domain.setVcpusFlags(cpu_cores, libvirt.VIR_DOMAIN_VCPU_CONFIG)
                        changes_made.append(f"vCPUs set to {cpu_cores} (config only)")
                else:
                    # VM is stopped, modify configuration
                    domain.setVcpusFlags(cpu_cores, libvirt.VIR_DOMAIN_VCPU_CONFIG)
                    changes_made.append(f"vCPUs set to {cpu_cores}")
            
            logger.info(f"Updated resources for VM '{vm_name}': {changes_made}")
            
            return {
                'name': vm_name,
                'changes': changes_made,
                'status': 'updated'
            }
            
        except (VMNotFoundError, ResourceAllocationError):
            raise
        except libvirt.libvirtError as e:
            error_msg = f"Libvirt error updating VM resources: {e}"
            logger.error(error_msg)
            raise ResourceAllocationError('update', error_msg)
        except Exception as e:
            error_msg = f"Unexpected error updating VM resources: {e}"
            logger.error(error_msg)
            raise ResourceAllocationError('update', error_msg)
    
    async def get_vm_resource_usage(self, name: str = None, uuid: str = None) -> Dict[str, Any]:
        """Get detailed resource usage for a VM.
        
        Args:
            name: VM name.
            uuid: VM UUID.
            
        Returns:
            Dict with resource usage details.
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
            
            # Get detailed stats if VM is running
            stats = {}
            state = info[0]
            if state == libvirt.VIR_DOMAIN_RUNNING:
                try:
                    # CPU stats
                    cpu_stats = domain.getCPUStats(True)
                    
                    # Memory stats
                    memory_stats = domain.memoryStats()
                    
                    # Block device stats
                    block_stats = {}
                    try:
                        # Get all block devices
                        xml_desc = domain.XMLDesc(0)
                        import xml.etree.ElementTree as ET
                        root = ET.fromstring(xml_desc)
                        
                        for disk in root.findall('.//disk'):
                            target = disk.find('target')
                            if target is not None:
                                dev = target.get('dev')
                                if dev:
                                    block_stats[dev] = domain.blockStats(dev)
                    except:
                        pass
                    
                    # Network interface stats
                    interface_stats = {}
                    try:
                        for interface in root.findall('.//interface'):
                            target = interface.find('target')
                            if target is not None:
                                dev = target.get('dev')
                                if dev:
                                    interface_stats[dev] = domain.interfaceStats(dev)
                    except:
                        pass
                    
                    stats = {
                        'cpu_stats': cpu_stats,
                        'memory_stats': memory_stats,
                        'block_stats': block_stats,
                        'interface_stats': interface_stats
                    }
                    
                except libvirt.libvirtError as e:
                    logger.warning(f"Failed to get detailed stats for VM '{vm_name}': {e}")
            
            return {
                'name': vm_name,
                'uuid': domain.UUIDString(),
                'state': state,
                'max_memory_kb': info[1],
                'current_memory_kb': info[2],
                'vcpus': info[3],
                'cpu_time_ns': info[4],
                'detailed_stats': stats
            }
            
        except (VMNotFoundError):
            raise
        except libvirt.libvirtError as e:
            error_msg = f"Libvirt error getting VM resource usage: {e}"
            logger.error(error_msg)
            raise ResourceAllocationError('usage', error_msg)
        except Exception as e:
            error_msg = f"Unexpected error getting VM resource usage: {e}"
            logger.error(error_msg)
            raise ResourceAllocationError('usage', error_msg)
    
    async def set_resource_limits(self, name: str = None, uuid: str = None,
                                 cpu_shares: int = None, cpu_period: int = None,
                                 cpu_quota: int = None, memory_hard_limit: int = None,
                                 memory_soft_limit: int = None) -> Dict[str, Any]:
        """Set resource limits and QoS parameters for a VM.
        
        Args:
            name: VM name.
            uuid: VM UUID.
            cpu_shares: CPU shares (relative weight).
            cpu_period: CPU period in microseconds.
            cpu_quota: CPU quota in microseconds.
            memory_hard_limit: Hard memory limit in KB.
            memory_soft_limit: Soft memory limit in KB.
            
        Returns:
            Dict with operation results.
        """
        try:
            # Get domain
            if uuid:
                domain = self.manager.get_domain_by_uuid(uuid)
                vm_name = domain.name()
            else:
                domain = self.manager.get_domain_by_name(name)
                vm_name = name
            
            limits_set = []
            
            # Set CPU limits
            if any([cpu_shares, cpu_period, cpu_quota]):
                cpu_params = {}
                
                if cpu_shares is not None:
                    cpu_params['cpu_shares'] = cpu_shares
                if cpu_period is not None:
                    cpu_params['vcpu_period'] = cpu_period
                if cpu_quota is not None:
                    cpu_params['vcpu_quota'] = cpu_quota
                
                if cpu_params:
                    domain.setSchedulerParameters(cpu_params)
                    limits_set.append(f"CPU limits: {cpu_params}")
            
            # Set memory limits
            if memory_hard_limit is not None or memory_soft_limit is not None:
                memory_params = {}
                
                if memory_hard_limit is not None:
                    memory_params['hard_limit'] = memory_hard_limit
                if memory_soft_limit is not None:
                    memory_params['soft_limit'] = memory_soft_limit
                
                if memory_params:
                    domain.setMemoryParameters(memory_params)
                    limits_set.append(f"Memory limits: {memory_params}")
            
            logger.info(f"Set resource limits for VM '{vm_name}': {limits_set}")
            
            return {
                'name': vm_name,
                'limits_set': limits_set,
                'status': 'completed'
            }
            
        except (VMNotFoundError):
            raise
        except libvirt.libvirtError as e:
            error_msg = f"Libvirt error setting resource limits: {e}"
            logger.error(error_msg)
            raise ResourceAllocationError('limits', error_msg)
        except Exception as e:
            error_msg = f"Unexpected error setting resource limits: {e}"
            logger.error(error_msg)
            raise ResourceAllocationError('limits', error_msg)