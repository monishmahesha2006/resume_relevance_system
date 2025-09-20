"""
Database Manager for Resume Relevance System
Handles SQLite database operations
"""

import sqlite3
import json
import os
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manage SQLite database operations"""
    
    def __init__(self, db_path: str = "resume_matching.db"):
        self.db_path = db_path
        self._ensure_database_exists()
        self._initialize_database()
    
    def _ensure_database_exists(self):
        """Ensure database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _initialize_database(self):
        """Initialize database with schema"""
        # Try multiple possible schema paths
        possible_paths = [
            os.path.join(os.path.dirname(self.db_path), "schema.sql"),
            os.path.join("database", "schema.sql"),
            os.path.join("..", "database", "schema.sql"),
            "schema.sql"
        ]
        
        schema_path = None
        for path in possible_paths:
            if os.path.exists(path):
                schema_path = path
                break
        
        if schema_path:
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.executescript(schema_sql)
                conn.commit()
            logger.info("Database initialized with schema")
        else:
            logger.warning(f"Schema file not found in any of these locations: {possible_paths}")
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def save_job_description(self, file_name: str, file_path: str, raw_text: str, processed_data: Dict) -> int:
        """Save job description to database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO job_descriptions (file_name, file_path, raw_text, processed_data)
                VALUES (?, ?, ?, ?)
            """, (file_name, file_path, raw_text, json.dumps(processed_data)))
            conn.commit()
            return cursor.lastrowid
    
    def save_resume(self, file_name: str, file_path: str, raw_text: str, processed_data: Dict) -> int:
        """Save resume to database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO resumes (file_name, file_path, raw_text, processed_data)
                VALUES (?, ?, ?, ?)
            """, (file_name, file_path, raw_text, json.dumps(processed_data)))
            conn.commit()
            return cursor.lastrowid
    
    def save_matching_result(self, resume_id: int, jd_id: int, analysis_result: Dict) -> int:
        """Save matching result to database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO matching_results (
                    resume_id, jd_id, relevance_score, verdict, hard_match_score, 
                    soft_match_score, missing_skills, missing_education, 
                    experience_analysis, feedback, strengths, improvement_areas
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                resume_id, jd_id, analysis_result['relevance_score'],
                analysis_result['verdict'], analysis_result['hard_match_score'],
                analysis_result['soft_match_score'],
                json.dumps(analysis_result.get('missing_skills', [])),
                json.dumps(analysis_result.get('missing_education', [])),
                json.dumps(analysis_result.get('experience_analysis', {})),
                analysis_result.get('feedback', ''),
                json.dumps(analysis_result.get('strengths', [])),
                json.dumps(analysis_result.get('improvement_areas', []))
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_job_descriptions(self) -> List[Dict]:
        """Get all job descriptions"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM job_descriptions ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_resumes(self) -> List[Dict]:
        """Get all resumes"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM resumes ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_matching_results(self, limit: Optional[int] = None) -> List[Dict]:
        """Get all matching results"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            query = "SELECT * FROM matching_results ORDER BY relevance_score DESC"
            if limit:
                query += f" LIMIT {limit}"
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_matching_summary(self) -> List[Dict]:
        """Get matching summary using view"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM v_matching_summary ORDER BY relevance_score DESC")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_top_matches(self, limit: int = 10) -> List[Dict]:
        """Get top matches using view"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM v_top_matches LIMIT {limit}")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_matches_by_verdict(self, verdict: str) -> List[Dict]:
        """Get matches by verdict (High, Medium, Low)"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM v_matching_summary 
                WHERE verdict = ? 
                ORDER BY relevance_score DESC
            """, (verdict,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_matches_for_resume(self, resume_id: int) -> List[Dict]:
        """Get all matches for a specific resume"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT mr.*, jd.file_name as jd_name
                FROM matching_results mr
                JOIN job_descriptions jd ON mr.jd_id = jd.id
                WHERE mr.resume_id = ?
                ORDER BY mr.relevance_score DESC
            """, (resume_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_matches_for_jd(self, jd_id: int) -> List[Dict]:
        """Get all matches for a specific job description"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT mr.*, r.file_name as resume_name
                FROM matching_results mr
                JOIN resumes r ON mr.resume_id = r.id
                WHERE mr.jd_id = ?
                ORDER BY mr.relevance_score DESC
            """, (jd_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def search_matches(self, query: str) -> List[Dict]:
        """Search matches by resume or JD name"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM v_matching_summary 
                WHERE resume_name LIKE ? OR jd_name LIKE ?
                ORDER BY relevance_score DESC
            """, (f"%{query}%", f"%{query}%"))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Count records
            cursor.execute("SELECT COUNT(*) FROM job_descriptions")
            jd_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM resumes")
            resume_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM matching_results")
            match_count = cursor.fetchone()[0]
            
            # Average scores
            cursor.execute("SELECT AVG(relevance_score) FROM matching_results")
            avg_score = cursor.fetchone()[0] or 0
            
            # Verdict distribution
            cursor.execute("""
                SELECT verdict, COUNT(*) as count 
                FROM matching_results 
                GROUP BY verdict
            """)
            verdict_dist = dict(cursor.fetchall())
            
            return {
                'job_descriptions': jd_count,
                'resumes': resume_count,
                'matching_results': match_count,
                'average_score': round(avg_score, 2),
                'verdict_distribution': verdict_dist
            }
    
    def delete_job_description(self, jd_id: int) -> bool:
        """Delete job description and related matches"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Delete related matches first
                cursor.execute("DELETE FROM matching_results WHERE jd_id = ?", (jd_id,))
                # Delete job description
                cursor.execute("DELETE FROM job_descriptions WHERE id = ?", (jd_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to delete job description {jd_id}: {e}")
            return False
    
    def delete_resume(self, resume_id: int) -> bool:
        """Delete resume and related matches"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Delete related matches first
                cursor.execute("DELETE FROM matching_results WHERE resume_id = ?", (resume_id,))
                # Delete resume
                cursor.execute("DELETE FROM resumes WHERE id = ?", (resume_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to delete resume {resume_id}: {e}")
            return False


def main():
    """Test the database manager"""
    db_manager = DatabaseManager()
    
    # Test statistics
    stats = db_manager.get_statistics()
    print("Database Statistics:")
    for key, value in stats.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
