export enum ServerStatus {
  ONLINE = 'online',
  OFFLINE = 'offline',
  MAINTENANCE = 'maintenance',
  ERROR = 'error'
}

export interface ServerSystemInfo {
  os_version: string;
  cpu_cores: number;
  memory_gb: number;
  disk_gb: number;
}

export interface Server {
  id: number;
  hostname: string;
  ip_address: string;
  port: number;
  status: ServerStatus;
  os_version?: string;
  cpu_cores?: number;
  memory_gb?: number;
  disk_gb?: number;
  agent_version?: string;
  last_heartbeat?: string;
  vm_count: number;
  created_at: string;
  updated_at: string;
}

export interface ServerRegistrationRequest {
  hostname: string;
  ip_address: string;
  agent_version: string;
  system_info: ServerSystemInfo;
  auth_token: string;
}

export interface ServerUpdate {
  hostname?: string;
  ip_address?: string;
  port?: number;
  status?: ServerStatus;
  os_version?: string;
  cpu_cores?: number;
  memory_gb?: number;
  disk_gb?: number;
  agent_version?: string;
}

export interface ServerListResponse {
  servers: Server[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface ServerDiscoverRequest {
  subnet: string;
  port: number;
  timeout: number;
}

export interface ServerDiscoverResponse {
  discovered_servers: string[];
  scan_duration: number;
  total_found: number;
}

export interface ServerStatusResponse {
  id: number;
  hostname: string;
  ip_address: string;
  status: ServerStatus;
  last_heartbeat?: string;
  agent_version?: string;
  uptime_seconds?: number;
  is_reachable: boolean;
}

export interface ServerMetrics {
  id: number;
  hostname: string;
  timestamp: string;
  cpu_usage_percent?: number;
  memory_usage_percent?: number;
  memory_used_gb?: number;
  memory_total_gb?: number;
  disk_usage_percent?: number;
  disk_used_gb?: number;
  disk_total_gb?: number;
  network_rx_bytes?: number;
  network_tx_bytes?: number;
  load_average?: number;
}

export interface ServerHealthCheck {
  id: number;
  hostname: string;
  status: ServerStatus;
  timestamp: string;
  checks: { [key: string]: any };
  overall_health: 'healthy' | 'warning' | 'critical';
}

export interface ServerOperationResponse {
  id: number;
  hostname: string;
  operation: string;
  status: string;
  message?: string;
  timestamp: string;
}

export interface ServerFilter {
  status?: ServerStatus;
  hostname?: string;
  agent_version?: string;
  page?: number;
  per_page?: number;
}