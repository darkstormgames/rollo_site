"""Error codes for VM Service API responses."""

from enum import Enum
from typing import Dict, Any


class ErrorCode(str, Enum):
    """Standard error codes for API responses."""
    
    # General errors (1000-1099)
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    
    # Authentication/Authorization errors (1100-1199)
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    
    # Resource errors (1200-1299)
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    
    # VM-specific errors (2000-2099)
    VM_NOT_FOUND = "VM_NOT_FOUND"
    VM_CREATE_FAILED = "VM_CREATE_FAILED"
    VM_START_FAILED = "VM_START_FAILED"
    VM_STOP_FAILED = "VM_STOP_FAILED"
    VM_DELETE_FAILED = "VM_DELETE_FAILED"
    VM_CLONE_FAILED = "VM_CLONE_FAILED"
    VM_STATE_INVALID = "VM_STATE_INVALID"
    VM_OPERATION_FAILED = "VM_OPERATION_FAILED"
    
    # Resource allocation errors (2100-2199)
    INSUFFICIENT_MEMORY = "INSUFFICIENT_MEMORY"
    INSUFFICIENT_CPU = "INSUFFICIENT_CPU"
    INSUFFICIENT_STORAGE = "INSUFFICIENT_STORAGE"
    RESOURCE_ALLOCATION_FAILED = "RESOURCE_ALLOCATION_FAILED"
    
    # Libvirt/Virtualization errors (2200-2299)
    LIBVIRT_CONNECTION_FAILED = "LIBVIRT_CONNECTION_FAILED"
    LIBVIRT_OPERATION_FAILED = "LIBVIRT_OPERATION_FAILED"
    TEMPLATE_GENERATION_FAILED = "TEMPLATE_GENERATION_FAILED"
    NETWORK_CONFIGURATION_FAILED = "NETWORK_CONFIGURATION_FAILED"
    STORAGE_CONFIGURATION_FAILED = "STORAGE_CONFIGURATION_FAILED"
    
    # Server errors (3000-3099)
    SERVER_NOT_FOUND = "SERVER_NOT_FOUND"
    SERVER_UNAVAILABLE = "SERVER_UNAVAILABLE"
    SERVER_CONNECTION_FAILED = "SERVER_CONNECTION_FAILED"
    
    # External service errors (4000-4099)
    EXTERNAL_SERVICE_UNAVAILABLE = "EXTERNAL_SERVICE_UNAVAILABLE"
    EXTERNAL_SERVICE_TIMEOUT = "EXTERNAL_SERVICE_TIMEOUT"


class ErrorCategory(str, Enum):
    """Error categories for grouping related errors."""
    
    SYSTEM = "system"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    RESOURCE = "resource"
    VIRTUALIZATION = "virtualization"
    NETWORK = "network"
    EXTERNAL = "external"


