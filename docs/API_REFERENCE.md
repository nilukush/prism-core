# PRISM API Reference

## Overview

The PRISM API is a RESTful API that provides programmatic access to all PRISM features. This document covers the core endpoints and their usage.

## Base URL

```
http://localhost:8100/api/v1
```

For production, replace with your domain:
```
https://api.your-domain.com/api/v1
```

## Authentication

PRISM uses JWT (JSON Web Token) authentication. Most endpoints require authentication.

### Login

```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=yourpassword&grant_type=password
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "refresh_expires_in": 604800
}
```

### Using the Token

Include the access token in the Authorization header:
```http
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### Refresh Token

```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "YOUR_REFRESH_TOKEN"
}
```

## Core Endpoints

### Organizations

#### List Organizations
```http
GET /organizations
Authorization: Bearer YOUR_ACCESS_TOKEN
```

Response:
```json
[
  {
    "id": 1,
    "name": "My Organization",
    "slug": "my-org",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

### Projects

#### List Projects
```http
GET /projects
Authorization: Bearer YOUR_ACCESS_TOKEN
```

Query Parameters:
- `organization_id` (optional): Filter by organization
- `page` (default: 1): Page number
- `limit` (default: 20): Items per page

#### Create Project
```http
POST /projects
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "name": "New Project",
  "key": "PROJ",
  "description": "Project description",
  "organization_id": 1
}
```

### Product Requirements Documents (PRDs)

#### Generate PRD with AI
```http
POST /ai/generate/prd
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "product_name": "My Product",
  "product_description": "A revolutionary product that...",
  "target_audience": "Developers and product managers",
  "key_features": ["Feature 1", "Feature 2"],
  "success_metrics": ["User adoption", "Revenue growth"],
  "constraints": ["Budget: $100k", "Timeline: 6 months"],
  "provider": "anthropic"  // or "openai", "ollama"
}
```

Response:
```json
{
  "content": "# Product Requirements Document\n\n## Executive Summary...",
  "metadata": {
    "provider": "anthropic",
    "model": "claude-3-sonnet-20240229",
    "tokens_used": 2500,
    "generation_time": 15.3
  }
}
```

#### Save PRD
```http
POST /documents/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "title": "My Product PRD",
  "content": "# Product Requirements Document...",
  "document_type": "prd",
  "project_id": 1,
  "metadata": {
    "ai_generated": true,
    "provider": "anthropic"
  }
}
```

#### List Documents
```http
GET /documents/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

Query Parameters:
- `project_id`: Filter by project
- `document_type`: Filter by type (prd, story, spec)
- `status`: Filter by status (draft, published, archived)

### User Stories

#### Generate User Stories
```http
POST /ai/generate/stories
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "requirements": [
    "Users should be able to login with email",
    "Users should be able to reset their password"
  ],
  "project_context": "E-commerce platform",
  "format": "detailed",
  "include_acceptance_criteria": true,
  "include_test_cases": true
}
```

### Analytics

#### Sprint Velocity Analysis
```http
POST /ai/analyze/velocity
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "sprint_data": [
    {
      "sprint_name": "Sprint 1",
      "planned_points": 40,
      "completed_points": 35,
      "team_size": 5
    }
  ],
  "include_predictions": true
}
```

## Error Handling

All errors follow this format:
```json
{
  "detail": "Error message",
  "status_code": 400,
  "type": "validation_error"
}
```

Common error codes:
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `429` - Rate Limited
- `500` - Internal Server Error

## Rate Limiting

Default rate limits:
- **General endpoints**: 60 requests/minute
- **AI endpoints**: 10 requests/minute
- **Auth endpoints**: 20 requests/hour

Rate limit headers:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640995200
```

## Pagination

List endpoints support pagination:
```http
GET /projects?page=2&limit=50
```

Response includes pagination metadata:
```json
{
  "items": [...],
  "total": 150,
  "page": 2,
  "limit": 50,
  "pages": 3
}
```

## Webhooks

Configure webhooks for real-time updates:
```http
POST /webhooks
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "url": "https://your-domain.com/webhook",
  "events": ["document.created", "project.updated"],
  "secret": "your-webhook-secret"
}
```

## SDKs and Libraries

Official SDKs (coming soon):
- Python: `pip install prism-sdk`
- JavaScript/TypeScript: `npm install @prism/sdk`
- Go: `go get github.com/prism/prism-go`

## API Versioning

The API version is included in the URL path. The current version is `v1`.

When we release v2, v1 will continue to work for at least 6 months.

## OpenAPI Specification

The complete OpenAPI (Swagger) specification is available at:
```
http://localhost:8100/docs
```

You can also download the OpenAPI JSON:
```
http://localhost:8100/openapi.json
```

## Support

For API support:
- [GitHub Issues](https://github.com/nilukush/prism-core/issues)
- [API Discussion Forum](https://github.com/nilukush/prism-core/discussions/categories/api)