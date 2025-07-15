#!/bin/bash

# Script to check for AI API calls in logs and identify potential sources

echo "=== Checking for AI API Calls in Backend Logs ==="
echo

echo "1. Checking for Anthropic API calls..."
docker compose logs backend | grep -E "anthropic|claude|sk-ant" | tail -20

echo
echo "2. Checking for health check calls..."
docker compose logs backend | grep -E "health.*detailed|check_external_services" | tail -20

echo
echo "3. Checking for PRD generation calls..."
docker compose logs backend | grep -E "/ai/generate/prd|generate_prd" | tail -20

echo
echo "4. Checking current running processes that might call APIs..."
ps aux | grep -E "curl|wget|health" | grep -v grep

echo
echo "5. Checking cron jobs..."
crontab -l 2>/dev/null || echo "No crontab for current user"

echo
echo "6. Checking for any monitoring containers..."
docker ps | grep -E "prometheus|grafana|monitor"

echo
echo "=== Recommendations ==="
echo "1. Monitor your Anthropic console for the next hour"
echo "2. If costs continue to increase, check:"
echo "   - Browser developer tools (Network tab) for auto-refresh"
echo "   - Any API testing tools (Postman, Insomnia) with collections"
echo "   - CI/CD pipelines that might be testing health endpoints"
echo "3. The health check fix has been applied - AI providers will no longer be called"