# 🤖 Configure AI for PRISM Production

Since you've successfully tested AI PRD generation locally, here's how to configure it for production.

## 🎯 Your Current Setup

**Local (Working)**:
- Provider: Anthropic
- Model: Claude 3 Sonnet
- Successfully generating PRDs

**Production (To Configure)**:
- Currently: Mock provider
- Goal: Real AI with cost controls

## 💰 AI Provider Options for Production

### Option 1: OpenAI GPT-3.5 (Most Cost-Effective)

**Monthly Cost Estimate**: $5-20 for startup usage

```bash
# Add to .env.production
DEFAULT_LLM_PROVIDER=openai
DEFAULT_LLM_MODEL=gpt-3.5-turbo
OPENAI_API_KEY=sk-...your-key-here

# Cost controls
LLM_MAX_TOKENS=2000              # Sufficient for PRDs
LLM_TEMPERATURE=0.7              # Balanced output
AI_MONTHLY_BUDGET_USD=20         # Stop at $20
AI_CACHE_ENABLED=true            # Save 80% with caching
AI_CACHE_TTL=86400               # 24-hour cache
```

**Get Free Credits**:
1. Sign up at https://platform.openai.com ($5 free)
2. Create API key
3. Good for ~2,500 PRD generations!

### Option 2: Anthropic Claude (Your Local Choice)

**Monthly Cost Estimate**: $15-50 for startup usage

```bash
# Add to .env.production
DEFAULT_LLM_PROVIDER=anthropic
DEFAULT_LLM_MODEL=claude-3-haiku-20240307  # Cheaper than Sonnet
# Or keep: claude-3-sonnet-20240229 (better quality)
ANTHROPIC_API_KEY=sk-ant-api03-...your-key-here

# Anthropic settings
LLM_MAX_TOKENS=3000              # Claude handles more
LLM_TEMPERATURE=0.7
AI_CACHE_ENABLED=true
```

**Note**: Claude Haiku is 10x cheaper than Sonnet with good quality

### Option 3: Hybrid Approach (Recommended)

Use different models for different features:

```bash
# Primary: Cheap model for most tasks
DEFAULT_LLM_PROVIDER=openai
DEFAULT_LLM_MODEL=gpt-3.5-turbo
OPENAI_API_KEY=sk-...

# Fallback: Quality model for complex PRDs
FALLBACK_LLM_PROVIDER=anthropic
FALLBACK_LLM_MODEL=claude-3-haiku-20240307
ANTHROPIC_API_KEY=sk-ant-...

# Feature-specific models
AI_MODEL_CONFIG={
  "simple_stories": "gpt-3.5-turbo",
  "complex_prd": "claude-3-sonnet-20240229",
  "chat": "gpt-3.5-turbo"
}
```

## 🚀 Production Setup Steps

### Step 1: Choose Your Strategy

Based on your testing and budget:

**A) Start Cheap (Recommended)**:
- Use OpenAI GPT-3.5 for everything
- Cost: ~$0.002 per PRD
- Upgrade later if needed

**B) Match Local Setup**:
- Use Claude 3 Haiku (not Sonnet)
- Cost: ~$0.003 per PRD
- Similar quality, much cheaper

**C) Premium Experience**:
- Keep Claude 3 Sonnet
- Cost: ~$0.015 per PRD
- Best quality

### Step 2: Update .env.production

```bash
cd /Users/nileshkumar/gh/prism/prism-core

# Edit the file
nano .env.production
```

Replace the AI section:

```bash
# ===== AI CONFIGURATION =====
# Option A: OpenAI (Cheapest)
DEFAULT_LLM_PROVIDER=openai
DEFAULT_LLM_MODEL=gpt-3.5-turbo
OPENAI_API_KEY=sk-proj-...your-key-here

# Option B: Anthropic Haiku (Balanced)
# DEFAULT_LLM_PROVIDER=anthropic
# DEFAULT_LLM_MODEL=claude-3-haiku-20240307
# ANTHROPIC_API_KEY=sk-ant-api03-...your-key-here

# Essential Settings
LLM_MAX_TOKENS=2000
LLM_TEMPERATURE=0.7
LLM_REQUEST_TIMEOUT=60

# Cost Controls (IMPORTANT!)
AI_CACHE_ENABLED=true
AI_CACHE_TTL=86400
RATE_LIMIT_AI_PER_MINUTE=5
AI_DAILY_REQUEST_LIMIT=500
AI_USER_MONTHLY_LIMIT=20
```

