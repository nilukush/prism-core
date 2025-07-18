# PRISM Deployment Checklist

## Pre-Deployment

### Environment Setup
- [ ] Verify all environment variables are set in Vercel dashboard
- [ ] Confirm API URL is correct (currently: https://prism-backend-bwfx.onrender.com)
- [ ] Check NEXTAUTH_URL matches deployment URL
- [ ] Ensure NEXTAUTH_SECRET is set in Vercel environment variables

### Code Verification
- [ ] Run `npm run build` locally to check for build errors
- [ ] Run `npm run type-check` to verify TypeScript
- [ ] Run `npm run lint` to check for linting issues
- [ ] Test critical user flows locally

## Deployment Process

### Manual Deployment (Current Setup)
1. [ ] Commit all changes locally
2. [ ] Push to your repository
3. [ ] In Vercel Dashboard: Click "Deploy" or use Vercel CLI
4. [ ] Monitor build logs for any errors
5. [ ] Verify deployment URL is correct

### Post-Deployment
- [ ] Test authentication flow
- [ ] Verify API connections are working
- [ ] Check CORS settings are allowing requests
- [ ] Test core features (create project, generate requirements, etc.)
- [ ] Monitor error logs in Vercel dashboard

## URL Configuration

### Current Setup
- Frontend: https://prism-app.vercel.app
- Backend: https://prism-backend-bwfx.onrender.com

### Future Custom Domain Setup
When ready to add custom domain:
1. [ ] Purchase domain (recommended: prism.app, getprism.app, or prismai.app)
2. [ ] Add domain in Vercel Dashboard → Domains
3. [ ] Configure DNS records as instructed by Vercel
4. [ ] Update environment variables with new domain
5. [ ] Set up redirects from old URLs

## Rollback Procedure

If issues occur after deployment:
1. Go to Vercel Dashboard → Deployments
2. Find the last working deployment
3. Click "..." menu → "Promote to Production"
4. Verify rollback was successful

## Future GitHub Integration

When ready to connect GitHub:
1. [ ] Create production branch separate from main
2. [ ] Set up branch protection rules
3. [ ] Configure Vercel to deploy from production branch
4. [ ] Set up preview deployments for PRs
5. [ ] Document deployment workflow for team

## Security Checklist

- [ ] No sensitive keys in frontend code
- [ ] API endpoints properly secured
- [ ] CORS configured correctly
- [ ] Environment variables not exposed in client bundle
- [ ] Authentication properly implemented