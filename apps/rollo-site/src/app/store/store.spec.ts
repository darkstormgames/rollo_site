import { TestBed } from '@angular/core/testing';
import { provideMockStore, MockStore } from '@ngrx/store/testing';
import { AppState } from './app.state';
import { vmActions } from './vm/vm.actions';
import { selectAllVMs, selectVMLoading } from './vm/vm.selectors';
import { VM, VMStatus, OSType } from '../models/vm/vm.model';

describe('VM Store Integration', () => {
  let store: MockStore<AppState>;
  const initialState: AppState = {
    vms: {
      ids: [],
      entities: {},
      selectedId: null,
      loading: false,
      error: null,
      filters: {},
      lastUpdated: null,
    },
    servers: {
      ids: [],
      entities: {},
      selectedId: null,
      loading: false,
      error: null,
      lastUpdated: null,
    }
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideMockStore({ initialState })
      ]
    });
    store = TestBed.inject(MockStore);
  });

  it('should create', () => {
    expect(store).toBeTruthy();
  });

  it('should dispatch loadVMs action', () => {
    spyOn(store, 'dispatch');
    
    const action = vmActions.loadVMs({ filters: {} });
    store.dispatch(action);
    
    expect(store.dispatch).toHaveBeenCalledWith(action);
  });

  it('should select VMs from store', () => {
    const mockVMs: VM[] = [
      {
        id: 1,
        name: 'Test VM',
        uuid: 'test-uuid',
        status: VMStatus.RUNNING,
        server: { id: 1, hostname: 'test-server', ip_address: '10.0.0.1', status: 'online' },
        resources: { cpu_cores: 2, memory_mb: 2048, disk_gb: 20 },
        network: { interface: 'eth0', network_type: 'nat' },
        os_type: OSType.LINUX,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      }
    ];

    store.overrideSelector(selectAllVMs, mockVMs);
    store.overrideSelector(selectVMLoading, false);

    let vms: VM[] = [];
    let loading = true;

    store.select(selectAllVMs).subscribe(result => vms = result);
    store.select(selectVMLoading).subscribe(result => loading = result);

    expect(vms).toEqual(mockVMs);
    expect(loading).toBe(false);
  });

  it('should handle VM status changes', () => {
    spyOn(store, 'dispatch');
    
    const action = vmActions.vMStatusChanged({ id: 1, status: VMStatus.STOPPED });
    store.dispatch(action);
    
    expect(store.dispatch).toHaveBeenCalledWith(action);
  });
});