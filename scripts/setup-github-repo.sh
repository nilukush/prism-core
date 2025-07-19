#!/bin/bash

# Script to configure GitHub repository settings for open source release
# Requires GitHub CLI (gh) to be installed and authenticated

echo "🚀 Setting up GitHub repository for open source release..."

# Repository details
REPO="prism-ai/prism-core"

# Enable issues
echo "✅ Enabling Issues..."
gh repo edit $REPO --enable-issues

# Enable discussions
echo "✅ Enabling Discussions..."
gh repo edit $REPO --enable-discussions

# Enable wiki (optional)
echo "✅ Enabling Wiki..."
gh repo edit $REPO --enable-wiki

# Set topics for discoverability
echo "✅ Setting repository topics..."
gh repo edit $REPO --add-topic "ai"
gh repo edit $REPO --add-topic "product-management"
gh repo edit $REPO --add-topic "fastapi"
gh repo edit $REPO --add-topic "nextjs"
gh repo edit $REPO --add-topic "opensource"
gh repo edit $REPO --add-topic "python"
gh repo edit $REPO --add-topic "typescript"
gh repo edit $REPO --add-topic "llm"
gh repo edit $REPO --add-topic "gpt-4"
gh repo edit $REPO --add-topic "claude"

# Create labels for issue management
echo "✅ Creating issue labels..."
gh label create "good first issue" --description "Good for newcomers" --color "7057ff"
gh label create "help wanted" --description "Extra attention is needed" --color "008672"
gh label create "priority: high" --description "High priority issue" --color "d73a4a"
gh label create "priority: medium" --description "Medium priority issue" --color "fbca04"
gh label create "priority: low" --description "Low priority issue" --color "0e8a16"
gh label create "type: security" --description "Security issue" --color "ee0701"
gh label create "type: performance" --description "Performance issue" --color "1d76db"
gh label create "status: in progress" --description "Work in progress" --color "fef2c0"
gh label create "status: blocked" --description "Blocked by external factors" --color "b60205"

# Create GitHub Pages branch (for future documentation site)
echo "✅ Creating gh-pages branch for documentation..."
git checkout --orphan gh-pages
git rm -rf .
echo "# PRISM Documentation" > index.md
git add index.md
git commit -m "Initial GitHub Pages commit"
git push origin gh-pages
git checkout main

# Create initial milestones
echo "✅ Creating milestones..."
gh api repos/$REPO/milestones -X POST -f title="v0.2.0" -f description="Jira/Confluence integration, real-time collaboration" -f due_on="2025-03-01T00:00:00Z"
gh api repos/$REPO/milestones -X POST -f title="v0.3.0" -f description="Advanced analytics, market research automation" -f due_on="2025-05-01T00:00:00Z"
gh api repos/$REPO/milestones -X POST -f title="v1.0.0" -f description="Production-ready release with enterprise support" -f due_on="2025-07-01T00:00:00Z"

# Create initial discussions
echo "✅ Creating welcome discussion..."
gh discussion create --repo $REPO --category "General" --title "Welcome to PRISM! 👋" --body "Welcome to the PRISM community! This is the place to discuss ideas, share feedback, and connect with other users and contributors.

## Getting Started
- Read our [README](https://github.com/prism-ai/prism-core#readme)
- Check out the [Contributing Guide](https://github.com/prism-ai/prism-core/blob/main/CONTRIBUTING.md)
- Report bugs in [Issues](https://github.com/prism-ai/prism-core/issues)

## Community Guidelines
Please be respectful and follow our [Code of Conduct](https://github.com/prism-ai/prism-core/blob/main/CODE_OF_CONDUCT.md).

Looking forward to building something amazing together! 🚀"

echo "✅ Creating roadmap discussion..."
gh discussion create --repo $REPO --category "Ideas" --title "PRISM Roadmap & Feature Requests" --body "This thread is for discussing the PRISM roadmap and suggesting new features.

## Current Roadmap

### v0.2.0 (March 2025)
- [ ] Jira integration
- [ ] Confluence integration  
- [ ] Real-time collaboration
- [ ] Slack notifications

### v0.3.0 (May 2025)
- [ ] Advanced analytics dashboard
- [ ] Market research automation
- [ ] Custom AI agent builder
- [ ] Plugin marketplace

### v1.0.0 (July 2025)
- [ ] Enterprise features
- [ ] Professional support
- [ ] SLA guarantees
- [ ] Advanced security features

What features would you like to see? Please share your ideas below!"

echo "
✅ GitHub repository setup complete!

Next steps:
1. Add repository secrets for CI/CD:
   - CODECOV_TOKEN
   - DOCKERHUB_USERNAME / DOCKERHUB_TOKEN
   - RENDER_API_KEY (if using Render)
   - VERCEL_TOKEN (if using Vercel)

2. Configure branch protection rules:
   - Go to Settings > Branches
   - Add rule for 'main' branch
   - Require PR reviews, status checks, etc.

3. Set up GitHub Pages:
   - Go to Settings > Pages
   - Source: Deploy from branch (gh-pages)

4. Create initial issues from TODO_TRACKER.md

5. Announce the release! 🎉
"