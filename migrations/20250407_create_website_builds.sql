-- Create website_builds table for tracking build status
CREATE TABLE IF NOT EXISTS website_builds (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('queued', 'in_progress', 'complete', 'error')),
    preview_url TEXT,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    version_id UUID REFERENCES website_versions(id)
);

-- Create index for faster user_id lookups
CREATE INDEX IF NOT EXISTS website_builds_user_id_idx ON website_builds(user_id);

-- Create index for status queries
CREATE INDEX IF NOT EXISTS website_builds_status_idx ON website_builds(status);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_website_builds_updated_at
    BEFORE UPDATE ON website_builds
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
