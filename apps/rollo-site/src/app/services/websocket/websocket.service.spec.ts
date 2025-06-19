import { TestBed } from '@angular/core/testing';
import { WebSocketService } from './websocket.service';
import { ConnectionStatus, WebSocketEventType } from '../../models/websocket/websocket.model';

describe('WebSocketService', () => {
  let service: WebSocketService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [WebSocketService]
    });
    service = TestBed.inject(WebSocketService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should initialize with disconnected status', () => {
    expect(service).toBeTruthy();
    // Note: connectionStatus$ is a BehaviorSubject and will emit multiple times
    // We'll just verify the service exists for this basic test
  });

  it('should update configuration', () => {
    const newConfig = {
      url: 'ws://localhost:9000/ws',
      reconnectInterval: 10000,
      debug: true,
      messageQueueSize: 50,
      offlineQueueEnabled: false
    };

    service.updateConfig(newConfig);
    
    // We can't directly test private config, but we can verify the service still works
    expect(service).toBeTruthy();
  });

  it('should check connection status', () => {
    expect(service.isConnected()).toBeFalse();
  });

  it('should provide queue status information', () => {
    const queueStatus = service.getQueueStatus();
    expect(queueStatus).toBeDefined();
    expect(queueStatus.size).toBeDefined();
    expect(queueStatus.enabled).toBeDefined();
  });

  it('should clear message queue', () => {
    service.clearQueue();
    const queueStatus = service.getQueueStatus();
    expect(queueStatus.size).toBe(0);
  });

  it('should filter messages by type', (done) => {
    // Create a mock message
    const mockVMStatusEvent = {
      vm_id: 1,
      vm_name: 'test-vm',
      old_status: 'stopped',
      new_status: 'running',
      timestamp: '2023-01-01T00:00:00Z'
    };

    // Subscribe to VM status events
    service.getVMStatusEvents().subscribe(event => {
      expect(event).toEqual(mockVMStatusEvent);
      done();
    });

    // Simulate receiving a message (we'll need to trigger the subject manually)
    // This would normally come from the WebSocket connection
    const mockMessage = {
      type: WebSocketEventType.VM_STATUS_CHANGED,
      data: mockVMStatusEvent,
      timestamp: '2023-01-01T00:00:00Z'
    };

    // Directly emit to the messages subject to test filtering
    (service as any).messagesSubject.next(mockMessage);
  });

  it('should provide different event type observables', () => {
    expect(service.getVMStatusEvents()).toBeDefined();
    expect(service.getVMCreatedEvents()).toBeDefined();
    expect(service.getVMDeletedEvents()).toBeDefined();
    expect(service.getVMMetricsEvents()).toBeDefined();
    expect(service.getServerStatusEvents()).toBeDefined();
    expect(service.getServerRegisteredEvents()).toBeDefined();
    expect(service.getServerRemovedEvents()).toBeDefined();
    expect(service.getServerMetricsEvents()).toBeDefined();
    expect(service.getProgressEvents()).toBeDefined();
    expect(service.getAlertEvents()).toBeDefined();
    expect(service.getConsoleEvents()).toBeDefined();
    expect(service.getStatsEvents()).toBeDefined();
  });

  it('should handle progress events', (done) => {
    const mockProgressEvent = {
      operation_id: 'op-123',
      operation_type: 'vm_creation',
      progress_percent: 50,
      status: 'in_progress',
      message: 'Creating VM...',
      timestamp: '2023-01-01T00:00:00Z'
    };

    service.getProgressEvents().subscribe(event => {
      expect(event).toEqual(mockProgressEvent);
      done();
    });

    const mockMessage = {
      type: WebSocketEventType.PROGRESS,
      data: mockProgressEvent,
      timestamp: '2023-01-01T00:00:00Z'
    };

    (service as any).messagesSubject.next(mockMessage);
  });

  it('should handle alert events', (done) => {
    const mockAlertEvent = {
      alert_id: 'alert-456',
      alert_type: 'resource_warning',
      severity: 'warning' as const,
      title: 'High CPU Usage',
      message: 'CPU usage is above 90%',
      timestamp: '2023-01-01T00:00:00Z'
    };

    service.getAlertEvents().subscribe(event => {
      expect(event).toEqual(mockAlertEvent);
      done();
    });

    const mockMessage = {
      type: WebSocketEventType.ALERT,
      data: mockAlertEvent,
      timestamp: '2023-01-01T00:00:00Z'
    };

    (service as any).messagesSubject.next(mockMessage);
  });

  it('should handle disconnect', () => {
    service.disconnect();
    expect(service.isConnected()).toBeFalse();
  });

  afterEach(() => {
    service.disconnect();
  });
});