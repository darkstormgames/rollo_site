import { Component, Inject } from '@angular/core';
import { MAT_SNACK_BAR_DATA, MatSnackBarRef } from '@angular/material/snack-bar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { CommonModule } from '@angular/common';

export interface ToastData {
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
  action?: string;
  duration?: number;
  retryable?: boolean;
}

@Component({
  selector: 'app-toast',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatIconModule],
  template: `
    <div class="toast-container" [class]="'toast-' + data.type">
      <div class="toast-content">
        <mat-icon class="toast-icon">{{ getIcon() }}</mat-icon>
        <span class="toast-message">{{ data.message }}</span>
      </div>
      
      <div class="toast-actions" *ngIf="data.action || data.retryable">
        <button mat-button 
                *ngIf="data.retryable" 
                (click)="onRetry()"
                class="toast-action-button retry-button">
          <mat-icon>refresh</mat-icon>
          Retry
        </button>
        
        <button mat-button 
                *ngIf="data.action && !data.retryable" 
                (click)="onAction()"
                class="toast-action-button">
          {{ data.action }}
        </button>
        
        <button mat-icon-button 
                (click)="onDismiss()"
                class="toast-close-button"
                aria-label="Close notification">
          <mat-icon>close</mat-icon>
        </button>
      </div>
    </div>
  `,
  styles: [`
    .toast-container {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 16px;
      min-height: 48px;
      color: white;
      border-radius: 4px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
      max-width: 500px;
      min-width: 300px;
    }

    .toast-content {
      display: flex;
      align-items: center;
      flex: 1;
      gap: 12px;
    }

    .toast-icon {
      font-size: 20px;
      width: 20px;
      height: 20px;
      flex-shrink: 0;
    }

    .toast-message {
      flex: 1;
      font-size: 14px;
      line-height: 1.4;
    }

    .toast-actions {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-left: 16px;
    }

    .toast-action-button {
      color: inherit !important;
      font-weight: 500;
      font-size: 12px;
      padding: 4px 8px;
      min-width: auto;
      height: 32px;
      border: 1px solid rgba(255, 255, 255, 0.3);
    }

    .retry-button {
      gap: 4px;
    }

    .toast-close-button {
      color: inherit !important;
      width: 32px;
      height: 32px;
    }

    .toast-close-button mat-icon {
      font-size: 18px;
      width: 18px;
      height: 18px;
    }

    /* Success toast */
    .toast-success {
      background-color: #4caf50;
    }

    .toast-success .toast-action-button {
      background-color: rgba(255, 255, 255, 0.1);
    }

    .toast-success .toast-action-button:hover {
      background-color: rgba(255, 255, 255, 0.2);
    }

    /* Error toast */
    .toast-error {
      background-color: #f44336;
    }

    .toast-error .toast-action-button {
      background-color: rgba(255, 255, 255, 0.1);
    }

    .toast-error .toast-action-button:hover {
      background-color: rgba(255, 255, 255, 0.2);
    }

    /* Warning toast */
    .toast-warning {
      background-color: #ff9800;
    }

    .toast-warning .toast-action-button {
      background-color: rgba(255, 255, 255, 0.1);
    }

    .toast-warning .toast-action-button:hover {
      background-color: rgba(255, 255, 255, 0.2);
    }

    /* Info toast */
    .toast-info {
      background-color: #2196f3;
    }

    .toast-info .toast-action-button {
      background-color: rgba(255, 255, 255, 0.1);
    }

    .toast-info .toast-action-button:hover {
      background-color: rgba(255, 255, 255, 0.2);
    }

    /* Responsive design */
    @media (max-width: 600px) {
      .toast-container {
        min-width: 250px;
        max-width: 300px;
      }

      .toast-message {
        font-size: 13px;
      }

      .toast-actions {
        margin-left: 8px;
      }

      .toast-action-button {
        padding: 2px 6px;
        font-size: 11px;
      }
    }
  `]
})
export class ToastComponent {
  
  constructor(
    private snackBarRef: MatSnackBarRef<ToastComponent>,
    @Inject(MAT_SNACK_BAR_DATA) public data: ToastData
  ) {}

  getIcon(): string {
    switch (this.data.type) {
      case 'success': return 'check_circle';
      case 'error': return 'error';
      case 'warning': return 'warning';
      case 'info': return 'info';
      default: return 'info';
    }
  }

  onAction(): void {
    this.snackBarRef.dismissWithAction();
  }

  onRetry(): void {
    this.snackBarRef.dismissWithAction();
  }

  onDismiss(): void {
    this.snackBarRef.dismiss();
  }
}