import { TestBed } from '@angular/core/testing';
import { VMService } from './vm.service';
import { ApiService } from '../shared/api.service';
import { of } from 'rxjs';
import { VM, VMStatus, OSType, VMCreate, VMListResponse } from '../../models/vm/vm.model';

describe('VMService', () => {
  let service: VMService;
  let apiServiceSpy: jasmine.SpyObj<ApiService>;

  const mockVM: VM = {
    id: 1,
    name: 'test-vm',
    uuid: 'test-uuid',
    status: VMStatus.RUNNING,
    server: {
      id: 1,
      hostname: 'test-server',
      ip_address: '192.168.1.100',
      status: 'online'
    },
    resources: {
      cpu_cores: 2,
      memory_mb: 2048,
      disk_gb: 20
    },
    network: {
      interface: 'eth0',
      ip_address: '192.168.1.10',
      mac_address: '00:00:00:00:00:01',
      network_type: 'bridge'
    },
    os_type: OSType.LINUX,
    os_version: 'Ubuntu 22.04',
    vnc_port: 5900,
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-01T00:00:00Z'
  };

  beforeEach(() => {
    const spy = jasmine.createSpyObj('ApiService', ['get', 'post', 'put', 'delete']);

    TestBed.configureTestingModule({
      providers: [
        VMService,
        { provide: ApiService, useValue: spy }
      ]
    });
    
    service = TestBed.inject(VMService);
    apiServiceSpy = TestBed.inject(ApiService) as jasmine.SpyObj<ApiService>;
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should get VMs', () => {
    const mockResponse: VMListResponse = {
      vms: [mockVM],
      total: 1,
      page: 1,
      per_page: 10,
      total_pages: 1
    };

    apiServiceSpy.get.and.returnValue(of(mockResponse));

    service.getVMs().subscribe(response => {
      expect(response).toEqual(mockResponse);
      expect(response.vms.length).toBe(1);
      expect(response.vms[0]).toEqual(mockVM);
    });

    expect(apiServiceSpy.get).toHaveBeenCalledWith('/vms', undefined);
  });

  it('should get VM by ID', () => {
    apiServiceSpy.get.and.returnValue(of(mockVM));

    service.getVM(1).subscribe(vm => {
      expect(vm).toEqual(mockVM);
    });

    expect(apiServiceSpy.get).toHaveBeenCalledWith('/vms/1');
  });

  it('should create VM', () => {
    const vmCreate: VMCreate = {
      name: 'new-vm',
      server_id: 1,
      os_type: OSType.LINUX,
      cpu_cores: 2,
      memory_mb: 2048,
      disk_gb: 20,
      vnc_enabled: true,
      network_config: {}
    };

    apiServiceSpy.post.and.returnValue(of(mockVM));

    service.createVM(vmCreate).subscribe(vm => {
      expect(vm).toEqual(mockVM);
    });

    expect(apiServiceSpy.post).toHaveBeenCalledWith('/vms', vmCreate);
  });

  it('should start VM', () => {
    const mockResponse = {
      id: 1,
      name: 'test-vm',
      operation: 'start',
      status: 'starting',
      message: 'VM is starting'
    };

    apiServiceSpy.post.and.returnValue(of(mockResponse));

    service.startVM(1).subscribe(response => {
      expect(response).toEqual(mockResponse);
    });

    expect(apiServiceSpy.post).toHaveBeenCalledWith('/vms/1/start', {});
  });

  it('should stop VM', () => {
    const mockResponse = {
      id: 1,
      name: 'test-vm',
      operation: 'stop',
      status: 'stopping',
      message: 'VM is stopping'
    };

    apiServiceSpy.post.and.returnValue(of(mockResponse));

    service.stopVM(1, false).subscribe(response => {
      expect(response).toEqual(mockResponse);
    });

    expect(apiServiceSpy.post).toHaveBeenCalledWith('/vms/1/stop', { force: false });
  });

  it('should delete VM', () => {
    const mockResponse = { message: 'VM deleted successfully' };

    apiServiceSpy.delete.and.returnValue(of(mockResponse));

    service.deleteVM(1, true).subscribe(response => {
      expect(response).toEqual(mockResponse);
    });

    expect(apiServiceSpy.delete).toHaveBeenCalledWith('/vms/1?delete_disks=true');
  });

  it('should get VM metrics', () => {
    const mockMetrics = {
      id: 1,
      name: 'test-vm',
      timestamp: '2023-01-01T00:00:00Z',
      cpu_usage_percent: 45.5,
      memory_usage_percent: 60.2,
      memory_used_mb: 1229,
      network_rx_bytes: 1024,
      network_tx_bytes: 2048,
      disk_read_bytes: 512,
      disk_write_bytes: 1536
    };

    apiServiceSpy.get.and.returnValue(of(mockMetrics));

    service.getVMMetrics(1).subscribe(metrics => {
      expect(metrics).toEqual(mockMetrics);
    });

    expect(apiServiceSpy.get).toHaveBeenCalledWith('/vms/1/metrics');
  });
});