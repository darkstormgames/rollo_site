export enum VMStatus {
  RUNNING = 'running',
  STOPPED = 'stopped',
  PAUSED = 'paused',
  STARTING = 'starting',
  STOPPING = 'stopping',
  ERROR = 'error'
}

export enum OSType {
  LINUX = 'linux',
  WINDOWS = 'windows',
  OTHER = 'other'
}

export interface VMResources {
  cpu_cores: number;
  memory_mb: number;
  disk_gb: number;
}

export interface VMNetwork {
  interface: string;
  ip_address?: string;
  mac_address?: string;
  network_type: string;
}

export interface ServerInfo {
  id: number;
  hostname: string;
  ip_address: string;
  status: string;
}

export interface VM {
  id: number;
  name: string;
  uuid: string;
  status: VMStatus;
  server: ServerInfo;
  resources: VMResources;
  network: VMNetwork;
  os_type: OSType;
  os_version?: string;
  vnc_port?: number;
  created_at: string;
  updated_at: string;
}

export interface VMConfig {
  id: number;
  name: string;
  uuid: string;
  cpu_cores: number;
  memory_mb: number;
  disk_gb: number;
  os_type: OSType;
  os_version?: string;
  vnc_enabled: boolean;
  vnc_port?: number;
  network_config: { [key: string]: any };
  xml_config?: string;
}

export interface VMCreate {
  name: string;
  server_id: number;
  os_type: OSType;
  os_version?: string;
  cpu_cores: number;
  memory_mb: number;
  disk_gb: number;
  vnc_enabled: boolean;
  network_config: { [key: string]: any };
  xml_config?: string;
}

export interface VMUpdate {
  name?: string;
  cpu_cores?: number;
  memory_mb?: number;
  disk_gb?: number;
  os_version?: string;
  vnc_enabled?: boolean;
  network_config?: { [key: string]: any };
}

export interface VMResize {
  cpu_cores?: number;
  memory_mb?: number;
  disk_gb?: number;
}

export interface VMListResponse {
  vms: VM[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface VMOperationResponse {
  id: number;
  name: string;
  operation: string;
  status: string;
  message?: string;
  details?: { [key: string]: any };
}

export interface VMFilter {
  name?: string;
  status?: VMStatus;
  server_id?: number;
  os_type?: OSType;
  page?: number;
  per_page?: number;
}

export interface VMMetrics {
  id: number;
  name: string;
  timestamp: string;
  cpu_usage_percent?: number;
  memory_usage_percent?: number;
  memory_used_mb?: number;
  network_rx_bytes?: number;
  network_tx_bytes?: number;
  disk_read_bytes?: number;
  disk_write_bytes?: number;
}

export interface OperationStatus {
  success: boolean;
  message: string;
  operation_id?: string;
}