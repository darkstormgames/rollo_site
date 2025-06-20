import { createActionGroup, emptyProps, props } from '@ngrx/store';
import { VM, VMCreate, VMUpdate, VMResize, VMStatus, VMFilter } from '../../models/vm/vm.model';

export const vmActions = createActionGroup({
  source: 'VM',
  events: {
    // Loading VMs
    'Load VMs': props<{ filters?: VMFilter }>(),
    'Load VMs Success': props<{ vms: VM[] }>(),
    'Load VMs Failure': props<{ error: Error }>(),
    
    // VM CRUD operations
    'Create VM': props<{ vmData: VMCreate }>(),
    'Create VM Success': props<{ vm: VM }>(),
    'Create VM Failure': props<{ error: Error }>(),
    
    'Update VM': props<{ id: number; changes: VMUpdate }>(),
    'Update VM Success': props<{ vm: VM }>(),
    'Update VM Failure': props<{ id: number; error: Error }>(),
    
    'Delete VM': props<{ id: number }>(),
    'Delete VM Success': props<{ id: number }>(),
    'Delete VM Failure': props<{ id: number; error: Error }>(),
    
    // VM Operations
    'Start VM': props<{ id: number }>(),
    'Start VM Success': props<{ id: number; vm: VM }>(),
    'Start VM Failure': props<{ id: number; error: Error }>(),
    
    'Stop VM': props<{ id: number; force?: boolean }>(),
    'Stop VM Success': props<{ id: number; vm: VM }>(),
    'Stop VM Failure': props<{ id: number; error: Error }>(),
    
    'Restart VM': props<{ id: number; force?: boolean }>(),
    'Restart VM Success': props<{ id: number; vm: VM }>(),
    'Restart VM Failure': props<{ id: number; error: Error }>(),
    
    'Pause VM': props<{ id: number }>(),
    'Pause VM Success': props<{ id: number; vm: VM }>(),
    'Pause VM Failure': props<{ id: number; error: Error }>(),
    
    'Resume VM': props<{ id: number }>(),
    'Resume VM Success': props<{ id: number; vm: VM }>(),
    'Resume VM Failure': props<{ id: number; error: Error }>(),
    
    // Selection and UI
    'Select VM': props<{ id: string }>(),
    'Clear Selection': emptyProps(),
    'Set Filters': props<{ filters: VMFilter }>(),
    'Clear Filters': emptyProps(),
    
    // Real-time updates from WebSocket
    'VM Status Changed': props<{ id: number; status: VMStatus }>(),
    'VM Created Real Time': props<{ vm: VM }>(),
    'VM Deleted Real Time': props<{ id: number }>(),
    'VM Metrics Updated': props<{ id: number; metrics: any }>(),
    
    // Optimistic updates
    'Update VM Optimistic': props<{ id: number; changes: Partial<VM> }>(),
    'Revert VM Update': props<{ id: number }>(),
  }
});