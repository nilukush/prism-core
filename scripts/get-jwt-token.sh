#!/bin/bash

echo "📋 How to Get Your JWT Token"
echo "=========================="
echo ""
echo "You're already on the PRISM page. Follow these steps:"
echo ""
echo "1. You already have DevTools open (as shown in screenshot)"
echo "2. Click on the 'Console' tab at the bottom"
echo "3. Type this command and press Enter:"
echo ""
echo "   localStorage.getItem('token')"
echo ""
echo "4. Copy the token that appears (it starts with 'eyJ...')"
echo "5. Use it in the delete script"
echo ""
echo "Alternative - Copy this entire command to run the delete script with token:"
echo ""
echo 'TOKEN=$(localStorage.getItem("token")); console.log("Your token:", TOKEN);'
echo ""
echo "Then use it like this:"
echo 'curl -X DELETE https://prism-backend-bwfx.onrender.com/api/v1/organizations/1/ -H "Authorization: Bearer YOUR_TOKEN_HERE"'