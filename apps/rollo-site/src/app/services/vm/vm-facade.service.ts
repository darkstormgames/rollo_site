import { Injectable } from '@angular/core';
import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';

import { AppState } from '../../store/app.state';
import { vmActions } from '../../store/vm/vm.actions';
import { 
  selectAllVMs, 
  selectVMLoading, 
  selectVMError, 
  selectFilteredVMs,
  selectVMSummary,
  selectVMById,
  selectVMsByStatus,
  selectRunningVMs 
} from '../../store/vm/vm.selectors';
import { VM, VMCreate, VMUpdate, VMFilter, VMStatus } from '../../models/vm/vm.model';

/**
 * VM Facade Service
 * 
 * Provides a clean API for components to interact with VM state
 * without directly coupling to NgRx store implementation details.
 */
@Injectable({
  providedIn: 'root'
})
export class VMFacade {

  constructor(private store: Store<AppState>) {}

  // Selectors - initialized after store injection
  get vms$() { return this.store.select(selectAllVMs); }
  get filteredVMs$() { return this.store.select(selectFilteredVMs); }
  get loading$() { return this.store.select(selectVMLoading); }
  get error$() { return this.store.select(selectVMError); }
  get summary$() { return this.store.select(selectVMSummary); }
  get runningVMs$() { return this.store.select(selectRunningVMs); }

  // VM Data Loading
  loadVMs(filters?: VMFilter): void {
    this.store.dispatch(vmActions.loadVMs({ filters: filters || {} }));
  }

  // VM Operations
  createVM(vmData: VMCreate): void {
    this.store.dispatch(vmActions.createVM({ vmData }));
  }

  updateVM(id: number, changes: VMUpdate): void {
    this.store.dispatch(vmActions.updateVM({ id, changes }));
  }

  deleteVM(id: number): void {
    this.store.dispatch(vmActions.deleteVM({ id }));
  }

  // VM Lifecycle Operations
  startVM(id: number): void {
    this.store.dispatch(vmActions.startVM({ id }));
  }

  stopVM(id: number, force = false): void {
    this.store.dispatch(vmActions.stopVM({ id, force }));
  }

  restartVM(id: number, force = false): void {
    this.store.dispatch(vmActions.restartVM({ id, force }));
  }

  pauseVM(id: number): void {
    this.store.dispatch(vmActions.pauseVM({ id }));
  }

  resumeVM(id: number): void {
    this.store.dispatch(vmActions.resumeVM({ id }));
  }

  // Selection and Filtering
  selectVM(id: string): void {
    this.store.dispatch(vmActions.selectVM({ id }));
  }

  clearSelection(): void {
    this.store.dispatch(vmActions.clearSelection());
  }

  setFilters(filters: VMFilter): void {
    this.store.dispatch(vmActions.setFilters({ filters }));
  }

  clearFilters(): void {
    this.store.dispatch(vmActions.clearFilters());
  }

  // Specific Selectors
  getVMById(id: number): Observable<VM | undefined> {
    return this.store.select(selectVMById(id));
  }

  getVMsByStatus(status: VMStatus): Observable<VM[]> {
    return this.store.select(selectVMsByStatus(status));
  }

  // Bulk Operations
  bulkStartVMs(vmIds: number[]): void {
    vmIds.forEach(id => this.startVM(id));
  }

  bulkStopVMs(vmIds: number[]): void {
    vmIds.forEach(id => this.stopVM(id));
  }

  bulkDeleteVMs(vmIds: number[]): void {
    vmIds.forEach(id => this.deleteVM(id));
  }
}