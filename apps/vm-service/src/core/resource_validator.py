"""Resource validation system for VM management."""

import psutil
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.virtual_machine import VirtualMachine, VMStatus
from models.server import Server
from schemas.resources import (
    CPUConfig, MemoryConfig, DiskConfig, NetworkConfig, 
    ResourceLimits, ResourceValidationResult, VMResources
)
from core.logging import get_logger

logger = get_logger("resource_validator")


class ResourceValidator:
    """Resource validation and limit checking system."""
    
    def __init__(self, db: Session):
        self.db = db
        
    def get_system_limits(self) -> ResourceLimits:
        """Get system resource limits."""
        # Get system information
        cpu_count = psutil.cpu_count(logical=False)  # Physical cores
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/var/lib/libvirt/images')
        
        # Calculate available resources (leave some headroom)
        max_cpu_cores = min(32, cpu_count)  # Cap at 32 cores per VM
        max_memory_mb = min(65536, int(memory_info.total * 0.8 / (1024 * 1024)))  # 80% of total RAM
        max_disk_gb = min(2000.0, disk_info.free / (1024 ** 3) * 0.9)  # 90% of free space
        
        # Get current allocation
        allocated = self._get_current_allocation()
        
        return ResourceLimits(
            max_cpu_cores=max_cpu_cores,
            max_memory_mb=max_memory_mb,
            max_disk_gb=max_disk_gb,
            max_disks=10,
            max_networks=5,
            available_cpu_cores=max_cpu_cores - allocated["cpu_cores"],
            available_memory_mb=max_memory_mb - allocated["memory_mb"],
            available_disk_gb=max_disk_gb - allocated["disk_gb"]
        )
    
    def _get_current_allocation(self) -> Dict[str, Any]:
        """Get current resource allocation across all VMs."""
        result = self.db.query(
            func.sum(VirtualMachine.cpu_cores).label('cpu_cores'),
            func.sum(VirtualMachine.memory_mb).label('memory_mb'),
            func.sum(VirtualMachine.disk_gb).label('disk_gb'),
            func.count(VirtualMachine.id).label('vm_count')
        ).filter(
            VirtualMachine.status.in_([VMStatus.RUNNING, VMStatus.STOPPED, VMStatus.PAUSED])
        ).first()
        
        return {
            "cpu_cores": result.cpu_cores or 0,
            "memory_mb": result.memory_mb or 0,
            "disk_gb": result.disk_gb or 0,
            "vm_count": result.vm_count or 0
        }
    
    def validate_cpu_config(self, cpu: CPUConfig) -> ResourceValidationResult:
        """Validate CPU configuration."""
        errors = []
        warnings = []
        
        # Basic validation
        if cpu.cores < 1 or cpu.cores > 32:
            errors.append("CPU cores must be between 1 and 32")
        
        if cpu.sockets < 1 or cpu.sockets > 4:
            errors.append("CPU sockets must be between 1 and 4")
        
        if cpu.threads < 1 or cpu.threads > 2:
            errors.append("CPU threads per core must be 1 or 2")
        
        # Check if total logical CPUs exceed system capacity
        total_logical_cpus = cpu.cores * cpu.sockets * cpu.threads
        system_cpus = psutil.cpu_count(logical=True)
        if total_logical_cpus > system_cpus:
            errors.append(f"Total logical CPUs ({total_logical_cpus}) exceeds system capacity ({system_cpus})")
        
        # Validate CPU pinning
        if cpu.pinning:
            system_cpus = psutil.cpu_count(logical=True)
            for core in cpu.pinning:
                if core < 0 or core >= system_cpus:
                    errors.append(f"CPU pinning core {core} is invalid (system has {system_cpus} cores)")
            
            if len(cpu.pinning) != cpu.cores:
                errors.append("CPU pinning list length must match number of cores")
        
        # Validate CPU shares and limits
        if cpu.shares is not None and (cpu.shares < 1 or cpu.shares > 2048):
            errors.append("CPU shares must be between 1 and 2048")
        
        if cpu.limit is not None and (cpu.limit < 1 or cpu.limit > 100):
            errors.append("CPU limit must be between 1 and 100 percent")
        
        return ResourceValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_memory_config(self, memory: MemoryConfig) -> ResourceValidationResult:
        """Validate memory configuration."""
        errors = []
        warnings = []
        
        # Basic validation
        if memory.size_mb < 512:
            errors.append("Memory size must be at least 512MB")
        
        if memory.size_mb > 65536:
            errors.append("Memory size cannot exceed 64GB")
        
        # Check system memory availability
        system_memory_mb = psutil.virtual_memory().total / (1024 * 1024)
        if memory.size_mb > system_memory_mb * 0.9:
            errors.append(f"Memory allocation ({memory.size_mb}MB) exceeds 90% of system memory ({int(system_memory_mb)}MB)")
        
        # Validate memory shares
        if memory.shares is not None and (memory.shares < 1 or memory.shares > 2048):
            errors.append("Memory shares must be between 1 and 2048")
        
        # Validate overcommit ratio
        if memory.overcommit_ratio is not None and (memory.overcommit_ratio < 0.5 or memory.overcommit_ratio > 2.0):
            errors.append("Memory overcommit ratio must be between 0.5 and 2.0")
        
        # Check hugepages availability (simplified check)
        if memory.hugepages:
            warnings.append("Hugepages support requires proper system configuration")
        
        return ResourceValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_disk_config(self, disks: List[DiskConfig]) -> ResourceValidationResult:
        """Validate disk configuration."""
        errors = []
        warnings = []
        
        if not disks:
            errors.append("At least one disk is required")
            return ResourceValidationResult(valid=False, errors=errors, warnings=warnings)
        
        if len(disks) > 10:
            errors.append("Maximum 10 disks allowed per VM")
        
        bootable_count = sum(1 for disk in disks if disk.bootable)
        if bootable_count == 0:
            warnings.append("No bootable disk specified")
        elif bootable_count > 1:
            errors.append("Only one disk can be marked as bootable")
        
        # Validate individual disks
        disk_names = set()
        total_size_gb = 0
        
        for disk in disks:
            # Check for duplicate names
            if disk.name in disk_names:
                errors.append(f"Duplicate disk name: {disk.name}")
            disk_names.add(disk.name)
            
            # Validate disk size
            if disk.size_gb < 1.0:
                errors.append(f"Disk {disk.name} size must be at least 1GB")
            
            if disk.size_gb > 2000.0:
                errors.append(f"Disk {disk.name} size cannot exceed 2TB")
            
            total_size_gb += disk.size_gb
            
            # Validate disk format
            if disk.format not in ["qcow2", "raw", "vmdk"]:
                errors.append(f"Disk {disk.name} format must be qcow2, raw, or vmdk")
            
            # Validate cache mode
            if disk.cache not in ["none", "writeback", "writethrough", "directsync", "unsafe"]:
                errors.append(f"Disk {disk.name} cache mode is invalid")
        
        # Check total disk space
        try:
            disk_info = psutil.disk_usage('/var/lib/libvirt/images')
            available_gb = disk_info.free / (1024 ** 3)
            if total_size_gb > available_gb * 0.9:
                errors.append(f"Total disk allocation ({total_size_gb:.1f}GB) exceeds available space ({available_gb:.1f}GB)")
        except Exception as e:
            warnings.append(f"Could not check disk space: {str(e)}")
        
        return ResourceValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_network_config(self, networks: List[NetworkConfig]) -> ResourceValidationResult:
        """Validate network configuration."""
        errors = []
        warnings = []
        
        if not networks:
            errors.append("At least one network interface is required")
            return ResourceValidationResult(valid=False, errors=errors, warnings=warnings)
        
        if len(networks) > 5:
            errors.append("Maximum 5 network interfaces allowed per VM")
        
        # Validate individual network interfaces
        interface_names = set()
        mac_addresses = set()
        
        for network in networks:
            # Check for duplicate names
            if network.name in interface_names:
                errors.append(f"Duplicate network interface name: {network.name}")
            interface_names.add(network.name)
            
            # Validate MAC address if provided
            if network.mac_address:
                if network.mac_address in mac_addresses:
                    errors.append(f"Duplicate MAC address: {network.mac_address}")
                mac_addresses.add(network.mac_address)
                
                # Basic MAC address format validation
                if not self._is_valid_mac_address(network.mac_address):
                    errors.append(f"Invalid MAC address format: {network.mac_address}")
            
            # Validate VLAN ID
            if network.vlan_id is not None and (network.vlan_id < 1 or network.vlan_id > 4094):
                errors.append(f"VLAN ID for {network.name} must be between 1 and 4094")
            
            # Validate IP configuration
            if network.ip_address:
                if not self._is_valid_ip_address(network.ip_address):
                    errors.append(f"Invalid IP address for {network.name}: {network.ip_address}")
            
            # Validate bandwidth limit
            if network.bandwidth_limit is not None and network.bandwidth_limit < 1:
                errors.append(f"Bandwidth limit for {network.name} must be at least 1 Mbps")
        
        return ResourceValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_vm_resources(self, resources: VMResources) -> ResourceValidationResult:
        """Validate complete VM resource configuration."""
        all_errors = []
        all_warnings = []
        
        # Validate individual components
        cpu_result = self.validate_cpu_config(resources.cpu)
        memory_result = self.validate_memory_config(resources.memory)
        disk_result = self.validate_disk_config(resources.disks)
        network_result = self.validate_network_config(resources.network)
        
        # Collect all errors and warnings
        all_errors.extend(cpu_result.errors)
        all_errors.extend(memory_result.errors)
        all_errors.extend(disk_result.errors)
        all_errors.extend(network_result.errors)
        
        all_warnings.extend(cpu_result.warnings)
        all_warnings.extend(memory_result.warnings)
        all_warnings.extend(disk_result.warnings)
        all_warnings.extend(network_result.warnings)
        
        # Cross-validation checks
        # Check if resource allocation would exceed system limits
        limits = self.get_system_limits()
        
        if resources.cpu.cores > limits.available_cpu_cores:
            all_errors.append(f"Not enough CPU cores available (requested: {resources.cpu.cores}, available: {limits.available_cpu_cores})")
        
        if resources.memory.size_mb > limits.available_memory_mb:
            all_errors.append(f"Not enough memory available (requested: {resources.memory.size_mb}MB, available: {limits.available_memory_mb}MB)")
        
        total_disk_gb = sum(disk.size_gb for disk in resources.disks)
        if total_disk_gb > limits.available_disk_gb:
            all_errors.append(f"Not enough disk space available (requested: {total_disk_gb:.1f}GB, available: {limits.available_disk_gb:.1f}GB)")
        
        return ResourceValidationResult(
            valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings
        )
    
    def _is_valid_mac_address(self, mac: str) -> bool:
        """Validate MAC address format."""
        import re
        pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
        return bool(re.match(pattern, mac))
    
    def _is_valid_ip_address(self, ip: str) -> bool:
        """Validate IP address format."""
        import ipaddress
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False