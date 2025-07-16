#!/bin/bash

# Quick Render deployment status checker

echo "🔍 Checking Render deployment status..."
echo "================================"

# Test with your likely Render URL
URL="https://prism-backend.onrender.com"

# Check health endpoint
echo -n "Health check: "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$URL/health" 2>/dev/null || echo "000")

case $STATUS in
    200)
        echo "✅ Service is LIVE!"
        echo ""
        echo "🎉 Your deployment is successful!"
        echo "Backend URL: $URL"
        echo ""
        echo "Next steps:"
        echo "1. Update BACKEND_URL in Render dashboard to: $URL"
        echo "2. Update CORS_ALLOWED_ORIGINS to include your Vercel URL"
        echo "3. Deploy frontend to Vercel"
        ;;
    503)
        echo "⏳ Still deploying... (this is normal)"
        echo ""
        echo "First deployments can take 5-10 minutes."
        echo "Check Render dashboard for build logs."
        ;;
    000)
        echo "❌ Cannot connect"
        echo ""
        echo "Possible reasons:"
        echo "- Still building (check Render logs)"
        echo "- Wrong URL (check your Render dashboard)"
        echo "- Network issue"
        ;;
    *)
        echo "⚠️  Unexpected status: $STATUS"
        echo ""
        echo "Check Render logs for details."
        ;;
esac

echo ""
echo "💡 Tip: Run this script again in 1-2 minutes"
echo "   ./scripts/check-render-status.sh"