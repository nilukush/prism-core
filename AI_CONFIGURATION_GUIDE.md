# PRISM AI Configuration Guide

## Overview

This guide explains how to configure PRISM to use real AI providers (OpenAI, Anthropic, etc.) instead of the mock service for PRD generation and other AI features.

## Supported AI Providers

PRISM supports the following AI providers:

1. **OpenAI** - GPT-4, GPT-4 Turbo, GPT-3.5 Turbo
2. **Anthropic** - Claude 3 Opus, Sonnet, Haiku
3. **Ollama** - Local models (Llama2, Mixtral)
4. **Mock** - Testing service (default)

## Configuration Steps

### 1. Choose Your AI Provider

Based on enterprise best practices for 2025:

#### For PRD Generation (Recommended):
- **Primary**: Anthropic Claude 3 Sonnet - Best for writing tasks, content generation
- **Fallback**: OpenAI GPT-4 Turbo - Better for complex reasoning
- **Budget**: Claude 3 Haiku or GPT-3.5 Turbo - For high-volume, simpler tasks

#### Cost Comparison (per 1M tokens):
| Model | Input | Output | Best For |
|-------|-------|--------|----------|
| Claude 3 Opus | $15 | $75 | Complex analysis |
| Claude 3 Sonnet | $3 | $15 | PRDs, documentation |
| Claude 3 Haiku | $0.25 | $1.25 | Simple tasks |
| GPT-4 Turbo | $10 | $30 | Complex reasoning |
| GPT-3.5 Turbo | $0.50 | $1.50 | Budget option |

### 2. Obtain API Keys

#### OpenAI:
1. Go to https://platform.openai.com/api-keys
2. Create a new secret key
3. Set usage limits to prevent unexpected costs
4. Enable only required models

#### Anthropic:
1. Go to https://console.anthropic.com/
2. Generate an API key
3. Set up usage alerts
4. Configure rate limits

### 3. Update Environment Configuration

Edit `backend/.env`:

```env
# AI Provider Selection
DEFAULT_LLM_PROVIDER=anthropic  # Options: openai, anthropic, ollama, mock
DEFAULT_LLM_MODEL=claude-3-sonnet-20240229  # Or your chosen model

# OpenAI Configuration (if using OpenAI)
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_ORG_ID=org-your-org-id  # Optional
OPENAI_API_BASE=https://api.openai.com/v1  # Default

# Anthropic Configuration (if using Anthropic)
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Model Settings
LLM_TEMPERATURE=0.7  # 0-2, higher = more creative
LLM_MAX_TOKENS=4000  # Increase for longer PRDs
LLM_REQUEST_TIMEOUT=60  # Seconds

# Cost Control
LLM_ENABLE_STREAMING=true  # Better UX, same cost
LLM_CACHE_ENABLED=true  # Cache responses
LLM_CACHE_TTL=3600  # Cache for 1 hour
```

### 4. Multi-Model Strategy (Advanced)

For cost optimization, configure model routing based on task complexity:

```env
# Model Routing Rules
PRD_GENERATION_MODEL=claude-3-sonnet-20240229
STORY_GENERATION_MODEL=claude-3-haiku-20240307
COMPLEX_ANALYSIS_MODEL=gpt-4-turbo-preview
SIMPLE_TASKS_MODEL=gpt-3.5-turbo
```

### 5. Security Best Practices

#### API Key Management:
```bash
# Never commit API keys to version control
echo "OPENAI_API_KEY=" >> .gitignore
echo "ANTHROPIC_API_KEY=" >> .gitignore

# Use environment-specific files
cp backend/.env backend/.env.local
```

#### Rate Limiting:
```env
# Protect against abuse
RATE_LIMIT_ENABLED=true
AI_RATE_LIMIT_PER_MINUTE=10
AI_RATE_LIMIT_PER_HOUR=100
```

#### Data Privacy:
```env
# Don't send sensitive data to AI
AI_REDACT_SENSITIVE_DATA=true
AI_LOG_PROMPTS=false  # Disable in production
```

### 6. Restart Services

After updating configuration:

```bash
# Restart backend to apply changes
docker compose restart backend

# Verify configuration
docker compose exec backend python -c "from backend.src.core.config import settings; print(f'AI Provider: {settings.DEFAULT_LLM_PROVIDER}')"
```

## Testing AI Integration

### 1. Test Connection

