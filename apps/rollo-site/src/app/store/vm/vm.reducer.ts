import { createReducer, on } from '@ngrx/store';
import { createEntityAdapter, EntityAdapter } from '@ngrx/entity';
import { VM } from '../../models/vm/vm.model';
import { VMState, initialVMState } from './vm.state';
import { vmActions } from './vm.actions';

export const vmAdapter: EntityAdapter<VM> = createEntityAdapter<VM>({
  selectId: (vm: VM) => vm.id,
  sortComparer: (a: VM, b: VM) => a.name.localeCompare(b.name),
});

const vmEntityState = vmAdapter.getInitialState(initialVMState);

export const vmReducer = createReducer(
  vmEntityState,
  
  // Load VMs
  on(vmActions.loadVMs, (state, { filters }) => ({
    ...state,
    loading: true,
    error: null,
    filters: filters || state.filters,
  })),
  
  on(vmActions.loadVMsSuccess, (state, { vms }) => 
    vmAdapter.setAll(vms, {
      ...state,
      loading: false,
      error: null,
      lastUpdated: new Date().toISOString(),
    })
  ),
  
  on(vmActions.loadVMsFailure, (state, { error }) => ({
    ...state,
    loading: false,
    error,
  })),
  
  // Create VM
  on(vmActions.createVM, (state) => ({
    ...state,
    loading: true,
    error: null,
  })),
  
  on(vmActions.createVMSuccess, (state, { vm }) =>
    vmAdapter.addOne(vm, {
      ...state,
      loading: false,
      error: null,
    })
  ),
  
  on(vmActions.createVMFailure, (state, { error }) => ({
    ...state,
    loading: false,
    error,
  })),
  
  // Update VM
  on(vmActions.updateVM, (state) => ({
    ...state,
    loading: true,
    error: null,
  })),
  
  on(vmActions.updateVMSuccess, (state, { vm }) =>
    vmAdapter.updateOne(
      { id: vm.id, changes: vm },
      {
        ...state,
        loading: false,
        error: null,
      }
    )
  ),
  
  on(vmActions.updateVMFailure, (state, { error }) => ({
    ...state,
    loading: false,
    error,
  })),
  
  // Delete VM
  on(vmActions.deleteVM, (state) => ({
    ...state,
    loading: true,
    error: null,
  })),
  
  on(vmActions.deleteVMSuccess, (state, { id }) =>
    vmAdapter.removeOne(id, {
      ...state,
      loading: false,
      error: null,
      selectedId: state.selectedId === id.toString() ? null : state.selectedId,
    })
  ),
  
  on(vmActions.deleteVMFailure, (state, { error }) => ({
    ...state,
    loading: false,
    error,
  })),
  
  // VM Operations (Start, Stop, etc.)
  on(
    vmActions.startVM,
    vmActions.stopVM,
    vmActions.restartVM,
    vmActions.pauseVM,
    vmActions.resumeVM,
    (state) => ({
      ...state,
      loading: true,
      error: null,
    })
  ),
  
  on(
    vmActions.startVMSuccess,
    vmActions.stopVMSuccess,
    vmActions.restartVMSuccess,
    vmActions.pauseVMSuccess,
    vmActions.resumeVMSuccess,
    (state, { vm }) =>
      vmAdapter.updateOne(
        { id: vm.id, changes: vm },
        {
          ...state,
          loading: false,
          error: null,
        }
      )
  ),
  
  on(
    vmActions.startVMFailure,
    vmActions.stopVMFailure,
    vmActions.restartVMFailure,
    vmActions.pauseVMFailure,
    vmActions.resumeVMFailure,
    (state, { error }) => ({
      ...state,
      loading: false,
      error,
    })
  ),
  
  // Selection and UI
  on(vmActions.selectVM, (state, { id }) => ({
    ...state,
    selectedId: id,
  })),
  
  on(vmActions.clearSelection, (state) => ({
    ...state,
    selectedId: null,
  })),
  
  on(vmActions.setFilters, (state, { filters }) => ({
    ...state,
    filters,
  })),
  
  on(vmActions.clearFilters, (state) => ({
    ...state,
    filters: {},
  })),
  
  // Real-time updates
  on(vmActions.vMStatusChanged, (state, { id, status }) =>
    vmAdapter.updateOne(
      { id, changes: { status, updated_at: new Date().toISOString() } },
      state
    )
  ),
  
  on(vmActions.vMCreatedRealTime, (state, { vm }) =>
    vmAdapter.addOne(vm, state)
  ),
  
  on(vmActions.vMDeletedRealTime, (state, { id }) =>
    vmAdapter.removeOne(id, {
      ...state,
      selectedId: state.selectedId === id.toString() ? null : state.selectedId,
    })
  ),
  
  on(vmActions.vMMetricsUpdated, (state, { id, metrics }) =>
    vmAdapter.updateOne(
      { id, changes: { updated_at: new Date().toISOString() } },
      state
    )
  ),
  
  // Optimistic updates
  on(vmActions.updateVMOptimistic, (state, { id, changes }) =>
    vmAdapter.updateOne(
      { id, changes },
      state
    )
  ),
  
  on(vmActions.revertVMUpdate, (state, { id }) => {
    // For a complete implementation, we'd store the original state
    // For now, we'll just trigger a reload
    return {
      ...state,
      error: new Error('Update failed, please refresh'),
    };
  })
);