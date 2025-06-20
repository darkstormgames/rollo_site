import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatExpansionModule } from '@angular/material/expansion';
import { CommonModule } from '@angular/common';
import { ClipboardModule } from '@angular/cdk/clipboard';
import { MatSnackBar } from '@angular/material/snack-bar';

export interface ErrorDialogData {
  code: string;
  message: string;
  details?: any;
  category?: string;
  timestamp?: string;
  request_id?: string;
  severity?: 'low' | 'medium' | 'high' | 'critical';
  retryable?: boolean;
  user_message?: string;
}

@Component({
  selector: 'app-error-dialog',
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    MatExpansionModule,
    ClipboardModule
  ],
  template: `
    <div class="error-dialog">
      <div class="error-header" [class]="'severity-' + (data.severity || 'medium')">
        <mat-icon class="error-icon">{{ getErrorIcon() }}</mat-icon>
        <h2 mat-dialog-title>{{ getErrorTitle() }}</h2>
      </div>

      <mat-dialog-content class="error-content">
        <div class="error-message">
          <p>{{ data.user_message || data.message }}</p>
        </div>

        <mat-expansion-panel class="error-details-panel" *ngIf="hasDetails()">
          <mat-expansion-panel-header>
            <mat-panel-title>
              <mat-icon>info</mat-icon>
              Technical Details
            </mat-panel-title>
          </mat-expansion-panel-header>
          
          <div class="error-details">
            <div class="detail-row" *ngIf="data.code">
              <strong>Error Code:</strong>
              <span class="detail-value">{{ data.code }}</span>
              <button mat-icon-button 
                      [cdkCopyToClipboard]="data.code"
                      (cdkCopyToClipboardCopied)="onCopy('Error code copied')"
                      title="Copy error code">
                <mat-icon>content_copy</mat-icon>
              </button>
            </div>

            <div class="detail-row" *ngIf="data.request_id">
              <strong>Request ID:</strong>
              <span class="detail-value">{{ data.request_id }}</span>
              <button mat-icon-button 
                      [cdkCopyToClipboard]="data.request_id"
                      (cdkCopyToClipboardCopied)="onCopy('Request ID copied')"
                      title="Copy request ID">
                <mat-icon>content_copy</mat-icon>
              </button>
            </div>

            <div class="detail-row" *ngIf="data.category">
              <strong>Category:</strong>
              <span class="detail-value">{{ data.category }}</span>
            </div>

            <div class="detail-row" *ngIf="data.timestamp">
              <strong>Timestamp:</strong>
              <span class="detail-value">{{ formatTimestamp(data.timestamp) }}</span>
            </div>

            <div class="detail-row" *ngIf="data.details">
              <strong>Additional Details:</strong>
              <pre class="detail-json">{{ formatDetails(data.details) }}</pre>
              <button mat-icon-button 
                      [cdkCopyToClipboard]="formatDetails(data.details)"
                      (cdkCopyToClipboardCopied)="onCopy('Details copied')"
                      title="Copy details">
                <mat-icon>content_copy</mat-icon>
              </button>
            </div>
          </div>
        </mat-expansion-panel>

        <div class="error-actions" *ngIf="data.retryable">
          <mat-icon class="retry-icon">refresh</mat-icon>
          <p class="retry-message">This error might be temporary. You can try the operation again.</p>
        </div>
      </mat-dialog-content>

      <mat-dialog-actions class="error-dialog-actions">
        <button mat-button 
                *ngIf="data.retryable" 
                (click)="onRetry()"
                color="primary">
          <mat-icon>refresh</mat-icon>
          Retry
        </button>
        
        <button mat-button (click)="onReportIssue()" *ngIf="shouldShowReportButton()">
          <mat-icon>bug_report</mat-icon>
          Report Issue
        </button>
        
        <button mat-button (click)="onClose()" color="accent">
          Close
        </button>
      </mat-dialog-actions>
    </div>
  `,
  styles: [`
    .error-dialog {
      max-width: 600px;
      min-width: 400px;
    }

    .error-header {
      display: flex;
      align-items: center;
      padding: 16px 24px;
      margin: -24px -24px 16px -24px;
      border-radius: 4px 4px 0 0;
    }

    .error-header.severity-low {
      background-color: #fff3e0;
      color: #ef6c00;
    }

    .error-header.severity-medium {
      background-color: #ffebee;
      color: #c62828;
    }

    .error-header.severity-high {
      background-color: #ffebee;
      color: #b71c1c;
    }

    .error-header.severity-critical {
      background-color: #ffebee;
      color: #b71c1c;
      border-left: 4px solid #f44336;
    }

    .error-icon {
      margin-right: 12px;
      font-size: 24px;
      width: 24px;
      height: 24px;
    }

    .error-content {
      padding: 0 !important;
    }

    .error-message {
      margin-bottom: 16px;
      font-size: 16px;
      line-height: 1.5;
    }

    .error-details-panel {
      margin-bottom: 16px;
      box-shadow: none;
      border: 1px solid #e0e0e0;
    }

    .error-details {
      padding-top: 16px;
    }

    .detail-row {
      display: flex;
      align-items: flex-start;
      margin-bottom: 12px;
      gap: 8px;
    }

    .detail-row strong {
      min-width: 120px;
      font-weight: 500;
    }

    .detail-value {
      flex: 1;
      word-break: break-all;
      font-family: 'Roboto Mono', monospace;
      font-size: 14px;
    }

    .detail-json {
      flex: 1;
      background-color: #f5f5f5;
      padding: 8px;
      border-radius: 4px;
      font-family: 'Roboto Mono', monospace;
      font-size: 12px;
      white-space: pre-wrap;
      word-break: break-all;
      max-height: 200px;
      overflow-y: auto;
    }

    .error-actions {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 16px;
      background-color: #f0f7ff;
      border-radius: 4px;
      margin-top: 16px;
    }

    .retry-icon {
      color: #1976d2;
    }

    .retry-message {
      margin: 0;
      font-size: 14px;
      color: #666;
    }

    .error-dialog-actions {
      gap: 8px;
      justify-content: flex-end;
    }

    .mat-expansion-panel-header-title {
      display: flex;
      align-items: center;
      gap: 8px;
    }
  `]
})
export class ErrorDialogComponent {
  
