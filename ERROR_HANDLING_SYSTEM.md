# Error Handling and User Notifications System

This document describes the comprehensive error handling and notification system implemented for both backend and frontend.

## Overview

The error handling system provides:
- Standardized error responses from the backend
- Automatic error interception and retry logic
- User-friendly notifications (toasts, dialogs)
- Offline detection and handling
- Error recovery mechanisms
- Request tracking with unique IDs

## Backend Components

### Error Codes (`core/error_codes.py`)

Defines standardized error codes organized by category:

```python
from core.error_codes import ErrorCode

# Usage examples
ErrorCode.VM_CREATE_FAILED        # VM-specific errors
ErrorCode.INSUFFICIENT_MEMORY     # Resource errors
ErrorCode.VALIDATION_ERROR        # Input validation errors
ErrorCode.INTERNAL_SERVER_ERROR   # System errors
```

Error codes are automatically mapped to:
- HTTP status codes
- Error categories (system, authentication, validation, etc.)
- Severity levels

### Custom Exceptions (`core/exceptions.py`)

Enhanced exception classes with structured error information:

```python
from core.exceptions import VMOperationException, ResourceAllocationException

# Detailed VM operation error
raise VMOperationException(
    operation="create",
    vm_name="test-vm",
    reason="Insufficient resources",
    details={
        "requested_memory": 4096,
        "available_memory": 2048
    }
)

# Resource allocation error
raise ResourceAllocationException(
    resource_type="memory",
    requested="4GB",
    available="2GB"
)
```

### Global Exception Handler (`core/exception_handlers.py`)

Automatically converts exceptions to standardized error responses:

```json
{
  "error": {
    "code": "VM_CREATE_FAILED",
    "message": "Failed to create virtual machine",
    "details": {
      "reason": "Insufficient resources",
      "available_memory": 2048,
      "requested_memory": 4096
    },
    "timestamp": "2024-01-20T10:30:00Z",
    "request_id": "req_123456",
    "category": "virtualization"
  }
}
```

### Request ID Middleware (`core/request_id.py`)

Adds unique request IDs to track requests across the system:

```python
# Automatically added to all requests
X-Request-ID: req_123456
```

## Frontend Components

### Notification Service (`services/shared/notification.service.ts`)

Central service for displaying notifications:

```typescript
import { NotificationService } from './notification.service';

constructor(private notificationService: NotificationService) {}

// Success notification (auto-dismisses in 3s)
this.notificationService.showSuccess('VM created successfully!');

// Error notification (manual dismiss)
this.notificationService.showError('Failed to create VM');

// Warning notification (auto-dismisses in 5s)
this.notificationService.showWarning('Low disk space detected');

// Info notification
this.notificationService.showInfo('Starting VM creation...');

// Critical error dialog
this.notificationService.showErrorDialog({
  code: 'VM_CREATE_FAILED',
  message: 'Critical error occurred',
  severity: 'critical',
  retryable: true
});
```

### Toast Component (`components/shared/toast/toast.component.ts`)

Custom toast component with different styles for each notification type:

- **Success**: Green, checkmark icon, auto-dismiss (3s)
- **Error**: Red, error icon, manual dismiss
- **Warning**: Orange, warning icon, auto-dismiss (5s)
- **Info**: Blue, info icon, auto-dismiss (3s)

### Error Dialog Component (`components/shared/error-dialog/error-dialog.component.ts`)

Modal dialog for critical errors with:
- Error details expansion panel
- Copy to clipboard functionality
- Retry and report issue buttons
- Technical information display

### Enhanced Error Interceptor (`services/shared/error.interceptor.ts`)

HTTP interceptor with automatic retry logic:

```typescript
// Features:
- Automatic retry for network errors (exponential backoff)
- Smart error categorization
- Integration with notification service
- Request ID tracking
- Offline handling
```

### Offline Detection Service (`services/shared/offline-detection.service.ts`)

Monitors network connectivity:

```typescript
// Check if online
if (this.offlineDetection.requireOnline('create VM')) {
  // Proceed with operation
}

// Subscribe to connection changes
this.offlineDetection.isOnline$.subscribe(isOnline => {
  // Handle connection changes
});
```

### Error Recovery Service (`services/shared/error-recovery.service.ts`)

Provides retry and recovery strategies:

