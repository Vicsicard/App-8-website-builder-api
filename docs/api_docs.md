# Personal Brand Website Builder API Documentation

## Overview

The Website Builder API provides endpoints for building and publishing personal brand websites. It supports asynchronous builds with status tracking and preview functionality.

## Base URL

```
https://api.websitebuilder.com/v1
```

## Authentication

All API requests require a valid API key in the `Authorization` header:

```
Authorization: Bearer your-api-key
```

## Endpoints

### Build Website

Triggers a new website build for a user.

```
POST /build-site
```

#### Request Body

```json
{
    "user_id": "string",       // Required: User's unique identifier
    "preview_only": boolean    // Optional: If true, only creates preview (default: false)
}
```

#### Response Format

```json
{
    "build_id": "string",      // Unique build identifier
    "status": "string",        // Initial status (always "queued")
    "preview_url": "string"    // Optional: URL to preview (if available)
}
```

#### Example Request

```bash
curl -X POST https://api.websitebuilder.com/v1/build-site \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "preview_only": true
  }'
```

#### Example Response

```json
{
    "build_id": "build_abc123",
    "status": "queued"
}
```

### Check Build Status

Get the current status of a build.

```
GET /build-status/{build_id}
```

#### Response Format

```json
{
    "build_id": "string",      // Build identifier
    "status": "string",        // Current status
    "preview_url": "string",   // Preview URL (if complete)
    "created_at": "string",    // ISO timestamp
    "updated_at": "string",    // ISO timestamp
    "error_message": "string"  // Error details (if failed)
}
```

#### Example Response

```json
{
    "build_id": "build_abc123",
    "status": "complete",
    "preview_url": "https://preview.websitebuilder.com/sites/user_123/latest/index.html",
    "created_at": "2025-04-07T12:00:00Z",
    "updated_at": "2025-04-07T12:01:30Z"
}
```

### Get Preview Frame

Get an HTML iframe for previewing a build.

```
GET /preview/{build_id}?height=800
```

#### Query Parameters

- `height`: Iframe height in pixels (default: 800, min: 100, max: 4000)

#### Response

Returns HTML with an embedded iframe for the preview.

## Status Codes

| Status | Description |
|--------|-------------|
| `queued` | Build is queued for processing |
| `in_progress` | Build is currently being processed |
| `complete` | Build completed successfully |
| `error` | Build failed (check error_message) |

## Error Codes

| HTTP Code | Message | Description |
|-----------|---------|-------------|
| 400 | Invalid request | Request body is malformed |
| 401 | Unauthorized | Missing or invalid API key |
| 404 | Build not found | Specified build_id doesn't exist |
| 422 | Validation error | Invalid input parameters |
| 429 | Too many requests | Rate limit exceeded |
| 500 | Internal error | Server-side error |

## Common Errors

1. **Missing Content**
   ```json
   {
       "status": "error",
       "error_message": "User has no approved bio content"
   }
   ```

2. **Build Failed**
   ```json
   {
       "status": "error",
       "error_message": "Failed to publish to storage: Network error"
   }
   ```

## Data Formats

### Story Chunks
```json
{
    "story_chunks": [
        {
            "title": "string",       // Required
            "content": "string",     // Required, HTML content
            "image": "string",       // Optional, URL
            "order_index": number,   // Required
            "tags": ["string"]       // Optional
        }
    ]
}
```
Fallback: If empty or missing, story section will not be rendered

### Values
```json
{
    "values": [
        {
            "title": "string",       // Required
            "description": "string", // Required
            "icon": "string",       // Optional, CSS class name
            "order_index": number    // Required
        }
    ]
}
```
Fallback: If empty or missing, values section will not be rendered

### Social Links
```json
{
    "social_links": [
        {
            "platform": "string",    // Required (e.g., "twitter")
            "url": "string",         // Required
            "icon": "string"         // Required, CSS class name
        }
    ]
}
```
Fallback: If empty or missing, social links section will not be rendered

### Required Content
The following content is required for a successful build:

1. **Bio**: At minimum must include:
   - `name`: User's name
   - `summary`: Brief bio text

2. **Images**: At minimum must include:
   - `profile`: Profile photo URL
   - `background`: Background image URL

All other content sections are optional and will be gracefully omitted if missing.

## Rate Limits

- 60 requests per minute per API key
- 10 concurrent builds per user
- 100 builds per day per user

## Deployment Checklist

1. **Environment Setup**
   - [ ] Set `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`
   - [ ] Configure CORS origins for App 5 domain
   - [ ] Set rate limiting parameters

2. **Database Setup**
   - [ ] Run migrations for `website_builds` table
   - [ ] Run migrations for `website_versions` table
   - [ ] Create necessary indexes

3. **Storage Setup**
   - [ ] Create `websites` bucket
   - [ ] Create `previews` bucket
   - [ ] Configure CORS for preview bucket
   - [ ] Set up storage policies

4. **API Deployment**
   - [ ] Update API base URL in App 5
   - [ ] Deploy API with proper scaling
   - [ ] Set up monitoring
   - [ ] Configure error reporting

5. **Testing**
   - [ ] Run unit tests
   - [ ] Run integration tests
   - [ ] Verify CORS with App 5
   - [ ] Test preview functionality

6. **Security**
   - [ ] Review API key permissions
   - [ ] Check storage access policies
   - [ ] Verify rate limits
   - [ ] Enable request logging

7. **Monitoring**
   - [ ] Set up build status alerts
   - [ ] Configure error notifications
   - [ ] Set up usage metrics
   - [ ] Monitor storage usage

## Best Practices

1. **Error Handling**
   - Always check build status before accessing preview
   - Implement exponential backoff for status polling
   - Handle network errors gracefully

2. **Performance**
   - Use preview_only for rapid iterations
   - Clean up old previews
   - Optimize asset sizes

3. **Integration**
   ```javascript
   // Example App 5 integration
   async function buildWebsite(userId) {
       // Start build
       const buildResponse = await fetch('/api/build-site', {
           method: 'POST',
           headers: {
               'Authorization': `Bearer ${API_KEY}`,
               'Content-Type': 'application/json'
           },
           body: JSON.stringify({ user_id: userId })
       });
       
       const { build_id } = await buildResponse.json();
       
       // Poll status
       while (true) {
           const statusResponse = await fetch(`/api/build-status/${build_id}`);
           const status = await statusResponse.json();
           
           if (status.status === 'complete') {
               return status.preview_url;
           }
           
           if (status.status === 'error') {
               throw new Error(status.error_message);
           }
           
           await new Promise(resolve => setTimeout(resolve, 1000));
       }
   }
   ```
