# Render CLI Installation and Usage Guide

## Installation

Since you're on macOS (Darwin), you have two installation options:

### Option 1: Using Homebrew (Recommended)
```bash
brew update && brew install render
```

### Option 2: Using the Install Script
```bash
curl -fsSL https://raw.githubusercontent.com/render-oss/cli/refs/heads/main/bin/install.sh | sh
```

## Authentication

After installation, authenticate with Render:

```bash
render login
```

This will open your browser to generate a CLI token. The token will be saved locally for future use.

### Alternative: Using API Key
If you prefer non-interactive authentication (useful for scripts), you can use an API key:

```bash
export RENDER_API_KEY="your-api-key-here"
```

## Monitoring Your Deployment

### 1. List Your Services
First, list all your services to find your prism-backend service:

```bash
render services
```

### 2. Check Deployment Status
View recent deployments for your service:

```bash
# List all deployments
render deploys list --service-name prism-backend-bwfx

# Or if you know the service ID
render deploys list --service-id srv-XXXXX
```

### 3. View Deployment Logs
To see logs for a specific deployment:

```bash
# Get logs for the most recent deployment
render logs --service-name prism-backend-bwfx

# Follow logs in real-time (like tail -f)
render logs --service-name prism-backend-bwfx --tail

# Get logs for a specific deployment
render deploys logs --deployment-id dep-XXXXX
```

### 4. Check Service Status
Get detailed information about your service:

```bash
render services show --name prism-backend-bwfx
```

### 5. SSH into Your Service (if available)
For debugging purposes, you can SSH into your running service:

```bash
render ssh --service-name prism-backend-bwfx
```

## Useful Commands for Monitoring

### Real-time Monitoring Script
Create a monitoring script to continuously check your deployment:

```bash
#!/bin/bash
# monitor-prism.sh

echo "Monitoring PRISM Backend on Render..."
echo "=================================="

# Show service status
echo "Service Status:"
render services show --name prism-backend-bwfx --output json | jq '.status, .suspendedAt, .createdAt'

echo -e "\nRecent Deployments:"
render deploys list --service-name prism-backend-bwfx --limit 5

echo -e "\nTailing logs (press Ctrl+C to stop):"
render logs --service-name prism-backend-bwfx --tail
```

### Check Deployment Health
```bash
# Get JSON output for scripting
render services show --name prism-backend-bwfx --output json

# Check if service is running
render services show --name prism-backend-bwfx --output json | jq '.suspended'
```

### Trigger a New Deployment
If you need to manually trigger a deployment:

```bash
render deploys create --service-name prism-backend-bwfx
```

## Troubleshooting Common Issues

### 1. Service Not Found
If you get a "service not found" error, try:
- List all services: `render services`
- Use the service ID instead of name
- Check if you're logged into the correct account

### 2. Authentication Issues
- Run `render login` again
- Check if your API key is expired
- Ensure you have the correct permissions

### 3. Log Access Issues
- Some service types may have limited log retention
- Free tier services may have shorter log history

## Environment Variables
You can also check and update environment variables:

```bash
# List environment variables
render env list --service-name prism-backend-bwfx

# Set an environment variable
render env set KEY=value --service-name prism-backend-bwfx
```

## Quick Reference

| Command | Description |
|---------|-------------|
| `render login` | Authenticate with Render |
| `render services` | List all services |
| `render logs --service-name NAME --tail` | Follow service logs |
| `render deploys list --service-name NAME` | List deployments |
| `render deploys create --service-name NAME` | Trigger deployment |
| `render ssh --service-name NAME` | SSH into service |
| `render services show --name NAME` | Get service details |

## Next Steps

1. Install the CLI using one of the methods above
2. Run `render login` to authenticate
3. Use `render services` to confirm your service name
4. Start monitoring with `render logs --service-name prism-backend-bwfx --tail`

For more detailed documentation, visit: https://render.com/docs/cli