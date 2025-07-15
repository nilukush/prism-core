-- PostgreSQL initialization script for PRISM
-- This script runs when the PostgreSQL container is first created

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- Create custom types
DO $$ BEGIN
    CREATE TYPE user_status AS ENUM ('active', 'inactive', 'pending', 'suspended');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Removed user_role type as it conflicts with user_role table

DO $$ BEGIN
    CREATE TYPE project_status AS ENUM ('planning', 'active', 'on_hold', 'completed', 'archived');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE story_status AS ENUM ('draft', 'ready', 'in_progress', 'review', 'done', 'archived');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE story_priority AS ENUM ('critical', 'high', 'medium', 'low');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create indexes for better performance
-- These will be created after tables are created by migrations

-- Grant permissions to the application user
GRANT ALL PRIVILEGES ON DATABASE prism_dev TO prism;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO prism;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO prism;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO prism;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO prism;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO prism;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO prism;

-- Create a function for updating updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create a function for generating slugs
CREATE OR REPLACE FUNCTION generate_slug(input_text TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN LOWER(
        REGEXP_REPLACE(
            REGEXP_REPLACE(
                REGEXP_REPLACE(
                    TRIM(input_text),
                    '[^a-zA-Z0-9\s-]', '', 'g'
                ),
                '\s+', '-', 'g'
            ),
            '-+', '-', 'g'
        )
    );
END;
$$ LANGUAGE plpgsql;

-- Performance settings for development
-- Adjust these for production
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET min_wal_size = '1GB';
ALTER SYSTEM SET max_wal_size = '4GB';

-- Log slow queries (development only)
ALTER SYSTEM SET log_min_duration_statement = '1000';  -- Log queries taking more than 1 second

-- Apply configuration changes
SELECT pg_reload_conf();

-- Create initial schema version tracking table
CREATE TABLE IF NOT EXISTS schema_version (
    version VARCHAR(50) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- Insert initial version
INSERT INTO schema_version (version, description) 
VALUES ('1.0.0', 'Initial PRISM database setup')
ON CONFLICT (version) DO NOTHING;

-- Log initialization complete
DO $$
BEGIN
    RAISE NOTICE 'PRISM database initialization completed successfully';
END $$;