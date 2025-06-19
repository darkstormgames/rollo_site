import { Component, OnInit, OnDestroy } from '@angular/core';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { 
  WebSocketService 
} from '../../services/websocket/websocket.service';
import {
  WebSocketEventType,
  SubscriptionOptions,
  VMStatusEvent,
  VMMetricsEvent,
  ServerStatusEvent,
  ServerMetricsEvent,
  ProgressEvent,
  AlertEvent,
  ConnectionStatus
} from '../../models/websocket/websocket.model';

interface VMInfo {
  id: number;
  name: string;
  status: string;
  metrics?: any;
}

interface ServerInfo {
  id: number;
  hostname: string;
  status: string;
  metrics?: any;
}

@Component({
  selector: 'app-realtime-monitor',
  template: `
    <div class="realtime-monitor">
      <header class="monitor-header">
        <h2>Real-Time System Monitor</h2>
        <app-connection-status></app-connection-status>
        <div class="controls">
          <button *ngIf="!isConnected" (click)="connect()" class="btn btn-primary">
            Connect
          </button>
          <button *ngIf="isConnected" (click)="disconnect()" class="btn btn-secondary">
            Disconnect
          </button>
        </div>
      </header>

      <div class="monitor-content" *ngIf="isConnected">
        <!-- Progress Updates -->
        <div class="progress-section" *ngIf="activeOperations.length > 0">
          <h3>Active Operations</h3>
          <div class="progress-list">
            <div *ngFor="let progress of activeOperations" class="progress-item">
              <div class="progress-header">
                <span>{{ progress.operation_type }}</span>
                <span class="progress-percent">{{ progress.progress_percent }}%</span>
              </div>
              <div class="progress-bar">
                <div class="progress-fill" [style.width.%]="progress.progress_percent"></div>
              </div>
              <div class="progress-message" *ngIf="progress.message">{{ progress.message }}</div>
            </div>
          </div>
        </div>

        <!-- Alerts -->
        <div class="alerts-section" *ngIf="alerts.length > 0">
          <h3>Recent Alerts</h3>
          <div class="alerts-list">
            <div *ngFor="let alert of alerts" class="alert-item" [ngClass]="'alert-' + alert.severity">
              <div class="alert-header">
                <span class="alert-title">{{ alert.title }}</span>
                <span class="alert-time">{{ formatTime(alert.timestamp) }}</span>
              </div>
              <div class="alert-message">{{ alert.message }}</div>
            </div>
          </div>
        </div>

        <!-- VMs Status -->
        <div class="vms-section">
          <h3>Virtual Machines</h3>
          <div class="vm-grid">
            <div *ngFor="let vm of vms" class="vm-card">
              <div class="vm-header">
                <span class="vm-name">{{ vm.name }}</span>
                <span class="vm-status" [ngClass]="'status-' + vm.status">{{ vm.status }}</span>
              </div>
              <div class="vm-metrics" *ngIf="vm.metrics">
                <div class="metric">
                  <span>CPU:</span>
                  <span>{{ vm.metrics.cpu_usage_percent || 0 }}%</span>
                </div>
                <div class="metric">
                  <span>Memory:</span>
                  <span>{{ vm.metrics.memory_usage_percent || 0 }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Servers Status -->
        <div class="servers-section">
          <h3>Servers</h3>
          <div class="server-grid">
            <div *ngFor="let server of servers" class="server-card">
              <div class="server-header">
                <span class="server-name">{{ server.hostname }}</span>
                <span class="server-status" [ngClass]="'status-' + server.status">{{ server.status }}</span>
              </div>
              <div class="server-metrics" *ngIf="server.metrics">
                <div class="metric">
                  <span>CPU:</span>
                  <span>{{ server.metrics.cpu_usage_percent || 0 }}%</span>
                </div>
                <div class="metric">
                  <span>Memory:</span>
                  <span>{{ server.metrics.memory_usage_percent || 0 }}%</span>
                </div>
                <div class="metric">
                  <span>Load:</span>
                  <span>{{ server.metrics.load_average || 0 }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Event Log -->
        <div class="events-section">
          <h3>Event Log</h3>
          <div class="events-list">
            <div *ngFor="let event of recentEvents" class="event-item">
              <span class="event-time">{{ formatTime(event.timestamp) }}</span>
              <span class="event-type">{{ event.type }}</span>
              <span class="event-description">{{ formatEventDescription(event) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .realtime-monitor {
      padding: 20px;
    }

    .monitor-header {
      display: flex;
      align-items: center;
      gap: 20px;
      margin-bottom: 20px;
      padding-bottom: 10px;
      border-bottom: 1px solid #ddd;
    }

    .monitor-header h2 {
      margin: 0;
      flex: 1;
    }

    .btn {
      padding: 8px 16px;
      border: none;
      border-radius: 4px;
      cursor: pointer;
    }

    .btn-primary {
      background-color: #007bff;
      color: white;
    }

    .btn-secondary {
      background-color: #6c757d;
      color: white;
    }

    .progress-section, .alerts-section, .vms-section, .servers-section, .events-section {
      margin-bottom: 30px;
    }

    .progress-item {
      border: 1px solid #ddd;
      padding: 15px;
      margin-bottom: 10px;
      border-radius: 4px;
    }

    .progress-header {
      display: flex;
      justify-content: space-between;
      margin-bottom: 10px;
    }

    .progress-bar {
      height: 20px;
      background-color: #f8f9fa;
      border-radius: 10px;
      overflow: hidden;
    }

    .progress-fill {
      height: 100%;
      background-color: #007bff;
      transition: width 0.3s ease;
    }

    .alert-item {
      padding: 10px;
      margin-bottom: 10px;
      border-radius: 4px;
      border-left: 4px solid;
    }

    .alert-info { border-left-color: #17a2b8; background-color: #d1ecf1; }
    .alert-warning { border-left-color: #ffc107; background-color: #fff3cd; }
    .alert-error { border-left-color: #dc3545; background-color: #f8d7da; }
    .alert-critical { border-left-color: #721c24; background-color: #f5c6cb; }

    .vm-grid, .server-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 15px;
    }

    .vm-card, .server-card {
      border: 1px solid #ddd;
      border-radius: 4px;
      padding: 15px;
    }

    .vm-header, .server-header {
      display: flex;
      justify-content: space-between;
      margin-bottom: 10px;
    }

    .vm-name, .server-name {
      font-weight: bold;
    }

    .status-running { color: #28a745; }
    .status-stopped { color: #dc3545; }
    .status-online { color: #28a745; }
    .status-offline { color: #dc3545; }
    .status-maintenance { color: #ffc107; }

    .metric {
      display: flex;
      justify-content: space-between;
      margin-bottom: 5px;
    }

    .events-list {
      max-height: 300px;
      overflow-y: auto;
      border: 1px solid #ddd;
      border-radius: 4px;
    }

    .event-item {
      display: grid;
      grid-template-columns: 120px 150px 1fr;
      gap: 15px;
      padding: 8px 15px;
      border-bottom: 1px solid #eee;
      font-size: 14px;
    }

    .event-time {
      color: #666;
    }

    .event-type {
      font-weight: 500;
      color: #007bff;
    }
  `]
})
export class RealtimeMonitorComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  
  isConnected = false;
  vms: VMInfo[] = [];
  servers: ServerInfo[] = [];
  activeOperations: ProgressEvent[] = [];
  alerts: AlertEvent[] = [];
  recentEvents: any[] = [];

  constructor(private websocketService: WebSocketService) {}

  ngOnInit(): void {
    // Monitor connection status
    this.websocketService.connectionStatus$
      .pipe(takeUntil(this.destroy$))
      .subscribe(status => {
        this.isConnected = status === ConnectionStatus.CONNECTED;
      });

    // Subscribe to VM status events
    this.websocketService.getVMStatusEvents()
      .pipe(takeUntil(this.destroy$))
      .subscribe(event => {
        this.handleVMStatusChange(event);
        this.addToEventLog(event, 'VM Status Change');
      });

    // Subscribe to VM metrics events
    this.websocketService.getVMMetricsEvents()
      .pipe(takeUntil(this.destroy$))
      .subscribe(event => {
        this.handleVMMetrics(event);
      });

    // Subscribe to server status events
    this.websocketService.getServerStatusEvents()
      .pipe(takeUntil(this.destroy$))
      .subscribe(event => {
        this.handleServerStatusChange(event);
        this.addToEventLog(event, 'Server Status Change');
      });

    // Subscribe to server metrics events
    this.websocketService.getServerMetricsEvents()
      .pipe(takeUntil(this.destroy$))
      .subscribe(event => {
        this.handleServerMetrics(event);
      });

    // Subscribe to progress events
    this.websocketService.getProgressEvents()
      .pipe(takeUntil(this.destroy$))
      .subscribe(event => {
        this.handleProgress(event);
      });

    // Subscribe to alert events
    this.websocketService.getAlertEvents()
      .pipe(takeUntil(this.destroy$))
      .subscribe(event => {
        this.handleAlert(event);
        this.addToEventLog(event, 'Alert');
      });

    // Initialize sample data
    this.initializeSampleData();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  connect(): void {
    const subscriptions: SubscriptionOptions = {
      events: [
        WebSocketEventType.VM_STATUS_CHANGED,
        WebSocketEventType.VM_METRICS_UPDATE,
        WebSocketEventType.SERVER_STATUS_CHANGED,
        WebSocketEventType.SERVER_METRICS_UPDATE,
        WebSocketEventType.PROGRESS,
        WebSocketEventType.ALERT
      ]
    };

    this.websocketService.connect(undefined, subscriptions).subscribe();
  }

  disconnect(): void {
    this.websocketService.disconnect();
  }

  private handleVMStatusChange(event: VMStatusEvent): void {
    let vm = this.vms.find(v => v.id === event.vm_id);
    if (!vm) {
      vm = {
        id: event.vm_id,
        name: event.vm_name,
        status: event.new_status
      };
      this.vms.push(vm);
    } else {
      vm.status = event.new_status;
    }
  }

  private handleVMMetrics(event: VMMetricsEvent): void {
    const vm = this.vms.find(v => v.id === event.vm_id);
    if (vm) {
      vm.metrics = event.metrics;
    }
  }

  private handleServerStatusChange(event: ServerStatusEvent): void {
    let server = this.servers.find(s => s.id === event.server_id);
    if (!server) {
      server = {
        id: event.server_id,
        hostname: event.hostname,
        status: event.new_status
      };
      this.servers.push(server);
    } else {
      server.status = event.new_status;
    }
  }

  private handleServerMetrics(event: ServerMetricsEvent): void {
    const server = this.servers.find(s => s.id === event.server_id);
    if (server) {
      server.metrics = event.metrics;
    }
  }

  private handleProgress(event: ProgressEvent): void {
    const existingIndex = this.activeOperations.findIndex(
      op => op.operation_id === event.operation_id
    );

    if (existingIndex >= 0) {
      if (event.progress_percent >= 100 || event.status === 'completed' || event.status === 'failed') {
        // Remove completed operations
        this.activeOperations.splice(existingIndex, 1);
      } else {
        // Update existing operation
        this.activeOperations[existingIndex] = event;
      }
    } else if (event.progress_percent < 100) {
      // Add new operation
      this.activeOperations.push(event);
    }
  }

  private handleAlert(event: AlertEvent): void {
    this.alerts.unshift(event);
    
    // Keep only last 10 alerts
    if (this.alerts.length > 10) {
      this.alerts = this.alerts.slice(0, 10);
    }
  }

  private addToEventLog(event: any, type: string): void {
    this.recentEvents.unshift({
      ...event,
      type,
      timestamp: event.timestamp || new Date().toISOString()
    });

    // Keep only last 50 events
    if (this.recentEvents.length > 50) {
      this.recentEvents = this.recentEvents.slice(0, 50);
    }
  }

  formatTime(timestamp: string): string {
    return new Date(timestamp).toLocaleTimeString();
  }

  formatEventDescription(event: any): string {
    switch (event.type) {
      case 'VM Status Change':
        return `${event.vm_name}: ${event.old_status} → ${event.new_status}`;
      case 'Server Status Change':
        return `${event.hostname}: ${event.old_status} → ${event.new_status}`;
      case 'Alert':
        return `${event.severity.toUpperCase()}: ${event.message}`;
      default:
        return JSON.stringify(event);
    }
  }

  private initializeSampleData(): void {
    // Initialize with some sample data for demonstration
    this.vms = [
      { id: 1, name: 'web-server-01', status: 'running' },
      { id: 2, name: 'db-server-01', status: 'running' },
      { id: 3, name: 'cache-server-01', status: 'stopped' }
    ];

    this.servers = [
      { id: 1, hostname: 'host-01.example.com', status: 'online' },
      { id: 2, hostname: 'host-02.example.com', status: 'online' },
      { id: 3, hostname: 'host-03.example.com', status: 'maintenance' }
    ];
  }
}