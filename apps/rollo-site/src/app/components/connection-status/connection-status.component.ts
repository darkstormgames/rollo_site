import { Component, OnInit, OnDestroy } from '@angular/core';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { ConnectionStatus } from '../../models/websocket/websocket.model';
import { WebSocketService } from '../../services/websocket/websocket.service';

@Component({
  selector: 'app-connection-status',
  template: `
    <div class="connection-status" [ngClass]="statusClass">
      <span class="status-indicator"></span>
      <span class="status-text">{{ statusText }}</span>
      <span *ngIf="queueSize > 0" class="queue-info">({{ queueSize }} queued)</span>
    </div>
  `,
  styles: [`
    .connection-status {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 12px;
      border: 1px solid;
    }

    .status-indicator {
      width: 8px;
      height: 8px;
      border-radius: 50%;
    }

    .connected {
      background-color: #d4edda;
      border-color: #c3e6cb;
      color: #155724;
    }
    .connected .status-indicator {
      background-color: #28a745;
    }

    .connecting, .reconnecting {
      background-color: #fff3cd;
      border-color: #ffeaa7;
      color: #856404;
    }
    .connecting .status-indicator, .reconnecting .status-indicator {
      background-color: #ffc107;
      animation: pulse 1s infinite;
    }

    .disconnected, .error {
      background-color: #f8d7da;
      border-color: #f5c6cb;
      color: #721c24;
    }
    .disconnected .status-indicator, .error .status-indicator {
      background-color: #dc3545;
    }

    .queue-info {
      font-weight: 500;
      opacity: 0.8;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }
  `]
})
export class ConnectionStatusComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  
  connectionStatus = ConnectionStatus.DISCONNECTED;
  queueSize = 0;

  constructor(private websocketService: WebSocketService) {}

  ngOnInit(): void {
    // Subscribe to connection status
    this.websocketService.connectionStatus$
      .pipe(takeUntil(this.destroy$))
      .subscribe(status => {
        this.connectionStatus = status;
        this.updateQueueInfo();
      });

    // Update queue size periodically
    setInterval(() => {
      this.updateQueueInfo();
    }, 1000);
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private updateQueueInfo(): void {
    const queueStatus = this.websocketService.getQueueStatus();
    this.queueSize = queueStatus.size;
  }

  get statusClass(): string {
    return this.connectionStatus.toLowerCase();
  }

  get statusText(): string {
    switch (this.connectionStatus) {
      case ConnectionStatus.CONNECTED:
        return 'Connected';
      case ConnectionStatus.CONNECTING:
        return 'Connecting...';
      case ConnectionStatus.RECONNECTING:
        return 'Reconnecting...';
      case ConnectionStatus.DISCONNECTED:
        return 'Disconnected';
      case ConnectionStatus.ERROR:
        return 'Connection Error';
      default:
        return 'Unknown';
    }
  }
}