import { Component, Input, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { VM } from '../../../models/vm/vm.model';
import { LoadingSpinnerComponent } from '../../shared/loading-spinner/loading-spinner.component';

@Component({
  selector: 'app-vm-console',
  standalone: true,
  imports: [CommonModule, FormsModule, LoadingSpinnerComponent],
  template: `
    <div class="vm-console" [attr.aria-label]="'Console for ' + vm?.name">
      <div class="console-header">
        <h3>VM Console - {{ vm?.name }}</h3>
        <div class="console-controls">
          <button 
            class="btn btn-secondary"
            (click)="toggleFullscreen()"
            [attr.aria-label]="isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'"
            title="Toggle Fullscreen">
            <span [attr.aria-hidden]="true">{{ isFullscreen ? '⤢' : '⤡' }}</span>
          </button>
          <button 
            class="btn btn-secondary"
            (click)="reconnect()"
            [disabled]="isConnecting"
            aria-label="Reconnect to console"
            title="Reconnect">
            <span [attr.aria-hidden]="true">🔄</span>
          </button>
          <button 
            class="btn btn-danger"
            (click)="disconnect()"
            [disabled]="!isConnected"
            aria-label="Disconnect from console"
            title="Disconnect">
            <span [attr.aria-hidden]="true">⏹</span>
          </button>
        </div>
      </div>

      <div class="console-content" [class.fullscreen]="isFullscreen">
        <div *ngIf="isConnecting" class="console-loading">
          <app-loading-spinner size="medium"></app-loading-spinner>
          <p>Connecting to console...</p>
        </div>

        <div *ngIf="error" class="console-error" role="alert">
          <p>{{ error }}</p>
          <button class="btn btn-primary" (click)="reconnect()">
            Try Again
          </button>
        </div>

        <div 
          #consoleOutput 
          class="console-output"
          [class.hidden]="isConnecting || error"
          role="log"
          aria-live="polite"
          aria-label="Console output"
          tabindex="0">
          <div *ngFor="let line of consoleLines; trackBy: trackByIndex" class="console-line">
            {{ line }}
          </div>
        </div>

        <div class="console-input" [class.hidden]="isConnecting || error || !isConnected">
          <input 
            #consoleInput
            type="text"
            class="console-command-input"
            [(ngModel)]="currentCommand"
            (keydown)="onKeyDown($event)"
            placeholder="Type commands here..."
            [disabled]="!isConnected"
            aria-label="Console command input"
            autocomplete="off">
        </div>
      </div>

      <div class="console-status" role="status" aria-live="polite">
        <span class="status-indicator" [class.connected]="isConnected" [class.connecting]="isConnecting">
          {{ getStatusText() }}
        </span>
        <span class="connection-info">
          {{ vm?.name }} - {{ vm?.status }}
        </span>
      </div>
    </div>
  `,
  styleUrls: ['./vm-console.component.css']
})
export class VmConsoleComponent implements OnInit, OnDestroy, AfterViewInit {
  @Input() vm: VM | null = null;
  @ViewChild('consoleOutput') consoleOutput!: ElementRef;
  @ViewChild('consoleInput') consoleInput!: ElementRef;

  consoleLines: string[] = [];
  currentCommand = '';
  isConnected = false;
  isConnecting = false;
  isFullscreen = false;
  error: string | null = null;

  private websocket: WebSocket | null = null;
  private commandHistory: string[] = [];
  private historyIndex = -1;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 3;

  ngOnInit() {
    if (this.vm) {
      this.connect();
    }
  }

  ngAfterViewInit() {
    // Focus the console input when component loads
    setTimeout(() => {
      if (this.consoleInput?.nativeElement) {
        this.consoleInput.nativeElement.focus();
      }
    }, 100);
  }

  ngOnDestroy() {
    this.disconnect();
  }

  connect() {
    if (!this.vm || this.isConnecting) return;

    this.isConnecting = true;
    this.error = null;
    this.addConsoleLine('Connecting to VM console...');

    try {
      // In a real implementation, this would connect to the actual VM console WebSocket
      // For now, we'll simulate a connection
      this.simulateConnection();
    } catch (error) {
      this.handleConnectionError('Failed to connect to console');
    }
  }

  private simulateConnection() {
    // Simulate connection delay
    setTimeout(() => {
      this.isConnecting = false;
      this.isConnected = true;
      this.reconnectAttempts = 0;
      this.addConsoleLine('Connected to VM console');
      this.addConsoleLine(`${this.vm?.name} login: `);
      
      if (this.consoleInput?.nativeElement) {
        this.consoleInput.nativeElement.focus();
      }
    }, 2000);
  }

  disconnect() {
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }
    this.isConnected = false;
    this.isConnecting = false;
    this.addConsoleLine('Disconnected from console');
  }

  reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      this.disconnect();
      setTimeout(() => this.connect(), 1000);
    } else {
      this.error = 'Maximum reconnection attempts exceeded. Please try again later.';
    }
  }

  onKeyDown(event: KeyboardEvent) {
    switch (event.key) {
      case 'Enter':
        this.sendCommand();
        break;
      case 'ArrowUp':
        event.preventDefault();
        this.navigateHistory(-1);
        break;
      case 'ArrowDown':
        event.preventDefault();
        this.navigateHistory(1);
        break;
      case 'Tab':
        event.preventDefault();
        // Could implement command completion here
        break;
    }
  }

  sendCommand() {
    if (!this.currentCommand.trim() || !this.isConnected) return;

    const command = this.currentCommand.trim();
    this.addConsoleLine(`$ ${command}`);
    
    // Add to command history
    this.commandHistory.unshift(command);
    if (this.commandHistory.length > 100) {
      this.commandHistory.pop();
    }
    this.historyIndex = -1;

    // Simulate command response
    this.simulateCommandResponse(command);
    
    this.currentCommand = '';
  }

  private simulateCommandResponse(command: string) {
    setTimeout(() => {
      switch (command.toLowerCase()) {
        case 'ls':
          this.addConsoleLine('bin  boot  dev  etc  home  lib  media  mnt  opt  proc  root  run  sbin  srv  sys  tmp  usr  var');
          break;
        case 'pwd':
          this.addConsoleLine('/home/user');
          break;
        case 'whoami':
          this.addConsoleLine('user');
          break;
        case 'clear':
          this.consoleLines = [];
          break;
        case 'help':
          this.addConsoleLine('Available commands: ls, pwd, whoami, clear, help, exit');
          break;
        case 'exit':
          this.addConsoleLine('logout');
          this.disconnect();
          break;
        default:
          if (command.startsWith('echo ')) {
            this.addConsoleLine(command.substring(5));
          } else {
            this.addConsoleLine(`bash: ${command}: command not found`);
          }
      }
      this.addConsoleLine('$ ');
    }, 500);
  }

  private navigateHistory(direction: number) {
    if (this.commandHistory.length === 0) return;

    this.historyIndex = Math.max(-1, Math.min(
      this.commandHistory.length - 1,
      this.historyIndex + direction
    ));

    this.currentCommand = this.historyIndex >= 0 
      ? this.commandHistory[this.historyIndex] 
      : '';
  }

  private addConsoleLine(line: string) {
    this.consoleLines.push(line);
    
    // Limit console history
    if (this.consoleLines.length > 1000) {
      this.consoleLines = this.consoleLines.slice(-800);
    }

    // Auto-scroll to bottom
    setTimeout(() => {
      if (this.consoleOutput?.nativeElement) {
        const element = this.consoleOutput.nativeElement;
        element.scrollTop = element.scrollHeight;
      }
    }, 10);
  }

  private handleConnectionError(message: string) {
    this.isConnecting = false;
    this.isConnected = false;
    this.error = message;
    this.addConsoleLine(`Error: ${message}`);
  }

  toggleFullscreen() {
    this.isFullscreen = !this.isFullscreen;
    
    // Focus input after fullscreen toggle
    setTimeout(() => {
      if (this.consoleInput?.nativeElement) {
        this.consoleInput.nativeElement.focus();
      }
    }, 100);
  }

  getStatusText(): string {
    if (this.isConnecting) return 'Connecting...';
    if (this.isConnected) return 'Connected';
    if (this.error) return 'Error';
    return 'Disconnected';
  }

  trackByIndex(index: number): number {
    return index;
  }
}