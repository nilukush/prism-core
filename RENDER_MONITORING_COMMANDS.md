# 🚀 Render Deployment Monitoring Commands

## Your Service Details
- **Service ID**: `srv-d1r6j47fte5s73cnonqg`
- **Service Name**: `prism-backend`
- **URL**: https://prism-backend-bwfx.onrender.com

## Monitor Deployment Status

### 1. Check Current Deployment Status
```bash
render deploys list srv-d1r6j47fte5s73cnonqg -o json | jq '.[0] | {status: .status, started: .startedAt, trigger: .trigger}'
```

### 2. Watch Deployment Progress (run this every 10 seconds)
```bash
while true; do 
  clear
  echo "=== Deployment Status ==="
  render deploys list srv-d1r6j47fte5s73cnonqg -o json | jq '.[0] | {status: .status, started: .startedAt}'
  sleep 10
done
```

### 3. View Build Logs (after deployment completes)
```bash
# Get the latest deployment ID
DEPLOY_ID=$(render deploys list srv-d1r6j47fte5s73cnonqg -o json | jq -r '.[0].id')
echo "Deployment ID: $DEPLOY_ID"
```

### 4. Check Service Health
```bash
# Check if service is running
curl -I https://prism-backend-bwfx.onrender.com/api/health
```

### 5. SSH into Service (to verify DEBUG=true)
```bash
render ssh srv-d1r6j47fte5s73cnonqg
# Once connected, run:
env | grep DEBUG
```

## Quick Status Check

Run this command to see current deployment status:
```bash
render deploys list srv-d1r6j47fte5s73cnonqg -o json | jq -r '.[0] | "Status: \(.status)\nStarted: \(.startedAt)\nTrigger: \(.trigger)"'
```

## Expected Deployment Flow
1. `build_in_progress` - Building Docker image
2. `update_in_progress` - Deploying new version
3. `live` - Deployment complete

## After Deployment Completes

Test if DEBUG mode is working:
```bash
# This should now allow login with pending users
curl -X POST https://prism-backend-bwfx.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=nilukush@gmail.com&password=YOUR_PASSWORD&grant_type=password"
```

If successful, you'll get an access token!