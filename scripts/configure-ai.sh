#!/bin/bash

# PRISM AI Configuration Script
# Helps you set up AI providers for production

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════╗"
echo "║        PRISM AI Configuration             ║"
echo "╚═══════════════════════════════════════════╝"
echo -e "${NC}"

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    echo -e "${RED}❌ .env.production not found!${NC}"
    echo -e "${YELLOW}Run ./scripts/prepare-deployment.sh first${NC}"
    exit 1
fi

# Function to update env file
update_env() {
    local key=$1
    local value=$2
    local file=$3
    
    if grep -q "^${key}=" "$file"; then
        sed -i.bak "s|^${key}=.*|${key}=${value}|" "$file"
    else
        echo "${key}=${value}" >> "$file"
    fi
}

# Choose AI Provider
echo -e "${BLUE}Choose your AI provider:${NC}"
echo "1) OpenAI GPT-3.5 (Cheapest - $0.002/PRD)"
echo "2) OpenAI GPT-4 (Premium - $0.06/PRD)"
echo "3) Anthropic Claude Haiku (Balanced - $0.003/PRD)"
echo "4) Anthropic Claude Sonnet (Quality - $0.015/PRD)"
echo "5) Keep Mock (Free - No AI)"
echo ""
read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        provider="openai"
        model="gpt-3.5-turbo"
        echo -e "\n${GREEN}Selected: OpenAI GPT-3.5-turbo${NC}"
        echo -e "${YELLOW}Get your API key from: https://platform.openai.com/api-keys${NC}"
        echo -e "${YELLOW}New users get $5 free credits!${NC}"
        read -p "Enter your OpenAI API key: " api_key
        
        # Update configuration
        update_env "DEFAULT_LLM_PROVIDER" "$provider" ".env.production"
        update_env "DEFAULT_LLM_MODEL" "$model" ".env.production"
        update_env "OPENAI_API_KEY" "$api_key" ".env.production"
        ;;
        
    2)
        provider="openai"
        model="gpt-4"
        echo -e "\n${GREEN}Selected: OpenAI GPT-4${NC}"
        echo -e "${YELLOW}⚠️  Warning: This is expensive (~$0.06/PRD)${NC}"
        echo -e "${YELLOW}Get your API key from: https://platform.openai.com/api-keys${NC}"
        read -p "Enter your OpenAI API key: " api_key
        
        update_env "DEFAULT_LLM_PROVIDER" "$provider" ".env.production"
        update_env "DEFAULT_LLM_MODEL" "$model" ".env.production"
        update_env "OPENAI_API_KEY" "$api_key" ".env.production"
        ;;
        
    3)
        provider="anthropic"
        model="claude-3-haiku-20240307"
        echo -e "\n${GREEN}Selected: Anthropic Claude 3 Haiku${NC}"
        echo -e "${YELLOW}Get your API key from: https://console.anthropic.com${NC}"
        read -p "Enter your Anthropic API key: " api_key
        
        update_env "DEFAULT_LLM_PROVIDER" "$provider" ".env.production"
        update_env "DEFAULT_LLM_MODEL" "$model" ".env.production"
        update_env "ANTHROPIC_API_KEY" "$api_key" ".env.production"
        ;;
        
    4)
        provider="anthropic"
        model="claude-3-sonnet-20240229"
        echo -e "\n${GREEN}Selected: Anthropic Claude 3 Sonnet${NC}"
        echo -e "${YELLOW}Get your API key from: https://console.anthropic.com${NC}"
        read -p "Enter your Anthropic API key: " api_key
        
        update_env "DEFAULT_LLM_PROVIDER" "$provider" ".env.production"
        update_env "DEFAULT_LLM_MODEL" "$model" ".env.production"
        update_env "ANTHROPIC_API_KEY" "$api_key" ".env.production"
        ;;
        
    5)
        echo -e "\n${GREEN}Keeping Mock provider (free)${NC}"
        update_env "DEFAULT_LLM_PROVIDER" "mock" ".env.production"
        update_env "DEFAULT_LLM_MODEL" "mock-model" ".env.production"
        ;;
        
    *)
        echo -e "${RED}Invalid choice!${NC}"
        exit 1
        ;;
esac

# Configure cost controls
echo -e "\n${BLUE}Configuring cost controls...${NC}"

# Set default cost control values
update_env "LLM_MAX_TOKENS" "2000" ".env.production"
update_env "AI_CACHE_ENABLED" "true" ".env.production"
update_env "AI_CACHE_TTL" "86400" ".env.production"
update_env "RATE_LIMIT_AI_PER_MINUTE" "5" ".env.production"

# Ask for monthly budget
if [ "$choice" != "5" ]; then
    echo -e "${YELLOW}Set your monthly AI budget limit:${NC}"
    echo "1) $10/month (Conservative)"
    echo "2) $20/month (Moderate)"
    echo "3) $50/month (Growth)"
    echo "4) $100/month (Scale)"
    echo "5) No limit (Dangerous!)"
    read -p "Enter your choice (1-5): " budget_choice
    
    case $budget_choice in
        1) budget="10" ;;
        2) budget="20" ;;
        3) budget="50" ;;
        4) budget="100" ;;
        5) budget="9999" ;;
        *) budget="20" ;;
    esac
    
    update_env "AI_MONTHLY_BUDGET_USD" "$budget" ".env.production"
    echo -e "${GREEN}✓ Monthly budget set to: \$$budget${NC}"
fi

# Test configuration
if [ "$choice" != "5" ]; then
    echo -e "\n${BLUE}Testing AI configuration...${NC}"
    
    # Create test script
    cat > test_ai_config.py << EOF
import os
import sys

# Set environment
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', '')
os.environ['ANTHROPIC_API_KEY'] = os.getenv('ANTHROPIC_API_KEY', '')

provider = "$provider"
model = "$model"

try:
    if provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say 'AI configured successfully' in 5 words or less"}],
            max_tokens=20
        )
        print(f"✓ {response.choices[0].message.content}")
        
    elif provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        response = client.messages.create(
            model=model,
            messages=[{"role": "user", "content": "Say 'AI configured successfully' in 5 words or less"}],
            max_tokens=20
        )
        print(f"✓ {response.content[0].text}")
        
    print("✓ AI provider configured successfully!")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    print("Please check your API key and try again.")
    sys.exit(1)
EOF

    # Run test
    python test_ai_config.py
    rm -f test_ai_config.py
fi

# Summary
echo -e "\n${GREEN}════════════════════════════════════${NC}"
echo -e "${GREEN}✅ AI Configuration Complete!${NC}"
echo -e "${GREEN}════════════════════════════════════${NC}"

if [ "$choice" != "5" ]; then
    echo -e "\nYour configuration:"
    echo -e "Provider: ${BLUE}$provider${NC}"
    echo -e "Model: ${BLUE}$model${NC}"
    echo -e "Monthly Budget: ${BLUE}\$${budget}${NC}"
    echo -e "Caching: ${GREEN}Enabled (24 hours)${NC}"
    echo -e "Rate Limit: ${GREEN}5 requests/minute${NC}"
fi

echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Deploy to Render with these environment variables"
echo "2. Monitor usage at your provider's dashboard"
echo "3. Adjust limits based on actual usage"

echo -e "\n${BLUE}Cost saving tips:${NC}"
echo "• Caching saves ~80% on repeated requests"
echo "• Set user monthly limits to prevent abuse"
echo "• Start with GPT-3.5, upgrade only if needed"
echo "• Monitor daily costs for the first week"

# Clean up
rm -f .env.production.bak 2>/dev/null || true

echo -e "\n${GREEN}Happy building! 🚀${NC}"