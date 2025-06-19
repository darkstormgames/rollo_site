# Security API Documentation

This document describes the SSH key management and secure communication layer APIs for the Rollo site.

## Overview

The Security API provides comprehensive SSH key management and TLS certificate generation capabilities with the following features:

- **SSH Key Management**: Generate, store, deploy, and rotate RSA 4096-bit SSH keys
- **TLS Certificate Management**: Generate and manage X.509 certificates for secure communications
- **Security Audit Logging**: Comprehensive logging of all security operations
- **Encrypted Storage**: All private keys are encrypted at rest using AES-256-GCM

## Authentication

All endpoints require JWT authentication via the Authorization header:

```
Authorization: Bearer <access_token>
```

## SSH Key Management

### Generate SSH Key Pair

**POST** `/api/security/keys/generate`

Generate a new RSA 4096-bit SSH key pair.

#### Request Body

```json
{
  "name": "string (required, 1-255 chars)",
  "description": "string (optional, max 1000 chars)",
  "expiresInDays": "integer (optional, 1-3650 days)"
}
```

#### Response

```json
{
  "message": "SSH key pair generated successfully",
  "key": {
    "keyId": "uuid",
    "name": "string",
    "publicKey": "ssh-rsa AAAAB3...",
    "fingerprint": "aa:bb:cc:dd:ee:ff...",
    "keySize": 4096,
    "expiresAt": "2024-12-31T23:59:59.000Z",
    "createdAt": "2024-01-01T00:00:00.000Z"
  }
}
```

### List SSH Keys

**GET** `/api/security/keys`

List all SSH keys for the authenticated user.

#### Query Parameters

- `page` (optional): Page number (default: 1)
- `limit` (optional): Results per page (default: 20, max: 100)
- `active` (optional): Filter by active status (true/false)

#### Response

```json
{
  "keys": [
    {
      "id": 1,
      "keyId": "uuid",
      "name": "string",
      "description": "string",
      "fingerprint": "aa:bb:cc:dd:ee:ff...",
      "keySize": 4096,
      "isActive": true,
      "lastUsed": "2024-01-01T00:00:00.000Z",
      "expiresAt": "2024-12-31T23:59:59.000Z",
      "createdAt": "2024-01-01T00:00:00.000Z",
      "revokedAt": null,
      "revocationReason": null
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 5,
    "pages": 1
  }
}
```

### Deploy SSH Key

**POST** `/api/security/keys/{keyId}/deploy`

Deploy an SSH public key to a remote server.

#### Path Parameters

- `keyId` (required): UUID of the SSH key

#### Request Body

```json
{
  "host": "192.168.1.100",
  "port": 22,
  "username": "ubuntu",
  "password": "password123",
  "existingKeyId": "uuid (optional, for key-based auth)"
}
```

#### Response

```json
{
  "message": "SSH key deployed successfully",
  "result": {
    "success": true,
    "message": "Key deployed successfully"
  }
}
```

### Revoke SSH Key

**DELETE** `/api/security/keys/{keyId}`

Revoke an SSH key, making it inactive.

#### Path Parameters

- `keyId` (required): UUID of the SSH key

#### Request Body

```json
{
  "reason": "string (optional, max 255 chars)"
}
```

#### Response

```json
{
  "message": "SSH key revoked successfully"
}
```

## TLS Certificate Management

### Generate TLS Certificate

**POST** `/api/security/certs/generate`

Generate a new TLS certificate and private key.

#### Request Body

```json
{
  "name": "string (required, 1-255 chars)",
  "commonName": "string (required, 1-255 chars)",
  "organization": "string (optional, max 255 chars)",
  "validityDays": "integer (optional, 1-3650, default: 365)",
  "altNames": [
    "array of alternative names (optional)"
  ]
}
```

#### Response

```json
{
  "message": "TLS certificate generated successfully",
  "certificate": {
    "certificateId": "uuid",
    "name": "string",
    "certificate": "-----BEGIN CERTIFICATE-----...",
    "fingerprint": "AA:BB:CC:DD:EE:FF...",
    "subject": "CN=example.com,O=Organization",
    "validFrom": "2024-01-01T00:00:00.000Z",
    "validTo": "2024-12-31T23:59:59.000Z",
    "createdAt": "2024-01-01T00:00:00.000Z"
  }
}
```

### List TLS Certificates

**GET** `/api/security/certs`

List all TLS certificates for the authenticated user.

#### Query Parameters

- `page` (optional): Page number (default: 1)
- `limit` (optional): Results per page (default: 20, max: 100)
- `active` (optional): Filter by active status (true/false)

#### Response

```json
{
  "certificates": [
    {
      "id": 1,
      "certificateId": "uuid",
      "name": "string",
      "fingerprint": "AA:BB:CC:DD:EE:FF...",
      "subject": "CN=example.com,O=Organization",
      "validFrom": "2024-01-01T00:00:00.000Z",
      "validTo": "2024-12-31T23:59:59.000Z",
      "isActive": true,
      "lastUsed": "2024-01-01T00:00:00.000Z",
      "createdAt": "2024-01-01T00:00:00.000Z",
      "revokedAt": null
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 3,
    "pages": 1
  }
}
```

