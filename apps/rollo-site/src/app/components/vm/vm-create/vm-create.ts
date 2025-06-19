import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, NgForm } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { Subject, takeUntil, forkJoin } from 'rxjs';

import { VMService } from '../../../services/vm/vm.service';
import { ServerService } from '../../../services/server/server.service';
import { VMCreate, OSType } from '../../../models/vm/vm.model';
import { Server } from '../../../models/server/server.model';

interface CreateVMFormData {
  name: string;
  server_id: number | null;
  os_type: OSType;
  os_version: string;
  cpu_cores: number;
  memory_mb: number;
  disk_gb: number;
  vnc_enabled: boolean;
  network_config: {
    interface_type: string;
    network_name: string;
  };
}

@Component({
  selector: 'app-vm-create',
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './vm-create.html',
  styleUrl: './vm-create.scss'
})
export class VmCreate implements OnInit, OnDestroy {
  currentStep = 1;
  totalSteps = 4;
  loading = false;
  error: string | null = null;
  creating = false;

  servers: Server[] = [];
  
  formData: CreateVMFormData = {
    name: '',
    server_id: null,
    os_type: OSType.LINUX,
    os_version: '',
    cpu_cores: 2,
    memory_mb: 2048,
    disk_gb: 20,
    vnc_enabled: true,
    network_config: {
      interface_type: 'bridge',
      network_name: 'default'
    }
  };

  // Enum references for template
  OSType = OSType;

  // Predefined options
  osVersions = {
    [OSType.LINUX]: [
      'Ubuntu 22.04 LTS',
      'Ubuntu 20.04 LTS',
      'CentOS 8',
      'Debian 11',
      'Fedora 36',
      'Rocky Linux 8'
    ],
    [OSType.WINDOWS]: [
      'Windows Server 2022',
      'Windows Server 2019',
      'Windows 11',
      'Windows 10'
    ],
    [OSType.OTHER]: [
      'FreeBSD 13',
      'OpenBSD 7.1',
      'Other'
    ]
  };

  cpuOptions = [1, 2, 4, 6, 8, 12, 16];
  memoryOptions = [1024, 2048, 4096, 8192, 16384, 32768]; // MB
  diskOptions = [10, 20, 40, 80, 120, 250, 500]; // GB

  private destroy$ = new Subject<void>();

  constructor(
    private vmService: VMService,
    private serverService: ServerService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadServers();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadServers(): void {
    this.loading = true;
    this.error = null;

    this.serverService.getServers({ per_page: 100 }).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (response) => {
        this.servers = response.servers.filter(server => server.status === 'online');
        this.loading = false;
      },
      error: (error) => {
        this.error = error.error || 'Failed to load servers';
        this.loading = false;
      }
    });
  }

  nextStep(): void {
    if (this.currentStep < this.totalSteps) {
      this.currentStep++;
    }
  }

  previousStep(): void {
    if (this.currentStep > 1) {
      this.currentStep--;
    }
  }

  canProceedFromStep(step: number): boolean {
    switch (step) {
      case 1:
        return !!(this.formData.name && this.formData.server_id);
      case 2:
        return !!(this.formData.os_type && this.formData.os_version);
      case 3:
        return this.formData.cpu_cores > 0 && this.formData.memory_mb > 0 && this.formData.disk_gb > 0;
      case 4:
        return true;
      default:
        return false;
    }
  }

  getAvailableOSVersions(): string[] {
    return this.osVersions[this.formData.os_type] || [];
  }

  onOSTypeChange(): void {
    this.formData.os_version = '';
  }

  formatMemory(mb: number): string {
    if (mb >= 1024) {
      return `${mb / 1024} GB`;
    }
    return `${mb} MB`;
  }

  getStepTitle(step: number): string {
    switch (step) {
      case 1: return 'Basic Information';
      case 2: return 'Operating System';
      case 3: return 'Resources';
      case 4: return 'Network & Review';
      default: return '';
    }
  }

  createVM(): void {
    if (!this.canProceedFromStep(this.currentStep) || !this.formData.server_id) {
      return;
    }

    this.creating = true;
    this.error = null;

    const vmCreate: VMCreate = {
      name: this.formData.name,
      server_id: this.formData.server_id,
      os_type: this.formData.os_type,
      os_version: this.formData.os_version,
      cpu_cores: this.formData.cpu_cores,
      memory_mb: this.formData.memory_mb,
      disk_gb: this.formData.disk_gb,
      vnc_enabled: this.formData.vnc_enabled,
      network_config: this.formData.network_config
    };

    this.vmService.createVM(vmCreate).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (vm) => {
        this.creating = false;
        this.router.navigate(['/dashboard/vms', vm.id]);
      },
      error: (error) => {
        this.error = error.error || 'Failed to create VM';
        this.creating = false;
      }
    });
  }

  cancel(): void {
    this.router.navigate(['/dashboard/vms']);
  }

  getSelectedServer(): Server | null {
    return this.servers.find(server => server.id === this.formData.server_id) || null;
  }

  getTotalResourcesText(): string {
    return `${this.formData.cpu_cores} CPU, ${this.formatMemory(this.formData.memory_mb)}, ${this.formData.disk_gb} GB Storage`;
  }
}