/**
 * Notification service for displaying toast messages and error dialogs.
 */

import { Injectable } from '@angular/core';
import { MatSnackBar, MatSnackBarConfig, MatSnackBarRef } from '@angular/material/snack-bar';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';
import { BehaviorSubject, Observable } from 'rxjs';
import { ToastComponent, ToastData } from '../../components/shared/toast/toast.component';

export interface NotificationOptions {
  duration?: number;
  action?: string;
  horizontalPosition?: 'start' | 'center' | 'end' | 'left' | 'right';
  verticalPosition?: 'top' | 'bottom';
  panelClass?: string | string[];
  data?: any;
}

export interface AppError {
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

export interface ToastNotification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  timestamp: Date;
  duration?: number;
  dismissed?: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  private notificationsSubject = new BehaviorSubject<ToastNotification[]>([]);
  public notifications$ = this.notificationsSubject.asObservable();

  private notificationId = 0;

  constructor(
    private snackBar: MatSnackBar,
    private dialog: MatDialog
  ) {}

  /**
   * Show success notification
   */
  showSuccess(message: string, options?: NotificationOptions): MatSnackBarRef<any> {
    const toastData: ToastData = {
      message,
      type: 'success',
      action: options?.action,
      duration: options?.duration || 3000
    };

    const config = this.getSnackBarConfig('success', options);
    const snackBarRef = this.snackBar.openFromComponent(ToastComponent, {
      ...config,
      data: toastData
    });
    
    this.addToHistory('success', message, options?.duration);
    
    return snackBarRef;
  }

  /**
   * Show error notification
   */
  showError(message: string, options?: NotificationOptions): MatSnackBarRef<any> {
    const toastData: ToastData = {
      message,
      type: 'error',
      action: options?.action,
      duration: 0 // Error messages don't auto-dismiss
    };

    const config = this.getSnackBarConfig('error', options);
    config.duration = 0; // Override duration for errors
    
    const snackBarRef = this.snackBar.openFromComponent(ToastComponent, {
      ...config,
      data: toastData
    });
    
    this.addToHistory('error', message, 0);
    
    return snackBarRef;
  }

  /**
   * Show warning notification
   */
  showWarning(message: string, options?: NotificationOptions): MatSnackBarRef<any> {
    const toastData: ToastData = {
      message,
      type: 'warning',
      action: options?.action,
      duration: options?.duration || 5000
    };

    const config = this.getSnackBarConfig('warning', options);
    config.duration = options?.duration || 5000;
    
    const snackBarRef = this.snackBar.openFromComponent(ToastComponent, {
      ...config,
      data: toastData
    });
    
    this.addToHistory('warning', message, config.duration);
    
    return snackBarRef;
  }

  /**
   * Show info notification
   */
  showInfo(message: string, options?: NotificationOptions): MatSnackBarRef<any> {
    const toastData: ToastData = {
      message,
      type: 'info',
      action: options?.action,
      duration: options?.duration || 3000
    };

    const config = this.getSnackBarConfig('info', options);
    
    const snackBarRef = this.snackBar.openFromComponent(ToastComponent, {
      ...config,
      data: toastData
    });
    
    this.addToHistory('info', message, options?.duration);
    
    return snackBarRef;
  }

  /**
   * Show error dialog for critical errors
   */
  showErrorDialog(error: AppError): Promise<MatDialogRef<any>> {
    // Import the ErrorDialogComponent dynamically to avoid circular dependencies
    return import('../../components/shared/error-dialog/error-dialog.component').then(module => {
      return this.dialog.open(module.ErrorDialogComponent, {
        width: '500px',
        maxWidth: '90vw',
        data: error,
        disableClose: false,
        autoFocus: true,
        restoreFocus: true,
        panelClass: 'error-dialog-panel'
      });
    }).catch(() => {
      // Fallback to simple snack bar if dialog component is not available
      this.showError(`Error: ${error.message || error.code}`, {
        action: 'DISMISS'
      });
      return Promise.reject('Dialog component not available');
    });
  }

  /**
   * Handle API errors and show appropriate notifications
   */
  handleApiError(error: any): void {
    const appError = this.parseApiError(error);
    
    if (appError.severity === 'critical' || appError.category === 'system') {
      this.showErrorDialog(appError);
    } else {
      const message = appError.user_message || appError.message || 'An error occurred';
      this.showError(message, {
        action: appError.retryable ? 'RETRY' : 'DISMISS'
      });
    }
  }