## Security Features

### Key Security Policies

- **SSH Keys**: RSA 4096-bit minimum size
- **TLS Certificates**: RSA 2048-bit minimum size
- **Encryption**: All private keys encrypted with AES-256-GCM
- **Automatic Rotation**: SSH keys rotated every 90 days
- **Certificate Expiry**: Default 1 year validity
- **Failed Auth Limit**: 5 attempts before lockout

### Audit Logging

All security operations are logged with the following information:

- Event type and action performed
- Resource type and ID
- User ID, IP address, and User-Agent
- Success/failure status
- Detailed error messages
- Severity level (LOW, MEDIUM, HIGH, CRITICAL)

### Security Headers

All API responses include security headers:

- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`

## Error Responses

All endpoints return consistent error responses:

```json
{
  "error": "Description of the error",
  "details": "Additional error details",
  "code": "ERROR_CODE"
}
```

### Common HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Access denied
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Rate Limiting

API endpoints are rate limited to prevent abuse:

- **Default**: 100 requests per 15-minute window per IP
- **Headers**: Rate limit information included in response headers
- **Exceeded**: Returns 429 status with retry information

## Examples

### Example: Generate and Deploy SSH Key

```bash
# 1. Generate SSH key
curl -X POST http://localhost:3000/api/security/keys/generate \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Web Server Key",
    "description": "SSH key for production web server",
    "expiresInDays": 90
  }'

# 2. Deploy to server
curl -X POST http://localhost:3000/api/security/keys/{keyId}/deploy \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "host": "192.168.1.100",
    "port": 22,
    "username": "ubuntu",
    "password": "password123"
  }'
```

### Example: Generate TLS Certificate

```bash
curl -X POST http://localhost:3000/api/security/certs/generate \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Web Certificate",
    "commonName": "api.rollo.games",
    "organization": "Rollo Games",
    "validityDays": 365,
    "altNames": [
      {"type": 2, "value": "api.rollo.games"},
      {"type": 2, "value": "www.api.rollo.games"}
    ]
  }'
```

## Database Schema

### SSH Keys Table

```sql
CREATE TABLE ssh_keys (
  id INT AUTO_INCREMENT PRIMARY KEY,
  key_id VARCHAR(36) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  public_key TEXT NOT NULL,
  private_key_encrypted TEXT NOT NULL,
  encryption_iv VARCHAR(32) NOT NULL,
  encryption_auth_tag VARCHAR(32) NOT NULL,
  fingerprint VARCHAR(255) UNIQUE NOT NULL,
  key_size INT DEFAULT 4096,
  is_active BOOLEAN DEFAULT TRUE,
  last_used DATETIME,
  expires_at DATETIME,
  created_by INT NOT NULL,
  created_at DATETIME DEFAULT NOW(),
  updated_at DATETIME DEFAULT NOW(),
  revoked_at DATETIME,
  revoked_by INT,
  revocation_reason VARCHAR(255)
);
```

### TLS Certificates Table

```sql
CREATE TABLE tls_certificates (
  id INT AUTO_INCREMENT PRIMARY KEY,
  certificate_id VARCHAR(36) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  certificate TEXT NOT NULL,
  private_key_encrypted TEXT NOT NULL,
  public_key TEXT NOT NULL,
  fingerprint VARCHAR(255) UNIQUE NOT NULL,
  serial_number VARCHAR(255) NOT NULL,
  subject TEXT NOT NULL,
  issuer TEXT NOT NULL,
  valid_from DATETIME NOT NULL,
  valid_to DATETIME NOT NULL,
  key_size INT DEFAULT 2048,
  algorithm VARCHAR(50) DEFAULT 'RSA',
  is_ca BOOLEAN DEFAULT FALSE,
  is_active BOOLEAN DEFAULT TRUE,
  ca_certificate_id VARCHAR(36),
  last_used DATETIME,
  created_by INT NOT NULL,
  created_at DATETIME DEFAULT NOW(),
  updated_at DATETIME DEFAULT NOW(),
  revoked_at DATETIME,
  revoked_by INT,
  revocation_reason VARCHAR(255)
);
```

### Security Audit Log Table

```sql
CREATE TABLE security_audit_logs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  event_type VARCHAR(100) NOT NULL,
  resource_type VARCHAR(50) NOT NULL,
  resource_id VARCHAR(255),
  user_id INT,
  ip_address VARCHAR(45),
  user_agent TEXT,
  action VARCHAR(100) NOT NULL,
  result ENUM('SUCCESS', 'FAILURE', 'ERROR') DEFAULT 'SUCCESS',
  details JSON,
  error_message TEXT,
  severity ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') DEFAULT 'LOW',
  created_at DATETIME DEFAULT NOW()
);
```