# ⚠️ IMPORTANT SECURITY NOTICE

## Your OpenAI API Key is Exposed

Your OpenAI API key is currently visible in `.env.production`.

**IMPORTANT**: Never commit real API keys to version control!

## Immediate Actions Required

### 1. Regenerate Your API Key
1. Go to https://platform.openai.com/api-keys
2. Delete the exposed key
3. Create a new key
4. Update in Render dashboard (NOT in files)

### 2. Check for Unauthorized Usage
1. Go to https://platform.openai.com/usage
2. Check for any unexpected usage
3. Set up billing alerts

### 3. Never Commit API Keys
```bash
# Add to .gitignore
.env.production
.env*
*api_key*
```

## Best Practices for Open Source Projects

### Use Environment Variables Only
```bash
# In code, always use:
api_key = os.getenv("OPENAI_API_KEY")

# Never hardcode:
api_key = "sk-proj-..."  # NEVER DO THIS
```

### For Local Development
```bash
# Create .env.local (gitignored)
cp .env.example .env.local
# Add your keys to .env.local only
```

### For Production (Render)
- Add API keys directly in Render dashboard
- Use "Secret" type for sensitive values
- Never commit them to repository

## Setting Usage Limits

To protect against abuse:

1. **OpenAI Dashboard**:
   - Set monthly budget: $20
   - Enable email alerts at $10, $15, $20

2. **In Your App** (already configured):
   ```bash
   AI_MONTHLY_BUDGET_USD=20
   AI_USER_MONTHLY_LIMIT=50
   RATE_LIMIT_AI_PER_MINUTE=5
   ```

## Remember

- API keys are like passwords
- Anyone with your key can use your account
- Costs can accumulate quickly without limits
- Always use environment variables
- Regenerate keys if exposed

Stay safe! 🔐