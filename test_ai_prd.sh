#!/bin/bash

# Test AI PRD Generation

echo "🤖 Testing AI PRD Generation"
echo "============================"
echo

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
sleep 5

# 1. Login to get token
echo "1. Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=nilukush@gmail.com&password=Test123!@#&grant_type=password")

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
  echo "❌ Login failed. Response:"
  echo $LOGIN_RESPONSE | jq .
  exit 1
fi
echo "✅ Login successful"

# 2. Test PRD generation without specifying provider (should use Anthropic)
echo -e "\n2. Testing PRD generation (using backend default provider)..."
PRD_DATA='{
  "product_name": "AI-Powered Analytics Dashboard",
  "description": "A real-time analytics dashboard that uses AI to provide predictive insights and automated recommendations for business metrics",
  "target_audience": "Business analysts and executives at mid-to-large enterprises",
  "key_features": [
    "Real-time data visualization",
    "AI-powered predictive analytics",
    "Automated anomaly detection",
    "Natural language insights"
  ],
  "constraints": [
    "Must integrate with existing data warehouses",
    "GDPR compliant"
  ]
}'

echo "Request data:"
echo $PRD_DATA | jq .

echo -e "\nSending request..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8100/api/v1/ai/generate/prd \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$PRD_DATA")

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
RESPONSE_BODY=$(echo "$RESPONSE" | sed '$d')

echo -e "\nHTTP Status Code: $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ PRD generation successful!"
  
  # Extract metadata
  PROVIDER=$(echo "$RESPONSE_BODY" | jq -r '.metadata.provider')
  MODEL=$(echo "$RESPONSE_BODY" | jq -r '.metadata.model')
  TOKENS=$(echo "$RESPONSE_BODY" | jq -r '.metadata.tokens_used')
  
  echo -e "\nMetadata:"
  echo "- Provider: $PROVIDER"
  echo "- Model: $MODEL"
  echo "- Tokens Used: $TOKENS"
  
  # Check if it's using real AI
  if [ "$PROVIDER" = "mock" ]; then
    echo -e "\n⚠️  WARNING: Still using mock provider!"
    echo "Please check backend configuration."
  else
    echo -e "\n✅ Using real AI provider: $PROVIDER"
    
    # Show first 500 characters of PRD
    PRD_CONTENT=$(echo "$RESPONSE_BODY" | jq -r '.prd' | head -c 500)
    echo -e "\nPRD Preview (first 500 chars):"
    echo "================================"
    echo "$PRD_CONTENT..."
  fi
else
  echo "❌ PRD generation failed!"
  echo "Response:"
  echo "$RESPONSE_BODY" | jq . 2>/dev/null || echo "$RESPONSE_BODY"
fi

# 3. Test with explicit provider
echo -e "\n\n3. Testing with explicit Anthropic provider..."
PRD_DATA_WITH_PROVIDER=$(echo "$PRD_DATA" | jq '. + {provider: "anthropic"}')

RESPONSE2=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8100/api/v1/ai/generate/prd \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$PRD_DATA_WITH_PROVIDER")

HTTP_CODE2=$(echo "$RESPONSE2" | tail -n 1)
RESPONSE_BODY2=$(echo "$RESPONSE2" | sed '$d')

if [ "$HTTP_CODE2" = "200" ]; then
  PROVIDER2=$(echo "$RESPONSE_BODY2" | jq -r '.metadata.provider')
  echo "✅ Explicit provider test successful: $PROVIDER2"
else
  echo "❌ Explicit provider test failed"
fi