```typescript
// Retry with exponential backoff
this.errorRecovery.retryWithBackoff(
  () => this.http.post('/api/vms', data),
  { maxAttempts: 3, delay: 1000 }
);

// Execute with online check
this.errorRecovery.executeWithOnlineCheck(
  () => this.someOperation(),
  'perform this action'
);

// Graceful degradation
this.errorRecovery.gracefulDegrade(
  () => this.getLiveData(),
  this.cachedData,
  'Using cached data due to connectivity issues'
);
```

## Integration Examples

### Service Integration

```typescript
// services/vm/vm.service.ts
export class VmService {
  createVM(vmData: CreateVMRequest): Observable<VM> {
    return this.errorRecovery.retryWithBackoff(
      () => this.http.post<VM>('/api/vms', vmData),
      { maxAttempts: 2, showNotifications: true }
    ).pipe(
      map(vm => {
        this.notificationService.showSuccess(
          `VM "${vm.name}" created successfully!`
        );
        return vm;
      }),
      catchError(error => {
        // Handle specific errors
        if (error?.error?.code === 'INSUFFICIENT_MEMORY') {
          this.notificationService.showError(
            'Not enough memory available. Try reducing allocation.',
            { action: 'ADJUST SETTINGS' }
          );
        }
        throw error;
      })
    );
  }
}
```

### Component Integration

```typescript
// components/vm-list/vm-list.component.ts
export class VmListComponent {
  loadVMs(): void {
    this.vmService.getVMs()
      .pipe(
        takeUntil(this.destroy$),
        finalize(() => this.loading = false)
      )
      .subscribe({
        next: (vms) => this.vms = vms,
        error: (error) => {
          // Error handling is automatic via interceptor
          console.error('Failed to load VMs:', error);
        }
      });
  }
}
```

## Error Handling Patterns

### 1. Automatic Retry
For transient errors (network timeouts, temporary service unavailable):
```typescript
// Automatically retried by error interceptor
// No additional code needed in components
```

### 2. User Notification
For user-actionable errors:
```typescript
// Backend sends structured error
// Frontend shows appropriate notification
// User gets clear next steps
```

### 3. Critical Error Dialog
For system errors requiring attention:
```typescript
// Shows detailed error dialog
// Includes technical details
// Provides report functionality
```

### 4. Graceful Degradation
For non-critical feature failures:
```typescript
// Falls back to cached data
// Shows degraded mode notification
// Maintains core functionality
```

### 5. Offline Handling
For network connectivity issues:
```typescript
// Detects offline state
// Prevents futile requests
// Shows appropriate messaging
```

## Error Code Categories

| Category | Description | Examples |
|----------|-------------|----------|
| `system` | Internal system errors | `INTERNAL_SERVER_ERROR` |
| `authentication` | Auth/permission errors | `UNAUTHORIZED`, `FORBIDDEN` |
| `validation` | Input validation errors | `VALIDATION_ERROR` |
| `resource` | Resource not found | `VM_NOT_FOUND`, `SERVER_NOT_FOUND` |
| `virtualization` | VM operation errors | `VM_CREATE_FAILED`, `INSUFFICIENT_MEMORY` |
| `network` | Network/connectivity | `NETWORK_CONFIGURATION_FAILED` |
| `external` | External service errors | `EXTERNAL_SERVICE_UNAVAILABLE` |

## Testing the System

The system includes a demo component (`components/examples/error-handling-example.component.ts`) that demonstrates:

1. **Connection Status**: Shows online/offline state
2. **Error Scenarios**: Test different notification types
3. **Real Operations**: VM management with error handling
4. **Recovery Testing**: Retry and fallback mechanisms

## Best Practices

### Backend
1. Use specific error codes for different scenarios
2. Include helpful details in error responses
3. Log errors with request IDs for debugging
4. Provide user-friendly messages alongside technical details

### Frontend
1. Let the error interceptor handle common errors
2. Add specific handling only for business logic errors
3. Use loading states and provide feedback
4. Test offline scenarios
5. Implement graceful degradation where possible

## Configuration

### Backend Configuration
```python
# app.py
from core.exception_handlers import setup_exception_handlers

app = FastAPI()
setup_exception_handlers(app)  # Enable global error handling
```

### Frontend Configuration
```typescript
// app.config.ts
import { ErrorInterceptor } from './services/shared/error.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    // ... other providers
    { provide: HTTP_INTERCEPTORS, useClass: ErrorInterceptor, multi: true }
  ]
};
```

## Monitoring and Analytics

The system provides error tracking through:
- Request IDs for tracing errors across services
- Structured error logging with categorization
- Client-side error history in NotificationService
- Error severity classification for prioritization

This enables effective monitoring and debugging of issues in production environments.