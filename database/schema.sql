-- Database Schema for Resume Relevance System
-- SQLite optimized schema

-- Job Descriptions table
CREATE TABLE IF NOT EXISTS job_descriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    raw_text TEXT,
    processed_data TEXT, -- JSON string of processed data
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(file_path)
);

-- Resumes table
CREATE TABLE IF NOT EXISTS resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    raw_text TEXT,
    processed_data TEXT, -- JSON string of processed data
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(file_path)
);

-- Matching Results table
CREATE TABLE IF NOT EXISTS matching_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resume_id INTEGER NOT NULL,
    jd_id INTEGER NOT NULL,
    relevance_score REAL NOT NULL CHECK (relevance_score >= 0 AND relevance_score <= 1),
    verdict TEXT NOT NULL CHECK (verdict IN ('High', 'Medium', 'Low', 'Poor')),
    hard_match_score REAL NOT NULL CHECK (hard_match_score >= 0 AND hard_match_score <= 1),
    soft_match_score REAL NOT NULL CHECK (soft_match_score >= 0 AND soft_match_score <= 1),
    missing_skills TEXT, -- JSON array of missing skills
    missing_education TEXT, -- JSON array of missing education
    experience_analysis TEXT, -- JSON object of experience analysis
    feedback TEXT,
    strengths TEXT, -- JSON array of strengths
    improvement_areas TEXT, -- JSON array of improvement areas
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resume_id) REFERENCES resumes (id) ON DELETE CASCADE,
    FOREIGN KEY (jd_id) REFERENCES job_descriptions (id) ON DELETE CASCADE,
    UNIQUE(resume_id, jd_id)
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_matching_results_score ON matching_results(relevance_score DESC);
CREATE INDEX IF NOT EXISTS idx_matching_results_verdict ON matching_results(verdict);
CREATE INDEX IF NOT EXISTS idx_matching_results_resume ON matching_results(resume_id);
CREATE INDEX IF NOT EXISTS idx_matching_results_jd ON matching_results(jd_id);
CREATE INDEX IF NOT EXISTS idx_matching_results_created_at ON matching_results(created_at DESC);

-- Additional indexes for common queries
CREATE INDEX IF NOT EXISTS idx_resumes_file_name ON resumes(file_name);
CREATE INDEX IF NOT EXISTS idx_job_descriptions_file_name ON job_descriptions(file_name);
CREATE INDEX IF NOT EXISTS idx_resumes_created_at ON resumes(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_job_descriptions_created_at ON job_descriptions(created_at DESC);

-- Views for easier querying
CREATE VIEW IF NOT EXISTS v_matching_summary AS
SELECT 
    r.file_name as resume_name,
    jd.file_name as jd_name,
    mr.relevance_score,
    mr.verdict,
    mr.hard_match_score,
    mr.soft_match_score,
    mr.created_at
FROM matching_results mr
JOIN resumes r ON mr.resume_id = r.id
JOIN job_descriptions jd ON mr.jd_id = jd.id;

-- View for top matches
CREATE VIEW IF NOT EXISTS v_top_matches AS
SELECT 
    r.file_name as resume_name,
    jd.file_name as jd_name,
    mr.relevance_score,
    mr.verdict,
    mr.feedback
FROM matching_results mr
JOIN resumes r ON mr.resume_id = r.id
JOIN job_descriptions jd ON mr.jd_id = jd.id
WHERE mr.verdict IN ('High', 'Medium')
ORDER BY mr.relevance_score DESC;

-- View for detailed matching results with all analysis
CREATE VIEW IF NOT EXISTS v_detailed_matches AS
SELECT 
    r.file_name as resume_name,
    r.file_path as resume_path,
    jd.file_name as jd_name,
    jd.file_path as jd_path,
    mr.relevance_score,
    mr.verdict,
    mr.hard_match_score,
    mr.soft_match_score,
    mr.missing_skills,
    mr.missing_education,
    mr.experience_analysis,
    mr.feedback,
    mr.strengths,
    mr.improvement_areas,
    mr.created_at
FROM matching_results mr
JOIN resumes r ON mr.resume_id = r.id
JOIN job_descriptions jd ON mr.jd_id = jd.id;

-- Trigger to update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_job_descriptions_timestamp 
    AFTER UPDATE ON job_descriptions
    FOR EACH ROW
    BEGIN
        UPDATE job_descriptions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_resumes_timestamp 
    AFTER UPDATE ON resumes
    FOR EACH ROW
    BEGIN
        UPDATE resumes SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- Trigger to update updated_at timestamp for matching_results
CREATE TRIGGER IF NOT EXISTS update_matching_results_timestamp 
    AFTER UPDATE ON matching_results
    FOR EACH ROW
    BEGIN
        UPDATE matching_results SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;
