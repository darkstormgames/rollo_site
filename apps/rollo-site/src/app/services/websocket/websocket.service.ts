import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, Subject, timer, NEVER } from 'rxjs';
import { switchMap, retryWhen, delay, tap, takeUntil, filter } from 'rxjs/operators';
import {
  WebSocketMessage,
  WebSocketEventType,
  ConnectionStatus,
  WebSocketConfig,
  SubscriptionOptions,
  VMStatusEvent,
  VMCreatedEvent,
  VMDeletedEvent,
  VMMetricsEvent,
  ServerStatusEvent,
  ServerRegisteredEvent,
  ServerRemovedEvent,
  ServerMetricsEvent,
  ProgressEvent,
  AlertEvent,
  ConsoleEvent,
  WebSocketStats
} from '../../models/websocket/websocket.model';

@Injectable({
  providedIn: 'root'
})
export class WebSocketService {
  private socket: WebSocket | null = null;
  private config: WebSocketConfig = {
    url: 'ws://localhost:8000/ws',
    reconnectInterval: 5000,
    maxReconnectAttempts: 10,
    heartbeatInterval: 30000,
    debug: false,
    messageQueueSize: 100,
    offlineQueueEnabled: true
  };

  private connectionStatusSubject = new BehaviorSubject<ConnectionStatus>(ConnectionStatus.DISCONNECTED);
  private messagesSubject = new Subject<WebSocketMessage>();
  private destroySubject = new Subject<void>();

  private reconnectAttempts = 0;
  private heartbeatTimer: any = null;
  private messageQueue: WebSocketMessage[] = [];

  public connectionStatus$ = this.connectionStatusSubject.asObservable();
  public messages$ = this.messagesSubject.asObservable();

  constructor() {}

  /**
   * Connect to WebSocket server
   */
  connect(token?: string, subscriptions?: SubscriptionOptions): Observable<ConnectionStatus> {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      return this.connectionStatus$;
    }

    this.disconnect();
    this.connectionStatusSubject.next(ConnectionStatus.CONNECTING);

    const url = token 
      ? `${this.config.url}?token=${token}`
      : this.config.url;

    return new Observable<ConnectionStatus>(observer => {
      try {
        this.socket = new WebSocket(url);

        this.socket.onopen = () => {
          this.log('WebSocket connected');
          this.connectionStatusSubject.next(ConnectionStatus.CONNECTED);
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          
          // Process queued messages
          this.processMessageQueue();
          
          // Subscribe to events if provided
          if (subscriptions) {
            this.subscribe(subscriptions);
          }
          
          observer.next(ConnectionStatus.CONNECTED);
        };

        this.socket.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.log('Received message:', message);
            
            // Handle special message types
            if (message.type === WebSocketEventType.PONG) {
              this.log('Received pong response');
              return;
            }
            
            this.messagesSubject.next(message);
          } catch (error) {
            this.log('Error parsing message:', error);
          }
        };

        this.socket.onclose = (event) => {
          this.log('WebSocket closed:', event.code, event.reason);
          this.connectionStatusSubject.next(ConnectionStatus.DISCONNECTED);
          this.stopHeartbeat();
          
          if (!event.wasClean && this.reconnectAttempts < this.config.maxReconnectAttempts) {
            this.scheduleReconnect(token, subscriptions);
          }
          
          observer.next(ConnectionStatus.DISCONNECTED);
        };

        this.socket.onerror = (error) => {
          this.log('WebSocket error:', error);
          this.connectionStatusSubject.next(ConnectionStatus.ERROR);
          observer.next(ConnectionStatus.ERROR);
        };

      } catch (error) {
        this.log('Failed to create WebSocket:', error);
        this.connectionStatusSubject.next(ConnectionStatus.ERROR);
        observer.next(ConnectionStatus.ERROR);
      }
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.stopHeartbeat();
    
    if (this.socket) {
      this.socket.close(1000, 'Manual disconnect');
      this.socket = null;
    }
    