  /**
   * Parse API error response into AppError format
   */
  private parseApiError(error: any): AppError {
    // Handle standardized backend error format
    if (error?.error?.code) {
      return {
        code: error.error.code,
        message: error.error.message || 'Unknown error',
        details: error.error.details,
        category: error.error.category,
        timestamp: error.error.timestamp,
        request_id: error.error.request_id,
        severity: this.getSeverityFromCode(error.error.code),
        retryable: this.isRetryableError(error.error.code),
        user_message: error.error.message
      };
    }
    
    // Handle HTTP error responses
    if (error?.status) {
      return {
        code: `HTTP_${error.status}`,
        message: error.message || error.statusText || 'Network error',
        details: { status: error.status, url: error.url },
        severity: this.getSeverityFromStatus(error.status),
        retryable: this.isRetryableStatus(error.status),
        user_message: this.getUserMessageFromStatus(error.status)
      };
    }
    
    // Handle generic errors
    return {
      code: 'UNKNOWN_ERROR',
      message: error?.message || 'An unexpected error occurred',
      severity: 'medium',
      retryable: false,
      user_message: 'An unexpected error occurred. Please try again or contact support.'
    };
  }

  /**
   * Get notification history
   */
  getNotificationHistory(): ToastNotification[] {
    return this.notificationsSubject.value;
  }

  /**
   * Clear notification history
   */
  clearNotificationHistory(): void {
    this.notificationsSubject.next([]);
  }

  /**
   * Dismiss all notifications
   */
  dismissAll(): void {
    this.snackBar.dismiss();
  }

  private getSnackBarConfig(type: string, options?: NotificationOptions): MatSnackBarConfig {
    const defaultDuration = type === 'error' ? 0 : (type === 'warning' ? 5000 : 3000);
    
    return {
      duration: options?.duration ?? defaultDuration,
      horizontalPosition: options?.horizontalPosition || 'right',
      verticalPosition: options?.verticalPosition || 'top',
      panelClass: [
        'notification-snackbar',
        `notification-${type}`,
        ...(options?.panelClass ? (Array.isArray(options.panelClass) ? options.panelClass : [options.panelClass]) : [])
      ],
      data: options?.data
    };
  }

  private addToHistory(type: 'success' | 'error' | 'warning' | 'info', message: string, duration?: number): void {
    const notification: ToastNotification = {
      id: (++this.notificationId).toString(),
      type,
      message,
      timestamp: new Date(),
      duration
    };

    const currentNotifications = this.notificationsSubject.value;
    const updatedNotifications = [notification, ...currentNotifications].slice(0, 100); // Keep last 100
    this.notificationsSubject.next(updatedNotifications);
  }

  private getSeverityFromCode(code: string): 'low' | 'medium' | 'high' | 'critical' {
    const criticalCodes = ['INTERNAL_SERVER_ERROR', 'LIBVIRT_CONNECTION_FAILED', 'EXTERNAL_SERVICE_UNAVAILABLE'];
    const highCodes = ['VM_CREATE_FAILED', 'VM_DELETE_FAILED', 'RESOURCE_ALLOCATION_FAILED'];
    const lowCodes = ['VALIDATION_ERROR', 'RESOURCE_NOT_FOUND'];
    
    if (criticalCodes.some(c => code.includes(c))) return 'critical';
    if (highCodes.some(c => code.includes(c))) return 'high';
    if (lowCodes.some(c => code.includes(c))) return 'low';
    return 'medium';
  }

  private getSeverityFromStatus(status: number): 'low' | 'medium' | 'high' | 'critical' {
    if (status >= 500) return 'critical';
    if (status >= 400) return 'medium';
    return 'low';
  }

  private isRetryableError(code: string): boolean {
    const retryableCodes = [
      'EXTERNAL_SERVICE_UNAVAILABLE',
      'EXTERNAL_SERVICE_TIMEOUT',
      'SERVER_UNAVAILABLE',
      'LIBVIRT_CONNECTION_FAILED'
    ];
    return retryableCodes.some(c => code.includes(c));
  }

  private isRetryableStatus(status: number): boolean {
    const retryableStatuses = [408, 429, 502, 503, 504];
    return retryableStatuses.includes(status);
  }

  private getUserMessageFromStatus(status: number): string {
    switch (status) {
      case 400: return 'Invalid request. Please check your input and try again.';
      case 401: return 'Authentication required. Please log in and try again.';
      case 403: return 'You do not have permission to perform this action.';
      case 404: return 'The requested resource was not found.';
      case 409: return 'A conflict occurred. The resource may already exist.';
      case 422: return 'The request contains invalid data.';
      case 429: return 'Too many requests. Please wait a moment and try again.';
      case 500: return 'A server error occurred. Please try again later.';
      case 502: return 'Service temporarily unavailable. Please try again later.';
      case 503: return 'Service temporarily unavailable. Please try again later.';
      case 504: return 'Request timeout. Please try again.';
      default: return 'An error occurred. Please try again or contact support.';
    }
  }
}