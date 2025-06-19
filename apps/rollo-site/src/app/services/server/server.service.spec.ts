import { TestBed } from '@angular/core/testing';
import { ServerService } from './server.service';
import { ApiService } from '../shared/api.service';
import { of } from 'rxjs';
import { Server, ServerStatus, ServerListResponse } from '../../models/server/server.model';

describe('ServerService', () => {
  let service: ServerService;
  let apiServiceSpy: jasmine.SpyObj<ApiService>;

  const mockServer: Server = {
    id: 1,
    hostname: 'test-server',
    ip_address: '192.168.1.100',
    port: 22,
    status: ServerStatus.ONLINE,
    os_version: 'Ubuntu 22.04',
    cpu_cores: 8,
    memory_gb: 16,
    disk_gb: 500,
    agent_version: '1.0.0',
    last_heartbeat: '2023-01-01T00:00:00Z',
    vm_count: 3,
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-01T00:00:00Z'
  };

  beforeEach(() => {
    const spy = jasmine.createSpyObj('ApiService', ['get', 'post', 'put', 'delete']);

    TestBed.configureTestingModule({
      providers: [
        ServerService,
        { provide: ApiService, useValue: spy }
      ]
    });
    
    service = TestBed.inject(ServerService);
    apiServiceSpy = TestBed.inject(ApiService) as jasmine.SpyObj<ApiService>;
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should get servers', () => {
    const mockResponse: ServerListResponse = {
      servers: [mockServer],
      total: 1,
      page: 1,
      per_page: 10,
      total_pages: 1
    };

    apiServiceSpy.get.and.returnValue(of(mockResponse));

    service.getServers().subscribe(response => {
      expect(response).toEqual(mockResponse);
      expect(response.servers.length).toBe(1);
      expect(response.servers[0]).toEqual(mockServer);
    });

    expect(apiServiceSpy.get).toHaveBeenCalledWith('/servers', undefined);
  });

  it('should get server by ID', () => {
    apiServiceSpy.get.and.returnValue(of(mockServer));

    service.getServer(1).subscribe(server => {
      expect(server).toEqual(mockServer);
    });

    expect(apiServiceSpy.get).toHaveBeenCalledWith('/servers/1');
  });

  it('should register server', () => {
    const registrationData = {
      hostname: 'new-server',
      ip_address: '192.168.1.101',
      agent_version: '1.0.0',
      system_info: {
        os_version: 'Ubuntu 22.04',
        cpu_cores: 4,
        memory_gb: 8,
        disk_gb: 100
      },
      auth_token: 'test-token'
    };

    apiServiceSpy.post.and.returnValue(of(mockServer));

    service.registerServer(registrationData).subscribe(server => {
      expect(server).toEqual(mockServer);
    });

    expect(apiServiceSpy.post).toHaveBeenCalledWith('/servers/register', registrationData);
  });

  it('should get server status', () => {
    const mockStatus = {
      id: 1,
      hostname: 'test-server',
      ip_address: '192.168.1.100',
      status: ServerStatus.ONLINE,
      last_heartbeat: '2023-01-01T00:00:00Z',
      agent_version: '1.0.0',
      uptime_seconds: 86400,
      is_reachable: true
    };

    apiServiceSpy.get.and.returnValue(of(mockStatus));

    service.getServerStatus(1).subscribe(status => {
      expect(status).toEqual(mockStatus);
    });

    expect(apiServiceSpy.get).toHaveBeenCalledWith('/servers/1/status');
  });

  it('should get server metrics', () => {
    const mockMetrics = {
      id: 1,
      hostname: 'test-server',
      timestamp: '2023-01-01T00:00:00Z',
      cpu_usage_percent: 45.5,
      memory_usage_percent: 60.2,
      memory_used_gb: 9.6,
      memory_total_gb: 16,
      disk_usage_percent: 75.0,
      disk_used_gb: 375,
      disk_total_gb: 500,
      network_rx_bytes: 1024000,
      network_tx_bytes: 2048000,
      load_average: 1.5
    };

    apiServiceSpy.get.and.returnValue(of(mockMetrics));

    service.getServerMetrics(1).subscribe(metrics => {
      expect(metrics).toEqual(mockMetrics);
    });

    expect(apiServiceSpy.get).toHaveBeenCalledWith('/servers/1/metrics');
  });

  it('should discover servers', () => {
    const discoverRequest = {
      subnet: '192.168.1.0/24',
      port: 22,
      timeout: 5
    };

    const mockResponse = {
      discovered_servers: ['192.168.1.100', '192.168.1.101'],
      scan_duration: 12.5,
      total_found: 2
    };

    apiServiceSpy.post.and.returnValue(of(mockResponse));

    service.discoverServers(discoverRequest).subscribe(response => {
      expect(response).toEqual(mockResponse);
    });

    expect(apiServiceSpy.post).toHaveBeenCalledWith('/servers/discover', discoverRequest);
  });

  it('should update server heartbeat', () => {
    const mockResponse = {
      message: 'Heartbeat updated',
      timestamp: '2023-01-01T00:00:00Z'
    };

    apiServiceSpy.post.and.returnValue(of(mockResponse));

    service.heartbeat(1).subscribe(response => {
      expect(response).toEqual(mockResponse);
    });

    expect(apiServiceSpy.post).toHaveBeenCalledWith('/servers/1/heartbeat', {});
  });

  it('should get servers statistics', () => {
    const mockStats = {
      total: 5,
      online: 4,
      offline: 1,
      maintenance: 0,
      error: 0,
      total_vms: 15
    };

    apiServiceSpy.get.and.returnValue(of(mockStats));

    service.getServersStats().subscribe(stats => {
      expect(stats).toEqual(mockStats);
    });

    expect(apiServiceSpy.get).toHaveBeenCalledWith('/servers/stats');
  });
});