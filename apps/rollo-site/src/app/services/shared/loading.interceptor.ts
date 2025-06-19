import { Injectable } from '@angular/core';
import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent } from '@angular/common/http';
import { Observable } from 'rxjs';
import { finalize } from 'rxjs/operators';
import { LoadingService } from './loading.service';

@Injectable()
export class LoadingInterceptor implements HttpInterceptor {
  private activeRequests = 0;

  constructor(private loadingService: LoadingService) {}

  intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    // Check if this request should show loading indicator
    const showLoading = this.shouldShowLoading(request);
    
    if (showLoading) {
      this.activeRequests++;
      this.loadingService.setLoading(true);
    }

    return next.handle(request).pipe(
      finalize(() => {
        if (showLoading) {
          this.activeRequests--;
          if (this.activeRequests === 0) {
            this.loadingService.setLoading(false);
          }
        }
      })
    );
  }

  private shouldShowLoading(request: HttpRequest<any>): boolean {
    // Skip loading for certain requests (like heartbeat, metrics polling, etc.)
    const skipLoadingPaths = [
      '/heartbeat',
      '/metrics',
      '/status',
      '/ping'
    ];

    // Skip loading for requests with custom header
    if (request.headers.has('X-Skip-Loading')) {
      return false;
    }

    // Skip loading for GET requests to specific endpoints
    if (request.method === 'GET' && skipLoadingPaths.some(path => request.url.includes(path))) {
      return false;
    }

    return true;
  }
}