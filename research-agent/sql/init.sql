-- Research Agent Database Schema
-- Version: 1.0.0
-- Description: Initial database schema for research agent with user management

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create custom types
CREATE TYPE task_status AS ENUM (
    'pending',
    'analyzing',
    'searching',
    'fetching',
    'synthesizing',
    'generating',
    'completed',
    'failed',
    'cancelled'
);

CREATE TYPE research_depth AS ENUM (
    'quick',
    'standard',
    'comprehensive'
);

CREATE TYPE share_permission AS ENUM (
    'read',
    'comment',
    'edit',
    'admin'
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    last_login TIMESTAMP WITH TIME ZONE,
    preferences JSONB DEFAULT '{}'::jsonb,
    CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- User sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    refresh_token VARCHAR(500) UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

-- Research tasks table
CREATE TABLE IF NOT EXISTS research_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    task_id VARCHAR(50) UNIQUE NOT NULL,
    query TEXT NOT NULL,
    status task_status NOT NULL DEFAULT 'pending',
    depth research_depth DEFAULT 'standard',
    max_sources INTEGER DEFAULT 20 CHECK (max_sources > 0 AND max_sources <= 100),
    options JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    error_message TEXT
);

-- Research results table
CREATE TABLE IF NOT EXISTS research_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL UNIQUE REFERENCES research_tasks(id) ON DELETE CASCADE,
    synthesis JSONB NOT NULL,
    sources JSONB NOT NULL,
    query_analysis JSONB,
    detailed_analysis JSONB,
    metadata JSONB,
    featured_media JSONB,
    sources_used INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Research artifacts table
CREATE TABLE IF NOT EXISTS research_artifacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES research_tasks(id) ON DELETE CASCADE,
    artifact_type VARCHAR(50) NOT NULL,
    artifact_name VARCHAR(255),
    content TEXT,
    metadata JSONB,
    size_bytes INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Research shares table
CREATE TABLE IF NOT EXISTS research_shares (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES research_tasks(id) ON DELETE CASCADE,
    shared_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    shared_with UUID REFERENCES users(id) ON DELETE CASCADE,
    share_token VARCHAR(100) UNIQUE,
    permission_level share_permission DEFAULT 'read',
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_public BOOLEAN DEFAULT false
);

-- Create indexes for performance
CREATE INDEX idx_research_tasks_user_id ON research_tasks(user_id);
CREATE INDEX idx_research_tasks_status ON research_tasks(status);
CREATE INDEX idx_research_tasks_created_at ON research_tasks(created_at DESC);
CREATE INDEX idx_research_results_task_id ON research_results(task_id);
CREATE INDEX idx_research_artifacts_task_id ON research_artifacts(task_id);
CREATE INDEX idx_research_artifacts_type ON research_artifacts(artifact_type);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX idx_research_shares_task_id ON research_shares(task_id);
CREATE INDEX idx_research_shares_token ON research_shares(share_token);

-- Full-text search indexes
CREATE INDEX idx_research_tasks_query_gin ON research_tasks USING gin(to_tsvector('english', query));
CREATE INDEX idx_research_results_synthesis_gin ON research_results USING gin(synthesis);

-- Audit triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_research_results_updated_at BEFORE UPDATE ON research_results
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Default admin user (for development)
-- Password: admin123 (you should change this!)
INSERT INTO users (email, username, password_hash, full_name, is_active, is_verified)
VALUES (
    'admin@research-agent.local',
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY/x.2AkJ5.aVXa6', -- bcrypt hash of 'admin123'
    'System Administrator',
    true,
    true
) ON CONFLICT (email) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO research_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO research_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO research_user;