    this.connectionStatusSubject.next(ConnectionStatus.DISCONNECTED);
  }

  /**
   * Subscribe to specific events
   */
  subscribe(options: SubscriptionOptions): void {
    const message = {
      type: 'subscribe',
      data: options
    };
    
    if (this.sendMessage(message)) {
      this.log('Subscribed to events:', options);
    } else {
      this.log('Subscription queued:', options);
    }
  }

  /**
   * Unsubscribe from specific events
   */
  unsubscribe(options: SubscriptionOptions): void {
    const message = {
      type: 'unsubscribe',
      data: options
    };
    
    if (this.sendMessage(message)) {
      this.log('Unsubscribed from events:', options);
    } else {
      this.log('Unsubscription queued:', options);
    }
  }

  /**
   * Get messages filtered by event type
   */
  getMessagesByType<T>(eventType: WebSocketEventType): Observable<T> {
    return this.messages$.pipe(
      filter(message => message.type === eventType),
      tap(message => this.log(`Filtered message for ${eventType}:`, message)),
      switchMap(message => [message.data as T])
    );
  }

  /**
   * Get VM status change events
   */
  getVMStatusEvents(): Observable<VMStatusEvent> {
    return this.getMessagesByType<VMStatusEvent>(WebSocketEventType.VM_STATUS_CHANGED);
  }

  /**
   * Get VM creation events
   */
  getVMCreatedEvents(): Observable<VMCreatedEvent> {
    return this.getMessagesByType<VMCreatedEvent>(WebSocketEventType.VM_CREATED);
  }

  /**
   * Get VM deletion events
   */
  getVMDeletedEvents(): Observable<VMDeletedEvent> {
    return this.getMessagesByType<VMDeletedEvent>(WebSocketEventType.VM_DELETED);
  }

  /**
   * Get VM metrics events
   */
  getVMMetricsEvents(): Observable<VMMetricsEvent> {
    return this.getMessagesByType<VMMetricsEvent>(WebSocketEventType.VM_METRICS_UPDATE);
  }

  /**
   * Get server status change events
   */
  getServerStatusEvents(): Observable<ServerStatusEvent> {
    return this.getMessagesByType<ServerStatusEvent>(WebSocketEventType.SERVER_STATUS_CHANGED);
  }

  /**
   * Get server registration events
   */
  getServerRegisteredEvents(): Observable<ServerRegisteredEvent> {
    return this.getMessagesByType<ServerRegisteredEvent>(WebSocketEventType.SERVER_REGISTERED);
  }

  /**
   * Get server removal events
   */
  getServerRemovedEvents(): Observable<ServerRemovedEvent> {
    return this.getMessagesByType<ServerRemovedEvent>(WebSocketEventType.SERVER_REMOVED);
  }

  /**
   * Get server metrics events
   */
  getServerMetricsEvents(): Observable<ServerMetricsEvent> {
    return this.getMessagesByType<ServerMetricsEvent>(WebSocketEventType.SERVER_METRICS_UPDATE);
  }

  /**
   * Get progress update events
   */
  getProgressEvents(): Observable<ProgressEvent> {
    return this.getMessagesByType<ProgressEvent>(WebSocketEventType.PROGRESS);
  }

  /**
   * Get alert events
   */
  getAlertEvents(): Observable<AlertEvent> {
    return this.getMessagesByType<AlertEvent>(WebSocketEventType.ALERT);
  }

  /**
   * Get console output events
   */
  getConsoleEvents(): Observable<ConsoleEvent> {
    return this.getMessagesByType<ConsoleEvent>(WebSocketEventType.CONSOLE_OUTPUT);
  }

  /**
   * Get WebSocket statistics events
   */
  getStatsEvents(): Observable<WebSocketStats> {
    return this.getMessagesByType<WebSocketStats>(WebSocketEventType.WEBSOCKET_STATS);
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.socket !== null && this.socket.readyState === WebSocket.OPEN;
  }

  /**
   * Update WebSocket configuration
   */
  updateConfig(config: Partial<WebSocketConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * Send message to server with queuing support
   */
  sendMessage(message: any): boolean {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      try {
        this.socket.send(JSON.stringify(message));
        this.log('Sent message:', message);
        return true;
      } catch (error) {
        this.log('Failed to send message:', error);
        this.queueMessage(message);
        return false;
      }
    } else {
      this.queueMessage(message);
      return false;
    }
  }

  /**
   * Queue message for later delivery when connection is restored
   */
  private queueMessage(message: any): void {
    if (!this.config.offlineQueueEnabled) {
      return;
    }

    // Add timestamp to message
    const queuedMessage: WebSocketMessage = {
      ...message,
      timestamp: new Date().toISOString()
    };

    this.messageQueue.push(queuedMessage);
    
    // Limit queue size
    if (this.messageQueue.length > (this.config.messageQueueSize || 100)) {
      this.messageQueue.shift(); // Remove oldest message
    }
    
    this.log('Message queued for delivery:', queuedMessage);
  }

  /**
   * Process queued messages when connection is restored
   */
  private processMessageQueue(): void {
    if (this.messageQueue.length === 0) {
      return;
    }

    this.log(`Processing ${this.messageQueue.length} queued messages`);
    
    const messages = [...this.messageQueue];
    this.messageQueue = [];
    
    messages.forEach(message => {
      this.sendMessage(message);
    });
  }

  /**
   * Get message queue status
   */
  getQueueStatus(): { size: number; enabled: boolean } {
    return {
      size: this.messageQueue.length,
      enabled: this.config.offlineQueueEnabled || false
    };
  }

  /**
   * Clear message queue
   */
  clearQueue(): void {
    const size = this.messageQueue.length;
    this.messageQueue = [];
    this.log(`Cleared ${size} queued messages`);
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(token?: string, subscriptions?: SubscriptionOptions): void {
    this.reconnectAttempts++;
    this.connectionStatusSubject.next(ConnectionStatus.RECONNECTING);
    
    this.log(`Scheduling reconnect attempt ${this.reconnectAttempts}/${this.config.maxReconnectAttempts}`);
    
    timer(this.config.reconnectInterval)
      .pipe(takeUntil(this.destroySubject))
      .subscribe(() => {
        this.connect(token, subscriptions).subscribe();
      });
  }

  /**
   * Start heartbeat mechanism
   */
  private startHeartbeat(): void {
    this.stopHeartbeat();
    
    this.heartbeatTimer = setInterval(() => {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        const heartbeat = {
          type: 'ping',
          timestamp: new Date().toISOString()
        };
        this.sendMessage(heartbeat);
      }
    }, this.config.heartbeatInterval);
  }

  /**
   * Stop heartbeat mechanism
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  /**
   * Log debug messages
   */
  private log(...args: any[]): void {
    if (this.config.debug) {
      console.log('[WebSocketService]', ...args);
    }
  }

  /**
   * Cleanup on service destruction
   */
  ngOnDestroy(): void {
    this.destroySubject.next();
    this.destroySubject.complete();
    this.disconnect();
  }
}