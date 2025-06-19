# WebSocket Real-Time Monitoring System

This document describes the WebSocket-based real-time monitoring system implemented for the Rollo VM management platform.

## Overview

The WebSocket system provides real-time updates for:
- VM status changes and metrics
- Server status changes and metrics  
- Operation progress tracking
- System alerts and notifications
- Console streaming

## Architecture

### Backend (FastAPI)

#### WebSocket Manager
The `WebSocketManager` class handles:
- Connection lifecycle management
- Room-based subscriptions
- Message broadcasting
- Authentication integration

#### Event Broadcasting
The `EventBroadcaster` class provides structured events:
- VM events: status changes, creation/deletion, metrics
- Server events: status changes, registration/removal, metrics
- Progress events: operation tracking with percentage completion
- Alert events: system notifications with severity levels

#### Authentication
WebSocket connections support:
- Token-based authentication using JWT
- Anonymous access for public information
- Permission-based access control

### Frontend (Angular)

#### WebSocket Service
Enhanced features include:
- Auto-reconnection with exponential backoff
- Message queuing for offline scenarios  
- Event type filtering with RxJS observables
- Connection status monitoring

#### UI Components
- `ConnectionStatusComponent`: Visual connection indicator
- `RealtimeMonitorComponent`: Comprehensive monitoring dashboard

## WebSocket Endpoints

### `/ws/monitor`
Main monitoring endpoint for general system updates.

**Query Parameters:**
- `token` (optional): JWT authentication token

**Supported Events:**
- VM status changes
- Server status changes
- Metrics updates
- Progress notifications
- System alerts

### `/ws/vm/{vm_id}`
VM-specific monitoring endpoint.

**Features:**
- Auto-subscribes to VM-specific events
- VM metrics in real-time
- VM operation progress
- VM-specific alerts

### `/ws/server/{server_id}`
Server-specific monitoring endpoint.

**Features:**
- Auto-subscribes to server-specific events
- Server metrics in real-time
- Server alerts

### `/ws/console/{vm_id}`
Console streaming endpoint for VM console access.

**Features:**
- Real-time console output
- Console input handling
- Console session management

### `/ws/stats`
WebSocket system statistics (admin only).

**Provides:**
- Active connection counts
- Room subscription statistics
- System health metrics

## Message Protocol

### Client to Server Messages

#### Subscribe to Events
```json
{
  "type": "subscribe",
  "data": {
    "events": ["vm_status_changed", "vm_metrics_update"],
    "vm_ids": [1, 2, 3],
    "server_ids": [1]
  }
}
```

#### Unsubscribe from Events
```json
{
  "type": "unsubscribe", 
  "data": {
    "events": ["vm_status_changed"],
    "vm_ids": [1]
  }
}
```

