#!/bin/bash

# Script to push PRISM to GitHub
# This script assumes you want to create a new repository on GitHub

echo "==================================="
echo "PRISM GitHub Push Script"
echo "==================================="
echo

echo "This script will help you push PRISM to GitHub."
echo "Please follow these steps:"
echo

echo "1. First, create a new repository on GitHub:"
echo "   - Go to https://github.com/new"
echo "   - Repository name: prism-core (or your preferred name)"
echo "   - Description: AI-Powered Product Management Platform"
echo "   - Choose: Public (for open source)"
echo "   - DO NOT initialize with README, .gitignore, or license"
echo

read -p "Press Enter when you've created the repository..."

echo
echo "2. Enter your GitHub repository URL:"
echo "   Example: https://github.com/yourusername/prism-core.git"
echo "   or: git@github.com:yourusername/prism-core.git"
echo

read -p "Repository URL: " REPO_URL

if [ -z "$REPO_URL" ]; then
    echo "Error: Repository URL cannot be empty"
    exit 1
fi

echo
echo "Adding remote origin..."
git remote add origin "$REPO_URL"

echo "Setting up main branch..."
git branch -M main

echo
echo "3. Pushing to GitHub..."
echo "   This will push all 428 files (91,669 lines of code)"
echo

read -p "Ready to push? (y/n): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Pushing to GitHub..."
    git push -u origin main
    
    if [ $? -eq 0 ]; then
        echo
        echo "✅ Successfully pushed PRISM to GitHub!"
        echo
        echo "Your repository is now available at:"
        echo "$REPO_URL"
        echo
        echo "Next steps:"
        echo "1. Add a GitHub Actions secret for CI/CD:"
        echo "   - Go to Settings > Secrets > Actions"
        echo "   - Add GITHUB_TOKEN (automatically provided)"
        echo
        echo "2. Enable GitHub Pages for documentation (optional):"
        echo "   - Go to Settings > Pages"
        echo "   - Source: Deploy from a branch"
        echo "   - Branch: main, folder: /docs"
        echo
        echo "3. Set up branch protection rules:"
        echo "   - Go to Settings > Branches"
        echo "   - Add rule for 'main' branch"
        echo "   - Require pull request reviews"
        echo
        echo "4. Add topics to your repository:"
        echo "   - product-management"
        echo "   - ai-powered"
        echo "   - fastapi"
        echo "   - nextjs"
        echo "   - open-source"
        echo
    else
        echo
        echo "❌ Push failed. Common issues:"
        echo "1. Authentication: Make sure you're logged in to git"
        echo "   - For HTTPS: Use personal access token as password"
        echo "   - For SSH: Add your SSH key to GitHub"
        echo
        echo "2. Repository exists: Make sure the repository is empty"
        echo
        echo "3. Network issues: Check your internet connection"
        echo
        echo "To retry: git push -u origin main"
    fi
else
    echo "Push cancelled."
    echo "To push later, run: git push -u origin main"
fi