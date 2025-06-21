import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { Subject, takeUntil, interval, switchMap, forkJoin } from 'rxjs';

import { VMService } from '../../services/vm/vm.service';
import { ServerService } from '../../services/server/server.service';
import { VM, VMStatus, VMMetrics } from '../../models/vm/vm.model';
import { LoadingSpinner } from '../../components/shared/loading-spinner/loading-spinner';
import { StatusIndicator } from '../../components/monitoring/status-indicator/status-indicator';

interface SystemMetrics {
  totalVMs: number;
  runningVMs: number;
  totalCPU: number;
  totalMemoryMB: number;
  totalStorageGB: number;
  averageCPUUsage: number;
  averageMemoryUsage: number;
}

@Component({
  selector: 'app-monitoring-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, LoadingSpinner, StatusIndicator],
  templateUrl: './monitoring-dashboard.html',
  styleUrls: ['./monitoring-dashboard.scss']
})
export class MonitoringDashboard implements OnInit, OnDestroy {
  vms: VM[] = [];
  vmMetrics: Map<number, VMMetrics> = new Map();
  systemMetrics: SystemMetrics | null = null;
  loading = false;
  error: string | null = null;

  private destroy$ = new Subject<void>();

  constructor(
    private vmService: VMService,
    private serverService: ServerService
  ) {}

  ngOnInit(): void {
    this.loadData();
    this.startMetricsPolling();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadData(): void {
    this.loading = true;
    this.error = null;

    // Load VMs first, then load metrics for each
    this.vmService.getVMs({ per_page: 100 }).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (response) => {
        this.vms = response.vms;
        this.loadVMMetrics();
        this.loading = false;
      },
      error: (error) => {
        this.error = error.error || 'Failed to load VMs';
        this.loading = false;
      }
    });
  }

  loadVMMetrics(): void {
    if (this.vms.length === 0) return;

    // Load metrics for all VMs
    const metricsRequests = this.vms.map(vm => 
      this.vmService.getVMMetrics(vm.id)
    );

    forkJoin(metricsRequests).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (metrics) => {
        // Update metrics map
        metrics.forEach((metric, index) => {
          if (metric) {
            this.vmMetrics.set(this.vms[index].id, metric);
          }
        });
        this.calculateSystemMetrics();
      },
      error: (error) => {
        console.warn('Failed to load some VM metrics:', error);
        this.calculateSystemMetrics(); // Calculate with available data
      }
    });
  }

  startMetricsPolling(): void {
    // Poll metrics every 30 seconds
    interval(30000).pipe(
      switchMap(() => this.vmService.getVMs({ per_page: 100 })),
      takeUntil(this.destroy$)
    ).subscribe({
      next: (response) => {
        this.vms = response.vms;
        this.loadVMMetrics();
      },
      error: (error) => {
        console.warn('Failed to poll VM data:', error);
      }
    });
  }

  calculateSystemMetrics(): void {
    const runningVMs = this.vms.filter(vm => vm.status === VMStatus.RUNNING);
    
    let totalCPUUsage = 0;
    let totalMemoryUsage = 0;
    let metricsCount = 0;

    runningVMs.forEach(vm => {
      const metrics = this.vmMetrics.get(vm.id);
      if (metrics) {
        if (metrics.cpu_usage_percent !== undefined) {
          totalCPUUsage += metrics.cpu_usage_percent;
          metricsCount++;
        }
        if (metrics.memory_usage_percent !== undefined) {
          totalMemoryUsage += metrics.memory_usage_percent;
        }
      }
    });

    this.systemMetrics = {
      totalVMs: this.vms.length,
      runningVMs: runningVMs.length,
      totalCPU: this.vms.reduce((sum, vm) => sum + vm.resources.cpu_cores, 0),
      totalMemoryMB: this.vms.reduce((sum, vm) => sum + vm.resources.memory_mb, 0),
      totalStorageGB: this.vms.reduce((sum, vm) => sum + vm.resources.disk_gb, 0),
      averageCPUUsage: metricsCount > 0 ? Math.round(totalCPUUsage / metricsCount) : 0,
      averageMemoryUsage: runningVMs.length > 0 ? Math.round(totalMemoryUsage / runningVMs.length) : 0
    };
  }

  getVMMetrics(vmId: number): VMMetrics | null {
    return this.vmMetrics.get(vmId) || null;
  }

  getResourceUsageColor(percentage: number): string {
    if (percentage < 50) return '#27ae60';
    if (percentage < 80) return '#f39c12';
    return '#e74c3c';
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
}