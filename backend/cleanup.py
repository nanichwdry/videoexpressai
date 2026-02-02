"""
TASK 4: Storage cleanup utility
Removes old completed/failed jobs and their artifacts
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta
import sys

DB_PATH = os.getenv("DB_PATH", "./jobs.db")

def cleanup_old_jobs(days_old: int = 7, dry_run: bool = True):
    """
    Delete jobs older than N days and cleanup their storage artifacts
    
    Args:
        days_old: Delete jobs older than this many days
        dry_run: If True, only show what would be deleted
    """
    conn = sqlite3.connect(DB_PATH)
    cutoff_date = datetime.utcnow() - timedelta(days=days_old)
    
    # Find old jobs in terminal states
    rows = conn.execute("""
        SELECT job_id, type, status, output_urls, created_at 
        FROM jobs 
        WHERE status IN ('SUCCEEDED', 'FAILED', 'CANCELED')
        AND created_at < ?
    """, (cutoff_date.isoformat(),)).fetchall()
    
    print(f"Found {len(rows)} jobs older than {days_old} days")
    
    total_size = 0
    deleted_count = 0
    
    for job_id, job_type, status, output_urls_json, created_at in rows:
        output_urls = json.loads(output_urls_json) if output_urls_json else []
        
        print(f"\nJob: {job_id}")
        print(f"  Type: {job_type}")
        print(f"  Status: {status}")
        print(f"  Created: {created_at}")
        print(f"  Artifacts: {len(output_urls)}")
        
        # Calculate size and delete artifacts
        for url in output_urls:
            if url.startswith("file://"):
                file_path = url.replace("file://", "")
                if os.path.exists(file_path):
                    size = os.path.getsize(file_path)
                    total_size += size
                    print(f"    - {file_path} ({size / 1024 / 1024:.2f} MB)")
                    
                    if not dry_run:
                        os.remove(file_path)
                        print(f"      DELETED")
        
        # Delete from database
        if not dry_run:
            conn.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
            deleted_count += 1
    
    if not dry_run:
        conn.commit()
    
    conn.close()
    
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Summary:")
    print(f"  Jobs: {deleted_count if not dry_run else len(rows)}")
    print(f"  Storage freed: {total_size / 1024 / 1024:.2f} MB")
    
    if dry_run:
        print("\nRun with --execute to actually delete")

def cleanup_orphaned_files():
    """Find and remove video files without corresponding database entries"""
    conn = sqlite3.connect(DB_PATH)
    
    # Get all output URLs from database
    rows = conn.execute("SELECT output_urls FROM jobs WHERE output_urls IS NOT NULL").fetchall()
    known_files = set()
    
    for (output_urls_json,) in rows:
        output_urls = json.loads(output_urls_json) if output_urls_json else []
        for url in output_urls:
            if url.startswith("file://"):
                known_files.add(url.replace("file://", ""))
    
    conn.close()
    
    # Check /tmp for orphaned files
    tmp_dir = "/tmp"
    orphaned = []
    
    if os.path.exists(tmp_dir):
        for filename in os.listdir(tmp_dir):
            if filename.endswith(".mp4"):
                file_path = os.path.join(tmp_dir, filename)
                if file_path not in known_files:
                    size = os.path.getsize(file_path)
                    orphaned.append((file_path, size))
    
    if orphaned:
        print(f"\nFound {len(orphaned)} orphaned files:")
        total_size = 0
        for file_path, size in orphaned:
            total_size += size
            print(f"  - {file_path} ({size / 1024 / 1024:.2f} MB)")
        print(f"\nTotal: {total_size / 1024 / 1024:.2f} MB")
        print("\nThese files are not referenced by any job in the database.")
        print("They can be safely deleted manually if needed.")
    else:
        print("\nNo orphaned files found.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Cleanup old jobs and storage artifacts")
    parser.add_argument("--days", type=int, default=7, help="Delete jobs older than N days (default: 7)")
    parser.add_argument("--execute", action="store_true", help="Actually delete (default is dry-run)")
    parser.add_argument("--orphaned", action="store_true", help="Check for orphaned files")
    
    args = parser.parse_args()
    
    if args.orphaned:
        cleanup_orphaned_files()
    else:
        cleanup_old_jobs(days_old=args.days, dry_run=not args.execute)
