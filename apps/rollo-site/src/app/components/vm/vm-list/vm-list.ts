import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { Subject, takeUntil, debounceTime, distinctUntilChanged, Observable } from 'rxjs';
import { Store } from '@ngrx/store';

import { VMService } from '../../../services/vm/vm.service';
import { VMFacade } from '../../../services/vm/vm-facade.service';
import { VM, VMStatus, VMFilter, OSType } from '../../../models/vm/vm.model';
import { AppState } from '../../../store/app.state';
import { vmActions } from '../../../store/vm/vm.actions';
import { 
  selectAllVMs, 
  selectVMLoading, 
  selectVMError, 
  selectFilteredVMs,
  selectVMSummary 
} from '../../../store/vm/vm.selectors';

@Component({
  selector: 'app-vm-list',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './vm-list.html',
  styleUrls: ['./vm-list.scss']
})
export class VmList implements OnInit, OnDestroy {
  // Observables from store
  vms$: Observable<VM[]>;
  loading$: Observable<boolean>;
  error$: Observable<Error | null>;
  vmSummary$: Observable<any>;
  
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

  constructor(
    private store: Store<AppState>,
    private vmService: VMService,
    private vmFacade: VMFacade
  ) {
    // Initialize observables - can use either store directly or facade
    this.vms$ = this.vmFacade.filteredVMs$; // Using facade
    this.loading$ = this.store.select(selectVMLoading); // Using store directly
    this.error$ = this.store.select(selectVMError);
    this.vmSummary$ = this.store.select(selectVMSummary);
  }

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
      this.updateFilters();
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadVMs(): void {
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

    // Using facade for cleaner API
    this.vmFacade.loadVMs(filters);
  }

  updateFilters(): void {
    const filters: VMFilter = {};

    if (this.searchTerm) {
      filters.name = this.searchTerm;
    }
    if (this.statusFilter) {
      filters.status = this.statusFilter;
    }
    if (this.osTypeFilter) {
      filters.os_type = this.osTypeFilter;
    }

    // Using facade for filter updates
    this.vmFacade.setFilters(filters);
  }

  onSearch(event: Event): void {
    const target = event.target as HTMLInputElement;
    this.searchSubject.next(target.value);
  }

  onFilterChange(): void {
    this.currentPage = 1;
    this.updateFilters();
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
    // Subscribe to vms$ to get current list for selection
    this.vms$.pipe(takeUntil(this.destroy$)).subscribe(vms => {
      if (this.selectedVMs.size === vms.length) {
        this.selectedVMs.clear();
      } else {
        vms.forEach(vm => this.selectedVMs.add(vm.id));
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

  getSortDirection(column: string): string | null {
    if (this.sortBy !== column) {
      return null;
    }
    return this.sortDirection;
  }

  startVM(vm: VM): void {
    this.vmFacade.startVM(vm.id);
  }

  stopVM(vm: VM): void {
    this.vmFacade.stopVM(vm.id);
  }

  deleteVM(vm: VM): void {
    if (confirm(`Are you sure you want to delete VM "${vm.name}"?`)) {
      this.vmFacade.deleteVM(vm.id);
    }
  }

  bulkStart(): void {
    if (this.selectedVMs.size === 0) return;
    
    this.vmFacade.bulkStartVMs(Array.from(this.selectedVMs));
    this.selectedVMs.clear();
  }

  bulkStop(): void {
    if (this.selectedVMs.size === 0) return;
    
    this.vmFacade.bulkStopVMs(Array.from(this.selectedVMs));
    this.selectedVMs.clear();
  }

  bulkDelete(): void {
    if (this.selectedVMs.size === 0) return;
    
    if (confirm(`Are you sure you want to delete ${this.selectedVMs.size} VMs?`)) {
      this.vmFacade.bulkDeleteVMs(Array.from(this.selectedVMs));
      this.selectedVMs.clear();
    }
  }
}