"""
Database Initialization Script
Creates and initializes the SQLite database from schema.sql
"""

import sqlite3
import os
import sys
from pathlib import Path

def init_database(db_path="resume_matching.db"):
    """
    Initialize the SQLite database from schema.sql
    
    Args:
        db_path (str): Path to the SQLite database file
    """
    
    # Get the directory of this script
    script_dir = Path(__file__).parent
    schema_path = script_dir / "schema.sql"
    
    # Ensure the database directory exists
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        print(f"Removing existing database: {db_path}")
        os.remove(db_path)
    
    try:
        # Read the schema file
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Create database and execute schema
        with sqlite3.connect(db_path) as conn:
            print(f"Creating database: {db_path}")
            conn.executescript(schema_sql)
            conn.commit()
            
            # Verify tables were created
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            print("✅ Database created successfully!")
            print(f"📊 Tables created: {[table[0] for table in tables]}")
            
            # Verify views were created
            cursor.execute("SELECT name FROM sqlite_master WHERE type='view';")
            views = cursor.fetchall()
            print(f"📋 Views created: {[view[0] for view in views]}")
            
            # Verify triggers were created
            cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger';")
            triggers = cursor.fetchall()
            print(f"⚡ Triggers created: {[trigger[0] for trigger in triggers]}")
            
            # Verify indexes were created
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%';")
            indexes = cursor.fetchall()
            print(f"🔍 Indexes created: {[index[0] for index in indexes]}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

def verify_database(db_path="resume_matching.db"):
    """
    Verify the database structure and show statistics
    
    Args:
        db_path (str): Path to the SQLite database file
    """
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            print(f"\n📊 Database Statistics for: {db_path}")
            print("=" * 50)
            
            # Table information
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                count = cursor.fetchone()[0]
                print(f"📋 {table_name}: {count} records")
            
            # View information
            cursor.execute("SELECT name FROM sqlite_master WHERE type='view';")
            views = cursor.fetchall()
            if views:
                print(f"\n📋 Views: {[view[0] for view in views]}")
            
            # Index information
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%';")
            indexes = cursor.fetchall()
            if indexes:
                print(f"🔍 Indexes: {[index[0] for index in indexes]}")
            
            # Trigger information
            cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger';")
            triggers = cursor.fetchall()
            if triggers:
                print(f"⚡ Triggers: {[trigger[0] for trigger in triggers]}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error verifying database: {e}")
        return False

def create_sample_data(db_path="resume_matching.db"):
    """
    Create sample data for testing
    
    Args:
        db_path (str): Path to the SQLite database file
    """
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Sample job description
            cursor.execute("""
                INSERT INTO job_descriptions (file_name, file_path, raw_text, processed_data)
                VALUES (?, ?, ?, ?)
            """, (
                "sample_jd.pdf",
                "/path/to/sample_jd.pdf",
                "Software Engineer position requiring Python, Django, and 3+ years experience.",
                '{"skills": ["python", "django", "javascript"], "experience_years": 3, "education": ["bachelor computer science"]}'
            ))
            
            # Sample resume
            cursor.execute("""
                INSERT INTO resumes (file_name, file_path, raw_text, processed_data)
                VALUES (?, ?, ?, ?)
            """, (
                "sample_resume.pdf",
                "/path/to/sample_resume.pdf",
                "John Doe, Software Engineer with 5 years Python experience, Django, Flask, AWS.",
                '{"skills": ["python", "django", "flask", "aws"], "experience_years": 5, "education": ["bachelor computer science"]}'
            ))
            
            # Get the IDs
            jd_id = cursor.lastrowid
            cursor.execute("SELECT id FROM resumes WHERE file_name = 'sample_resume.pdf'")
            resume_id = cursor.fetchone()[0]
            
            # Sample matching result
            cursor.execute("""
                INSERT INTO matching_results (
                    resume_id, jd_id, relevance_score, verdict, hard_match_score, 
                    soft_match_score, missing_skills, missing_education, 
                    experience_analysis, feedback, strengths, improvement_areas
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                resume_id, jd_id, 0.85, "High", 0.9, 0.8,
                '["javascript"]', '[]',
                '{"gap": 0, "meets_requirement": true, "message": "Exceeds requirement by 2 years"}',
                "Excellent match! Strong technical skills and exceeds experience requirements.",
                '["Strong technical skills: python, django, aws"]',
                '[]'
            ))
            
            conn.commit()
            print("✅ Sample data created successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        return False

def main():
    """Main function to initialize the database"""
    
    print("🗄️ Resume Relevance System - Database Initialization")
    print("=" * 60)
    
    # Default database path
    db_path = "resume_matching.db"
    
    # Check if schema file exists
    schema_path = Path(__file__).parent / "schema.sql"
    if not schema_path.exists():
        print(f"❌ Schema file not found: {schema_path}")
        return False
    
    # Initialize database
    if init_database(db_path):
        print(f"\n✅ Database initialized successfully: {db_path}")
        
        # Verify database
        verify_database(db_path)
        
        # Ask if user wants sample data
        try:
            create_sample = input("\n🤔 Create sample data for testing? (y/n): ").strip().lower()
            if create_sample in ['y', 'yes']:
                create_sample_data(db_path)
                verify_database(db_path)
        except KeyboardInterrupt:
            print("\n👋 Database initialization completed!")
        
        print(f"\n🎉 Database ready! Location: {os.path.abspath(db_path)}")
        return True
    else:
        print("❌ Database initialization failed!")
        return False

if __name__ == "__main__":
    main()
