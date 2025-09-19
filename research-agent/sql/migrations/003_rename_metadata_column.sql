-- Migration: Rename metadata column to result_metadata in research_results table
-- Description: Fixes conflict between SQLAlchemy metadata attribute and database column name

-- Rename the metadata column to result_metadata to avoid SQLAlchemy naming conflicts
ALTER TABLE research_results RENAME COLUMN metadata TO result_metadata;

-- Update any existing indexes that might reference the old column name
-- (No specific indexes were found for the metadata column, but this is a precaution)

-- Note: This migration fixes the validation error where SQLAlchemy's built-in
-- metadata attribute was conflicting with the database column name, causing
-- the API to return MetaData() object instead of the JSONB column value.