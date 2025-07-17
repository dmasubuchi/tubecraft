-- TUBECRAFT Database Initialization Script
-- This script creates the necessary tables and indexes for the TUBECRAFT system

-- Create database if not exists (handled by docker-entrypoint)
-- CREATE DATABASE IF NOT EXISTS tubecraft_db;

-- Use the created database
-- \c tubecraft_db;

-- Create custom types
CREATE TYPE episode_status AS ENUM (
    'draft',
    'generating_script',
    'generating_audio',
    'generating_video',
    'completed',
    'failed',
    'cancelled'
);

CREATE TYPE content_style AS ENUM (
    'educational',
    'news',
    'entertainment',
    'podcast',
    'tutorial',
    'interview'
);

-- Episodes table - main content management
CREATE TABLE episodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    script JSONB,
    status episode_status NOT NULL DEFAULT 'draft',
    content_style content_style DEFAULT 'educational',
    
    -- File paths
    audio_path VARCHAR(1000),
    video_path VARCHAR(1000),
    thumbnail_path VARCHAR(1000),
    script_path VARCHAR(1000),
    
    -- Metadata
    duration_seconds INTEGER,
    file_size_mb INTEGER,
    target_duration_minutes INTEGER DEFAULT 15,
    
    -- Generation tracking
    generation_started_at TIMESTAMP,
    generation_completed_at TIMESTAMP,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}',
    tags TEXT[],
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Generation logs table - detailed process tracking
CREATE TABLE generation_logs (
    id SERIAL PRIMARY KEY,
    episode_id UUID REFERENCES episodes(id) ON DELETE CASCADE,
    step VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    message TEXT,
    execution_time_ms INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Content templates table - reusable script templates
CREATE TABLE content_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    content_style content_style NOT NULL,
    template_data JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System metrics table - performance monitoring
CREATE TABLE system_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,2) NOT NULL,
    metric_unit VARCHAR(20),
    metadata JSONB DEFAULT '{}',
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_episodes_status_created ON episodes(status, created_at DESC);
CREATE INDEX idx_episodes_generation_date ON episodes(generation_completed_at DESC) 
    WHERE generation_completed_at IS NOT NULL;
CREATE INDEX idx_episodes_status ON episodes(status);
CREATE INDEX idx_episodes_content_style ON episodes(content_style);
CREATE INDEX idx_episodes_tags ON episodes USING GIN(tags);
CREATE INDEX idx_episodes_metadata ON episodes USING GIN(metadata);

CREATE INDEX idx_generation_logs_episode_id ON generation_logs(episode_id);
CREATE INDEX idx_generation_logs_step ON generation_logs(step);
CREATE INDEX idx_generation_logs_created ON generation_logs(created_at DESC);

CREATE INDEX idx_content_templates_style ON content_templates(content_style);
CREATE INDEX idx_content_templates_active ON content_templates(is_active);

CREATE INDEX idx_system_metrics_name_recorded ON system_metrics(metric_name, recorded_at DESC);

-- Create a function to update the updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_episodes_updated_at 
    BEFORE UPDATE ON episodes 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_content_templates_updated_at 
    BEFORE UPDATE ON content_templates 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample content templates
INSERT INTO content_templates (name, description, content_style, template_data) VALUES
(
    'Educational Tech Talk',
    'Technical educational content template',
    'educational',
    '{
        "sections": [
            {"type": "intro", "duration": 60, "template": "今日は{topic}について解説します。"},
            {"type": "main_content", "duration": 720, "template": "まず、{topic}の基本概念から説明しましょう。"},
            {"type": "example", "duration": 300, "template": "具体的な例を見てみましょう。"},
            {"type": "conclusion", "duration": 120, "template": "今日学んだ{topic}のポイントをまとめます。"}
        ],
        "total_duration": 1200,
        "voice_settings": {"speed": 1.0, "tone": "professional"}
    }'
),
(
    'News Summary',
    'Daily news summary template',
    'news',
    '{
        "sections": [
            {"type": "opening", "duration": 30, "template": "本日のニュースをお伝えします。"},
            {"type": "top_stories", "duration": 600, "template": "まず、今日の主要なニュースから。"},
            {"type": "technology", "duration": 300, "template": "テクノロジー関連のニュースです。"},
            {"type": "closing", "duration": 30, "template": "以上、今日のニュースでした。"}
        ],
        "total_duration": 960,
        "voice_settings": {"speed": 1.1, "tone": "news_anchor"}
    }'
);

-- Insert sample episode for testing
INSERT INTO episodes (title, description, content_style, target_duration_minutes, status) VALUES
(
    'Docker入門 - コンテナ技術の基礎',
    'Dockerの基本概念から実際の使い方まで、初心者向けに分かりやすく解説します。',
    'educational',
    15,
    'draft'
);

-- Create a view for episode statistics
CREATE VIEW episode_stats AS
SELECT 
    content_style,
    status,
    COUNT(*) as count,
    AVG(duration_seconds) as avg_duration_seconds,
    AVG(file_size_mb) as avg_file_size_mb,
    MIN(created_at) as first_created,
    MAX(created_at) as last_created
FROM episodes 
GROUP BY content_style, status;

-- Create a view for recent activity
CREATE VIEW recent_activity AS
SELECT 
    e.id,
    e.title,
    e.status,
    e.created_at,
    e.updated_at,
    CASE 
        WHEN e.generation_completed_at IS NOT NULL THEN 
            EXTRACT(EPOCH FROM (e.generation_completed_at - e.generation_started_at))
        ELSE NULL
    END as generation_time_seconds
FROM episodes e
ORDER BY e.updated_at DESC
LIMIT 50;

-- Grant permissions for n8n user (if needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO tubecraft;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO tubecraft;

NOTIFY_MESSAGE 'TUBECRAFT database initialized successfully!';