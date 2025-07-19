# Changelog

All notable changes to PRISM will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.14.28] - 2025-01-19

### Added
- Comprehensive GitHub configuration for open source release:
  - Professional issue templates (bug report, feature request, documentation, security, question)
  - Pull request template with security and testing checklists
  - GitHub Actions workflows for CI/CD, security scanning, and automation
  - Dependabot configuration for automated dependency updates
  - CODEOWNERS file for automatic review assignments
  - Auto-labeler configuration
- Release documentation:
  - TODO_TRACKER.md listing remaining implementation tasks
  - OPEN_SOURCE_READY.md with release checklist
  - ANNOUNCEMENT_TEMPLATE.md with platform-specific templates
  - RELEASE_NOTES_v0.1.0.md for first public release
- GitHub repository setup script (scripts/setup-github-repo.sh)

### Changed
- Prepared repository for public open source release:
  - Removed 28 sensitive files (environment files, debug scripts, internal docs)
  - Enhanced .gitignore to prevent committing sensitive files
  - Updated .env.example with security warnings
  - Standardized all repository URLs to github.com/prism-ai/prism-core

### Fixed
- Critical SSRF vulnerability in Next.js (updated 14.1.0 → 14.2.30)
- High severity ReDoS vulnerability in jsPDF (updated 2.5.1 → 3.0.1)
- Render deployment failure due to gitignored debug modules:
  - Commented out imports for debug.py and simple_activation.py in router
  - Backend now successfully deploys to production

### Security
- Reduced total vulnerabilities from 37 to 23
- Fixed all critical vulnerabilities
- Created requirements-security-update.txt for Python security updates
- Removed all hardcoded credentials and sensitive information

### Tagged
- Released v0.1.0 (alpha) - First public open source release

## [0.14.27] - 2025-01-19

### Fixed
- Client-side exception after project creation: "Cannot read properties of undefined (reading 'name')"
- Multiple 404 errors for missing navigation routes
- Project list page crashing when organization or owner data is missing

### Added
- Placeholder pages for navigation routes to prevent 404 errors:
  - `/app/sprints` - Sprint management page
  - `/app/backlog` - Backlog management page
  - `/app/teams` - Team management page
  - `/app/settings` - Settings page with profile and account tabs
- Null safety checks for organization and owner fields in project list
- Data validation before rendering project components
- Defensive programming patterns throughout frontend

### Changed
- Made organization and owner fields optional in TypeScript interfaces
- Added fallback text for missing data: "No Organization", "Unknown Owner"
- Enhanced error handling with console warnings for invalid data
- Improved API response validation in project creation flow

### Technical
- Added optional chaining for all potentially undefined fields
- Implemented data filtering to exclude invalid projects
- Created reusable placeholder components for future pages
- Settings page includes tabbed interface ready for expansion

## [0.14.26] - 2025-01-19

### Fixed
- 404 NOT_FOUND error when accessing /app/organizations/new
- Organization creation page was missing after directory removal

### Added
- Recreated /app/organizations/new/page.tsx for organization creation
- Proper navigation flow: Account → Create Organization → Back to Account

### Technical
- Implemented pattern where parent route redirects but child routes remain accessible
- Follows GitHub/Vercel approach for organization creation flows
- Form redirects to /app/account?tab=organizations after successful creation

## [0.14.25] - 2025-01-19

### Fixed
- Vercel build error: "You cannot have two parallel pages that resolve to the same path"
- Removed conflicting page.tsx and route.ts files in /app/organizations/
- Organizations route now properly redirects via next.config.js

### Changed  
- Organizations navigation consolidated under Account tab only
- Main navigation reduced from 9 to 8 items for better UX
- Redirect implementation uses edge-level redirects for best performance

### Technical
- Deleted /app/organizations/ directory entirely
- Redirect configured in next.config.js (lines 80-83)
- All organization links updated to /app/account?tab=organizations

## [0.14.24] - 2025-01-19

### Changed
- Removed Organizations from main navigation bar
- Organizations now accessed exclusively through Account → Organizations tab
- Navigation order optimized: Projects, Backlog, Sprints, PRDs, Teams, Account, Settings

### Added
- URL parameter handling for direct tab access (/app/account?tab=organizations)
- Backward compatibility redirects for existing organization links
- Enterprise navigation best practices documentation

### Fixed
- Duplicate navigation items (Organizations appeared in two places)
- Cognitive overload from too many main navigation items

## [0.14.23] - 2025-01-18

