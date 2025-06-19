import { Injectable } from '@angular/core';
import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { Router } from '@angular/router';

@Injectable()
export class ErrorInterceptor implements HttpInterceptor {

  constructor(private router: Router) {}

  intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    return next.handle(request).pipe(
      catchError((error: HttpErrorResponse) => {
        // Handle different HTTP error status codes
        switch (error.status) {
          case 401:
            // Unauthorized - handled by AuthInterceptor
            break;
          
          case 403:
            // Forbidden - redirect to access denied page
            this.router.navigate(['/access-denied']);
            break;
          
          case 404:
            // Not found - log error
            console.error('Resource not found:', error.url);
            break;
          
          case 500:
            // Internal server error
            console.error('Internal server error:', error.message);
            this.handleServerError(error);
            break;
          
          case 503:
            // Service unavailable
            console.error('Service unavailable:', error.message);
            this.handleServiceUnavailable(error);
            break;
          
          default:
            // Generic error handling
            console.error('HTTP Error:', error);
            break;
        }

        // Transform error to consistent format
        const errorMessage = this.getErrorMessage(error);
        const transformedError = {
          error: errorMessage,
          status: error.status,
          statusText: error.statusText,
          url: error.url,
          originalError: error
        };

        return throwError(() => transformedError);
      })
    );
  }

  private getErrorMessage(error: HttpErrorResponse): string {
    if (error.error instanceof ErrorEvent) {
      // Client-side error
      return error.error.message;
    } else {
      // Server-side error
      if (error.error && error.error.error) {
        return error.error.error;
      } else if (error.error && error.error.message) {
        return error.error.message;
      } else if (error.message) {
        return error.message;
      } else {
        return `HTTP ${error.status}: ${error.statusText}`;
      }
    }
  }

  private handleServerError(error: HttpErrorResponse): void {
    // Show notification or redirect to error page
    // This could be integrated with a notification service
    console.error('Server error occurred. Please try again later.');
  }

  private handleServiceUnavailable(error: HttpErrorResponse): void {
    // Show maintenance message
    console.error('Service is temporarily unavailable. Please try again later.');
  }
}