# Error code to category mapping
ERROR_CATEGORIES: Dict[ErrorCode, ErrorCategory] = {
    # System errors
    ErrorCode.UNKNOWN_ERROR: ErrorCategory.SYSTEM,
    ErrorCode.INTERNAL_SERVER_ERROR: ErrorCategory.SYSTEM,
    
    # Authentication errors
    ErrorCode.UNAUTHORIZED: ErrorCategory.AUTHENTICATION,
    ErrorCode.FORBIDDEN: ErrorCategory.AUTHENTICATION,
    ErrorCode.INVALID_TOKEN: ErrorCategory.AUTHENTICATION,
    ErrorCode.TOKEN_EXPIRED: ErrorCategory.AUTHENTICATION,
    
    # Validation errors
    ErrorCode.VALIDATION_ERROR: ErrorCategory.VALIDATION,
    
    # Resource errors
    ErrorCode.RESOURCE_NOT_FOUND: ErrorCategory.RESOURCE,
    ErrorCode.RESOURCE_ALREADY_EXISTS: ErrorCategory.RESOURCE,
    ErrorCode.RESOURCE_CONFLICT: ErrorCategory.RESOURCE,
    ErrorCode.VM_NOT_FOUND: ErrorCategory.RESOURCE,
    ErrorCode.SERVER_NOT_FOUND: ErrorCategory.RESOURCE,
    
    # Virtualization errors
    ErrorCode.VM_CREATE_FAILED: ErrorCategory.VIRTUALIZATION,
    ErrorCode.VM_START_FAILED: ErrorCategory.VIRTUALIZATION,
    ErrorCode.VM_STOP_FAILED: ErrorCategory.VIRTUALIZATION,
    ErrorCode.VM_DELETE_FAILED: ErrorCategory.VIRTUALIZATION,
    ErrorCode.VM_CLONE_FAILED: ErrorCategory.VIRTUALIZATION,
    ErrorCode.VM_STATE_INVALID: ErrorCategory.VIRTUALIZATION,
    ErrorCode.VM_OPERATION_FAILED: ErrorCategory.VIRTUALIZATION,
    ErrorCode.INSUFFICIENT_MEMORY: ErrorCategory.VIRTUALIZATION,
    ErrorCode.INSUFFICIENT_CPU: ErrorCategory.VIRTUALIZATION,
    ErrorCode.INSUFFICIENT_STORAGE: ErrorCategory.VIRTUALIZATION,
    ErrorCode.RESOURCE_ALLOCATION_FAILED: ErrorCategory.VIRTUALIZATION,
    ErrorCode.LIBVIRT_CONNECTION_FAILED: ErrorCategory.VIRTUALIZATION,
    ErrorCode.LIBVIRT_OPERATION_FAILED: ErrorCategory.VIRTUALIZATION,
    ErrorCode.TEMPLATE_GENERATION_FAILED: ErrorCategory.VIRTUALIZATION,
    ErrorCode.STORAGE_CONFIGURATION_FAILED: ErrorCategory.VIRTUALIZATION,
    
    # Network errors
    ErrorCode.NETWORK_CONFIGURATION_FAILED: ErrorCategory.NETWORK,
    ErrorCode.SERVER_UNAVAILABLE: ErrorCategory.NETWORK,
    ErrorCode.SERVER_CONNECTION_FAILED: ErrorCategory.NETWORK,
    
    # External service errors
    ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE: ErrorCategory.EXTERNAL,
    ErrorCode.EXTERNAL_SERVICE_TIMEOUT: ErrorCategory.EXTERNAL,
}


def get_error_category(error_code: ErrorCode) -> ErrorCategory:
    """Get the category for an error code."""
    return ERROR_CATEGORIES.get(error_code, ErrorCategory.SYSTEM)


def get_http_status_code(error_code: ErrorCode) -> int:
    """Get the appropriate HTTP status code for an error code."""
    
    # Authentication/Authorization errors -> 401/403
    if error_code in [ErrorCode.UNAUTHORIZED, ErrorCode.INVALID_TOKEN, ErrorCode.TOKEN_EXPIRED]:
        return 401
    elif error_code == ErrorCode.FORBIDDEN:
        return 403
    
    # Not found errors -> 404
    elif error_code in [ErrorCode.RESOURCE_NOT_FOUND, ErrorCode.VM_NOT_FOUND, ErrorCode.SERVER_NOT_FOUND]:
        return 404
    
    # Conflict errors -> 409
    elif error_code in [ErrorCode.RESOURCE_ALREADY_EXISTS, ErrorCode.RESOURCE_CONFLICT, ErrorCode.VM_STATE_INVALID]:
        return 409
    
    # Validation errors -> 400
    elif error_code == ErrorCode.VALIDATION_ERROR:
        return 400
    
    # Resource allocation errors -> 422
    elif error_code in [ErrorCode.INSUFFICIENT_MEMORY, ErrorCode.INSUFFICIENT_CPU, ErrorCode.INSUFFICIENT_STORAGE]:
        return 422
    
    # External service errors -> 502/503
    elif error_code in [ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE, ErrorCode.SERVER_UNAVAILABLE]:
        return 503
    elif error_code == ErrorCode.EXTERNAL_SERVICE_TIMEOUT:
        return 504
    
    # All other errors -> 500
    else:
        return 500