import { EntityState } from '@ngrx/entity';
import { VM, VMFilter } from '../../models/vm/vm.model';

export interface VMState extends EntityState<VM> {
  selectedId: string | null;
  loading: boolean;
  error: Error | null;
  filters: VMFilter;
  lastUpdated: string | null;
}

export const initialVMState: VMState = {
  ids: [],
  entities: {},
  selectedId: null,
  loading: false,
  error: null,
  filters: {},
  lastUpdated: null,
};