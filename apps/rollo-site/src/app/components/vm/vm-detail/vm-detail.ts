import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Subject, takeUntil, interval, switchMap } from 'rxjs';

import { VMService } from '../../../services/vm/vm.service';
import { VM, VMStatus, VMMetrics } from '../../../models/vm/vm.model';
import { LoadingSpinnerComponent } from '../../shared/loading-spinner/loading-spinner.component';

@Component({
  selector: 'app-vm-detail',
  standalone: true,
  imports: [CommonModule, RouterLink, LoadingSpinnerComponent],
  templateUrl: './vm-detail.html',
  styleUrls: ['./vm-detail.scss']
})
export class VmDetail implements OnInit, OnDestroy {
  vm: VM | null = null;
  metrics: VMMetrics | null = null;
  loading = false;
  error: string | null = null;
  vmId: number = 0;

  private destroy$ = new Subject<void>();
  VMStatus = VMStatus;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private vmService: VMService
  ) {}

  ngOnInit(): void {
    this.route.params.pipe(
      takeUntil(this.destroy$)
    ).subscribe(params => {
      this.vmId = parseInt(params['id']);
      if (this.vmId) {
        this.loadVM();
        this.startMetricsPolling();
      }
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadVM(): void {
    this.loading = true;
    this.error = null;

    this.vmService.getVM(this.vmId).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (vm) => {
        this.vm = vm;
        this.loading = false;
      },
      error: (error) => {
        this.error = error.error || 'Failed to load VM details';
        this.loading = false;
      }
    });
  }

  startMetricsPolling(): void {
    // Poll metrics every 30 seconds
    interval(30000).pipe(
      switchMap(() => this.vmService.getVMMetrics(this.vmId)),
      takeUntil(this.destroy$)
    ).subscribe({
      next: (metrics) => {
        this.metrics = metrics;
      },
      error: (error) => {
        console.warn('Failed to load VM metrics:', error);
      }
    });

    // Load initial metrics
    this.vmService.getVMMetrics(this.vmId).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (metrics) => {
        this.metrics = metrics;
      },
      error: (error) => {
        console.warn('Failed to load initial VM metrics:', error);
      }
    });
  }

  getStatusClass(status: VMStatus): string {
    switch (status) {
      case VMStatus.RUNNING:
        return 'status-running';
      case VMStatus.STOPPED:
        return 'status-stopped';
      case VMStatus.PAUSED:
        return 'status-paused';
      case VMStatus.STARTING:
      case VMStatus.STOPPING:
        return 'status-transitioning';
      case VMStatus.ERROR:
        return 'status-error';
      default:
        return 'status-unknown';
    }
  }

  startVM(): void {
    if (!this.vm) return;
    
    this.vmService.startVM(this.vm.id).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: () => {
        this.loadVM(); // Refresh VM details
      },
      error: (error) => {
        this.error = error.error || 'Failed to start VM';
      }
    });
  }

  stopVM(): void {
    if (!this.vm) return;
    
    this.vmService.stopVM(this.vm.id).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: () => {
        this.loadVM(); // Refresh VM details
      },
      error: (error) => {
        this.error = error.error || 'Failed to stop VM';
      }
    });
  }

  pauseVM(): void {
    if (!this.vm) return;
    
    this.vmService.pauseVM(this.vm.id).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: () => {
        this.loadVM(); // Refresh VM details
      },
      error: (error) => {
        this.error = error.error || 'Failed to pause VM';
      }
    });
  }

  rebootVM(): void {
    if (!this.vm) return;
    
    if (confirm(`Are you sure you want to reboot VM "${this.vm.name}"?`)) {
      this.vmService.restartVM(this.vm.id).pipe(
        takeUntil(this.destroy$)
      ).subscribe({
        next: () => {
          this.loadVM(); // Refresh VM details
        },
        error: (error) => {
          this.error = error.error || 'Failed to reboot VM';
        }
      });
    }
  }

  deleteVM(): void {
    if (!this.vm) return;
    
    if (confirm(`Are you sure you want to delete VM "${this.vm.name}"? This action cannot be undone.`)) {
      this.vmService.deleteVM(this.vm.id).pipe(
        takeUntil(this.destroy$)
      ).subscribe({
        next: () => {
          this.router.navigate(['/dashboard/vms']);
        },
        error: (error) => {
          this.error = error.error || 'Failed to delete VM';
        }
      });
    }
  }

  cloneVM(): void {
    if (!this.vm) return;
    
    const newName = prompt(`Enter name for cloned VM:`, `${this.vm.name}-clone`);
    if (newName) {
      this.vmService.cloneVM(this.vm.id, newName).pipe(
        takeUntil(this.destroy$)
      ).subscribe({
        next: (clonedVM) => {
          this.router.navigate(['/dashboard/vms', clonedVM.id]);
        },
        error: (error) => {
          this.error = error.error || 'Failed to clone VM';
        }
      });
    }
  }

  formatMemory(mb: number): string {
    if (mb >= 1024) {
      return `${(mb / 1024).toFixed(1)} GB`;
    }
    return `${mb} MB`;
  }

  formatBytes(bytes: number): string {
    if (!bytes) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  getMemoryUsagePercentage(): number {
    if (!this.metrics || !this.vm) return 0;
    return Math.round((this.metrics.memory_used_mb || 0) / this.vm.resources.memory_mb * 100);
  }
}