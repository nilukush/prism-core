#!/bin/bash

# PRISM AI Configuration Script
# This script helps configure AI providers for PRISM

set -e

echo "🤖 PRISM AI Configuration"
echo "========================="
echo

# Function to update .env file
update_env() {
    local key=$1
    local value=$2
    local file="backend/.env"
    
    if grep -q "^${key}=" "$file"; then
        # Update existing key
        sed -i.bak "s|^${key}=.*|${key}=${value}|" "$file"
    else
        # Add new key
        echo "${key}=${value}" >> "$file"
    fi
}

# Select AI Provider
echo "Select your AI provider:"
echo "1) OpenAI (GPT-4, GPT-3.5)"
echo "2) Anthropic (Claude 3)"
echo "3) Ollama (Local models)"
echo "4) Mock (Testing only)"
echo
read -p "Enter choice (1-4): " provider_choice

case $provider_choice in
    1)
        provider="openai"
        echo
        echo "📝 OpenAI Configuration"
        echo "Get your API key from: https://platform.openai.com/api-keys"
        echo
        read -p "Enter OpenAI API Key (sk-...): " openai_key
        
        echo
        echo "Select default model:"
        echo "1) gpt-4-turbo-preview (Best, $10/$30 per 1M tokens)"
        echo "2) gpt-4 (Good, $30/$60 per 1M tokens)"
        echo "3) gpt-3.5-turbo (Budget, $0.50/$1.50 per 1M tokens)"
        read -p "Enter choice (1-3): " model_choice
        
        case $model_choice in
            1) model="gpt-4-turbo-preview" ;;
            2) model="gpt-4" ;;
            3) model="gpt-3.5-turbo" ;;
            *) model="gpt-3.5-turbo" ;;
        esac
        
        update_env "DEFAULT_LLM_PROVIDER" "$provider"
        update_env "DEFAULT_LLM_MODEL" "$model"
        update_env "OPENAI_API_KEY" "$openai_key"
        ;;
        
    2)
        provider="anthropic"
        echo
        echo "📝 Anthropic Configuration"
        echo "Get your API key from: https://console.anthropic.com/"
        echo
        read -p "Enter Anthropic API Key (sk-ant-...): " anthropic_key
        
        echo
        echo "Select default model:"
        echo "1) claude-3-opus-20240229 (Best, $15/$75 per 1M tokens)"
        echo "2) claude-3-sonnet-20240229 (Balanced, $3/$15 per 1M tokens) [Recommended for PRDs]"
        echo "3) claude-3-haiku-20240307 (Budget, $0.25/$1.25 per 1M tokens)"
        read -p "Enter choice (1-3): " model_choice
        
        case $model_choice in
            1) model="claude-3-opus-20240229" ;;
            2) model="claude-3-sonnet-20240229" ;;
            3) model="claude-3-haiku-20240307" ;;
            *) model="claude-3-sonnet-20240229" ;;
        esac
        
        update_env "DEFAULT_LLM_PROVIDER" "$provider"
        update_env "DEFAULT_LLM_MODEL" "$model"
        update_env "ANTHROPIC_API_KEY" "$anthropic_key"
        ;;
        
    3)
        provider="ollama"
        echo
        echo "📝 Ollama Configuration"
        echo "Make sure Ollama is running locally"
        echo
        read -p "Enter Ollama base URL (default: http://localhost:11434): " ollama_url
        ollama_url=${ollama_url:-http://localhost:11434}
        
        echo
        echo "Select default model:"
        echo "1) llama2"
        echo "2) mixtral"
        echo "3) Custom model"
        read -p "Enter choice (1-3): " model_choice
        
        case $model_choice in
            1) model="llama2" ;;
            2) model="mixtral" ;;
            3) 
                read -p "Enter custom model name: " model
                ;;
            *) model="llama2" ;;
        esac
        
        update_env "DEFAULT_LLM_PROVIDER" "$provider"
        update_env "DEFAULT_LLM_MODEL" "$model"
        update_env "OLLAMA_BASE_URL" "$ollama_url"
        ;;
        
    4)
        provider="mock"
        model="mock-model"
        update_env "DEFAULT_LLM_PROVIDER" "$provider"
        update_env "DEFAULT_LLM_MODEL" "$model"
        echo
        echo "✅ Mock provider configured (no API key needed)"
        ;;
        
    *)
        echo "Invalid choice. Keeping current configuration."
        exit 1
        ;;
esac

# Configure additional settings
echo
echo "📊 Additional Settings"
echo

read -p "Max tokens for PRD generation (default: 4000): " max_tokens
max_tokens=${max_tokens:-4000}
update_env "LLM_MAX_TOKENS" "$max_tokens"

read -p "Temperature 0-2 (0=focused, 2=creative, default: 0.7): " temperature
temperature=${temperature:-0.7}
update_env "LLM_TEMPERATURE" "$temperature"

read -p "Request timeout in seconds (default: 60): " timeout
timeout=${timeout:-60}
update_env "LLM_REQUEST_TIMEOUT" "$timeout"

read -p "Enable response caching? (y/n, default: y): " enable_cache
if [[ "$enable_cache" != "n" ]]; then
    update_env "LLM_CACHE_ENABLED" "true"
    update_env "LLM_CACHE_TTL" "3600"
else
    update_env "LLM_CACHE_ENABLED" "false"
fi

# Security settings
echo
echo "🔒 Security Settings"
echo

read -p "Enable rate limiting? (y/n, default: y): " enable_rate_limit
if [[ "$enable_rate_limit" != "n" ]]; then
    update_env "RATE_LIMIT_ENABLED" "true"
    update_env "AI_RATE_LIMIT_PER_MINUTE" "10"
    update_env "AI_RATE_LIMIT_PER_HOUR" "100"
else
    update_env "RATE_LIMIT_ENABLED" "false"
fi

# Create backup
cp backend/.env backend/.env.backup.$(date +%Y%m%d_%H%M%S)

echo
echo "✅ Configuration Complete!"
echo
echo "Summary:"
echo "- Provider: $provider"
echo "- Model: $model"
echo "- Max Tokens: $max_tokens"
echo "- Temperature: $temperature"
echo "- Timeout: ${timeout}s"
echo "- Caching: $([ "$enable_cache" != "n" ] && echo "Enabled" || echo "Disabled")"
echo "- Rate Limiting: $([ "$enable_rate_limit" != "n" ] && echo "Enabled" || echo "Disabled")"
echo
echo "📝 Configuration saved to: backend/.env"
echo "📋 Backup created: backend/.env.backup.*"
echo
echo "Next steps:"
echo "1. Restart the backend: docker compose restart backend"
echo "2. Test PRD generation in the web interface"
echo "3. Monitor costs in your AI provider dashboard"
echo
echo "⚠️  Remember to add your API keys to .gitignore!"
echo

# Offer to restart backend
read -p "Restart backend now? (y/n): " restart_now
if [[ "$restart_now" == "y" ]]; then
    echo "Restarting backend..."
    docker compose restart backend
    echo "✅ Backend restarted. AI configuration is now active!"
fi