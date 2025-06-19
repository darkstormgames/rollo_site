"""Custom exceptions for libvirt operations."""


class LibvirtError(Exception):
    """Base exception for all libvirt-related errors."""
    
    def __init__(self, message: str, error_code: int = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class LibvirtConnectionError(LibvirtError):
    """Exception raised when libvirt connection fails."""
    pass


class VMNotFoundError(LibvirtError):
    """Exception raised when a VM is not found."""
    
    def __init__(self, vm_name: str = None, vm_uuid: str = None):
        if vm_uuid:
            message = f"VM with UUID '{vm_uuid}' not found"
        elif vm_name:
            message = f"VM with name '{vm_name}' not found"
        else:
            message = "VM not found"
        super().__init__(message)


class VMOperationError(LibvirtError):
    """Exception raised when VM operations fail."""
    
    def __init__(self, operation: str, vm_name: str, message: str):
        self.operation = operation
        self.vm_name = vm_name
        full_message = f"Failed to {operation} VM '{vm_name}': {message}"
        super().__init__(full_message)


class ResourceAllocationError(LibvirtError):
    """Exception raised when resource allocation fails."""
    
    def __init__(self, resource_type: str, requested: str, available: str = None):
        if available:
            message = f"Insufficient {resource_type}: requested {requested}, available {available}"
        else:
            message = f"Failed to allocate {resource_type}: {requested}"
        super().__init__(message)


class TemplateGenerationError(LibvirtError):
    """Exception raised when XML template generation fails."""
    
    def __init__(self, template_type: str, message: str):
        self.template_type = template_type
        full_message = f"Failed to generate {template_type} template: {message}"
        super().__init__(full_message)


class NetworkConfigurationError(LibvirtError):
    """Exception raised when network configuration fails."""
    pass


class StorageConfigurationError(LibvirtError):
    """Exception raised when storage configuration fails."""
    pass


class VMStateError(LibvirtError):
    """Exception raised when VM is in an invalid state for the requested operation."""
    
    def __init__(self, vm_name: str, current_state: str, required_state: str):
        self.vm_name = vm_name
        self.current_state = current_state
        self.required_state = required_state
        message = f"VM '{vm_name}' is in state '{current_state}' but requires '{required_state}'"
        super().__init__(message)