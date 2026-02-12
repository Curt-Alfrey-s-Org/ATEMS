-- ATEMS PostgreSQL Initialization Script
-- Database: atems
-- User: atems_user

-- Set timezone
SET timezone = 'UTC';

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For fuzzy text search

-- Grant privileges (user already has access, but ensure full rights)
GRANT ALL PRIVILEGES ON DATABASE atems TO atems_user;

-- Create schema if not exists (default is public)
-- The Flask-SQLAlchemy will create tables via db.create_all() or migrations

-- Add indexes for common queries (will be created by migrations, but documenting here)
-- Tables: user, tools, checkout_history

-- Indexes to be created after initial migration:
-- CREATE INDEX IF NOT EXISTS idx_tools_tool_id_number ON tools(tool_id_number);
-- CREATE INDEX IF NOT EXISTS idx_tools_status ON tools(tool_status);
-- CREATE INDEX IF NOT EXISTS idx_tools_checked_out_by ON tools(checked_out_by);
-- CREATE INDEX IF NOT EXISTS idx_tools_category ON tools(category);
-- CREATE INDEX IF NOT EXISTS idx_user_username ON "user"(username);
-- CREATE INDEX IF NOT EXISTS idx_user_badge_id ON "user"(badge_id);
-- CREATE INDEX IF NOT EXISTS idx_checkout_history_tool_id ON checkout_history(tool_id);
-- CREATE INDEX IF NOT EXISTS idx_checkout_history_user_id ON checkout_history(user_id);

-- Configure text search for tool names and descriptions
-- CREATE INDEX IF NOT EXISTS idx_tools_search ON tools USING gin(to_tsvector('english', tool_name || ' ' || COALESCE(tool_location, '')));

-- Done
-- SQLAlchemy will handle table creation via migrations or db.create_all()
