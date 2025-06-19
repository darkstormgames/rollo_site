"""Local VM operations interface using libvirt."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import libvirt
    LIBVIRT_AVAILABLE = True
except ImportError:
    LIBVIRT_AVAILABLE = False
    logger.warning("libvirt not available - VM operations will be limited")


class VMOperationError(Exception):
    """Exception raised for VM operation errors."""
    pass


class VMOperations:
    """Interface for local VM operations via libvirt."""
    
    def __init__(self, libvirt_uri: str = "qemu:///system"):
        """Initialize VM operations."""
        self.libvirt_uri = libvirt_uri
        self._conn = None
        
    def _get_connection(self):
        """Get or create libvirt connection."""
        if not LIBVIRT_AVAILABLE:
            raise VMOperationError("libvirt not available")
            
        try:
            if self._conn is None or not self._is_connection_alive():
                self._conn = libvirt.open(self.libvirt_uri)
            return self._conn
        except Exception as e:
            raise VMOperationError(f"Failed to connect to libvirt: {e}")
    
    def _is_connection_alive(self) -> bool:
        """Check if libvirt connection is alive."""
        if not self._conn:
            return False
        try:
            self._conn.getVersion()
            return True
        except:
            return False
    
    def _get_domain(self, vm_name: str = None, vm_uuid: str = None):
        """Get domain by name or UUID."""
        conn = self._get_connection()
        
        try:
            if vm_uuid:
                return conn.lookupByUUIDString(vm_uuid)
            elif vm_name:
                return conn.lookupByName(vm_name)
            else:
                raise VMOperationError("Either vm_name or vm_uuid must be provided")
        except libvirt.libvirtError as e:
            raise VMOperationError(f"VM not found: {e}")
    
    async def list_vms(self) -> List[Dict[str, Any]]:
        """List all VMs on the host."""
        try:
            conn = self._get_connection()
            domains = conn.listAllDomains()
            
            vm_list = []
            for domain in domains:
                vm_info = {
                    "name": domain.name(),
                    "uuid": domain.UUIDString(),
                    "state": self._get_state_name(domain.state()[0]),
                    "memory": domain.info()[2] * 1024,  # Convert KB to bytes
                    "vcpus": domain.info()[3],
                    "autostart": domain.autostart()
                }
                vm_list.append(vm_info)
            
            return vm_list
            
        except Exception as e:
            raise VMOperationError(f"Failed to list VMs: {e}")
    
    async def get_vm_info(self, vm_name: str = None, vm_uuid: str = None) -> Dict[str, Any]:
        """Get detailed information about a specific VM."""
        try:
            domain = self._get_domain(vm_name, vm_uuid)
            info = domain.info()
            state = info[0]
            
            vm_info = {
                "name": domain.name(),
                "uuid": domain.UUIDString(),
                "state": self._get_state_name(state),
                "max_memory": info[1] * 1024,  # Convert KB to bytes
                "memory": info[2] * 1024,
                "vcpus": info[3],
                "cpu_time": info[4],
                "autostart": domain.autostart(),
                "persistent": domain.isPersistent(),
                "os_type": domain.OSType(),
                "id": domain.ID() if state == libvirt.VIR_DOMAIN_RUNNING else None
            }
            
            # Get XML description for additional details
            try:
                xml_desc = domain.XMLDesc(0)
                vm_info["xml_description"] = xml_desc
            except Exception:
                pass
            
            return vm_info
            
        except Exception as e:
            raise VMOperationError(f"Failed to get VM info: {e}")
    
    async def start_vm(self, vm_name: str = None, vm_uuid: str = None) -> Dict[str, Any]:
        """Start a VM."""
        try:
            domain = self._get_domain(vm_name, vm_uuid)
            
            if domain.state()[0] == libvirt.VIR_DOMAIN_RUNNING:
                return {
                    "success": True,
                    "message": "VM is already running",
                    "vm_name": domain.name(),
                    "state": "running"
                }
            
            domain.create()
            
            return {
                "success": True,
                "message": "VM started successfully",
                "vm_name": domain.name(),
                "state": "running",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise VMOperationError(f"Failed to start VM: {e}")
    
    async def stop_vm(self, vm_name: str = None, vm_uuid: str = None, force: bool = False) -> Dict[str, Any]:
        """Stop a VM gracefully or forcefully."""
        try:
            domain = self._get_domain(vm_name, vm_uuid)
            
            if domain.state()[0] != libvirt.VIR_DOMAIN_RUNNING:
                return {
                    "success": True,
                    "message": "VM is already stopped",
                    "vm_name": domain.name(),
                    "state": self._get_state_name(domain.state()[0])
                }
            
            if force:
                domain.destroy()
                message = "VM force stopped"
            else:
                domain.shutdown()
                message = "VM shutdown initiated"
            
            return {
                "success": True,
                "message": message,
                "vm_name": domain.name(),
                "force": force,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise VMOperationError(f"Failed to stop VM: {e}")
    
    async def restart_vm(self, vm_name: str = None, vm_uuid: str = None) -> Dict[str, Any]:
        """Restart a VM."""
        try:
            domain = self._get_domain(vm_name, vm_uuid)
            
            if domain.state()[0] == libvirt.VIR_DOMAIN_RUNNING:
                domain.reboot()
                message = "VM reboot initiated"
            else:
                domain.create()
                message = "VM started (was not running)"
            
            return {
                "success": True,
                "message": message,
                "vm_name": domain.name(),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise VMOperationError(f"Failed to restart VM: {e}")
    
    async def pause_vm(self, vm_name: str = None, vm_uuid: str = None) -> Dict[str, Any]:
        """Pause a VM."""
        try:
            domain = self._get_domain(vm_name, vm_uuid)
            
            if domain.state()[0] != libvirt.VIR_DOMAIN_RUNNING:
                return {
                    "success": False,
                    "message": "VM is not running",
                    "vm_name": domain.name(),
                    "state": self._get_state_name(domain.state()[0])
                }
            
            domain.suspend()
            
            return {
                "success": True,
                "message": "VM paused successfully",
                "vm_name": domain.name(),
                "state": "paused",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise VMOperationError(f"Failed to pause VM: {e}")
    
    async def resume_vm(self, vm_name: str = None, vm_uuid: str = None) -> Dict[str, Any]:
        """Resume a paused VM."""
        try:
            domain = self._get_domain(vm_name, vm_uuid)
            
            if domain.state()[0] != libvirt.VIR_DOMAIN_PAUSED:
                return {
                    "success": False,
                    "message": "VM is not paused",
                    "vm_name": domain.name(),
                    "state": self._get_state_name(domain.state()[0])
                }
            
            domain.resume()
            
            return {
                "success": True,
                "message": "VM resumed successfully",
                "vm_name": domain.name(),
                "state": "running",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise VMOperationError(f"Failed to resume VM: {e}")
    
    async def delete_vm(self, vm_name: str = None, vm_uuid: str = None, remove_storage: bool = False) -> Dict[str, Any]:
        """Delete a VM."""
        try:
            domain = self._get_domain(vm_name, vm_uuid)
            vm_name_actual = domain.name()
            
            # Stop the VM if it's running
            if domain.state()[0] == libvirt.VIR_DOMAIN_RUNNING:
                domain.destroy()
            
            # Undefine the domain
            flags = 0
            if remove_storage:
                flags = libvirt.VIR_DOMAIN_UNDEFINE_MANAGED_SAVE | libvirt.VIR_DOMAIN_UNDEFINE_SNAPSHOTS_METADATA
            
            domain.undefineFlags(flags)
            
            return {
                "success": True,
                "message": "VM deleted successfully",
                "vm_name": vm_name_actual,
                "removed_storage": remove_storage,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise VMOperationError(f"Failed to delete VM: {e}")
    
    async def create_snapshot(self, vm_name: str = None, vm_uuid: str = None, snapshot_name: str = None) -> Dict[str, Any]:
        """Create a VM snapshot."""
        try:
            domain = self._get_domain(vm_name, vm_uuid)
            
            if not snapshot_name:
                snapshot_name = f"snapshot_{int(datetime.now().timestamp())}"
            
            # Create snapshot XML
            snapshot_xml = f"""
            <domainsnapshot>
                <name>{snapshot_name}</name>
                <description>Agent created snapshot</description>
            </domainsnapshot>
            """
            
            domain.snapshotCreateXML(snapshot_xml)
            
            return {
                "success": True,
                "message": "Snapshot created successfully",
                "vm_name": domain.name(),
                "snapshot_name": snapshot_name,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise VMOperationError(f"Failed to create snapshot: {e}")
    
    async def execute_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a VM operation command."""
        try:
            operation = command.get("operation")
            vm_name = command.get("vm_name")
            vm_uuid = command.get("vm_uuid")
            parameters = command.get("parameters", {})
            
            if operation == "start":
                return await self.start_vm(vm_name, vm_uuid)
            elif operation == "stop":
                force = parameters.get("force", False)
                return await self.stop_vm(vm_name, vm_uuid, force)
            elif operation == "restart":
                return await self.restart_vm(vm_name, vm_uuid)
            elif operation == "pause":
                return await self.pause_vm(vm_name, vm_uuid)
            elif operation == "resume":
                return await self.resume_vm(vm_name, vm_uuid)
            elif operation == "delete":
                remove_storage = parameters.get("remove_storage", False)
                return await self.delete_vm(vm_name, vm_uuid, remove_storage)
            elif operation == "list":
                vms = await self.list_vms()
                return {"success": True, "vms": vms}
            elif operation == "info":
                info = await self.get_vm_info(vm_name, vm_uuid)
                return {"success": True, "vm_info": info}
            elif operation == "snapshot":
                snapshot_name = parameters.get("snapshot_name")
                return await self.create_snapshot(vm_name, vm_uuid, snapshot_name)
            else:
                return {
                    "success": False,
                    "message": f"Unknown operation: {operation}"
                }
                
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {
                "success": False,
                "message": str(e),
                "error_type": type(e).__name__
            }
    
    def _get_state_name(self, state: int) -> str:
        """Convert libvirt state code to readable name."""
        if not LIBVIRT_AVAILABLE:
            return "unknown"
            
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
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on libvirt connection."""
        try:
            conn = self._get_connection()
            version = conn.getVersion()
            hostname = conn.getHostname()
            
            # Count active domains
            active_domains = len(conn.listDomainsID())
            
            return {
                "status": "healthy",
                "libvirt_version": version,
                "hostname": hostname,
                "active_domains": active_domains,
                "uri": self.libvirt_uri
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "uri": self.libvirt_uri
            }
    
    def close(self):
        """Close libvirt connection."""
        if self._conn:
            try:
                self._conn.close()
            except:
                pass
            self._conn = None