import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../shared/api.service';
import {
  VM,
  VMCreate,
  VMUpdate,
  VMResize,
  VMConfig,
  VMListResponse,
  VMOperationResponse,
  VMFilter,
  VMMetrics,
  OperationStatus
} from '../../models/vm/vm.model';

@Injectable({
  providedIn: 'root'
})
export class VMService {
  private readonly endpoint = '/vms';

  constructor(private apiService: ApiService) {}

  /**
   * Get list of VMs with optional filtering
   */
  getVMs(filters?: VMFilter): Observable<VMListResponse> {
    return this.apiService.get<VMListResponse>(this.endpoint, filters);
  }

  /**
   * Get single VM by ID
   */
  getVM(id: number): Observable<VM> {
    return this.apiService.get<VM>(`${this.endpoint}/${id}`);
  }

  /**
   * Create a new VM
   */
  createVM(config: VMCreate): Observable<VM> {
    return this.apiService.post<VM>(this.endpoint, config);
  }

  /**
   * Update VM configuration
   */
  updateVM(id: number, update: VMUpdate): Observable<VM> {
    return this.apiService.put<VM>(`${this.endpoint}/${id}`, update);
  }

  /**
   * Delete VM
   */
  deleteVM(id: number, deleteDisks: boolean = true): Observable<{ message: string }> {
    const params = { delete_disks: deleteDisks };
    return this.apiService.delete<{ message: string }>(`${this.endpoint}/${id}?delete_disks=${deleteDisks}`);
  }

  /**
   * Start VM
   */
  startVM(id: number): Observable<VMOperationResponse> {
    return this.apiService.post<VMOperationResponse>(`${this.endpoint}/${id}/start`, {});
  }

  /**
   * Stop VM
   */
  stopVM(id: number, force: boolean = false): Observable<VMOperationResponse> {
    const body = { force };
    return this.apiService.post<VMOperationResponse>(`${this.endpoint}/${id}/stop`, body);
  }

  /**
   * Restart VM
   */
  restartVM(id: number, force: boolean = false): Observable<VMOperationResponse> {
    const body = { force };
    return this.apiService.post<VMOperationResponse>(`${this.endpoint}/${id}/restart`, body);
  }

  /**
   * Pause VM
   */
  pauseVM(id: number): Observable<VMOperationResponse> {
    return this.apiService.post<VMOperationResponse>(`${this.endpoint}/${id}/pause`, {});
  }

  /**
   * Resume VM
   */
  resumeVM(id: number): Observable<VMOperationResponse> {
    return this.apiService.post<VMOperationResponse>(`${this.endpoint}/${id}/resume`, {});
  }

  /**
   * Resize VM resources
   */
  resizeVM(id: number, resize: VMResize): Observable<VMOperationResponse> {
    return this.apiService.post<VMOperationResponse>(`${this.endpoint}/${id}/resize`, resize);
  }

  /**
   * Get VM configuration
   */
  getVMConfig(id: number): Observable<VMConfig> {
    return this.apiService.get<VMConfig>(`${this.endpoint}/${id}/config`);
  }

  /**
   * Update VM configuration
   */
  updateVMConfig(id: number, config: Partial<VMConfig>): Observable<VMConfig> {
    return this.apiService.put<VMConfig>(`${this.endpoint}/${id}/config`, config);
  }

  /**
   * Get VM metrics
   */
  getVMMetrics(id: number): Observable<VMMetrics> {
    return this.apiService.get<VMMetrics>(`${this.endpoint}/${id}/metrics`);
  }

  /**
   * Get VM status
   */
  getVMStatus(id: number): Observable<{ id: number; name: string; status: string; details?: any }> {
    return this.apiService.get<{ id: number; name: string; status: string; details?: any }>(`${this.endpoint}/${id}/status`);
  }

  /**
   * Clone VM
   */
  cloneVM(id: number, newName: string): Observable<VM> {
    const body = { name: newName };
    return this.apiService.post<VM>(`${this.endpoint}/${id}/clone`, body);
  }

  /**
   * Create VM snapshot
   */
  createSnapshot(id: number, name: string, description?: string): Observable<{ message: string; snapshot_name: string }> {
    const body = { name, description };
    return this.apiService.post<{ message: string; snapshot_name: string }>(`${this.endpoint}/${id}/snapshots`, body);
  }

  /**
   * Restore VM snapshot
   */
  restoreSnapshot(id: number, snapshotName: string): Observable<VMOperationResponse> {
    const body = { snapshot_name: snapshotName };
    return this.apiService.post<VMOperationResponse>(`${this.endpoint}/${id}/snapshots/restore`, body);
  }

  /**
   * Delete VM snapshot
   */
  deleteSnapshot(id: number, snapshotName: string): Observable<{ message: string }> {
    return this.apiService.delete<{ message: string }>(`${this.endpoint}/${id}/snapshots/${snapshotName}`);
  }

  /**
   * Get VM console URL (VNC)
   */
  getConsoleURL(id: number): Observable<{ url: string; token?: string }> {
    return this.apiService.get<{ url: string; token?: string }>(`${this.endpoint}/${id}/console`);
  }
}