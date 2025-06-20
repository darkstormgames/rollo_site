import { Component, Input, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { VM } from '../../../models/vm/vm.model';
import { LoadingSpinnerComponent } from '../../shared/loading-spinner/loading-spinner.component';
import { ConsoleService, ConsoleSession, ConsoleConnection } from '../../../services/console/console.service';
import { Subscription } from 'rxjs';

// Import noVNC
declare var RFB: any;

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
            (click)="sendSpecialKey('ctrl-alt-del')"
            [disabled]="!isConnected"
            title="Send Ctrl+Alt+Del">
            <span [attr.aria-hidden]="true">⌨️</span>
          </button>
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

        <!-- VNC Display Container -->
        <div 
          #vncDisplay 
          class="vnc-display"
          [class.hidden]="isConnecting || error"
          [style.width.px]="displayWidth"
          [style.height.px]="displayHeight">
          <!-- noVNC will be attached here -->
        </div>

        <!-- Fallback text console for non-VNC connections -->
        <div 
          #consoleOutput 
          class="console-output"
          [class.hidden]="isConnecting || error || isVncMode"
          role="log"
          aria-live="polite"
          aria-label="Console output"
          tabindex="0">
          <div *ngFor="let line of consoleLines; trackBy: trackByIndex" class="console-line">
            {{ line }}
          </div>
        </div>

        <div class="console-input" [class.hidden]="isConnecting || error || isVncMode || !isConnected">
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
          <span *ngIf="currentSession" class="session-info">
            - {{ currentSession.protocol.toUpperCase() }}
          </span>
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
  @ViewChild('vncDisplay') vncDisplay!: ElementRef;

  // Legacy text console properties
  consoleLines: string[] = [];
  currentCommand = '';
  
  // VNC console properties
  isConnected = false;
  isConnecting = false;
  isFullscreen = false;
  isVncMode = true; // Use VNC by default
  error: string | null = null;
  
  currentSession: ConsoleSession | null = null;
  displayWidth = 1024;
  displayHeight = 768;
  
  private rfb: any = null; // noVNC RFB connection
  private connectionSubscription?: Subscription;
  private commandHistory: string[] = [];
  private historyIndex = -1;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 3;

  constructor(private consoleService: ConsoleService) {}

  ngOnInit() {
    if (this.vm) {
      this.connect();
    }
    
    // Subscribe to connection status
    this.connectionSubscription = this.consoleService.connection$.subscribe(
      (connection: ConsoleConnection) => {
        this.handleConnectionUpdate(connection);
      }
    );
  }

  ngAfterViewInit() {
    // Focus handling will depend on connection mode
    setTimeout(() => {
      if (!this.isVncMode && this.consoleInput?.nativeElement) {
        this.consoleInput.nativeElement.focus();
      }
    }, 100);
  }

  ngOnDestroy() {
    this.disconnect();
    if (this.connectionSubscription) {
      this.connectionSubscription.unsubscribe();
    }
  }

  connect() {
    if (!this.vm || this.isConnecting) return;

    this.isConnecting = true;
    this.error = null;
    this.reconnectAttempts = 0;

    // Request console access
    this.consoleService.requestAccess(this.vm.id, 'vnc').subscribe({
      next: (session: ConsoleSession) => {
        console.log('Console session created:', session);
        this.currentSession = session;
        
        // Connect to VNC WebSocket
        this.consoleService.connect(session).subscribe({
          next: (connection: ConsoleConnection) => {
            console.log('Console connection update:', connection);
          },
          error: (error) => {
            console.error('Console connection error:', error);
            this.handleConnectionError('Failed to connect to console');
          }
        });
      },
      error: (error) => {
        console.error('Failed to request console access:', error);
        this.handleConnectionError('Failed to request console access');
      }
    });
  }

  private handleConnectionUpdate(connection: ConsoleConnection) {
    this.isConnecting = false;
    this.isConnected = connection.connected;
    this.currentSession = connection.session;
    this.error = connection.error;
    
    if (connection.connected && connection.session && this.vncDisplay?.nativeElement) {
      // Initialize noVNC when connected
      this.initializeVNC();
    }
  }

  private initializeVNC() {
    if (!this.currentSession || !this.vncDisplay?.nativeElement) return;
    
    try {
      // Create noVNC connection
      // Note: In a real implementation, we'd connect directly to the VNC WebSocket
      // For now, we'll create a placeholder VNC display
      this.createVNCPlaceholder();
      
    } catch (error) {
      console.error('Failed to initialize VNC:', error);
      this.handleConnectionError('Failed to initialize VNC display');
    }
  }

  private createVNCPlaceholder() {
    // Create a placeholder VNC display since we don't have a real VNC server
    if (!this.vncDisplay?.nativeElement) return;
    
    const canvas = document.createElement('canvas');
    canvas.width = this.displayWidth;
    canvas.height = this.displayHeight;
    canvas.style.border = '1px solid #ccc';
    canvas.style.backgroundColor = '#000';
    
    // Clear any existing content
    this.vncDisplay.nativeElement.innerHTML = '';
    this.vncDisplay.nativeElement.appendChild(canvas);
    
    // Draw a simple placeholder
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.fillStyle = '#333';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      
      ctx.fillStyle = '#fff';
      ctx.font = '24px Arial';
      ctx.textAlign = 'center';
      ctx.fillText('VNC Console Connected', canvas.width / 2, canvas.height / 2 - 20);
      ctx.fillText(`VM: ${this.vm?.name}`, canvas.width / 2, canvas.height / 2 + 20);
      ctx.fillText('(Placeholder - Real VNC integration would display here)', canvas.width / 2, canvas.height / 2 + 60);
    }
    
    // Add mouse and keyboard event listeners
    canvas.addEventListener('click', () => {
      console.log('VNC canvas clicked');
    });
    
    canvas.addEventListener('keydown', (event) => {
      console.log('VNC key pressed:', event.key);
      this.consoleService.sendKeys([event.key]);
      event.preventDefault();
    });
    
    // Make canvas focusable
    canvas.setAttribute('tabindex', '0');
    canvas.focus();
  }

  disconnect() {
    this.consoleService.disconnect();
    
    if (this.rfb) {
      this.rfb.disconnect();
      this.rfb = null;
    }
    
    this.isConnected = false;
    this.isConnecting = false;
    this.currentSession = null;
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

  sendSpecialKey(combination: string) {
    if (!this.isConnected) return;
    
    switch (combination) {
      case 'ctrl-alt-del':
        // Send Ctrl+Alt+Del sequence
        this.consoleService.sendKeys(['Control_L', 'Alt_L', 'Delete']);
        break;
      case 'ctrl-c':
        this.consoleService.sendKeys(['Control_L', 'c']);
        break;
      case 'alt-tab':
        this.consoleService.sendKeys(['Alt_L', 'Tab']);
        break;
      default:
        console.log('Unknown special key combination:', combination);
    }
  }

  getStatusText(): string {
    if (this.isConnecting) return 'Connecting...';
    if (this.isConnected && this.currentSession) {
      return `Connected (${this.currentSession.protocol.toUpperCase()})`;
    }
    if (this.error) return 'Error';
    return 'Disconnected';
  }

  trackByIndex(index: number): number {
    return index;
  }
}