"""Enhanced exception system for VM Service with error codes and standardized responses."""

from datetime import datetime
from typing import Dict, Any, Optional
from .error_codes import ErrorCode, get_error_category, get_http_status_code


class VMServiceException(Exception):
    """Base exception for VM Service with error code support."""
    
    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.user_message = user_message or message
        self.category = get_error_category(error_code)
        self.http_status = get_http_status_code(error_code)
        self.timestamp = datetime.utcnow()
        super().__init__(self.message)
    
    def to_dict(self, request_id: Optional[str] = None) -> Dict[str, Any]:
        """Convert exception to standardized error response format."""
        return {
            "error": {
                "code": self.error_code.value,
                "message": self.user_message,
                "details": self.details,
                "category": self.category.value,
                "timestamp": self.timestamp.isoformat() + "Z",
                "request_id": request_id
            }
        }


class ValidationException(VMServiceException):
    """Exception for validation errors."""
    
    def __init__(self, message: str, field: str = None, details: Dict[str, Any] = None):
        validation_details = details or {}
        if field:
            validation_details["field"] = field
        
        super().__init__(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=message,
            details=validation_details,
            user_message=message
        )


class ResourceNotFoundException(VMServiceException):
    """Exception for resource not found errors."""
    
    def __init__(self, resource_type: str, resource_id: str, details: Dict[str, Any] = None):
        message = f"{resource_type} with ID '{resource_id}' not found"
        resource_details = details or {}
        resource_details.update({
            "resource_type": resource_type,
            "resource_id": resource_id
        })
        
        super().__init__(
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            message=message,
            details=resource_details,
            user_message=f"The requested {resource_type.lower()} was not found."
        )


class VMNotFoundException(VMServiceException):
    """Exception for VM not found errors."""
    
    def __init__(self, vm_name: str = None, vm_uuid: str = None, details: Dict[str, Any] = None):
        vm_details = details or {}
        
        if vm_uuid:
            message = f"VM with UUID '{vm_uuid}' not found"
            vm_details["vm_uuid"] = vm_uuid
        elif vm_name:
            message = f"VM with name '{vm_name}' not found"
            vm_details["vm_name"] = vm_name
        else:
            message = "VM not found"
        
        super().__init__(
            error_code=ErrorCode.VM_NOT_FOUND,
            message=message,
            details=vm_details,
            user_message="The virtual machine you're looking for was not found."
        )


class VMOperationException(VMServiceException):
    """Exception for VM operation failures."""
    
    def __init__(self, operation: str, vm_name: str, reason: str, details: Dict[str, Any] = None):
        operation_details = details or {}
        operation_details.update({
            "operation": operation,
            "vm_name": vm_name,
            "reason": reason
        })
        
        # Map operation to specific error code
        error_code_map = {
            "create": ErrorCode.VM_CREATE_FAILED,
            "start": ErrorCode.VM_START_FAILED,
            "stop": ErrorCode.VM_STOP_FAILED,
            "delete": ErrorCode.VM_DELETE_FAILED,
            "clone": ErrorCode.VM_CLONE_FAILED,
        }
        
        error_code = error_code_map.get(operation, ErrorCode.VM_OPERATION_FAILED)
        message = f"Failed to {operation} VM '{vm_name}': {reason}"
        user_message = f"Unable to {operation} the virtual machine. {reason}"
        
        super().__init__(
            error_code=error_code,
            message=message,
            details=operation_details,
            user_message=user_message
        )


class ResourceAllocationException(VMServiceException):
    """Exception for resource allocation failures."""
    
    def __init__(self, resource_type: str, requested: str, available: str = None, details: Dict[str, Any] = None):
        allocation_details = details or {}
        allocation_details.update({
            "resource_type": resource_type,
            "requested": requested
        })
        
        if available:
            allocation_details["available"] = available
            message = f"Insufficient {resource_type}: requested {requested}, available {available}"
            user_message = f"Not enough {resource_type} available. You requested {requested} but only {available} is available."
        else:
            message = f"Failed to allocate {resource_type}: {requested}"
            user_message = f"Unable to allocate the requested {resource_type}: {requested}"
        
        # Map resource type to specific error code
        error_code_map = {
            "memory": ErrorCode.INSUFFICIENT_MEMORY,
            "cpu": ErrorCode.INSUFFICIENT_CPU,
            "storage": ErrorCode.INSUFFICIENT_STORAGE,
        }
        
        error_code = error_code_map.get(resource_type.lower(), ErrorCode.RESOURCE_ALLOCATION_FAILED)
        
        super().__init__(
            error_code=error_code,
            message=message,
            details=allocation_details,
            user_message=user_message
        )


class LibvirtException(VMServiceException):
    """Exception for libvirt-related errors."""
    
    def __init__(self, operation: str, reason: str, details: Dict[str, Any] = None):
        libvirt_details = details or {}
        libvirt_details.update({
            "operation": operation,
            "reason": reason
        })
        
        message = f"Libvirt {operation} failed: {reason}"
        user_message = f"A virtualization error occurred during {operation}. Please try again or contact support."
        
        super().__init__(
            error_code=ErrorCode.LIBVIRT_OPERATION_FAILED,
            message=message,
            details=libvirt_details,
            user_message=user_message
        )


class VMStateException(VMServiceException):
    """Exception for invalid VM state operations."""
    
    def __init__(self, vm_name: str, current_state: str, required_state: str, details: Dict[str, Any] = None):
        state_details = details or {}
        state_details.update({
            "vm_name": vm_name,
            "current_state": current_state,
            "required_state": required_state
        })
        
        message = f"VM '{vm_name}' is in state '{current_state}' but requires '{required_state}'"
        user_message = f"The virtual machine is currently {current_state} but needs to be {required_state} for this operation."
        
        super().__init__(
            error_code=ErrorCode.VM_STATE_INVALID,
            message=message,
            details=state_details,
            user_message=user_message
        )


class ServerNotFoundException(VMServiceException):
    """Exception for server not found errors."""
    
    def __init__(self, server_id: str, details: Dict[str, Any] = None):
        server_details = details or {}
        server_details["server_id"] = server_id
        
        message = f"Server with ID '{server_id}' not found"
        user_message = "The requested server was not found."
        
        super().__init__(
            error_code=ErrorCode.SERVER_NOT_FOUND,
            message=message,
            details=server_details,
            user_message=user_message
        )


class ExternalServiceException(VMServiceException):
    """Exception for external service errors."""
    
    def __init__(self, service_name: str, operation: str, reason: str, details: Dict[str, Any] = None):
        service_details = details or {}
        service_details.update({
            "service_name": service_name,
            "operation": operation,
            "reason": reason
        })
        
        message = f"External service '{service_name}' failed during {operation}: {reason}"
        user_message = f"An external service is currently unavailable. Please try again later."
        
        super().__init__(
            error_code=ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE,
            message=message,
            details=service_details,
            user_message=user_message
        )