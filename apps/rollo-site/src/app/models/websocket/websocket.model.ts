export enum WebSocketEventType {
  VM_STATUS_CHANGED = 'vm_status_changed',
  VM_CREATED = 'vm_created',
  VM_DELETED = 'vm_deleted',
  VM_METRICS_UPDATE = 'vm_metrics_update',
  SERVER_STATUS_CHANGED = 'server_status_changed',
  SERVER_REGISTERED = 'server_registered',
  SERVER_REMOVED = 'server_removed',
  SERVER_METRICS_UPDATE = 'server_metrics_update',
  CONNECTION_STATUS = 'connection_status',
  PROGRESS = 'progress',
  ALERT = 'alert',
  SUBSCRIPTION_CONFIRMED = 'subscription_confirmed',
  CONSOLE_OUTPUT = 'console_output',
  CONSOLE_STATUS = 'console_status',
  WEBSOCKET_STATS = 'websocket_stats'
}

export enum ConnectionStatus {
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  ERROR = 'error',
  RECONNECTING = 'reconnecting'
}

export interface WebSocketMessage {
  type: WebSocketEventType;
  data: any;
  timestamp: string;
}

export interface VMStatusEvent {
  vm_id: number;
  vm_name: string;
  old_status: string;
  new_status: string;
  timestamp: string;
}

export interface VMCreatedEvent {
  vm: {
    id: number;
    name: string;
    uuid: string;
    status: string;
    server_id: number;
  };
  timestamp: string;
}

export interface VMDeletedEvent {
  vm_id: number;
  vm_name: string;
  timestamp: string;
}

export interface VMMetricsEvent {
  vm_id: number;
  vm_name: string;
  metrics: {
    cpu_usage_percent?: number;
    memory_usage_percent?: number;
    memory_used_mb?: number;
    network_rx_bytes?: number;
    network_tx_bytes?: number;
    disk_read_bytes?: number;
    disk_write_bytes?: number;
  };
  timestamp: string;
}

export interface ServerStatusEvent {
  server_id: number;
  hostname: string;
  old_status: string;
  new_status: string;
  timestamp: string;
}

export interface ServerRegisteredEvent {
  server: {
    id: number;
    hostname: string;
    ip_address: string;
    status: string;
  };
  timestamp: string;
}

export interface ServerRemovedEvent {
  server_id: number;
  hostname: string;
  timestamp: string;
}

export interface ServerMetricsEvent {
  server_id: number;
  hostname: string;
  metrics: {
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
  };
  timestamp: string;
}

export interface WebSocketConfig {
  url: string;
  reconnectInterval: number;
  maxReconnectAttempts: number;
  heartbeatInterval: number;
  debug: boolean;
  messageQueueSize?: number;
  offlineQueueEnabled?: boolean;
}

export interface SubscriptionOptions {
  events: WebSocketEventType[];
  vm_ids?: number[];
  server_ids?: number[];
}

export interface ProgressEvent {
  operation_id: string;
  operation_type: string;
  progress_percent: number;
  status: string;
  message?: string;
  timestamp: string;
}

export interface AlertEvent {
  alert_id: string;
  alert_type: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  title: string;
  message: string;
  entity_type?: 'vm' | 'server';
  entity_id?: number;
  timestamp: string;
}

export interface ConsoleEvent {
  vm_id: number;
  output?: string;
  status?: string;
  message?: string;
  timestamp: string;
}

export interface WebSocketStats {
  active_connections: number;
  room_stats: { [key: string]: number };
  timestamp: string;
}