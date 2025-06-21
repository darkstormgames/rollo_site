import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { Subject, takeUntil, forkJoin } from 'rxjs';

import { VMService } from '../../services/vm/vm.service';
import { ServerService } from '../../services/server/server.service';
import { VM, VMStatus } from '../../models/vm/vm.model';

interface DashboardStats {
  totalVMs: number;
  runningVMs: number;
  stoppedVMs: number;
  totalServers: number;
  onlineServers: number;
  totalCPUs: number;
  totalMemoryGB: number;
  totalStorageGB: number;
}

@Component({
  selector: 'app-dashboard-overview',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './dashboard-overview.html',
  styleUrls: ['./dashboard-overview.scss']
})
export class DashboardOverview implements OnInit, OnDestroy {
  stats: DashboardStats = {
    totalVMs: 0,
    runningVMs: 0,
    stoppedVMs: 0,
    totalServers: 0,
    onlineServers: 0,
    totalCPUs: 0,
    totalMemoryGB: 0,
    totalStorageGB: 0
  };

  recentVMs: VM[] = [];
  loading = false;
  error: string | null = null;

  private destroy$ = new Subject<void>();

  constructor(
    private vmService: VMService,
    private serverService: ServerService
  ) {}

  ngOnInit(): void {
    this.loadDashboardData();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadDashboardData(): void {
    this.loading = true;
    this.error = null;

    // Load VMs and servers data
    forkJoin({
      vms: this.vmService.getVMs({ per_page: 50 }),
      servers: this.serverService.getServers({ per_page: 50 })
    }).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: ({ vms, servers }) => {
        this.calculateStats(vms.vms, servers.servers);
        this.recentVMs = vms.vms.slice(0, 5); // Get 5 most recent VMs
        this.loading = false;
      },
      error: (error) => {
        this.error = error.error || 'Failed to load dashboard data';
        this.loading = false;
      }
    });
  }

  private calculateStats(vms: VM[], servers: any[]): void {
    this.stats = {
      totalVMs: vms.length,
      runningVMs: vms.filter(vm => vm.status === VMStatus.RUNNING).length,
      stoppedVMs: vms.filter(vm => vm.status === VMStatus.STOPPED).length,
      totalServers: servers.length,
      onlineServers: servers.filter(server => server.status === 'online').length,
      totalCPUs: vms.reduce((sum, vm) => sum + vm.resources.cpu_cores, 0),
      totalMemoryGB: Math.round(vms.reduce((sum, vm) => sum + vm.resources.memory_mb, 0) / 1024),
      totalStorageGB: vms.reduce((sum, vm) => sum + vm.resources.disk_gb, 0)
    };
  }

  getStatusClass(status: VMStatus): string {
    switch (status) {
      case VMStatus.RUNNING:
        return 'status-running';
      case VMStatus.STOPPED:
        return 'status-stopped';
      case VMStatus.PAUSED:
        return 'status-paused';
      case VMStatus.ERROR:
        return 'status-error';
      default:
        return 'status-unknown';
    }
  }

  getUptimePercentage(): number {
    if (this.stats.totalVMs === 0) return 0;
    return Math.round((this.stats.runningVMs / this.stats.totalVMs) * 100);
  }

  getServerHealthPercentage(): number {
    if (this.stats.totalServers === 0) return 0;
    return Math.round((this.stats.onlineServers / this.stats.totalServers) * 100);
  }
}