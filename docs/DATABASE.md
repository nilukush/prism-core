# Database Schema Documentation

## Overview

PRISM uses PostgreSQL as its primary database with SQLAlchemy ORM for database operations. The schema follows a multi-tenant architecture with organizations at the top level.

## Database Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  organizations  │────<│ org_members     │>────│     users       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                                               │
         │                                               │
         ▼                                               ▼
┌─────────────────┐                            ┌─────────────────┐
│    projects     │                            │   user_sessions │
└─────────────────┘                            └─────────────────┘
         │
         ├──────────────┬────────────────┐
         ▼              ▼                ▼
┌─────────────────┐ ┌─────────────┐ ┌─────────────┐
│   documents     │ │   stories   │ │   sprints   │
└─────────────────┘ └─────────────┘ └─────────────┘
```

## Core Tables

### users
Primary user account table.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| email | VARCHAR(255) | Unique email address |
| username | VARCHAR(100) | Unique username |
| password_hash | VARCHAR(255) | Bcrypt password hash |
| full_name | VARCHAR(255) | User's full name |
| status | ENUM | active, inactive, pending |
| email_verified | BOOLEAN | Email verification status |
| created_at | TIMESTAMP | Account creation time |
| updated_at | TIMESTAMP | Last update time |

### organizations
Top-level tenant structure.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| name | VARCHAR(255) | Organization name |
| slug | VARCHAR(100) | URL-friendly identifier |
| owner_id | UUID | Foreign key to users |
| settings | JSONB | Organization settings |
| created_at | TIMESTAMP | Creation time |
| updated_at | TIMESTAMP | Last update time |

### organization_members
Many-to-many relationship between users and organizations.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| user_id | UUID | Foreign key to users |
| organization_id | INTEGER | Foreign key to organizations |
| role | VARCHAR(50) | admin, member, viewer |
| joined_at | TIMESTAMP | When user joined |

### projects
Projects belong to organizations.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| organization_id | INTEGER | Foreign key to organizations |
| name | VARCHAR(255) | Project name |
| key | VARCHAR(20) | Project key (e.g., PROJ) |
| description | TEXT | Project description |
| status | VARCHAR(50) | planning, active, on_hold, completed |
| owner_id | UUID | Foreign key to users |
| start_date | DATE | Project start date |
| end_date | DATE | Project end date |
| created_at | TIMESTAMP | Creation time |
| updated_at | TIMESTAMP | Last update time |

### documents
Stores PRDs, specifications, and other documents.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| project_id | INTEGER | Foreign key to projects |
| title | VARCHAR(255) | Document title |
| slug | VARCHAR(255) | URL-friendly identifier |
| content | TEXT | Document content (Markdown) |
| document_type | VARCHAR(50) | prd, spec, design, other |
| status | VARCHAR(50) | draft, published, archived |
| creator_id | UUID | Foreign key to users |
| metadata | JSONB | Additional metadata |
| created_at | TIMESTAMP | Creation time |
| updated_at | TIMESTAMP | Last update time |
| published_at | TIMESTAMP | Publication time |

### stories
User stories and tasks.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| project_id | INTEGER | Foreign key to projects |
| epic_id | INTEGER | Foreign key to epics (nullable) |
| sprint_id | INTEGER | Foreign key to sprints (nullable) |
| title | VARCHAR(255) | Story title |
| description | TEXT | Story description |
| acceptance_criteria | TEXT | Acceptance criteria |
| story_points | INTEGER | Estimated points |
| priority | VARCHAR(50) | high, medium, low |
| status | VARCHAR(50) | todo, in_progress, done |
| assignee_id | UUID | Foreign key to users |
| creator_id | UUID | Foreign key to users |
| created_at | TIMESTAMP | Creation time |
| updated_at | TIMESTAMP | Last update time |

### sprints
Sprint iterations.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| project_id | INTEGER | Foreign key to projects |
| name | VARCHAR(255) | Sprint name |
| goal | TEXT | Sprint goal |
| start_date | DATE | Sprint start |
| end_date | DATE | Sprint end |
| status | VARCHAR(50) | planning, active, completed |
| velocity | INTEGER | Completed story points |
| created_at | TIMESTAMP | Creation time |
| updated_at | TIMESTAMP | Last update time |

### ai_generations
Tracks AI-generated content.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| user_id | UUID | Foreign key to users |
| project_id | INTEGER | Foreign key to projects |
| generation_type | VARCHAR(50) | prd, story, analysis |
| provider | VARCHAR(50) | openai, anthropic, ollama |
| model | VARCHAR(100) | Model used |
| prompt | TEXT | Input prompt |
| response | TEXT | Generated response |
| tokens_used | INTEGER | Token count |
| cost | DECIMAL(10,4) | Estimated cost |
| metadata | JSONB | Additional data |
| created_at | TIMESTAMP | Generation time |

## Indexes

Key indexes for performance:

```sql
-- Users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);

-- Organizations
CREATE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_organizations_owner_id ON organizations(owner_id);

-- Projects
CREATE INDEX idx_projects_organization_id ON projects(organization_id);
CREATE INDEX idx_projects_status ON projects(status);

-- Documents
CREATE INDEX idx_documents_project_id ON documents(project_id);
CREATE INDEX idx_documents_type_status ON documents(document_type, status);
CREATE INDEX idx_documents_slug ON documents(slug);

-- Stories
CREATE INDEX idx_stories_project_id ON stories(project_id);
CREATE INDEX idx_stories_sprint_id ON stories(sprint_id);
CREATE INDEX idx_stories_assignee_id ON stories(assignee_id);
CREATE INDEX idx_stories_status ON stories(status);
```

## Migrations

Database migrations are managed with Alembic:

```bash
# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

## Backup and Restore

### Backup
```bash
# Full backup
pg_dump -U prism -h localhost prism_db > backup.sql

# Compressed backup
pg_dump -U prism -h localhost prism_db | gzip > backup.sql.gz

# Docker backup
docker exec prism-postgres pg_dump -U prism prism_db > backup.sql
```

### Restore
```bash
# Restore from backup
psql -U prism -h localhost prism_db < backup.sql

# Restore compressed backup
gunzip < backup.sql.gz | psql -U prism -h localhost prism_db

# Docker restore
docker exec -i prism-postgres psql -U prism prism_db < backup.sql
```

## Performance Considerations

1. **Connection Pooling**: Configure `DATABASE_POOL_SIZE` in .env
2. **Query Optimization**: Use `.options(selectinload())` for related data
3. **Pagination**: Always paginate large result sets
4. **Indexes**: Ensure proper indexes on foreign keys and filter columns
5. **JSONB**: Use GIN indexes for JSONB columns when querying

## Security

1. **Row-Level Security**: Implemented at application level
2. **Encryption**: Sensitive data encrypted at rest
3. **Audit Trail**: All changes tracked with timestamps
4. **SQL Injection**: Protected by SQLAlchemy ORM
5. **Access Control**: Enforced through organization membership