#### Heartbeat
```json
{
  "type": "ping",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Server to Client Messages

#### VM Status Change
```json
{
  "type": "vm_status_changed",
  "data": {
    "vm_id": 1,
    "vm_name": "web-server-01",
    "old_status": "stopped",
    "new_status": "running",
    "timestamp": "2024-01-01T00:00:00Z"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### VM Metrics Update
```json
{
  "type": "vm_metrics_update",
  "data": {
    "vm_id": 1,
    "vm_name": "web-server-01", 
    "metrics": {
      "cpu_usage_percent": 75.5,
      "memory_usage_percent": 60.2,
      "memory_used_mb": 1024,
      "network_rx_bytes": 1048576,
      "network_tx_bytes": 524288
    },
    "timestamp": "2024-01-01T00:00:00Z"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### Progress Update
```json
{
  "type": "progress",
  "data": {
    "operation_id": "vm-create-123",
    "operation_type": "vm_creation",
    "progress_percent": 50,
    "status": "in_progress",
    "message": "Creating virtual machine...",
    "timestamp": "2024-01-01T00:00:00Z"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### System Alert
```json
{
  "type": "alert",
  "data": {
    "alert_id": "alert-456",
    "alert_type": "resource_warning",
    "severity": "warning",
    "title": "High CPU Usage",
    "message": "CPU usage is above 90%",
    "entity_type": "vm",
    "entity_id": 1,
    "timestamp": "2024-01-01T00:00:00Z"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Frontend Usage

### Basic Connection
```typescript
import { WebSocketService } from './services/websocket/websocket.service';

constructor(private websocketService: WebSocketService) {}

ngOnInit() {
  // Connect with optional authentication
  this.websocketService.connect(authToken).subscribe(status => {
    console.log('Connection status:', status);
  });

  // Subscribe to VM status changes
  this.websocketService.getVMStatusEvents().subscribe(event => {
    console.log('VM status changed:', event);
    this.updateVMStatus(event.vm_id, event.new_status);
  });
}
```

### Event Subscriptions
```typescript
// Subscribe to specific events
const subscriptions = {
  events: [
    WebSocketEventType.VM_STATUS_CHANGED,
    WebSocketEventType.VM_METRICS_UPDATE,
    WebSocketEventType.PROGRESS,
    WebSocketEventType.ALERT
  ],
  vm_ids: [1, 2, 3],  // Optional: specific VMs
  server_ids: [1]     // Optional: specific servers
};

this.websocketService.connect(token, subscriptions).subscribe();
```

### Progress Tracking
```typescript
this.websocketService.getProgressEvents().subscribe(progress => {
  if (progress.operation_type === 'vm_creation') {
    this.updateProgressBar(progress.progress_percent);
    
    if (progress.progress_percent === 100) {
      this.showSuccessMessage('VM created successfully');
    }
  }
});
```

### Alert Handling
```typescript
this.websocketService.getAlertEvents().subscribe(alert => {
  this.showNotification({
    title: alert.title,
    message: alert.message,
    severity: alert.severity,
    timestamp: alert.timestamp
  });
});
```

### Connection Status Monitoring
```typescript
this.websocketService.connectionStatus$.subscribe(status => {
  this.isConnected = status === ConnectionStatus.CONNECTED;
  this.showConnectionStatus(status);
});

// Check message queue status
const queueStatus = this.websocketService.getQueueStatus();
console.log(`Queue size: ${queueStatus.size}, enabled: ${queueStatus.enabled}`);
```

## Backend Integration

### Broadcasting Events
```python
from websocket.events import event_broadcaster

# Broadcast VM status change
await event_broadcaster.broadcast_vm_status_change(
    vm_id=1,
    vm_name="web-server-01",
    old_status="stopped", 
    new_status="running"
)

# Broadcast progress update
await event_broadcaster.broadcast_progress_update(
    operation_id="vm-create-123",
    operation_type="vm_creation",
    progress_percent=75,
    status="in_progress",
    message="Installing operating system..."
)

# Broadcast system alert
await event_broadcaster.broadcast_alert(
    alert_id="alert-cpu-high",
    alert_type="resource_warning",
    severity="warning",
    title="High CPU Usage",
    message="CPU usage exceeded 90% for 5 minutes",
    entity_type="vm",
    entity_id=1
)
```

### Custom WebSocket Endpoints
```python
from fastapi import APIRouter, WebSocket
from websocket.manager import websocket_manager
from websocket.auth import get_websocket_user

router = APIRouter()

@router.websocket("/ws/custom")
async def custom_endpoint(websocket: WebSocket, token: str = None):
    user = await get_websocket_user(websocket, token)
    connection_id = await websocket_manager.connect(websocket, user)
    
    try:
        while True:
            message = await websocket.receive_text()
            # Handle custom messages
            await websocket_manager.handle_message(connection_id, json.loads(message))
    finally:
        websocket_manager.disconnect(connection_id)
```

## Configuration

### Frontend Configuration
```typescript
// Update WebSocket service configuration
this.websocketService.updateConfig({
  url: 'wss://your-server.com/ws',
  reconnectInterval: 3000,
  maxReconnectAttempts: 15,
  heartbeatInterval: 30000,
  messageQueueSize: 200,
  offlineQueueEnabled: true,
  debug: false
});
```

### Backend Configuration
The WebSocket system is automatically configured when the FastAPI app starts. No additional configuration is required.

## Error Handling

### Connection Errors
- Automatic reconnection with exponential backoff
- Message queuing during disconnections
- Graceful degradation for offline scenarios

### Authentication Errors
- WebSocket closes with appropriate error codes
- Frontend can retry with new authentication tokens

### Message Errors
- Invalid JSON messages are logged and ignored
- Malformed event data is handled gracefully

## Performance Considerations

### Connection Limits
- The system supports hundreds of concurrent connections
- Room-based broadcasting is efficient for large user bases
- Message queuing prevents memory leaks during disconnections

### Update Frequency
- VM/Server status: On change events only
- Metrics: Configurable interval (default 5 seconds)
- Progress: Every 1-2 seconds for active operations
- Alerts: Immediate delivery

### Resource Usage
- Memory usage scales with active connections
- CPU usage is minimal for message broadcasting
- Network usage depends on update frequency

## Testing

### Backend Tests
```bash
cd apps/vm-service
python -m pytest tests/test_websocket_manager.py -v
python -m pytest tests/test_websocket_events.py -v
```

### Frontend Tests
```bash
cd apps/rollo-site
npm test -- --testNamePattern="WebSocketService"
```

## Security

### Authentication
- JWT token validation for authenticated access
- Anonymous access limited to read-only operations
- Role-based permissions for admin features

### Rate Limiting
- Connection rate limiting per IP
- Message rate limiting per connection
- Automatic disconnection for abuse

### Data Validation
- All incoming messages are validated
- Sanitized error messages prevent information leakage
- CORS protection for cross-origin requests

## Monitoring

### WebSocket Statistics
Connect to `/ws/stats` with admin credentials to monitor:
- Active connection counts by room
- Message throughput statistics
- Error rates and connection failures
- Resource usage metrics

### Logging
- Connection events are logged with user information
- Error conditions are logged with context
- Debug mode provides detailed message tracing

## Troubleshooting

### Common Issues

#### Connection Fails
1. Check network connectivity
2. Verify WebSocket URL is correct
3. Ensure authentication token is valid
4. Check server logs for errors

#### Messages Not Received
1. Verify subscription to correct event types
2. Check connection status
3. Ensure user has proper permissions
4. Review message queue status

#### High Latency
1. Check network conditions
2. Verify server resource usage
3. Consider reducing update frequency
4. Monitor connection pool size

### Debug Mode
Enable debug logging in the frontend:
```typescript
this.websocketService.updateConfig({ debug: true });
```

This will log all WebSocket activity to the browser console.