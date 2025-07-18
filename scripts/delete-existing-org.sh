#!/bin/bash

# Quick script to delete existing organization

API_URL="https://prism-backend-bwfx.onrender.com"

echo "🗑️  Delete Existing Organization"
echo "==============================="
echo ""
echo "This will delete the existing organization so the create modal will appear."
echo ""

# Get token
echo "Please provide your JWT token from browser localStorage:"
read -p "Token: " TOKEN

if [ -z "$TOKEN" ]; then
    echo "❌ No token provided"
    exit 1
fi

# Get current organizations
echo -e "\nFetching organizations..."
ORG_RESPONSE=$(curl -s -X GET "$API_URL/api/v1/organizations/" \
    -H "Authorization: Bearer $TOKEN")

# Extract organization ID
ORG_ID=$(echo "$ORG_RESPONSE" | jq -r '.organizations[0].id' 2>/dev/null)
ORG_NAME=$(echo "$ORG_RESPONSE" | jq -r '.organizations[0].name' 2>/dev/null)

if [ "$ORG_ID" != "null" ] && [ -n "$ORG_ID" ]; then
    echo "Found organization: $ORG_NAME (ID: $ORG_ID)"
    echo ""
    read -p "Delete this organization? (yes/no): " CONFIRM
    
    if [ "$CONFIRM" = "yes" ]; then
        echo -e "\nDeleting organization..."
        
        # Note: The DELETE endpoint is being deployed, so this might fail initially
        DELETE_RESPONSE=$(curl -s -X DELETE "$API_URL/api/v1/organizations/$ORG_ID/" \
            -H "Authorization: Bearer $TOKEN" \
            -w "\n%{http_code}")
        
        HTTP_CODE=$(echo "$DELETE_RESPONSE" | tail -n1)
        
        if [ "$HTTP_CODE" = "204" ]; then
            echo "✅ Organization deleted successfully!"
            echo ""
            echo "Now you can visit: https://prism-frontend-kappa.vercel.app/app/projects/new"
            echo "The organization creation modal should appear automatically."
        elif [ "$HTTP_CODE" = "404" ]; then
            echo "⚠️  DELETE endpoint not yet deployed on backend."
            echo ""
            echo "The backend needs to be redeployed with the DELETE endpoint."
            echo "This usually takes 5-10 minutes on Render."
            echo ""
            echo "Alternative: Ask the user to manually delete from the database."
        else
            echo "❌ Failed to delete organization (HTTP $HTTP_CODE)"
            echo "Response: $(echo "$DELETE_RESPONSE" | head -n-1)"
        fi
    fi
else
    echo "✅ No organizations found!"
    echo "The modal should already be appearing."
fi