Create a test script `test_ai_connection.py`:

```python
import asyncio
from backend.src.services.ai.factory import AIServiceFactory
from backend.src.services.ai.base import AIProvider, AIRequest

async def test_ai():
    provider = AIProvider.ANTHROPIC  # or OPENAI
    service = AIServiceFactory.create(provider)
    
    request = AIRequest(
        prompt="Write a one-sentence summary about product management.",
        max_tokens=100
    )
    
    async with service as ai:
        response = await ai.generate(request)
        print(f"Provider: {response.provider}")
        print(f"Model: {response.model}")
        print(f"Response: {response.content}")
        print(f"Tokens used: {response.usage}")

asyncio.run(test_ai())
```

### 2. Test PRD Generation

Using the API:

```bash
# Get auth token
TOKEN=$(curl -s -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=nilukush@gmail.com&password=Test123!@#&grant_type=password" \
  | jq -r '.access_token')

# Generate PRD
curl -X POST http://localhost:8100/api/v1/ai/generate/prd \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "product_name": "AI-Powered Task Manager",
    "description": "A smart task management app that uses AI to prioritize and schedule tasks",
    "target_audience": "Busy professionals",
    "key_features": ["AI prioritization", "Calendar integration", "Team collaboration"],
    "ai_provider": "anthropic"
  }'
```

## Cost Monitoring & Optimization

### 1. Enable Usage Tracking

```env
# Track AI usage metrics
AI_METRICS_ENABLED=true
AI_COST_TRACKING_ENABLED=true
```

### 2. Set Budget Alerts

```python
# backend/src/core/ai_budget.py
AI_MONTHLY_BUDGET = {
    "openai": 500.00,  # USD
    "anthropic": 300.00,
    "total": 800.00
}

AI_ALERT_THRESHOLDS = [0.5, 0.8, 0.95]  # Alert at 50%, 80%, 95%
```

### 3. Implement Caching

```env
# Redis caching for repeated queries
AI_CACHE_ENABLED=true
AI_CACHE_KEY_PREFIX=ai_cache:
AI_CACHE_TTL=3600  # 1 hour
```

## Troubleshooting

### Common Issues:

1. **401 Unauthorized**
   - Check API key is correct
   - Verify key has required permissions
   - Ensure no extra spaces in .env file

2. **Rate Limit Errors**
   - Implement exponential backoff
   - Use different keys for dev/prod
   - Consider upgrading API tier

3. **Timeout Errors**
   - Increase `LLM_REQUEST_TIMEOUT`
   - Use streaming for long responses
   - Optimize prompts for brevity

4. **High Costs**
   - Monitor token usage
   - Use cheaper models for simple tasks
   - Implement prompt caching
   - Set strict max_tokens limits

### Debug Mode:

```env
# Enable detailed logging
AI_DEBUG_MODE=true
LOG_AI_REQUESTS=true
LOG_AI_RESPONSES=false  # Be careful with sensitive data
```

## Production Checklist

- [ ] API keys stored securely (environment variables, not in code)
- [ ] Rate limiting enabled
- [ ] Usage monitoring configured
- [ ] Budget alerts set up
- [ ] Caching enabled for common queries
- [ ] Fallback to mock service for failures
- [ ] Data privacy controls in place
- [ ] Audit logging enabled
- [ ] Model routing optimized for cost/performance
- [ ] Regular review of AI costs and usage

## Best Practices Summary

1. **Start Small**: Test with GPT-3.5 Turbo or Claude Haiku before upgrading
2. **Monitor Costs**: Set up alerts before hitting budget limits
3. **Cache Aggressively**: PRD templates rarely change
4. **Use Model Routing**: Send simple tasks to cheaper models
5. **Implement Fallbacks**: Always have a backup provider
6. **Secure Keys**: Rotate regularly, use separate keys per environment
7. **Optimize Prompts**: Shorter prompts = lower costs
8. **Stream Responses**: Better UX without extra cost
9. **Log Wisely**: Track usage without storing sensitive data
10. **Review Regularly**: AI models and pricing change frequently

## Next Steps

1. Choose your primary AI provider
2. Obtain and configure API keys
3. Update backend/.env with your configuration
4. Restart the backend service
5. Test PRD generation with real AI
6. Monitor usage and costs
7. Optimize based on actual usage patterns

Remember: The mock service is always available as a fallback during development or if API limits are reached.