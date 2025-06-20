import { Injectable } from '@angular/core';
import { Store } from '@ngrx/store';
import { WebSocketService } from '../websocket/websocket.service';
import { vmActions } from '../../store/vm/vm.actions';
import { AppState } from '../../store/app.state';
import { WebSocketEventType } from '../../models/websocket/websocket.model';

/**
 * Real-time Integration Service
 * 
 * Demonstrates how to connect WebSocket events to NgRx store updates
 * for real-time synchronization across the application.
 */
@Injectable({
  providedIn: 'root'
})
export class RealTimeIntegrationService {

  constructor(
    private store: Store<AppState>,
    private webSocketService: WebSocketService
  ) {
    this.initializeWebSocketIntegration();
  }

  private initializeWebSocketIntegration(): void {
    // Subscribe to WebSocket messages and dispatch appropriate store actions
    this.webSocketService.messages$.subscribe(message => {
      const { type, data } = message;
      
      switch (type) {
        case WebSocketEventType.VM_STATUS_CHANGED:
          this.store.dispatch(vmActions.vMStatusChanged({
            id: data.vm_id,
            status: data.new_status
          }));
          break;

        case WebSocketEventType.VM_CREATED:
          this.store.dispatch(vmActions.vMCreatedRealTime({
            vm: data.vm
          }));
          break;

        case WebSocketEventType.VM_DELETED:
          this.store.dispatch(vmActions.vMDeletedRealTime({
            id: data.vm_id
          }));
          break;

        case WebSocketEventType.VM_METRICS_UPDATE:
          this.store.dispatch(vmActions.vMMetricsUpdated({
            id: data.vm_id,
            metrics: data.metrics
          }));
          break;

        // Add server events when server state is fully implemented
        case WebSocketEventType.SERVER_STATUS_CHANGED:
          // TODO: Dispatch server status changed action
          console.log('Server status changed:', data);
          break;

        default:
          // Handle other message types or log unknown messages
          console.log('Unhandled WebSocket message:', message);
      }
    });
  }

  /**
   * Connect to WebSocket with authentication and subscription preferences
   */
  connect(authToken?: string): void {
    const subscriptions = {
      events: [
        WebSocketEventType.VM_STATUS_CHANGED,
        WebSocketEventType.VM_CREATED,
        WebSocketEventType.VM_DELETED,
        WebSocketEventType.VM_METRICS_UPDATE,
        WebSocketEventType.SERVER_STATUS_CHANGED,
        WebSocketEventType.SERVER_REGISTERED,
        WebSocketEventType.SERVER_REMOVED
      ]
    };

    this.webSocketService.connect(authToken, subscriptions).subscribe(
      status => {
        console.log('WebSocket connection status:', status);
      },
      error => {
        console.error('WebSocket connection error:', error);
      }
    );
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    this.webSocketService.disconnect();
  }
}