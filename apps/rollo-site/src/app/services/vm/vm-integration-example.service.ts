/**
 * Example service showing how to integrate with the error handling system
 */

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { NotificationService } from '../shared/notification.service';
import { ErrorRecoveryService } from '../shared/error-recovery.service';
import { OfflineDetectionService } from '../shared/offline-detection.service';

interface VM {
  id: string;
  name: string;
  status: string;
  server_id: string;
  cpu_cores: number;
  memory_mb: number;
}

interface CreateVMRequest {
  name: string;
  server_id: string;
  cpu_cores: number;
  memory_mb: number;
  disk_gb: number;
}

@Injectable({
  providedIn: 'root'
})
export class VmIntegrationExampleService {

  private readonly apiUrl = '/api';

  constructor(
    private http: HttpClient,
    private notificationService: NotificationService,
    private errorRecovery: ErrorRecoveryService,
    private offlineDetection: OfflineDetectionService
  ) {}

  /**
   * Example 1: Basic operation with error handling
   */
  getVMs(): Observable<VM[]> {
    return this.errorRecovery.executeWithOnlineCheck(
      () => this.http.get<VM[]>(`${this.apiUrl}/vms`),
      'load virtual machines'
    ).pipe(
      map(response => response || []),
      catchError(error => {
        // The error interceptor will handle showing notifications
        // We can add specific business logic here
        console.error('Failed to load VMs:', error);
        throw error;
      })
    );
  }

  /**
   * Example 2: Create operation with retry logic
   */
  createVM(vmData: CreateVMRequest): Observable<VM> {
    // Check if online first
    if (!this.offlineDetection.requireOnline('create a virtual machine')) {
      throw new Error('Offline');
    }

    return this.errorRecovery.retryWithBackoff(
      () => this.http.post<VM>(`${this.apiUrl}/vms`, vmData),
      {
        maxAttempts: 2, // Only retry once for create operations
        delay: 2000,
        showNotifications: true
      }
    ).pipe(
      map(vm => {
        this.notificationService.showSuccess(
          `Virtual machine "${vm.name}" created successfully!`
        );
        return vm;
      }),
      catchError(error => {
        // Handle specific VM creation errors
        if (error?.error?.code === 'INSUFFICIENT_MEMORY') {
          this.notificationService.showError(
            'Not enough memory available. Try reducing the memory allocation or contact your administrator.',
            { action: 'ADJUST SETTINGS' }
          );
        } else if (error?.error?.code === 'SERVER_NOT_FOUND') {
          this.notificationService.showError(
            'The selected server is not available. Please choose a different server.',
            { action: 'SELECT SERVER' }
          );
        }
        // Let the error bubble up for global handling
        throw error;
      })
    );
  }

  /**
   * Example 3: Operation with graceful degradation
   */
  getVMMetrics(vmId: string): Observable<any> {
    return this.errorRecovery.gracefulDegrade(
      () => this.http.get(`${this.apiUrl}/vms/${vmId}/metrics`),
      { cpu: 0, memory: 0, disk: 0 }, // Fallback data
      'Real-time metrics are temporarily unavailable. Showing cached data.'
    );
  }

  /**
   * Example 4: Critical operation with error dialog
   */
  deleteVM(vmId: string, vmName: string): Observable<void> {
    return this.errorRecovery.executeWithOnlineCheck(
      () => this.http.delete<void>(`${this.apiUrl}/vms/${vmId}`),
      'delete virtual machine'
    ).pipe(
      map(() => {
        this.notificationService.showSuccess(
          `Virtual machine "${vmName}" deleted successfully.`
        );
      }),
      catchError(error => {
        // For delete operations, show error dialog for critical issues
        if (error?.error?.severity === 'critical') {
          this.notificationService.showErrorDialog({
            code: error.error.code,
            message: error.error.message,
            details: error.error.details,
            category: error.error.category,
            severity: 'critical',
            user_message: `Failed to delete virtual machine "${vmName}". This may require manual intervention.`
          });
        }
        throw error;
      })
    );
  }

  /**
   * Example 5: Bulk operation with progress and error handling
   */
  startMultipleVMs(vmIds: string[]): Observable<{ success: string[], failed: string[] }> {
    const results: { success: string[], failed: string[] } = { success: [], failed: [] };
    
    const startOperations = vmIds.map(vmId => 
      this.errorRecovery.executeWithAutoRetry(
        () => this.http.post(`${this.apiUrl}/vms/${vmId}/start`, {})
      ).pipe(
        map(() => {
          results.success.push(vmId);
          return vmId;
        }),
        catchError(error => {
          results.failed.push(vmId);
          console.error(`Failed to start VM ${vmId}:`, error);
          return error; // Don't let individual failures stop the batch
        })
      )
    );

    return new Observable(observer => {
      Promise.allSettled(
        startOperations.map(op => op.toPromise())
      ).then(() => {
        // Show summary notification
        if (results.success.length > 0) {
          this.notificationService.showSuccess(
            `Started ${results.success.length} virtual machine(s) successfully.`
          );
        }
        
        if (results.failed.length > 0) {
          this.notificationService.showWarning(
            `Failed to start ${results.failed.length} virtual machine(s). Check individual VM status.`,
            { duration: 5000 }
          );
        }
        
        observer.next(results);
        observer.complete();
      });
    });
  }

  /**
   * Example 6: Long-running operation with progress updates
   */
  cloneVM(sourceVmId: string, newName: string): Observable<VM> {
    this.notificationService.showInfo(
      `Starting to clone virtual machine to "${newName}"...`,
      { duration: 3000 }
    );

    return this.errorRecovery.createRecoveryStrategy(
      // Primary operation
      () => this.http.post<VM>(`${this.apiUrl}/vms/${sourceVmId}/clone`, { name: newName }),
      // Fallback operation (if needed)
      undefined,
      {
        maxAttempts: 1, // Don't retry clone operations
        showNotifications: false // We'll handle notifications manually
      }
    ).pipe(
      map(vm => {
        this.notificationService.showSuccess(
          `Virtual machine "${newName}" cloned successfully!`,
          { action: 'VIEW VM' }
        );
        return vm;
      }),
      catchError(error => {
        // Show detailed error for clone failures
        this.notificationService.showErrorDialog({
          code: error?.error?.code || 'CLONE_FAILED',
          message: `Failed to clone virtual machine to "${newName}"`,
          details: error?.error?.details,
          severity: 'high',
          retryable: false,
          user_message: `The virtual machine clone operation failed. This could be due to insufficient storage space or network issues.`
        });
        throw error;
      })
    );
  }
}