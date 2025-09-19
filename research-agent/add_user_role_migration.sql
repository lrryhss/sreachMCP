-- Migration to add role field to users table

-- Create the enum type for user roles
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('user', 'admin');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Add the role column to users table with default value
ALTER TABLE users
ADD COLUMN IF NOT EXISTS role user_role NOT NULL DEFAULT 'user';

-- Create index on role column for performance
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Set the first user (usually the one who set up the system) as admin
-- This assumes the first user by creation date should be admin
UPDATE users
SET role = 'admin'
WHERE id = (
    SELECT id FROM users
    ORDER BY created_at ASC
    LIMIT 1
);

-- Output migration result
SELECT
    COUNT(*) as total_users,
    COUNT(CASE WHEN role = 'admin' THEN 1 END) as admin_count,
    COUNT(CASE WHEN role = 'user' THEN 1 END) as user_count
FROM users;