# 🔗 Connect Vercel to GitHub - Step by Step

## Method 1: Via Vercel Dashboard (Recommended)

### Step 1: Go to Git Settings
1. Visit: https://vercel.com/nilukushs-projects/frontend/settings/git
2. You should see "Connect Git Repository" option

### Step 2: Connect Repository
1. Click "Connect Git Repository"
2. Select "GitHub"
3. If prompted, authorize Vercel to access your GitHub
4. Search for: `nilukush/prism-core`
5. Click "Import"

### Step 3: Configure Import Settings
When the configuration screen appears:
- **Root Directory**: Set to `frontend`
- **Build & Development Settings**: Should auto-detect Next.js
- **Environment Variables**: Already configured

### Step 4: Save Configuration
Click "Save" to complete the connection

## Method 2: Alternative Import Flow

If the above doesn't work:

1. Go to: https://vercel.com/new/import
2. Enter Git URL: `https://github.com/nilukush/prism-core`
3. Configure:
   - Root Directory: `frontend`
   - Project: Select existing `frontend` project
4. Deploy

## Verification

After connecting, check:
1. Go to: https://vercel.com/nilukushs-projects/frontend/settings/git
2. You should see:
   - Repository: `nilukush/prism-core`
   - Production Branch: `main`
   - Root Directory: `frontend`

## Important Settings

### Ignored Build Step
To prevent unnecessary builds when backend changes:
1. Go to Settings → Git
2. Find "Ignored Build Step"
3. Add custom command:
   ```bash
   git diff HEAD^ HEAD --quiet ./frontend
   ```
   This will only build when frontend directory changes

## Troubleshooting

If you get errors:
- Make sure you're logged into GitHub
- Authorize Vercel app in GitHub if prompted
- Check that repository is public or you have access

Once connected, future pushes to `main` branch will auto-deploy!