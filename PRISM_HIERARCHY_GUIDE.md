# PRISM Data Hierarchy & Workflow Guide

## Overview

PRISM follows an enterprise-grade multi-tenant SaaS architecture with a strict hierarchical data model. This guide explains the data hierarchy, workflow requirements, and best practices for using PRISM effectively.

## Data Hierarchy Structure

```
User (Independent Entity)
 └── Organization (Tenant Container)
      ├── Workspace (Optional Grouping)
      ├── Project (Work Container)
      │    ├── Document/PRD (Product Requirements)
      │    ├── Sprint (Time-boxed Iterations)
      │    ├── Epic (Feature Groups)
      │    └── Story (Work Items)
      └── Team (Collaboration Groups)
```

## Required Creation Order

### 1. Organization → Project → PRD

**YES, you must follow this order:**

1. **Organization First**: Every user needs at least one organization
2. **Project Second**: Projects must belong to an organization
3. **PRD/Document Third**: Documents must belong to a project

### Current Setup for nilukush@gmail.com

Good news! Your account already has:
- ✅ **Organization**: "Personal Organization" (ID: 1)
- ✅ **User Role**: Owner (highest permission level)
- ✅ **Projects**: 3 existing projects (PCM, TPA, TEST3848)

## Workflow Steps

### Creating a New PRD

1. **Select or Create a Project**
   - Use existing project: Navigate to Projects → Select project
   - Create new project: Projects → New Project → Fill details

2. **Create PRD within Project**
   - Navigate to selected project
   - Click "Create PRD" or "New Document"
   - Select document type: "Product Requirements Document"
   - Fill in PRD details

### Complete Example Workflow

```bash
# 1. Login (you're already logged in)
# 2. Navigate to Projects page
# 3. Either:
   a) Select existing project (e.g., "Prompt Craft Master")
   b) Create new project with unique key
# 4. Within the project, create PRD
```

## Database Constraints & Rules

### Foreign Key Requirements

- **Project** requires valid `organization_id`
- **Document/PRD** requires valid `project_id`
- **All entities** require valid `creator_id` (user)

### Unique Constraints

- Organization slug must be unique globally
- Project key must be unique within organization
- Document slug must be unique globally

### Cascade Behavior

- Deleting Organization → Deletes all projects, workspaces, teams
- Deleting Project → Deletes all documents, stories, sprints, epics
- Soft delete supported (data retained with `is_deleted=true`)

## Multi-Tenant Architecture Details

### Organization-Based Isolation

- All data scoped to organizations
- Users access data through organization membership
- Cross-organization data access prevented by design

### Membership & Permissions

- **Owner**: Full control, can delete organization
- **Admin**: Manage projects, users, settings
- **Member**: Create/edit within assigned projects
- **Viewer**: Read-only access

### Resource Limits (by Plan)

```
Free Plan:
- max_users: 5
- max_projects: 10
- max_storage_gb: 5

Pro Plan:
- max_users: 50
- max_projects: 100
- max_storage_gb: 100

Enterprise Plan:
- max_users: Unlimited
- max_projects: Unlimited
- max_storage_gb: Custom
```

## Best Practices

### 1. Organization Strategy

- **Personal Projects**: Use default "Personal Organization"
- **Team Projects**: Create dedicated organization
- **Client Work**: Separate organization per client

### 2. Project Organization

- Use meaningful project keys (e.g., MOB for Mobile, API for API project)
- Group related work in same project
- Set appropriate project status (planning, active, on_hold, completed)

### 3. Document Management

- Create PRDs early in project lifecycle
- Use templates for consistency
- Link related documents (technical specs, design docs)

## Quick Start Commands

### Check Your Setup

```bash
# 1. Verify organization exists
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8100/api/v1/organizations/

# 2. List your projects
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8100/api/v1/projects/

# 3. Create new project
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"My Project","key":"MYPR","organization_id":1,"status":"planning"}' \
  http://localhost:8100/api/v1/projects/
```

### Common Operations

1. **Create Project**: Projects → New → Fill form → Create
2. **Create PRD**: Project → Documents → New PRD → Fill details → Save
3. **Add Team Member**: Organization → Teams → Invite → Set role

## Troubleshooting

### "No Organization Found"
- Check if logged in correctly
- Verify organization exists in database
- Contact admin to add you to organization

### "Cannot Create Project"
- Verify organization membership
- Check organization project limit
- Ensure unique project key

### "Cannot Create PRD"
- Verify project exists and is active
- Check project permissions
- Ensure you're not at document limit

## Enterprise Considerations

### Data Residency
- Organizations can specify data location
- Projects inherit organization's data residency
- Compliance with GDPR, SOC2, ISO 27001

### Backup & Recovery
- Daily automated backups
- Point-in-time recovery available
- Soft delete allows easy restoration

### API Integration
- All operations available via REST API
- Webhook support for automation
- OAuth2/JWT authentication

## Summary

The hierarchy **Organization → Project → PRD** is enforced by database constraints and is fundamental to PRISM's multi-tenant architecture. This design ensures:

1. **Data Isolation**: Complete separation between organizations
2. **Scalability**: Efficient resource allocation per tenant
3. **Security**: Role-based access control at every level
4. **Flexibility**: Support for various organizational structures

Your account is already set up with a default organization, so you can immediately create projects and PRDs within them!