"""VM lifecycle operations using libvirt."""

import asyncio
import logging
import os
from typing import Dict, Any, List, Optional, Union
import libvirt
from datetime import datetime

from .libvirt_manager import LibvirtManager
from .templates import XMLTemplateGenerator
from .exceptions import (
    VMNotFoundError,
    VMOperationError,
    VMStateError,
    LibvirtError,
    StorageConfigurationError
)
from models.virtual_machine import VMStatus, OSType
from core.config import settings


logger = logging.getLogger(__name__)


class VMOperations:
    """Handle VM lifecycle operations."""
    
    def __init__(self, libvirt_manager: LibvirtManager = None,
                 xml_generator: XMLTemplateGenerator = None):
        """Initialize VM operations.
        
        Args:
            libvirt_manager: LibvirtManager instance.
            xml_generator: XMLTemplateGenerator instance.
        """
        self.manager = libvirt_manager or LibvirtManager()
        self.xml_generator = xml_generator or XMLTemplateGenerator()
    
    async def create_vm(self, name: str, uuid: str, cpu_cores: int, memory_mb: int,
                       disk_gb: float, os_type: str = 'linux', os_version: str = None,
                       base_image: str = None, network: str = 'default',
                       vnc_enabled: bool = True, **kwargs) -> Dict[str, Any]:
        """Create a new virtual machine.
        
        Args:
            name: VM name.
            uuid: VM UUID.
            cpu_cores: Number of CPU cores.
            memory_mb: Memory in MB.
            disk_gb: Disk size in GB.
            os_type: Operating system type.
            os_version: OS version.
            base_image: Base image path for cloning.
            network: Network to connect to.
            vnc_enabled: Enable VNC access.
            **kwargs: Additional configuration.
            
        Returns:
            Dict with VM creation details.
            
        Raises:
            VMOperationError: If VM creation fails.
        """
        try:
            async with self.manager.get_connection() as conn:
                # Check if VM already exists
                try:
                    existing_domain = conn.lookupByName(name)
                    if existing_domain:
                        raise VMOperationError('create', name, 'VM already exists')
                except libvirt.libvirtError:
                    # VM doesn't exist, which is what we want
                    pass
                except Exception as e:
                    # Handle mock errors for testing - if it's a "not found" error, continue
                    if hasattr(e, 'get_error_code') and e.get_error_code() == 42:
                        # VM doesn't exist, which is what we want
                        pass
                    else:
                        raise
                
                # Create disk image
                disk_path = await self._create_disk_image(
                    name, disk_gb, base_image, os_type
                )
                
                # Generate VM XML configuration
                vm_config = {
                    'name': name,
                    'uuid': uuid,
                    'cpu_cores': cpu_cores,
                    'memory_mb': memory_mb,
                    'disks': [{
                        'path': disk_path,
                        'target': 'vda',
                        'bus': 'virtio'
                    }],
                    'network_interfaces': [{
                        'network': network,
                        'model': 'virtio'
                    }],
                    'vnc_enabled': vnc_enabled,
                    **kwargs
                }
                
                xml_config = self.xml_generator.generate_vm_xml(**vm_config)
                
                # Define the domain
                domain = conn.defineXML(xml_config)
                
                logger.info(f"VM '{name}' created successfully")
                
                return {
                    'name': name,
                    'uuid': uuid,
                    'status': 'created',
                    'disk_path': disk_path,
                    'xml_config': xml_config
                }
                
        except libvirt.libvirtError as e:
            error_msg = f"Libvirt error creating VM '{name}': {e}"
            logger.error(error_msg)
            raise VMOperationError('create', name, str(e))
        except Exception as e:
            error_msg = f"Unexpected error creating VM '{name}': {e}"
            logger.error(error_msg)
            raise VMOperationError('create', name, str(e))
    
    async def start_vm(self, name: str = None, uuid: str = None) -> Dict[str, Any]:
        """Start a virtual machine.
        
        Args:
            name: VM name.
            uuid: VM UUID.
            
        Returns:
            Dict with start operation details.
            
        Raises:
            VMNotFoundError: If VM not found.
            VMOperationError: If start fails.
        """
        try:
            async with self.manager.get_connection() as conn:
                # Get domain
                if uuid:
                    domain = self.manager.get_domain_by_uuid(uuid)
                    vm_name = domain.name()
                else:
                    domain = self.manager.get_domain_by_name(name)
                    vm_name = name
                
                # Check current state
                state, _ = domain.state()
                if state == libvirt.VIR_DOMAIN_RUNNING:
                    logger.warning(f"VM '{vm_name}' is already running")
                    return {'name': vm_name, 'status': 'already_running'}
                
                # Start the domain
                result = domain.create()
                if result == 0:
                    logger.info(f"VM '{vm_name}' started successfully")
                    return {'name': vm_name, 'status': 'started'}
                else:
                    raise VMOperationError('start', vm_name, f"Start returned code {result}")
                    
        except (VMNotFoundError, VMOperationError):
            raise
        except libvirt.libvirtError as e:
            error_msg = f"Libvirt error starting VM: {e}"
            logger.error(error_msg)
            raise VMOperationError('start', vm_name or 'unknown', str(e))
        except Exception as e:
            error_msg = f"Unexpected error starting VM: {e}"
            logger.error(error_msg)
            raise VMOperationError('start', vm_name or 'unknown', str(e))
    
    async def stop_vm(self, name: str = None, uuid: str = None,
                     force: bool = False) -> Dict[str, Any]:
        """Stop a virtual machine.
        
        Args:
            name: VM name.
            uuid: VM UUID.
            force: Force shutdown (destroy) instead of graceful shutdown.
            
        Returns:
            Dict with stop operation details.
        """
        try:
            async with self.manager.get_connection() as conn:
                # Get domain
                if uuid:
                    domain = self.manager.get_domain_by_uuid(uuid)
                    vm_name = domain.name()
                else:
                    domain = self.manager.get_domain_by_name(name)
                    vm_name = name
                
                # Check current state
                state, _ = domain.state()
                if state in [libvirt.VIR_DOMAIN_SHUTOFF, libvirt.VIR_DOMAIN_SHUTDOWN]:
                    logger.warning(f"VM '{vm_name}' is already stopped")
                    return {'name': vm_name, 'status': 'already_stopped'}
                
                # Stop the domain
                if force:
                    result = domain.destroy()
                    action = 'destroyed'
                else:
                    result = domain.shutdown()
                    action = 'shutdown'
                
                if result == 0:
                    logger.info(f"VM '{vm_name}' {action} successfully")
                    return {'name': vm_name, 'status': action}
                else:
                    raise VMOperationError('stop', vm_name, f"Stop returned code {result}")
                    
        except (VMNotFoundError, VMOperationError):
            raise
        except libvirt.libvirtError as e:
            error_msg = f"Libvirt error stopping VM: {e}"
            logger.error(error_msg)
            raise VMOperationError('stop', vm_name or 'unknown', str(e))
        except Exception as e:
            error_msg = f"Unexpected error stopping VM: {e}"
            logger.error(error_msg)
            raise VMOperationError('stop', vm_name or 'unknown', str(e))
    
    async def restart_vm(self, name: str = None, uuid: str = None,
                        force: bool = False) -> Dict[str, Any]:
        """Restart a virtual machine.
        
        Args:
            name: VM name.
            uuid: VM UUID.
            force: Force restart.
            
        Returns:
            Dict with restart operation details.
        """
        vm_identifier = uuid or name
        
        # Stop the VM
        stop_result = await self.stop_vm(name=name, uuid=uuid, force=force)
        
        # Wait a moment before starting
        await asyncio.sleep(2)
        
        # Start the VM
        start_result = await self.start_vm(name=name, uuid=uuid)
        
        return {
            'name': start_result['name'],
            'status': 'restarted',
            'stop_result': stop_result,
            'start_result': start_result
        }
    
    async def delete_vm(self, name: str = None, uuid: str = None,
                       delete_disks: bool = True) -> Dict[str, Any]:
        """Delete a virtual machine.
        
        Args:
            name: VM name.
            uuid: VM UUID.
            delete_disks: Whether to delete associated disk files.
            
        Returns:
            Dict with delete operation details.
        """
        try:
            async with self.manager.get_connection() as conn:
                # Get domain
                if uuid:
                    domain = self.manager.get_domain_by_uuid(uuid)
                    vm_name = domain.name()
                else:
                    domain = self.manager.get_domain_by_name(name)
                    vm_name = name
                
                # Get disk paths before deletion
                disk_paths = []
                if delete_disks:
                    disk_paths = await self._get_vm_disk_paths(domain)
                
                # Stop VM if running
                state, _ = domain.state()
                if state == libvirt.VIR_DOMAIN_RUNNING:
                    domain.destroy()
                    logger.info(f"Stopped running VM '{vm_name}' before deletion")
                
                # Undefine (delete) the domain
                result = domain.undefine()
                
                if result == 0:
                    logger.info(f"VM '{vm_name}' undefined successfully")
                    
                    # Delete disk files
                    deleted_disks = []
                    if delete_disks:
                        for disk_path in disk_paths:
                            try:
                                if os.path.exists(disk_path):
                                    os.remove(disk_path)
                                    deleted_disks.append(disk_path)
                                    logger.info(f"Deleted disk file: {disk_path}")
                            except OSError as e:
                                logger.warning(f"Failed to delete disk {disk_path}: {e}")
                    
                    return {
                        'name': vm_name,
                        'status': 'deleted',
                        'deleted_disks': deleted_disks
                    }
                else:
                    raise VMOperationError('delete', vm_name, f"Undefine returned code {result}")
                    
        except (VMNotFoundError, VMOperationError):
            raise
        except libvirt.libvirtError as e:
            error_msg = f"Libvirt error deleting VM: {e}"
            logger.error(error_msg)
            raise VMOperationError('delete', vm_name or 'unknown', str(e))
        except Exception as e:
            error_msg = f"Unexpected error deleting VM: {e}"
            logger.error(error_msg)
            raise VMOperationError('delete', vm_name or 'unknown', str(e))
    
    async def clone_vm(self, source_name: str, new_name: str, new_uuid: str) -> Dict[str, Any]:
        """Clone an existing virtual machine.
        
        Args:
            source_name: Source VM name.
            new_name: New VM name.
            new_uuid: New VM UUID.
            
        Returns:
            Dict with clone operation details.
        """
        try:
            async with self.manager.get_connection() as conn:
                # Get source domain
                source_domain = self.manager.get_domain_by_name(source_name)
                
                # Check if source VM is running
                state, _ = source_domain.state()
                if state == libvirt.VIR_DOMAIN_RUNNING:
                    raise VMStateError(source_name, 'running', 'stopped')
                
                # Get source VM XML
                source_xml = source_domain.XMLDesc(0)
                
                # Modify XML for new VM
                import xml.etree.ElementTree as ET
                root = ET.fromstring(source_xml)
                
                # Update name and UUID
                name_elem = root.find('name')
                name_elem.text = new_name
                
                uuid_elem = root.find('uuid')
                uuid_elem.text = new_uuid
                
                # Clone disk files
                disk_paths = []
                disks = root.findall('.//disk[@type="file"]')
                for disk in disks:
                    source_file = disk.find('source').get('file')
                    if source_file:
                        # Create new disk path
                        base_name = os.path.basename(source_file)
                        name_part, ext = os.path.splitext(base_name)
                        new_disk_path = os.path.join(
                            settings.vm_storage_path,
                            f"{new_name}_{name_part}{ext}"
                        )
                        
                        # Copy disk file
                        await self._copy_disk_file(source_file, new_disk_path)
                        disk_paths.append(new_disk_path)
                        
                        # Update XML with new path
                        disk.find('source').set('file', new_disk_path)
                
                # Generate new XML
                new_xml = ET.tostring(root, encoding='unicode')
                
                # Define new domain
                new_domain = conn.defineXML(new_xml)
                
                logger.info(f"VM '{source_name}' cloned to '{new_name}' successfully")
                
                return {
                    'source_name': source_name,
                    'new_name': new_name,
                    'new_uuid': new_uuid,
                    'status': 'cloned',
                    'disk_paths': disk_paths
                }
                
        except (VMNotFoundError, VMOperationError, VMStateError):
            raise
        except libvirt.libvirtError as e:
            error_msg = f"Libvirt error cloning VM: {e}"
            logger.error(error_msg)
            raise VMOperationError('clone', source_name, str(e))
        except Exception as e:
            error_msg = f"Unexpected error cloning VM: {e}"
            logger.error(error_msg)
            raise VMOperationError('clone', source_name, str(e))
    
    async def get_vm_status(self, name: str = None, uuid: str = None) -> Dict[str, Any]:
        """Get VM status and basic info.
        
        Args:
            name: VM name.
            uuid: VM UUID.
            
        Returns:
            Dict with VM status information.
        """
        try:
            # Get domain
            if uuid:
                domain = self.manager.get_domain_by_uuid(uuid)
                vm_name = domain.name()
            else:
                domain = self.manager.get_domain_by_name(name)
                vm_name = name
            
            # Get state
            state, reason = domain.state()
            
            # Convert state to our enum
            state_mapping = {
                libvirt.VIR_DOMAIN_NOSTATE: VMStatus.ERROR,
                libvirt.VIR_DOMAIN_RUNNING: VMStatus.RUNNING,
                libvirt.VIR_DOMAIN_BLOCKED: VMStatus.RUNNING,
                libvirt.VIR_DOMAIN_PAUSED: VMStatus.PAUSED,
                libvirt.VIR_DOMAIN_SHUTDOWN: VMStatus.STOPPING,
                libvirt.VIR_DOMAIN_SHUTOFF: VMStatus.STOPPED,
                libvirt.VIR_DOMAIN_CRASHED: VMStatus.ERROR,
                libvirt.VIR_DOMAIN_PMSUSPENDED: VMStatus.SUSPENDED
            }
            
            vm_status = state_mapping.get(state, VMStatus.ERROR)
            
            # Get basic info
            info = domain.info()
            
            return {
                'name': vm_name,
                'uuid': domain.UUIDString(),
                'status': vm_status.value,
                'state_reason': reason,
                'max_memory_kb': info[1],
                'memory_kb': info[2],
                'num_vcpus': info[3],
                'cpu_time_ns': info[4]
            }
            
        except (VMNotFoundError, VMOperationError):
            raise
        except libvirt.libvirtError as e:
            error_msg = f"Libvirt error getting VM status: {e}"
            logger.error(error_msg)
            raise VMOperationError('get_status', vm_name or 'unknown', str(e))
        except Exception as e:
            error_msg = f"Unexpected error getting VM status: {e}"
            logger.error(error_msg)
            raise VMOperationError('get_status', vm_name or 'unknown', str(e))
    
    async def _create_disk_image(self, name: str, size_gb: float,
                                base_image: str = None, os_type: str = 'linux') -> str:
        """Create disk image for VM.
        
        Args:
            name: VM name.
            size_gb: Disk size in GB.
            base_image: Base image to clone from.
            os_type: Operating system type.
            
        Returns:
            str: Path to created disk image.
        """
        disk_path = os.path.join(settings.vm_storage_path, f"{name}.qcow2")
        
        try:
            if base_image and os.path.exists(base_image):
                # Clone from base image
                cmd = f"qemu-img create -f qcow2 -b {base_image} {disk_path} {size_gb}G"
            else:
                # Create blank disk
                cmd = f"qemu-img create -f qcow2 {disk_path} {size_gb}G"
            
            # Execute command
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = f"Failed to create disk image: {stderr.decode()}"
                raise StorageConfigurationError(error_msg)
            
            logger.info(f"Created disk image: {disk_path}")
            return disk_path
            
        except Exception as e:
            logger.error(f"Error creating disk image: {e}")
            raise StorageConfigurationError(f"Failed to create disk image: {e}")
    
    async def _copy_disk_file(self, source_path: str, dest_path: str):
        """Copy disk file for cloning.
        
        Args:
            source_path: Source disk file path.
            dest_path: Destination disk file path.
        """
        cmd = f"cp {source_path} {dest_path}"
        
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = f"Failed to copy disk file: {stderr.decode()}"
            raise StorageConfigurationError(error_msg)
        
        logger.info(f"Copied disk file from {source_path} to {dest_path}")
    
    async def _get_vm_disk_paths(self, domain: libvirt.virDomain) -> List[str]:
        """Get disk file paths for a VM.
        
        Args:
            domain: Libvirt domain object.
            
        Returns:
            List of disk file paths.
        """
        import xml.etree.ElementTree as ET
        
        xml_desc = domain.XMLDesc(0)
        root = ET.fromstring(xml_desc)
        
        disk_paths = []
        disks = root.findall('.//disk[@type="file"]')
        for disk in disks:
            source_elem = disk.find('source')
            if source_elem is not None:
                file_path = source_elem.get('file')
                if file_path:
                    disk_paths.append(file_path)
        
        return disk_paths