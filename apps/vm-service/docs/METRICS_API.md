# Metrics API Documentation

## Overview

The Metrics API provides comprehensive access to server and VM performance metrics, including real-time data, historical trends, custom queries, and alerting capabilities.

## Base URL

All metrics endpoints are available under:
```
/api/metrics
```

## Authentication

All endpoints require authentication via JWT token or API key.

## Endpoints

### Server Metrics

#### Get Current Server Metrics
```http
GET /api/metrics/servers/{server_id}
```

**Response:**
```json
{
  "id": 1,
  "hostname": "server01.example.com",
  "timestamp": "2024-01-01T12:00:00Z",
  "cpu_usage_percent": 75.5,
  "memory_usage_percent": 68.2,
  "memory_used_gb": 5.5,
  "memory_total_gb": 8.0,
  "disk_usage_percent": 45.3,
  "disk_used_gb": 45.3,
  "disk_total_gb": 100.0,
  "network_rx_bytes": 1048576,
  "network_tx_bytes": 524288,
  "load_average": 1.25
}
```

#### Get Server Historical Metrics
```http
GET /api/metrics/servers/{server_id}/history?metric=cpu,memory&interval=5m&start=2024-01-01T00:00:00Z&end=2024-01-02T00:00:00Z&aggregation=avg
```

**Query Parameters:**
- `metric` (optional): Comma-separated list of metrics (cpu, memory, disk, network, system)
- `interval` (optional): Time interval (5s, 1m, 5m, 1h, 1d) - default: 5m
- `start` (optional): Start time (ISO 8601) - default: 24 hours ago
- `end` (optional): End time (ISO 8601) - default: now
- `aggregation` (optional): Aggregation function (avg, min, max, sum, count) - default: avg

**Response:**
```json
{
  "entity_type": "server",
  "entity_id": 1,
  "entity_name": "server01.example.com",
  "query": {
    "metric": ["cpu", "memory"],
    "interval": "5m",
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-02T00:00:00Z",
    "aggregation": "avg"
  },
  "metrics": [
    {
      "name": "cpu_usage",
      "entity_type": "server",
      "entity_id": 1,
      "values": [
        {
          "timestamp": "2024-01-01T00:00:00Z",
          "value": 75.5,
          "unit": "percent"
        }
      ]
    }
  ],
  "total_points": 288
}
```

### VM Metrics

#### Get Current VM Metrics
```http
GET /api/metrics/vms/{vm_id}
```

**Response:**
```json
{
  "id": 1,
  "name": "web-server-01",
  "uuid": "12345678-1234-1234-1234-123456789012",
  "timestamp": "2024-01-01T12:00:00Z",
  "cpu_usage_percent": 45.2,
  "cpu_steal_time": 2.1,
  "cpu_wait_time": 1.5,
  "memory_usage_percent": 72.8,
  "memory_active_mb": 1024,
  "memory_inactive_mb": 512,
  "memory_balloon_mb": 0,
  "disk_read_ops": 1500,
  "disk_write_ops": 800,
  "disk_read_bytes": 15728640,
  "disk_write_bytes": 8388608,
  "network_rx_bytes": 2097152,
  "network_tx_bytes": 1048576,
  "network_rx_packets": 1024,
  "network_tx_packets": 512,
  "response_time_ms": 150.5,
  "iops": 250.0
}
```

#### Get VM Historical Metrics
```http
GET /api/metrics/vms/{vm_id}/history?metric=cpu,memory&interval=5m&start=2024-01-01T00:00:00Z&end=2024-01-02T00:00:00Z&aggregation=avg
```

Same query parameters and response format as server historical metrics.

### Custom Queries

#### Execute Custom Metrics Query
```http
POST /api/metrics/query
```

**Request Body:**
```json
{
  "entity_type": "server",
  "entity_ids": [1, 2, 3],
  "metrics": ["cpu", "memory", "disk"],
  "start": "2024-01-01T00:00:00Z",
  "end": "2024-01-02T00:00:00Z",
  "interval": "5m",
  "aggregation": "avg",
  "filters": {
    "hostname": "web-*"
  }
}
```

**Response:**
```json
{
  "query": {
    "entity_type": "server",
    "entity_ids": [1, 2, 3],
    "metrics": ["cpu", "memory", "disk"],
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-02T00:00:00Z",
    "interval": "5m",
    "aggregation": "avg"
  },
  "results": [
    {
      "entity_type": "server",
      "entity_id": 1,
      "entity_name": "server01.example.com",
      "metrics": []
    }
  ],
  "execution_time_ms": 125.5
}
```

### Alerts

#### Get Active Alerts
```http
GET /api/metrics/alerts
```

**Response:**
```json
{
  "alerts": [
    {
      "id": 1001,
      "rule_name": "high_cpu_usage",
      "entity_type": "server",
      "entity_id": 1,
      "entity_name": "server01.example.com",
      "metric_type": "cpu",
      "current_value": 95.5,
      "threshold": 90.0,
      "condition": "> 90",
      "severity": "warning",
      "status": "active",
      "triggered_at": "2024-01-01T12:00:00Z",
      "last_updated": "2024-01-01T12:05:00Z",
      "duration_minutes": 15
    }
  ],
  "total": 1,
  "active_count": 1,
  "critical_count": 0,
  "warning_count": 1
}
```

### Collection Status

#### Get Metrics Collection Status
```http
GET /api/metrics/status/{entity_type}/{entity_id}
```

**Parameters:**
- `entity_type`: "server" or "vm"
- `entity_id`: Entity ID

**Response:**
```json
{
  "entity_type": "server",
  "entity_id": 1,
  "last_collection": "2024-01-01T12:00:00Z",
  "collection_interval_seconds": 5,
  "is_collecting": true,
  "error_count": 0,
  "last_error": null
}
```

### Recording Metrics (Agent Endpoints)

#### Record Server Metric
```http
POST /api/metrics/servers/{server_id}/record?metric_name=cpu_usage&value=75.5&unit=percent
```

#### Record VM Metric
```http
POST /api/metrics/vms/{vm_id}/record?metric_name=memory_usage&value=85.2&unit=percent
```

## Metric Types

### Server Metrics
- **CPU**: usage, load_average
- **Memory**: usage, free, cached
- **Disk**: usage, read_bytes, write_bytes
- **Network**: rx_bytes, tx_bytes
- **System**: uptime, processes

### VM Metrics
- **CPU**: usage, steal_time, wait_time
- **Memory**: usage, active, inactive, balloon
- **Disk**: read_ops, write_ops, read_bytes, write_bytes
- **Network**: rx_bytes, tx_bytes, rx_packets, tx_packets
- **Performance**: response_time, iops

## Time Intervals

- `5s` - 5 seconds
- `1m` - 1 minute
- `5m` - 5 minutes (default)
- `1h` - 1 hour
- `1d` - 1 day

## Aggregation Functions

- `avg` - Average (default)
- `min` - Minimum
- `max` - Maximum
- `sum` - Sum
- `count` - Count

## Error Responses

### 400 Bad Request
```json
{
  "detail": "End time must be after start time"
}
```

### 404 Not Found
```json
{
  "detail": "Server not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Error executing query"
}
```

## Rate Limits

- Default: 100 requests per minute per user
- Custom query endpoint: 10 requests per minute per user
- Recording endpoints: 1000 requests per minute per agent

## Data Retention

- 5-second data: 1 day
- 1-minute data: 7 days  
- 5-minute data: 30 days
- 1-hour data: 1 year
- 1-day data: 5 years