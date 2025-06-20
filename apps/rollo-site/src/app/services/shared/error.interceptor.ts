import { Injectable } from '@angular/core';
import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError, timer, of } from 'rxjs';
import { catchError, mergeMap, finalize, retry, retryWhen, tap } from 'rxjs/operators';
import { Router } from '@angular/router';
import { NotificationService } from './notification.service';

@Injectable()
export class ErrorInterceptor implements HttpInterceptor {

  private readonly maxRetries = 3;
  private readonly retryDelay = 1000; // Start with 1 second
  private readonly retryableStatusCodes = [0, 408, 429, 502, 503, 504];

  constructor(
    private router: Router,
    private notificationService: NotificationService
  ) {}

  intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    return next.handle(request).pipe(
      retryWhen(errors =>
        errors.pipe(
          mergeMap((error, i) => {
            const retryAttempt = i + 1;
            
            // Only retry specific errors and up to maxRetries
            if (retryAttempt > this.maxRetries || !this.shouldRetry(error)) {
              return throwError(() => error);
            }

            console.log(`Retry attempt ${retryAttempt} for ${request.method} ${request.url}`);
            
            // Exponential backoff: delay increases with each retry
            const delay = this.retryDelay * Math.pow(2, retryAttempt - 1);
            return timer(delay);
          })
        )
      ),
      catchError((error: HttpErrorResponse) => {
        this.handleError(request, error);
        return throwError(() => this.transformError(error));
      })
    );
  }

  private shouldRetry(error: HttpErrorResponse): boolean {
    // Don't retry authentication errors, client errors (4xx except specific ones), or certain server errors
    if (error.status === 401 || error.status === 403 || error.status === 404) {
      return false;
    }

    // Only retry specific status codes or network errors
    return this.retryableStatusCodes.includes(error.status) || 
           error.status === 0; // Network errors
  }

  private handleError(request: HttpRequest<any>, error: HttpErrorResponse): void {
    // Log the error for debugging
    console.error(`HTTP Error ${error.status} for ${request.method} ${request.url}:`, error);

    // Handle specific error types
    switch (error.status) {
      case 401:
        // Unauthorized - don't show notification, let auth system handle
        break;
      
      case 403:
        // Forbidden - redirect to access denied page
        this.router.navigate(['/access-denied']);
        this.notificationService.showError('You do not have permission to perform this action.');
        break;
      
      case 404:
        // Not found - only show notification for explicit API calls
        if (this.isApiRequest(request)) {
          this.notificationService.showWarning('The requested resource was not found.');
        }
        break;
      
      case 500:
        // Internal server error
        this.notificationService.handleApiError(error);
        break;
      
      case 503:
        // Service unavailable
        this.notificationService.showWarning(
          'Service is temporarily unavailable. Please try again later.',
          { duration: 5000 }
        );
        break;

      case 0:
        // Network error
        this.notificationService.showError(
          'Network connection failed. Please check your internet connection.',
          { action: 'RETRY' }
        );
        break;
      
      default:
        // For other errors, let the notification service handle based on severity
        if (error.status >= 500) {
          this.notificationService.handleApiError(error);
        } else if (error.status >= 400) {
          this.notificationService.showWarning(this.getErrorMessage(error));
        }
        break;
    }
  }

  private transformError(error: HttpErrorResponse): any {
    // Transform error to consistent format that matches backend error structure
    return {
      error: {
        code: this.getErrorCode(error),
        message: this.getErrorMessage(error),
        details: {
          status: error.status,
          statusText: error.statusText,
          url: error.url,
          timestamp: new Date().toISOString()
        },
        category: this.getErrorCategory(error.status),
        severity: this.getErrorSeverity(error.status),
        retryable: this.shouldRetry(error)
      },
      status: error.status,
      statusText: error.statusText,
      url: error.url,
      originalError: error
    };
  }

  private getErrorCode(error: HttpErrorResponse): string {
    // Extract error code from backend response if available
    if (error.error?.error?.code) {
      return error.error.error.code;
    }
    
    // Generate code based on status
    return `HTTP_${error.status || 'UNKNOWN'}`;
  }

  private getErrorCategory(status: number): string {
    if (status === 401 || status === 403) return 'authentication';
    if (status === 422 || status === 400) return 'validation';
    if (status === 404) return 'resource';
    if (status >= 500) return 'system';
    if (status === 0) return 'network';
    return 'unknown';
  }

  private getErrorSeverity(status: number): string {
    if (status >= 500) return 'high';
    if (status === 404 || status === 403) return 'medium';
    if (status === 400 || status === 422) return 'low';
    if (status === 0) return 'high'; // Network errors are serious
    return 'medium';
  }

  private isApiRequest(request: HttpRequest<any>): boolean {
    // Consider requests to /api/* as API requests
    return request.url.includes('/api/');
  }

  private getErrorMessage(error: HttpErrorResponse): string {
    // Check for backend error format first
    if (error.error?.error?.message) {
      return error.error.error.message;
    }
    
    if (error.error instanceof ErrorEvent) {
      // Client-side error
      return error.error.message;
    } else {
      // Server-side error
      if (error.error && error.error.message) {
        return error.error.message;
      } else if (error.message) {
        return error.message;
      } else {
        return `HTTP ${error.status}: ${error.statusText}`;
      }
    }
  }
}