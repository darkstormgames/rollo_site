import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../shared/api.service';
import {
  Server,
  ServerRegistrationRequest,
  ServerUpdate,
  ServerListResponse,
  ServerDiscoverRequest,
  ServerDiscoverResponse,
  ServerStatusResponse,
  ServerMetrics,
  ServerHealthCheck,
  ServerOperationResponse,
  ServerFilter
} from '../../models/server/server.model';

@Injectable({
  providedIn: 'root'
})
export class ServerService {
  private readonly endpoint = '/servers';

  constructor(private apiService: ApiService) {}

  /**
   * Get list of servers with optional filtering
   */
  getServers(filters?: ServerFilter): Observable<ServerListResponse> {
    return this.apiService.get<ServerListResponse>(this.endpoint, filters);
  }

  /**
   * Get single server by ID
   */
  getServer(id: number): Observable<Server> {
    return this.apiService.get<Server>(`${this.endpoint}/${id}`);
  }

  /**
   * Register a new server
   */
  registerServer(registration: ServerRegistrationRequest): Observable<Server> {
    return this.apiService.post<Server>(`${this.endpoint}/register`, registration);
  }

  /**
   * Update server information
   */
  updateServer(id: number, update: ServerUpdate): Observable<Server> {
    return this.apiService.put<Server>(`${this.endpoint}/${id}`, update);
  }

  /**
   * Remove server
   */
  removeServer(id: number, forceRemove: boolean = false): Observable<{ message: string }> {
    const params = { force: forceRemove };
    return this.apiService.delete<{ message: string }>(`${this.endpoint}/${id}?force=${forceRemove}`);
  }

  /**
   * Get server status
   */
  getServerStatus(id: number): Observable<ServerStatusResponse> {
    return this.apiService.get<ServerStatusResponse>(`${this.endpoint}/${id}/status`);
  }

  /**
   * Get server metrics
   */
  getServerMetrics(id: number): Observable<ServerMetrics> {
    return this.apiService.get<ServerMetrics>(`${this.endpoint}/${id}/metrics`);
  }

  /**
   * Get server health check
   */
  getServerHealth(id: number): Observable<ServerHealthCheck> {
    return this.apiService.get<ServerHealthCheck>(`${this.endpoint}/${id}/health`);
  }

  /**
   * Perform server discovery on subnet
   */
  discoverServers(request: ServerDiscoverRequest): Observable<ServerDiscoverResponse> {
    return this.apiService.post<ServerDiscoverResponse>(`${this.endpoint}/discover`, request);
  }

  /**
   * Update server heartbeat
   */
  heartbeat(id: number): Observable<{ message: string; timestamp: string }> {
    return this.apiService.post<{ message: string; timestamp: string }>(`${this.endpoint}/${id}/heartbeat`, {});
  }

  /**
   * Get servers statistics
   */
  getServersStats(): Observable<{
    total: number;
    online: number;
    offline: number;
    maintenance: number;
    error: number;
    total_vms: number;
  }> {
    return this.apiService.get<{
      total: number;
      online: number;
      offline: number;
      maintenance: number;
      error: number;
      total_vms: number;
    }>(`${this.endpoint}/stats`);
  }

  /**
   * Reboot server
   */
  rebootServer(id: number): Observable<ServerOperationResponse> {
    return this.apiService.post<ServerOperationResponse>(`${this.endpoint}/${id}/reboot`, {});
  }

  /**
   * Shutdown server
   */
  shutdownServer(id: number): Observable<ServerOperationResponse> {
    return this.apiService.post<ServerOperationResponse>(`${this.endpoint}/${id}/shutdown`, {});
  }

  /**
   * Set server maintenance mode
   */
  setMaintenanceMode(id: number, enabled: boolean, reason?: string): Observable<ServerOperationResponse> {
    const body = { enabled, reason };
    return this.apiService.post<ServerOperationResponse>(`${this.endpoint}/${id}/maintenance`, body);
  }

  /**
   * Get server logs
   */
  getServerLogs(id: number, limit: number = 100): Observable<{
    logs: Array<{
      timestamp: string;
      level: string;
      message: string;
      source?: string;
    }>;
    total: number;
  }> {
    const params = { limit };
    return this.apiService.get<{
      logs: Array<{
        timestamp: string;
        level: string;
        message: string;
        source?: string;
      }>;
      total: number;
    }>(`${this.endpoint}/${id}/logs`, params);
  }

  /**
   * Get server VMs
   */
  getServerVMs(id: number, page?: number, per_page?: number): Observable<{
    vms: Array<{
      id: number;
      name: string;
      status: string;
      cpu_cores: number;
      memory_mb: number;
      disk_gb: number;
    }>;
    total: number;
    page: number;
    per_page: number;
    total_pages: number;
  }> {
    const params = { page, per_page };
    return this.apiService.get<{
      vms: Array<{
        id: number;
        name: string;
        status: string;
        cpu_cores: number;
        memory_mb: number;
        disk_gb: number;
      }>;
      total: number;
      page: number;
      per_page: number;
      total_pages: number;
    }>(`${this.endpoint}/${id}/vms`, params);
  }
}