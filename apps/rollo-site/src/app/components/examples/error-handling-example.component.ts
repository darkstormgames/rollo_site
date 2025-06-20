/**
 * Example component showing how to integrate with the error handling system
 */

import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { Subject } from 'rxjs';
import { takeUntil, finalize } from 'rxjs/operators';

import { VmIntegrationExampleService } from '../../services/vm/vm-integration-example.service';
import { NotificationService } from '../../services/shared/notification.service';
import { OfflineDetectionService } from '../../services/shared/offline-detection.service';
import { LoadingService } from '../../services/shared/loading.service';

interface VM {
  id: string;
  name: string;
  status: string;
  server_id: string;
  cpu_cores: number;
  memory_mb: number;
}

@Component({
  selector: 'app-error-handling-example',
  standalone: true,
  imports: [
    CommonModule,
    MatButtonModule,
    MatCardModule,
    MatIconModule,
    MatProgressSpinnerModule
  ],
  template: `
    <div class="error-handling-demo">
      <mat-card>
        <mat-card-header>
          <mat-card-title>Error Handling System Demo</mat-card-title>
          <mat-card-subtitle>
            This demo shows various error handling scenarios
          </mat-card-subtitle>
        </mat-card-header>

        <mat-card-content>
          <!-- Connection Status -->
          <div class="status-section">
            <h3>Connection Status</h3>
            <div class="status-indicator" [class.online]="isOnline" [class.offline]="!isOnline">
              <mat-icon>{{ isOnline ? 'wifi' : 'wifi_off' }}</mat-icon>
              {{ isOnline ? 'Online' : 'Offline' }}
            </div>
          </div>

          <!-- VM List -->
          <div class="vm-section">
            <h3>Virtual Machines</h3>
            <div class="vm-actions">
              <button mat-raised-button 
                      color="primary"
                      (click)="loadVMs()"
                      [disabled]="loading">
                <mat-icon>refresh</mat-icon>
                Reload VMs
              </button>

              <button mat-raised-button 
                      color="accent"
                      (click)="createTestVM()"
                      [disabled]="loading || !isOnline">
                <mat-icon>add</mat-icon>
                Create Test VM
              </button>
            </div>

            <div class="vm-list" *ngIf="!loading">
              <div class="vm-item" *ngFor="let vm of vms">
                <div class="vm-info">
                  <strong>{{ vm.name }}</strong>
                  <span class="vm-status" [class]="'status-' + vm.status.toLowerCase()">
                    {{ vm.status }}
                  </span>
                </div>
                <div class="vm-actions">
                  <button mat-icon-button 
                          (click)="startVM(vm.id, vm.name)"
                          [disabled]="vm.status === 'running'"
                          title="Start VM">
                    <mat-icon>play_arrow</mat-icon>
                  </button>
                  <button mat-icon-button 
                          (click)="deleteVM(vm.id, vm.name)"
                          color="warn"
                          title="Delete VM">
                    <mat-icon>delete</mat-icon>
                  </button>
                </div>
              </div>

              <div class="empty-state" *ngIf="vms.length === 0">
                <mat-icon>computer</mat-icon>
                <p>No virtual machines found</p>
              </div>
            </div>

            <div class="loading-state" *ngIf="loading">
              <mat-spinner diameter="40"></mat-spinner>
              <p>Loading virtual machines...</p>
            </div>
          </div>

          <!-- Error Testing -->
          <div class="error-testing-section">
            <h3>Error Testing</h3>
            <p>Test different error scenarios:</p>
            
            <div class="test-buttons">
              <button mat-stroked-button (click)="testSuccess()">
                <mat-icon>check_circle</mat-icon>
                Success Notification
              </button>

              <button mat-stroked-button (click)="testWarning()">
                <mat-icon>warning</mat-icon>
                Warning Notification
              </button>

              <button mat-stroked-button (click)="testError()">
                <mat-icon>error</mat-icon>
                Error Notification
              </button>

              <button mat-stroked-button (click)="testCriticalError()">
                <mat-icon>dangerous</mat-icon>
                Critical Error Dialog
              </button>

              <button mat-stroked-button (click)="testRetryableError()">
                <mat-icon>refresh</mat-icon>
                Retryable Error
              </button>

              <button mat-stroked-button (click)="testOfflineError()" [disabled]="isOnline">
                <mat-icon>wifi_off</mat-icon>
                Offline Error
              </button>
            </div>
          </div>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [`
    .error-handling-demo {
      padding: 16px;
      max-width: 800px;
      margin: 0 auto;
    }

    .status-section,
    .vm-section,
    .error-testing-section {
      margin-bottom: 24px;
    }

    .status-indicator {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 4px;
      font-weight: 500;
    }

    .status-indicator.online {
      background-color: #e8f5e8;
      color: #2e7d2e;
    }

    .status-indicator.offline {
      background-color: #ffebee;
      color: #c62828;
    }

    .vm-actions {
      display: flex;
      gap: 12px;
      margin-bottom: 16px;
    }

    .vm-list {
      border: 1px solid #e0e0e0;
      border-radius: 4px;
      overflow: hidden;
    }

    .vm-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 16px;
      border-bottom: 1px solid #e0e0e0;
    }

    .vm-item:last-child {
      border-bottom: none;
    }

    .vm-info {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .vm-status {
      font-size: 12px;
      padding: 2px 8px;
      border-radius: 12px;
      text-transform: uppercase;
    }

    .vm-status.status-running {
      background-color: #e8f5e8;
      color: #2e7d2e;
    }

    .vm-status.status-stopped {
      background-color: #ffebee;
      color: #c62828;
    }

    .vm-actions {
      display: flex;
      gap: 4px;
    }

    .empty-state {
      text-align: center;
      padding: 24px;
      color: #666;
    }

    .empty-state mat-icon {
      font-size: 48px;
      width: 48px;
      height: 48px;
      margin-bottom: 8px;
      opacity: 0.5;
    }

    .loading-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 24px;
      gap: 16px;
    }

    .test-buttons {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 12px;
    }

    .test-buttons button {
      display: flex;
      align-items: center;
      gap: 8px;
      justify-content: flex-start;
    }
  `]
})
export class ErrorHandlingExampleComponent implements OnInit, OnDestroy {
  
  vms: VM[] = [];
  loading = false;
  isOnline = true;
  private destroy$ = new Subject<void>();

  constructor(
    private vmService: VmIntegrationExampleService,
    private notificationService: NotificationService,
    private offlineDetection: OfflineDetectionService,
    private loadingService: LoadingService
  ) {}

  ngOnInit(): void {
    // Monitor online status
    this.offlineDetection.isOnline$
      .pipe(takeUntil(this.destroy$))
      .subscribe(isOnline => {
        this.isOnline = isOnline;
      });

    // Load initial data
    this.loadVMs();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadVMs(): void {
    this.loading = true;
    this.loadingService.setLoadingForOperation('load-vms', true);

    this.vmService.getVMs()
      .pipe(
        takeUntil(this.destroy$),
        finalize(() => {
          this.loading = false;
          this.loadingService.setLoadingForOperation('load-vms', false);
        })
      )
      .subscribe({
        next: (vms) => {
          this.vms = vms;
        },
        error: (error) => {
          console.error('Failed to load VMs:', error);
          // Error handling is done by the service and interceptor
        }
      });
  }

  createTestVM(): void {
    const vmData = {
      name: `test-vm-${Date.now()}`,
      server_id: '1',
      cpu_cores: 2,
      memory_mb: 2048,
      disk_gb: 20
    };

    this.vmService.createVM(vmData)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (vm) => {
          this.vms = [...this.vms, vm];
        },
        error: (error) => {
          console.error('Failed to create VM:', error);
        }
      });
  }

  startVM(vmId: string, vmName: string): void {
    // Simulate VM start
    this.notificationService.showInfo(`Starting virtual machine "${vmName}"...`);
    
    // Update local state optimistically
    this.vms = this.vms.map(vm => 
      vm.id === vmId ? { ...vm, status: 'running' } : vm
    );
  }

  deleteVM(vmId: string, vmName: string): void {
    this.vmService.deleteVM(vmId, vmName)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.vms = this.vms.filter(vm => vm.id !== vmId);
        },
        error: (error) => {
          console.error('Failed to delete VM:', error);
        }
      });
  }

  // Test notification methods
  testSuccess(): void {
    this.notificationService.showSuccess('Operation completed successfully!');
  }

  testWarning(): void {
    this.notificationService.showWarning('This is a warning message that will auto-dismiss.');
  }

  testError(): void {
    this.notificationService.showError('This is an error message that requires dismissal.');
  }

  testCriticalError(): void {
    this.notificationService.showErrorDialog({
      code: 'CRITICAL_SYSTEM_ERROR',
      message: 'A critical system error has occurred',
      details: {
        component: 'ErrorHandlingDemo',
        timestamp: new Date().toISOString(),
        stack_trace: 'Sample stack trace information'
      },
      category: 'system',
      severity: 'critical',
      retryable: false,
      user_message: 'A critical error occurred in the demo. This is just a test.'
    });
  }

  testRetryableError(): void {
    this.notificationService.showError('Connection timeout occurred. You can retry this operation.', {
      action: 'RETRY'
    });
  }

  testOfflineError(): void {
    if (!this.isOnline) {
      this.notificationService.showError('You are currently offline. Please check your connection.');
    }
  }
}