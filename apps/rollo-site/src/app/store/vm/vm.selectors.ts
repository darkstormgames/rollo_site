import { createFeatureSelector, createSelector } from '@ngrx/store';
import { VMState } from './vm.state';
import { vmAdapter } from './vm.reducer';
import { VM, VMStatus } from '../../models/vm/vm.model';

export const selectVMState = createFeatureSelector<VMState>('vms');

// Entity selectors
const {
  selectIds: selectVMIds,
  selectEntities: selectVMEntities,
  selectAll: selectAllVMs,
  selectTotal: selectVMTotal,
} = vmAdapter.getSelectors(selectVMState);

// Base selectors
export const selectVMLoading = createSelector(
  selectVMState,
  (state) => state.loading
);

export const selectVMError = createSelector(
  selectVMState,
  (state) => state.error
);

export const selectVMFilters = createSelector(
  selectVMState,
  (state) => state.filters
);

export const selectSelectedVMId = createSelector(
  selectVMState,
  (state) => state.selectedId
);

export const selectLastUpdated = createSelector(
  selectVMState,
  (state) => state.lastUpdated
);

// Entity selectors (re-export)
export { selectVMIds, selectVMEntities, selectAllVMs, selectVMTotal };

// Derived selectors
export const selectSelectedVM = createSelector(
  selectVMEntities,
  selectSelectedVMId,
  (entities, selectedId) => selectedId ? entities[selectedId] : null
);

export const selectVMById = (id: number) => createSelector(
  selectVMEntities,
  (entities) => entities[id]
);

export const selectVMsByStatus = (status: VMStatus) => createSelector(
  selectAllVMs,
  (vms) => vms.filter(vm => vm.status === status)
);

export const selectRunningVMs = createSelector(
  selectAllVMs,
  (vms) => vms.filter(vm => vm.status === VMStatus.RUNNING)
);

export const selectStoppedVMs = createSelector(
  selectAllVMs,
  (vms) => vms.filter(vm => vm.status === VMStatus.STOPPED)
);

export const selectVMsByServer = (serverId: number) => createSelector(
  selectAllVMs,
  (vms) => vms.filter(vm => vm.server.id === serverId)
);

export const selectVMStatusCounts = createSelector(
  selectAllVMs,
  (vms) => {
    const counts = {
      [VMStatus.RUNNING]: 0,
      [VMStatus.STOPPED]: 0,
      [VMStatus.PAUSED]: 0,
      [VMStatus.STARTING]: 0,
      [VMStatus.STOPPING]: 0,
      [VMStatus.ERROR]: 0,
    };
    
    vms.forEach(vm => {
      counts[vm.status] = (counts[vm.status] || 0) + 1;
    });
    
    return counts;
  }
);

export const selectFilteredVMs = createSelector(
  selectAllVMs,
  selectVMFilters,
  (vms, filters) => {
    let filteredVMs = vms;
    
    if (filters.name) {
      const searchTerm = filters.name.toLowerCase();
      filteredVMs = filteredVMs.filter(vm => 
        vm.name.toLowerCase().includes(searchTerm)
      );
    }
    
    if (filters.status) {
      filteredVMs = filteredVMs.filter(vm => vm.status === filters.status);
    }
    
    if (filters.server_id) {
      filteredVMs = filteredVMs.filter(vm => vm.server.id === filters.server_id);
    }
    
    if (filters.os_type) {
      filteredVMs = filteredVMs.filter(vm => vm.os_type === filters.os_type);
    }
    
    return filteredVMs;
  }
);

export const selectVMSummary = createSelector(
  selectAllVMs,
  selectVMStatusCounts,
  (vms, statusCounts) => ({
    total: vms.length,
    running: statusCounts[VMStatus.RUNNING],
    stopped: statusCounts[VMStatus.STOPPED],
    paused: statusCounts[VMStatus.PAUSED],
    error: statusCounts[VMStatus.ERROR],
  })
);