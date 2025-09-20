# Database Setup and Management

This directory contains all the necessary files to set up and manage the SQLite database for the Resume Relevance System.

## 📁 Files

- **`schema.sql`** - Complete database schema with tables, views, indexes, and triggers
- **`init_database.py`** - Python script to initialize the database from schema
- **`init_database.bat`** - Windows batch script for easy database initialization
- **`init_database.sh`** - macOS/Linux shell script for database initialization
- **`db_manager.py`** - Comprehensive database management utility
- **`README.md`** - This documentation file

## 🚀 Quick Start

### Method 1: Using the Batch/Shell Scripts

**Windows:**
```cmd
init_database.bat
```

**macOS/Linux:**
```bash
./init_database.sh
```

### Method 2: Using Python Script

```bash
python init_database.py
```

### Method 3: Using Database Manager

```bash
python db_manager.py
```

## 🗄️ Database Schema

The database includes the following components:

### Tables
- **`job_descriptions`** - Stores job description files and processed data
- **`resumes`** - Stores resume files and processed data
- **`matching_results`** - Stores all matching results and analysis

### Views
- **`v_matching_summary`** - Summary view of all matches
- **`v_top_matches`** - Top matches (High/Medium verdict)
- **`v_detailed_matches`** - Detailed matching results with full analysis

### Indexes
- Performance indexes on frequently queried columns
- Composite indexes for complex queries

### Triggers
- Automatic timestamp updates for `updated_at` columns

## 🔧 Database Management

### Using db_manager.py

The database manager provides an interactive interface for:

1. **Show database info** - Display tables, views, indexes, and statistics
2. **Backup database** - Create timestamped backups
3. **Restore database** - Restore from backup files
4. **Export to CSV** - Export any table to CSV format
5. **Import from CSV** - Import data from CSV files
6. **Optimize database** - Run VACUUM for optimization
7. **Analyze database** - Run ANALYZE for query optimization

### Example Usage

```python
from db_manager import DatabaseManager

# Initialize database manager
db = DatabaseManager("resume_matching.db")

# Show database information
db.print_database_info()

# Create backup
db.backup_database("backup_20241220.db")

# Export table to CSV
db.export_to_csv("matching_results", "results.csv")
```

## 📊 Database Structure

### job_descriptions Table
```sql
CREATE TABLE job_descriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    raw_text TEXT,
    processed_data TEXT, -- JSON string
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(file_path)
);
```

### resumes Table
```sql
CREATE TABLE resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    raw_text TEXT,
    processed_data TEXT, -- JSON string
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(file_path)
);
```

### matching_results Table
```sql
CREATE TABLE matching_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resume_id INTEGER NOT NULL,
    jd_id INTEGER NOT NULL,
    relevance_score REAL NOT NULL CHECK (relevance_score >= 0 AND relevance_score <= 1),
    verdict TEXT NOT NULL CHECK (verdict IN ('High', 'Medium', 'Low', 'Poor')),
    hard_match_score REAL NOT NULL CHECK (hard_match_score >= 0 AND hard_match_score <= 1),
    soft_match_score REAL NOT NULL CHECK (soft_match_score >= 0 AND soft_match_score <= 1),
    missing_skills TEXT, -- JSON array
    missing_education TEXT, -- JSON array
    experience_analysis TEXT, -- JSON object
    feedback TEXT,
    strengths TEXT, -- JSON array
    improvement_areas TEXT, -- JSON array
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resume_id) REFERENCES resumes (id) ON DELETE CASCADE,
    FOREIGN KEY (jd_id) REFERENCES job_descriptions (id) ON DELETE CASCADE,
    UNIQUE(resume_id, jd_id)
);
```

## 🔍 Common Queries

### Get all matching results
```sql
SELECT * FROM v_matching_summary ORDER BY relevance_score DESC;
```

### Get top matches
```sql
SELECT * FROM v_top_matches LIMIT 10;
```

### Get detailed analysis for a specific match
```sql
SELECT * FROM v_detailed_matches 
WHERE resume_name = 'resume.pdf' AND jd_name = 'job_description.pdf';
```

### Get statistics by verdict
```sql
SELECT verdict, COUNT(*) as count, AVG(relevance_score) as avg_score
FROM matching_results 
GROUP BY verdict;
```

## 🚨 Troubleshooting

### Database not found
- Run `python init_database.py` to create the database
- Check file permissions in the database directory

### Permission errors
- Ensure write permissions in the database directory
- On Windows, run as administrator if needed

### Corrupted database
- Use `db_manager.py` to restore from backup
- Delete the database file and reinitialize

### Performance issues
- Run `VACUUM` to optimize the database
- Run `ANALYZE` to update query statistics
- Check if indexes are being used properly

## 📈 Performance Tips

1. **Regular Backups** - Create backups before major operations
2. **Index Usage** - Ensure queries use available indexes
3. **VACUUM** - Run periodically to reclaim space
4. **ANALYZE** - Update statistics for better query planning
5. **Batch Operations** - Use transactions for multiple operations

## 🔗 Integration

The database integrates with:
- **Backend API** - FastAPI endpoints for data access
- **Frontend Dashboard** - Streamlit interface for visualization
- **Pipeline Scripts** - Automated data processing
- **Analysis Tools** - Data export and reporting

## 📝 Notes

- The database uses SQLite for simplicity and portability
- All JSON data is stored as TEXT and parsed when needed
- Foreign key constraints ensure data integrity
- Triggers automatically update timestamps
- Views provide convenient query interfaces