### Added
- Complete Account Overview page at `/app/account` with tabbed interface (Organizations, Settings, Billing, Security)
- Dedicated organization creation page at `/app/organizations/new` replacing modal approach
- Reusable `EmptyState` component for professional empty states throughout the app
- `OrganizationsView` component with grid layout and organization statistics
- "Account" navigation item in sidebar (2nd position) and user dropdown menu
- Success message handling with query parameters (?deleted=true)
- Comprehensive UX research documentation analyzing Slack, GitHub, Teams, Notion patterns
- Organization deletion best practices guide
- Fix script for navigation issues (`scripts/fix-org-navigation.sh`)

### Changed
- Organization deletion now redirects to Account page instead of `/app/projects/new`
- Removed auto-modal behavior after organization deletion (identified as poor UX)
- Organization creation uses dedicated page flow instead of modal dialog
- Navigation order updated with Account in prominent 2nd position
- Empty states now show clear CTAs (Create Organization, Learn More)
- Create Organization buttons throughout app now navigate to dedicated page
- Modal only appears in development mode with debug controls

### Fixed
- Jarring user experience with auto-opening modals after deletion
- Confusing flow after deleting last organization
- Missing success feedback after organization deletion
- Unpredictable navigation patterns
- Lack of user control after destructive actions

### Security
- Production environment now hides all debug features and SQL queries
- Technical error details replaced with user-friendly messages
- Delete operations properly restricted to organization owners
- FixOrgModal only shows sensitive options in development

## [0.14.22] - 2025-01-18

### Security
- Implemented environment-based feature flags for production security
- FixOrgModal component now shows different content based on NODE_ENV
- SQL queries and debug options hidden in production environment
- Added `isDevelopment` flag using `process.env.NODE_ENV`

### Changed
- Production users see "contact administrator" message instead of technical details
- Development environment retains all debug features and SQL queries
- Delete button and technical options only visible to developers

## [0.14.21] - 2025-01-18

### Added
- Production deployment to Vercel (frontend), Render (backend), Neon (PostgreSQL), Upstash (Redis)
- Complete organization management workflow
- Organization creation endpoint: `POST /api/v1/organizations/`
- Frontend UI for organization creation with modal and forms
- Auto-activation for users (no email verification required)
- Organization deletion endpoint with proper cleanup
- Automatic data refresh on window focus and tab visibility
- Organizations management page with delete functionality
- Various deletion methods (API, SQL, scripts)

### Fixed
- CORS configuration for production URLs (Vercel domains)
- Organization creation 500 errors (multiple issues):
  - Logger TypeError with structured logging
  - Regex pattern errors in HTML
  - Invalid 'max_workspaces' field
  - UUID/Integer schema mismatch
- JWT "Not enough segments" error
- Authentication using localStorage instead of NextAuth sessions
- Organization deletion not working (401 Unauthorized)
- State not refreshing after deletion
- All authentication and schema validation issues

### Changed
- Frontend uses NextAuth session tokens instead of localStorage
- Organization deletion returns 204 for idempotent operations
- Backend returns simple dicts instead of Pydantic models for flexibility
- Added refresh query parameter for forcing data refresh

## [1.0.0] - 2024-01-15

### Added
- Initial release of PRISM - AI-Powered Product Management Platform
- Core features:
  - AI-powered user story generation
  - Acceptance criteria automation
  - Basic PRD generation
  - Multi-tenant support
  - JWT authentication
  - Role-based access control
- Integrations:
  - Jira integration (basic)
  - Slack notifications
  - Webhook support
- Infrastructure:
  - PostgreSQL for data persistence
  - Redis for caching and sessions
  - Docker support
  - Basic Kubernetes manifests
- API:
  - RESTful API with OpenAPI 3.0 documentation
  - GraphQL endpoint (beta)
  - Webhook system
- Documentation:
  - API documentation
  - Quick start guide
  - Deployment guides

[Unreleased]: https://github.com/prism-ai/prism-core/compare/v0.14.28...HEAD
[0.14.28]: https://github.com/prism-ai/prism-core/compare/v0.14.27...v0.14.28
[0.14.27]: https://github.com/prism-ai/prism-core/compare/v0.14.26...v0.14.27
[0.14.26]: https://github.com/prism-ai/prism-core/compare/v0.14.25...v0.14.26
[0.14.25]: https://github.com/prism-ai/prism-core/compare/v0.14.24...v0.14.25
[0.14.24]: https://github.com/prism-ai/prism-core/compare/v0.14.23...v0.14.24
[0.14.23]: https://github.com/prism-ai/prism-core/compare/v0.14.22...v0.14.23
[0.14.22]: https://github.com/prism-ai/prism-core/compare/v0.14.21...v0.14.22
[0.14.21]: https://github.com/prism-ai/prism-core/compare/v0.14.20...v0.14.21
[1.0.0]: https://github.com/prism-ai/prism-core/releases/tag/v1.0.0