  constructor(
    public dialogRef: MatDialogRef<ErrorDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: ErrorDialogData,
    private snackBar: MatSnackBar
  ) {}

  getErrorIcon(): string {
    switch (this.data.severity) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'info';
      case 'low': return 'info_outline';
      default: return 'error_outline';
    }
  }

  getErrorTitle(): string {
    switch (this.data.severity) {
      case 'critical': return 'Critical Error';
      case 'high': return 'Error';
      case 'medium': return 'Warning';
      case 'low': return 'Notice';
      default: return 'Error';
    }
  }

  hasDetails(): boolean {
    return !!(this.data.code || this.data.request_id || this.data.category || 
              this.data.timestamp || this.data.details);
  }

  shouldShowReportButton(): boolean {
    return this.data.severity === 'critical' || this.data.severity === 'high';
  }

  formatTimestamp(timestamp: string): string {
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return timestamp;
    }
  }

  formatDetails(details: any): string {
    try {
      return JSON.stringify(details, null, 2);
    } catch {
      return String(details);
    }
  }

  onCopy(message: string): void {
    this.snackBar.open(message, '', { duration: 2000 });
  }

  onRetry(): void {
    this.dialogRef.close('retry');
  }

  onReportIssue(): void {
    // In a real application, this would integrate with a bug reporting system
    const reportData = {
      code: this.data.code,
      message: this.data.message,
      details: this.data.details,
      request_id: this.data.request_id,
      timestamp: this.data.timestamp,
      user_agent: navigator.userAgent,
      url: window.location.href
    };

    // Copy to clipboard for now
    const reportText = `Error Report:\n${JSON.stringify(reportData, null, 2)}`;
    navigator.clipboard.writeText(reportText).then(() => {
      this.snackBar.open('Error details copied to clipboard. Please send this to support.', 'OK', {
        duration: 5000
      });
    }).catch(() => {
      this.snackBar.open('Unable to copy error details. Please manually report: ' + this.data.code, 'OK', {
        duration: 5000
      });
    });
  }

  onClose(): void {
    this.dialogRef.close();
  }
}