"""
Database Management Script
Provides utilities for managing the SQLite database
"""

import sqlite3
import os
import json
import sys
from pathlib import Path
from datetime import datetime

class DatabaseManager:
    """Enhanced database manager with additional utilities"""
    
    def __init__(self, db_path="resume_matching.db"):
        self.db_path = db_path
        self.ensure_database_exists()
    
    def ensure_database_exists(self):
        """Ensure database exists, create if not"""
        if not os.path.exists(self.db_path):
            print(f"Database not found: {self.db_path}")
            print("Creating database from schema...")
            self.init_from_schema()
    
    def init_from_schema(self):
        """Initialize database from schema.sql"""
        schema_path = Path(__file__).parent / "schema.sql"
        
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(schema_sql)
            conn.commit()
        
        print(f"✅ Database created: {self.db_path}")
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def backup_database(self, backup_path=None):
        """Create a backup of the database"""
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"backup_{timestamp}.db"
        
        try:
            # Create backup using SQLite's backup API
            source = sqlite3.connect(self.db_path)
            backup = sqlite3.connect(backup_path)
            
            source.backup(backup)
            source.close()
            backup.close()
            
            print(f"✅ Database backed up to: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return None
    
    def restore_database(self, backup_path):
        """Restore database from backup"""
        if not os.path.exists(backup_path):
            print(f"❌ Backup file not found: {backup_path}")
            return False
        
        try:
            # Create backup of current database
            current_backup = self.backup_database()
            
            # Copy backup to current database
            import shutil
            shutil.copy2(backup_path, self.db_path)
            
            print(f"✅ Database restored from: {backup_path}")
            print(f"📋 Previous database backed up to: {current_backup}")
            return True
        except Exception as e:
            print(f"❌ Restore failed: {e}")
            return False
    
    def get_database_info(self):
        """Get comprehensive database information"""
        info = {
            'file_path': os.path.abspath(self.db_path),
            'file_size': os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0,
            'tables': [],
            'views': [],
            'indexes': [],
            'triggers': [],
            'statistics': {}
        }
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                info['tables'] = [table[0] for table in tables]
                
                # Get views
                cursor.execute("SELECT name FROM sqlite_master WHERE type='view';")
                views = cursor.fetchall()
                info['views'] = [view[0] for view in views]
                
                # Get indexes
                cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%';")
                indexes = cursor.fetchall()
                info['indexes'] = [index[0] for index in indexes]
                
                # Get triggers
                cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger';")
                triggers = cursor.fetchall()
                info['triggers'] = [trigger[0] for trigger in triggers]
                
                # Get table statistics
                for table in info['tables']:
                    cursor.execute(f"SELECT COUNT(*) FROM {table};")
                    count = cursor.fetchone()[0]
                    info['statistics'][table] = count
                
        except Exception as e:
            print(f"❌ Error getting database info: {e}")
        
        return info
    
    def print_database_info(self):
        """Print formatted database information"""
        info = self.get_database_info()
        
        print(f"\n📊 Database Information")
        print("=" * 50)
        print(f"📁 File: {info['file_path']}")
        print(f"📏 Size: {info['file_size']:,} bytes")
        
        print(f"\n📋 Tables ({len(info['tables'])}):")
        for table in info['tables']:
            count = info['statistics'].get(table, 0)
            print(f"  • {table}: {count:,} records")
        
        if info['views']:
            print(f"\n📋 Views ({len(info['views'])}):")
            for view in info['views']:
                print(f"  • {view}")
        
        if info['indexes']:
            print(f"\n🔍 Indexes ({len(info['indexes'])}):")
            for index in info['indexes']:
                print(f"  • {index}")
        
        if info['triggers']:
            print(f"\n⚡ Triggers ({len(info['triggers'])}):")
            for trigger in info['triggers']:
                print(f"  • {trigger}")
    
    def export_to_csv(self, table_name, output_path=None):
        """Export table to CSV"""
        if output_path is None:
            output_path = f"{table_name}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        try:
            import pandas as pd
            
            with self.get_connection() as conn:
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                df.to_csv(output_path, index=False)
            
            print(f"✅ Table '{table_name}' exported to: {output_path}")
            return output_path
        except Exception as e:
            print(f"❌ Export failed: {e}")
            return None
    
    def import_from_csv(self, table_name, csv_path):
        """Import data from CSV to table"""
        if not os.path.exists(csv_path):
            print(f"❌ CSV file not found: {csv_path}")
            return False
        
        try:
            import pandas as pd
            
            df = pd.read_csv(csv_path)
            
            with self.get_connection() as conn:
                df.to_sql(table_name, conn, if_exists='append', index=False)
            
            print(f"✅ Data imported to '{table_name}' from: {csv_path}")
            return True
        except Exception as e:
            print(f"❌ Import failed: {e}")
            return False
    
    def vacuum_database(self):
        """Optimize database by running VACUUM"""
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
                conn.commit()
            
            print("✅ Database optimized (VACUUM completed)")
            return True
        except Exception as e:
            print(f"❌ VACUUM failed: {e}")
            return False
    
    def analyze_database(self):
        """Analyze database for query optimization"""
        try:
            with self.get_connection() as conn:
                conn.execute("ANALYZE")
                conn.commit()
            
            print("✅ Database analyzed for query optimization")
            return True
        except Exception as e:
            print(f"❌ ANALYZE failed: {e}")
            return False

def main():
    """Main function for database management"""
    
    print("🗄️ Resume Relevance System - Database Manager")
    print("=" * 60)
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    # Show database information
    db_manager.print_database_info()
    
    # Interactive menu
    while True:
        print(f"\n🔧 Database Management Options:")
        print("1. Show database info")
        print("2. Backup database")
        print("3. Restore database")
        print("4. Export table to CSV")
        print("5. Import data from CSV")
        print("6. Optimize database (VACUUM)")
        print("7. Analyze database")
        print("8. Exit")
        
        try:
            choice = input("\nEnter your choice (1-8): ").strip()
            
            if choice == '1':
                db_manager.print_database_info()
            
            elif choice == '2':
                backup_path = input("Enter backup path (or press Enter for default): ").strip()
                if not backup_path:
                    backup_path = None
                db_manager.backup_database(backup_path)
            
            elif choice == '3':
                backup_path = input("Enter backup file path: ").strip()
                if backup_path:
                    db_manager.restore_database(backup_path)
            
            elif choice == '4':
                table_name = input("Enter table name to export: ").strip()
                if table_name:
                    db_manager.export_to_csv(table_name)
            
            elif choice == '5':
                table_name = input("Enter table name to import to: ").strip()
                csv_path = input("Enter CSV file path: ").strip()
                if table_name and csv_path:
                    db_manager.import_from_csv(table_name, csv_path)
            
            elif choice == '6':
                db_manager.vacuum_database()
            
            elif choice == '7':
                db_manager.analyze_database()
            
            elif choice == '8':
                print("👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid choice. Please try again.")
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
