-- EligibAI Database Initialization Script
-- This script sets up the database schema for the EligibAI system

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User profiles table
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    age INTEGER NOT NULL,
    gender VARCHAR(50) NOT NULL,
    state VARCHAR(100) NOT NULL,
    district VARCHAR(100),
    category VARCHAR(50) NOT NULL,
    course VARCHAR(100) NOT NULL,
    year_of_study VARCHAR(50) NOT NULL,
    college_name VARCHAR(255) NOT NULL,
    annual_family_income DECIMAL(12,2) NOT NULL,
    disability_status VARCHAR(10) DEFAULT 'No',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- Scholarships table
CREATE TABLE IF NOT EXISTS scholarships (
    id VARCHAR(50) PRIMARY KEY,
    scheme_name VARCHAR(255) NOT NULL,
    provider VARCHAR(255) NOT NULL,
    state VARCHAR(100),
    academic_year VARCHAR(20) NOT NULL,
    benefit TEXT NOT NULL,
    deadline VARCHAR(50) NOT NULL,
    source_url TEXT NOT NULL,
    required_documents TEXT[],
    application_process TEXT,
    last_updated TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scholarship eligibility rules
CREATE TABLE IF NOT EXISTS scholarship_eligibility (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scholarship_id VARCHAR(50) REFERENCES scholarships(id) ON DELETE CASCADE,
    education TEXT[],
    income_max INTEGER,
    income_min INTEGER,
    category TEXT[],
    age_min INTEGER,
    age_max INTEGER,
    gender VARCHAR(50),
    state TEXT[],
    disability_required BOOLEAN,
    year_of_study TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(scholarship_id)
);

-- Search history table
CREATE TABLE IF NOT EXISTS search_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_profile_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    search_query TEXT NOT NULL,
    search_filters JSONB,
    results_count INTEGER,
    processing_time DECIMAL(10,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Eligibility results table
CREATE TABLE IF NOT EXISTS eligibility_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_profile_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    scholarship_id VARCHAR(50) REFERENCES scholarships(id) ON DELETE CASCADE,
    overall_status VARCHAR(50) NOT NULL,
    comparisons JSONB NOT NULL,
    reasons TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_profile_id, scholarship_id)
);

-- Feedback table
CREATE TABLE IF NOT EXISTS user_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_profile_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    scholarship_id VARCHAR(50) REFERENCES scholarships(id) ON DELETE SET NULL,
    feedback_type VARCHAR(50) NOT NULL,
    feedback_text TEXT,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance metrics table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,3) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_state ON user_profiles(state);
CREATE INDEX IF NOT EXISTS idx_user_profiles_category ON user_profiles(category);
CREATE INDEX IF NOT EXISTS idx_scholarships_state ON scholarships(state);
CREATE INDEX IF NOT EXISTS idx_scholarships_provider ON scholarships(provider);
CREATE INDEX IF NOT EXISTS idx_search_history_user ON search_history(user_profile_id);
CREATE INDEX IF NOT EXISTS idx_eligibility_results_user ON eligibility_results(user_profile_id);
CREATE INDEX IF NOT EXISTS idx_eligibility_results_status ON eligibility_results(overall_status);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_name ON performance_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics(timestamp);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for updated_at
CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scholarships_updated_at BEFORE UPDATE ON scholarships
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scholarship_eligibility_updated_at BEFORE UPDATE ON scholarship_eligibility
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample scholarship data (optional)
-- This would normally be populated by the application