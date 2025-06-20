import { Injectable } from '@angular/core';
import { Observable, of, timer } from 'rxjs';
import { retryWhen, mergeMap, take, catchError } from 'rxjs/operators';
import { NotificationService } from './notification.service';
import { OfflineDetectionService } from './offline-detection.service';

export interface RetryConfig {
  maxAttempts?: number;
  delay?: number;
  backoff?: boolean;
  showNotifications?: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class ErrorRecoveryService {

  constructor(
    private notificationService: NotificationService,
    private offlineDetection: OfflineDetectionService
  ) {}

  /**
   * Retry an operation with exponential backoff
   */
  retryWithBackoff<T>(
    operation: () => Observable<T>,
    config: RetryConfig = {}
  ): Observable<T> {
    const {
      maxAttempts = 3,
      delay = 1000,
      backoff = true,
      showNotifications = true
    } = config;

    let attempt = 0;

    return operation().pipe(
      retryWhen(errors =>
        errors.pipe(
          mergeMap(error => {
            attempt++;
            
            if (attempt > maxAttempts) {
              if (showNotifications) {
                this.notificationService.showError(
                  `Operation failed after ${maxAttempts} attempts. Please try again later.`
                );
              }
              throw error;
            }

            if (showNotifications && attempt > 1) {
              this.notificationService.showInfo(
                `Retrying... (attempt ${attempt} of ${maxAttempts})`,
                { duration: 2000 }
              );
            }

            const retryDelay = backoff ? delay * Math.pow(2, attempt - 1) : delay;
            return timer(retryDelay);
          }),
          take(maxAttempts)
        )
      ),
      catchError(error => {
        if (showNotifications) {
          this.notificationService.handleApiError(error);
        }
        throw error;
      })
    );
  }

  /**
   * Execute operation with online check
   */
  executeWithOnlineCheck<T>(
    operation: () => Observable<T>,
    actionName: string = 'perform this action'
  ): Observable<T> {
    if (!this.offlineDetection.requireOnline(actionName)) {
      return of(null as any); // Return empty observable if offline
    }

    return operation().pipe(
      catchError(error => {
        // If it's a network error and we're offline, show appropriate message
        if (error.status === 0 && this.offlineDetection.isOffline()) {
          this.notificationService.showError(
            'This action requires an internet connection. Please check your connection and try again.'
          );
        }
        throw error;
      })
    );
  }

  /**
   * Create a recovery strategy for failed operations
   */
  createRecoveryStrategy<T>(
    primaryOperation: () => Observable<T>,
    fallbackOperation?: () => Observable<T>,
    config: RetryConfig = {}
  ): Observable<T> {
    return this.retryWithBackoff(primaryOperation, config).pipe(
      catchError(error => {
        if (fallbackOperation) {
          this.notificationService.showWarning(
            'Primary operation failed, trying alternative approach...',
            { duration: 3000 }
          );
          return fallbackOperation();
        }
        throw error;
      })
    );
  }

  /**
   * Handle graceful degradation when features are unavailable
   */
  gracefulDegrade<T>(
    operation: () => Observable<T>,
    fallbackData: T,
    degradedMessage?: string
  ): Observable<T> {
    return operation().pipe(
      catchError(error => {
        if (degradedMessage) {
          this.notificationService.showWarning(degradedMessage, { duration: 5000 });
        }
        return of(fallbackData);
      })
    );
  }

  /**
   * Execute operation with automatic retry for specific error types
   */
  executeWithAutoRetry<T>(
    operation: () => Observable<T>,
    retryableErrors: number[] = [408, 429, 502, 503, 504]
  ): Observable<T> {
    return operation().pipe(
      retryWhen(errors =>
        errors.pipe(
          mergeMap((error, index) => {
            // Only retry if it's a retryable error and within limits
            if (retryableErrors.includes(error.status) && index < 2) {
              const delay = 1000 * Math.pow(2, index); // Exponential backoff
              this.notificationService.showInfo(
                `Temporary error occurred, retrying in ${delay / 1000} seconds...`,
                { duration: 2000 }
              );
              return timer(delay);
            }
            throw error;
          })
        )
      )
    );
  }
}