# SANGKURIANG API Documentation

## Overview

SANGKURIANG API is a RESTful API that provides cryptographic project auditing, funding, and community features for Indonesian developers. The API is built with FastAPI and provides comprehensive endpoints for authentication, project management, audit services, and payment processing.

## Base URL

```
Development: http://localhost:8000/api/v1
Production: https://api.sangkuriang.id/api/v1
```

## Authentication

The API uses JWT (JSON Web Token) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Getting a Token

**POST** `/auth/login`

Request:
```json
{
  "username": "user@example.com",
  "password": "your-password"
}
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "John Doe",
    "email": "user@example.com",
    "role": "user"
  }
}
```

## API Endpoints

### Authentication

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | Register new user | No |
| POST | `/auth/login` | Login user | No |
| GET | `/auth/verify` | Verify token | Yes |
| POST | `/auth/refresh` | Refresh token | Yes |
| POST | `/auth/reset-password` | Request password reset | No |
| POST | `/auth/reset-password/confirm` | Confirm password reset | No |
| PUT | `/auth/change-password` | Change password | Yes |
| GET | `/auth/me` | Get user profile | Yes |
| PUT | `/auth/me` | Update user profile | Yes |

### Projects

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/projects` | List all projects | Optional |
| GET | `/projects/{id}` | Get project details | Optional |
| POST | `/projects` | Create new project | Yes |
| PUT | `/projects/{id}` | Update project | Yes (Owner/Admin) |
| DELETE | `/projects/{id}` | Delete project | Yes (Owner/Admin) |
| GET | `/projects/{id}/funding` | Get project funding | Optional |
| POST | `/projects/{id}/funding` | Fund project | Yes |

### Audit Services

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/audit/request` | Request security audit | Yes |
| GET | `/audit/requests` | List audit requests | Yes |
| GET | `/audit/{id}` | Get audit details | Yes |
| GET | `/audit/badges` | List audit badges | Optional |
| GET | `/audit/badges/{id}` | Get badge details | Optional |

### Funding & Payments

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/funding/history` | Get funding history | Yes |
| GET | `/payment/methods` | List payment methods | Optional |
| POST | `/payment/process` | Process payment | Yes |
| GET | `/payment/transaction/{id}` | Get transaction details | Yes |

## Request/Response Examples

### Create Project

**POST** `/projects`

Request:
```json
{
  "title": "Secure Messaging Protocol",
  "description": "A new cryptographic protocol for secure messaging using post-quantum algorithms...",
  "category": "cryptography",
  "funding_goal": 50000000,
  "deadline": "2024-12-31T23:59:59Z",
  "github_url": "https://github.com/user/secure-messaging",
  "image_url": "https://example.com/project-image.jpg",
  "tags": ["cryptography", "messaging", "post-quantum"]
}
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Secure Messaging Protocol",
  "description": "A new cryptographic protocol for secure messaging...",
  "category": "cryptography",
  "funding_goal": 50000000,
  "current_funding": 0,
  "funding_percentage": 0,
  "backer_count": 0,
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "John Doe",
    "email": "user@example.com"
  }
}
```

### Request Security Audit

**POST** `/audit/request`

Request:
```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "notes": "Please focus on the cryptographic implementation and key management."
}
```

Response:
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "notes": "Please focus on the cryptographic implementation...",
  "created_at": "2024-01-01T12:00:00Z",
  "project": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Secure Messaging Protocol"
  }
}
```

### Process Payment

**POST** `/payment/process`

Request:
```json
{
  "funding_id": "770e8400-e29b-41d4-a716-446655440002",
  "payment_method": "gopay",
  "payment_details": {
    "phone_number": "081234567890"
  }
}
```

Response:
```json
{
  "success": true,
  "message": "Payment initiated successfully",
  "transaction_id": "TRX123456789",
  "payment_url": "https://payment.midtrans.com/redirect/TRX123456789",
  "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "amount": 100000,
  "status": "pending"
}
```

## Error Responses

All error responses follow this format:

```json
{
  "success": false,
  "error": "VALIDATION_ERROR",
  "message": "Validation failed",
  "details": {
    "field": "email",
    "message": "Invalid email format"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Error Codes

| Code | Description |
|------|-------------|
| VALIDATION_ERROR | Request validation failed |
| AUTHENTICATION_ERROR | Authentication failed |
| AUTHORIZATION_ERROR | Insufficient permissions |
| NOT_FOUND | Resource not found |
| RATE_LIMIT_ERROR | Rate limit exceeded |
| SERVER_ERROR | Internal server error |
| PAYMENT_ERROR | Payment processing failed |
| AUDIT_ERROR | Audit processing failed |

## Rate Limiting

API endpoints are rate-limited to prevent abuse:

- **Authentication endpoints**: 5 requests per minute per IP
- **General endpoints**: 60 requests per minute per user/IP
- **Payment endpoints**: 10 requests per minute per user
- **Audit endpoints**: 5 requests per minute per user

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640995200
```

## Pagination

List endpoints support pagination:

**GET** `/projects?page=2&limit=20&sort_by=created_at&sort_order=desc`

Response:
```json
{
  "items": [...],
  "total": 150,
  "page": 2,
  "limit": 20,
  "total_pages": 8
}
```

## Filtering and Search

List endpoints support filtering and search:

**GET** `/projects?search=cryptography&category=security&status=active`

Supported filters vary by endpoint but commonly include:
- `search`: Text search across relevant fields
- `category`: Filter by category
- `status`: Filter by status
- `date_from`, `date_to`: Date range filtering

## Webhooks

The API supports webhooks for real-time notifications:

### Webhook Events

- `payment.completed`: Payment completed successfully
- `payment.failed`: Payment failed
- `project.funded`: Project reached funding goal
- `audit.completed`: Security audit completed
- `user.registered`: New user registered

### Webhook Payload

```json
{
  "event": "payment.completed",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "transaction_id": "TRX123456789",
    "amount": 100000,
    "status": "completed",
    "project_id": "550e8400-e29b-41d4-a716-446655440000"
  },
  "signature": "sha256=abc123..."
}
```

### Webhook Security

Webhooks are signed with HMAC-SHA256. Verify the signature using your webhook secret.

## SDK and Libraries

### Official SDKs

- **JavaScript/TypeScript**: `@sangkuriang/sdk`
- **Python**: `sangkuriang-sdk`
- **Flutter/Dart**: `sangkuriang_flutter`

### Community Libraries

- **PHP**: `sangkuriang-php` (community maintained)
- **Go**: `sangkuriang-go` (community maintained)

## Testing

Use the sandbox environment for testing:

**Base URL**: `https://sandbox-api.sangkuriang.id/api/v1`

Test credentials and sample data are available in the sandbox environment.

## Support

For API support:
- **Documentation**: https://docs.sangkuriang.id
- **Support Email**: support@sangkuriang.id
- **Discord**: https://discord.gg/sangkuriang
- **GitHub Issues**: https://github.com/sangkuriang/api/issues