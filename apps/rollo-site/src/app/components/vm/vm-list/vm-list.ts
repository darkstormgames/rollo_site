import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { Subject, takeUntil, debounceTime, distinctUntilChanged } from 'rxjs';

import { VMService } from '../../../services/vm/vm.service';
import { VM, VMStatus, VMFilter, OSType } from '../../../models/vm/vm.model';

@Component({
  selector: 'app-vm-list',
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './vm-list.html',
  styleUrl: './vm-list.scss'
})
export class VmList implements OnInit, OnDestroy {
  vms: VM[] = [];
  loading = false;
  error: string | null = null;
  selectedVMs: Set<number> = new Set();
  
  // Pagination
  currentPage = 1;
  totalPages = 1;
  perPage = 10;
  total = 0;

  // Filtering and search
  searchTerm = '';
  statusFilter: VMStatus | '' = '';
  osTypeFilter: OSType | '' = '';
  serverFilter = '';

  // Sorting
  sortBy = 'name';
  sortDirection: 'asc' | 'desc' = 'asc';

  // For cleanup
  private destroy$ = new Subject<void>();
  private searchSubject = new Subject<string>();

  // Enum references for template
  VMStatus = VMStatus;
  OSType = OSType;
  Math = Math;

  constructor(private vmService: VMService) {}

  ngOnInit(): void {
    this.loadVMs();
    
    // Setup search debouncing
    this.searchSubject.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      takeUntil(this.destroy$)
    ).subscribe(searchTerm => {
      this.searchTerm = searchTerm;
      this.currentPage = 1;
      this.loadVMs();
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadVMs(): void {
    this.loading = true;
    this.error = null;

    const filters: VMFilter = {
      page: this.currentPage,
      per_page: this.perPage
    };

    if (this.searchTerm) {
      filters.name = this.searchTerm;
    }
    if (this.statusFilter) {
      filters.status = this.statusFilter;
    }
    if (this.osTypeFilter) {
      filters.os_type = this.osTypeFilter;
    }

    this.vmService.getVMs(filters).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (response) => {
        this.vms = response.vms;
        this.total = response.total;
        this.totalPages = response.total_pages;
        this.loading = false;
      },
      error: (error) => {
        this.error = error.error || 'Failed to load VMs';
        this.loading = false;
      }
    });
  }

  onSearch(event: Event): void {
    const target = event.target as HTMLInputElement;
    this.searchSubject.next(target.value);
  }

  onFilterChange(): void {
    this.currentPage = 1;
    this.loadVMs();
  }

  onSort(column: string): void {
    if (this.sortBy === column) {
      this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      this.sortBy = column;
      this.sortDirection = 'asc';
    }
    this.loadVMs();
  }

  onPageChange(page: number): void {
    this.currentPage = page;
    this.loadVMs();
  }

  toggleVMSelection(vmId: number): void {
    if (this.selectedVMs.has(vmId)) {
      this.selectedVMs.delete(vmId);
    } else {
      this.selectedVMs.add(vmId);
    }
  }

  selectAllVMs(): void {
    if (this.selectedVMs.size === this.vms.length) {
      this.selectedVMs.clear();
    } else {
      this.vms.forEach(vm => this.selectedVMs.add(vm.id));
    }
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

  startVM(vm: VM): void {
    this.vmService.startVM(vm.id).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: () => {
        this.loadVMs(); // Refresh the list
      },
      error: (error) => {
        this.error = error.error || 'Failed to start VM';
      }
    });
  }

  stopVM(vm: VM): void {
    this.vmService.stopVM(vm.id).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: () => {
        this.loadVMs(); // Refresh the list
      },
      error: (error) => {
        this.error = error.error || 'Failed to stop VM';
      }
    });
  }

  deleteVM(vm: VM): void {
    if (confirm(`Are you sure you want to delete VM "${vm.name}"?`)) {
      this.vmService.deleteVM(vm.id).pipe(
        takeUntil(this.destroy$)
      ).subscribe({
        next: () => {
          this.loadVMs(); // Refresh the list
        },
        error: (error) => {
          this.error = error.error || 'Failed to delete VM';
        }
      });
    }
  }

  bulkStart(): void {
    if (this.selectedVMs.size === 0) return;
    
    // Implementation for bulk operations would go here
    console.log('Bulk start:', Array.from(this.selectedVMs));
  }

  bulkStop(): void {
    if (this.selectedVMs.size === 0) return;
    
    // Implementation for bulk operations would go here
    console.log('Bulk stop:', Array.from(this.selectedVMs));
  }

  bulkDelete(): void {
    if (this.selectedVMs.size === 0) return;
    
    if (confirm(`Are you sure you want to delete ${this.selectedVMs.size} VMs?`)) {
      // Implementation for bulk operations would go here
      console.log('Bulk delete:', Array.from(this.selectedVMs));
    }
  }
}