### Step 3: Test Before Deploying

```bash
# Test your configuration
python scripts/verify-connections.py

# Test AI specifically
python -c "
import os
os.environ['OPENAI_API_KEY'] = 'sk-...'  # Your key
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(
    model='gpt-3.5-turbo',
    messages=[{'role': 'user', 'content': 'Test'}],
    max_tokens=10
)
print('✓ AI working:', response.choices[0].message.content)
"
```

### Step 4: Deploy with AI

When deploying to Render, add these environment variables:

```yaml
# Essential AI Config
DEFAULT_LLM_PROVIDER: openai
DEFAULT_LLM_MODEL: gpt-3.5-turbo
OPENAI_API_KEY: sk-...your-key

# Cost Protection
LLM_MAX_TOKENS: 2000
AI_CACHE_ENABLED: true
AI_CACHE_TTL: 86400
RATE_LIMIT_AI_PER_MINUTE: 5
AI_MONTHLY_BUDGET_USD: 20
```

## 💡 Cost Optimization Tips

### 1. Start with Heavy Caching
```python
# Reduces costs by 80%
AI_CACHE_ENABLED=true
AI_CACHE_TTL=86400  # 24 hours
AI_SEMANTIC_CACHE=true  # Cache similar queries
```

### 2. Implement User Limits
```python
# Prevent abuse
AI_USER_DAILY_LIMIT=5  # 5 PRDs per day per user
AI_USER_MONTHLY_LIMIT=50  # 50 per month
```

### 3. Use Tiered Models
```python
# Pseudocode for cost optimization
if len(requirements) < 500:
    model = "gpt-3.5-turbo"  # $0.002
elif complexity == "high":
    model = "claude-3-sonnet"  # $0.015
else:
    model = "claude-3-haiku"  # $0.003
```

## 📊 Expected Costs

### For 100 Active Users (Monthly)

| Scenario | Model | PRDs/User | Total Cost |
|----------|-------|-----------|------------|
| **Conservative** | GPT-3.5 | 5 | $1 |
| **Moderate** | GPT-3.5 | 20 | $4 |
| **Heavy** | GPT-3.5 | 50 | $10 |
| **Premium** | Claude Haiku | 20 | $6 |
| **Luxury** | Claude Sonnet | 20 | $30 |

## 🚨 Important Warnings

### 1. API Key Security
```bash
# NEVER commit API keys
echo ".env.production" >> .gitignore
echo "*api_key*" >> .gitignore
```

### 2. Set Budget Alerts
- OpenAI: Set at https://platform.openai.com/usage
- Anthropic: Set at https://console.anthropic.com/settings/billing

### 3. Monitor Usage Daily
```bash
# Add monitoring endpoint
curl https://your-backend.onrender.com/api/v1/admin/ai-usage
```

## 🎯 Recommended Production Config

For a zero-budget startup, here's the optimal configuration:

```bash
# .env.production
# ===== AI CONFIGURATION =====
DEFAULT_LLM_PROVIDER=openai
DEFAULT_LLM_MODEL=gpt-3.5-turbo
OPENAI_API_KEY=sk-...your-key-here

# Strict Limits
LLM_MAX_TOKENS=1500              # Enough for PRDs
LLM_TEMPERATURE=0.7              # Consistent output
AI_CACHE_ENABLED=true            # Essential!
AI_CACHE_TTL=86400               # 24-hour cache
RATE_LIMIT_AI_PER_MINUTE=3       # Prevent abuse
AI_MONTHLY_BUDGET_USD=10         # Hard stop at $10

# Monitoring
AI_USAGE_TRACKING=true
AI_COST_ALERTS=true
AI_ALERT_EMAIL=your-email@example.com
```

This configuration will:
- Cost ~$5-10/month for normal usage
- Serve 2,500-5,000 PRD generations
- Prevent runaway costs
- Maintain good quality

## 🚀 Next Steps

1. **Decide on provider**: OpenAI (cheap) or Anthropic (quality)
2. **Get API key**: Sign up and create key
3. **Update .env.production**: Add your configuration
4. **Test locally**: Verify it works
5. **Deploy**: Add to Render environment
6. **Monitor**: Check usage daily first week

With caching enabled, you can serve thousands of users for just a few dollars per month!