"""
Database migration script for hardening updates
Run this once to upgrade existing database schema
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "./jobs.db")

def migrate_database():
    """Migrate existing database to hardened schema"""
    
    print("Starting database migration...")
    conn = sqlite3.connect(DB_PATH)
    
    # Check if migration needed
    cursor = conn.execute("PRAGMA table_info(jobs)")
    columns = {row[1] for row in cursor.fetchall()}
    
    needs_migration = False
    
    # Add new columns
    if "last_heartbeat_at" not in columns:
        print("Adding last_heartbeat_at column...")
        conn.execute("ALTER TABLE jobs ADD COLUMN last_heartbeat_at TEXT")
        needs_migration = True
    
    if "started_at" not in columns:
        print("Adding started_at column...")
        conn.execute("ALTER TABLE jobs ADD COLUMN started_at TEXT")
        needs_migration = True
    
    if "finished_at" not in columns:
        print("Adding finished_at column...")
        conn.execute("ALTER TABLE jobs ADD COLUMN finished_at TEXT")
        needs_migration = True
    
    if "status_message" not in columns:
        print("Adding status_message column...")
        conn.execute("ALTER TABLE jobs ADD COLUMN status_message TEXT")
        needs_migration = True
    
    if "error_code" not in columns:
        print("Adding error_code column...")
        conn.execute("ALTER TABLE jobs ADD COLUMN error_code TEXT")
        needs_migration = True
    
    if "error_message" not in columns:
        print("Adding error_message column...")
        conn.execute("ALTER TABLE jobs ADD COLUMN error_message TEXT")
        needs_migration = True
    
    # Migrate old error column if exists
    if "error" in columns and "error_message" in columns:
        print("Migrating old error column to error_message...")
        conn.execute("UPDATE jobs SET error_message = error WHERE error IS NOT NULL AND error_message IS NULL")
        needs_migration = True
    
    # Create heartbeat index
    print("Creating heartbeat index...")
    try:
        conn.execute("CREATE INDEX IF NOT EXISTS idx_heartbeat ON jobs(last_heartbeat_at) WHERE status = 'RUNNING'")
    except sqlite3.OperationalError:
        pass
    
    # Enable WAL mode
    print("Enabling WAL mode...")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=5000")
    
    # Initialize heartbeat for existing RUNNING jobs
    print("Initializing heartbeat for existing RUNNING jobs...")
    now = datetime.utcnow().isoformat()
    conn.execute("UPDATE jobs SET last_heartbeat_at = ? WHERE status = 'RUNNING' AND last_heartbeat_at IS NULL", (now,))
    
    conn.commit()
    
    # Verify migration
    cursor = conn.execute("PRAGMA table_info(jobs)")
    final_columns = {row[1] for row in cursor.fetchall()}
    
    print("\nMigration complete!")
    print(f"Database columns: {', '.join(sorted(final_columns))}")
    
    # Show stats
    stats = conn.execute("""
        SELECT 
            status,
            COUNT(*) as count
        FROM jobs
        GROUP BY status
    """).fetchall()
    
    print("\nJob statistics:")
    for status, count in stats:
        print(f"  {status}: {count}")
    
    conn.close()
    
    if not needs_migration:
        print("\nDatabase was already up to date.")
    else:
        print("\nDatabase successfully migrated to hardened schema.")

if __name__ == "__main__":
    migrate_database()
