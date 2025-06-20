# VM Console VNC/SPICE Proxy Implementation

This document describes the implemented VM console access system using VNC/SPICE proxy functionality.

## Overview

The implementation provides secure, web-based console access to VMs through a VNC/SPICE proxy system with JWT-based authentication and session management.

## Architecture

### Backend Components

#### 1. Console Session Model (`models/console_session.py`)
- Manages console session lifecycle
- Stores session tokens, expiration times, and port mappings
- Supports both VNC and SPICE protocols
- Automatic session cleanup and expiration handling

#### 2. Console Service (`core/console_service.py`)
- Central service for console session management
- VNC/SPICE proxy implementation with WebSocket bridge
- Connection pooling and session management
- Real-time protocol conversion and data proxying

#### 3. Console API (`api/console.py`)
- RESTful endpoints for console access management:
  - `POST /api/vm/{vm_id}/console/request` - Request console access
  - `GET /api/vm/{vm_id}/console/status` - Check console availability
  - `DELETE /api/vm/{vm_id}/console/session` - Terminate session
  - `POST /api/vm/{vm_id}/console/extend` - Extend session

#### 4. WebSocket Proxy (`websocket/endpoints.py`)
- `WS /ws/console/vnc/{session_token}` - VNC proxy WebSocket endpoint
- Bidirectional data proxy between web client and VNC server
- Protocol message handling and conversion
- Connection lifecycle management

### Frontend Components

#### 1. Console Service (`services/console/console.service.ts`)
- Angular service for console session management
- WebSocket client for VNC protocol communication
- Connection status monitoring and error handling
- Message sending capabilities (keys, mouse, resize)

#### 2. Updated VM Console Component (`components/vm/vm-console/`)
- Enhanced console component with VNC display support
- noVNC integration for browser-based VNC client
- Console controls (connect/disconnect, special keys, fullscreen)
- Fallback to text console for legacy support

## Security Features

### Authentication & Authorization
- JWT token-based session authentication
- Time-limited sessions (15 minutes default, configurable)
- One session per VM per user (automatic cleanup of existing sessions)
- Session token validation on every WebSocket connection

### Session Management
- Secure session token generation using `secrets.token_urlsafe(32)`
- Automatic session expiration and cleanup
- Session extension capabilities for active users
- Connection audit logging

### Network Security
- WebSocket Secure (WSS) support ready
- IP address tracking for session monitoring
- Rate limiting and connection management
- User agent logging for security auditing

## Protocol Support

### VNC Protocol
- WebSocket to VNC bridge implementation
- Frame buffer updates and display synchronization
- Keyboard and mouse event forwarding
- Screen resize and resolution management
- Special key combinations (Ctrl+Alt+Del, etc.)

### SPICE Protocol (Ready for Implementation)
- Framework in place for SPICE protocol support
- Port allocation and session management
- Protocol switching capabilities

## Performance Optimizations

### Connection Management
- Connection pooling and reuse
- Asynchronous proxy operations
- Efficient WebSocket message handling
- Resource cleanup and memory management

### Data Handling
- Streaming protocol data
- Minimal latency proxy implementation
- Buffered I/O for optimal throughput
- Connection status monitoring

## API Usage Examples

### Request Console Access
```bash
curl -X POST http://localhost:8000/api/vm/1/console/request \
  -H "Content-Type: application/json" \
  -d '{"protocol": "vnc"}'
```

### Check Console Status
```bash
curl http://localhost:8000/api/vm/1/console/status
```

### Connect via WebSocket
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/console/vnc/SESSION_TOKEN');
```

## Frontend Integration

### Service Usage
```typescript
import { ConsoleService } from './services/console/console.service';

// Request console access
this.consoleService.requestAccess(vmId, 'vnc').subscribe(session => {
  // Connect to VNC
  this.consoleService.connect(session).subscribe(connection => {
    console.log('Console connected:', connection.connected);
  });
});

// Send special keys
this.consoleService.sendKeys(['Control_L', 'Alt_L', 'Delete']);

// Disconnect
this.consoleService.disconnect();
```

### Component Usage
```html
<app-vm-console [vm]="selectedVM"></app-vm-console>
```

## Configuration

### Backend Configuration
- Session timeout: 15 minutes (configurable via `expires_minutes`)
- VNC port range: 5900+ (based on VM ID)
- SPICE port range: 5930+ (based on VM ID)
- Maximum reconnection attempts: 3

### Frontend Configuration
- WebSocket reconnection: Automatic with exponential backoff
- Default VNC display size: 1024x768
- Console update interval: Real-time
- Error retry mechanism: Built-in

## Testing

### Backend Tests (`tests/test_console_service.py`)
- Console session creation and management
- Session expiration and cleanup
- VNC proxy functionality
- API endpoint testing
- Error handling scenarios

### Frontend Tests (`services/console/console.service.spec.ts`)
- HTTP API integration testing
- WebSocket connection management
- Service method functionality
- Error handling and edge cases

## Monitoring and Logging

### Audit Logging
- Console session creation/termination events
- Connection attempts and failures
- User access patterns and session duration
- Security-related events (failed authentication, etc.)

### Performance Monitoring
- WebSocket connection metrics
- Session count and resource usage
- Proxy throughput and latency
- Error rates and failure patterns

## Future Enhancements

### Planned Features
- File transfer capabilities
- Audio support for enhanced console experience
- Multi-monitor support
- Session recording and playback
- Advanced keyboard mapping
- Mobile device optimization

### Integration Opportunities
- Libvirt direct integration for real VNC servers
- QEMU Guest Agent integration
- Cloud-init integration for VM provisioning
- Load balancing for high-availability deployments

## Deployment Notes

### Dependencies
- Backend: FastAPI, WebSockets, SQLAlchemy, asyncio
- Frontend: Angular, noVNC, RxJS, WebSocket API
- Optional: libvirt-python for production VNC server integration

### Environment Setup
- WebSocket proxy requires persistent connections
- Database for session management
- Network access to VM console ports
- SSL/TLS certificates for secure WebSocket connections

This implementation provides a solid foundation for VM console access with room for future enhancements and production deployment.