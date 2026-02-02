#!/usr/bin/env python3
"""
Supabase migration script
Run: python migrate_supabase.py
"""
import os
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # Use service key for migrations

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Read schema file
with open("schema.sql", "r") as f:
    schema_sql = f.read()

print("Applying Supabase schema...")
print("Note: Run this SQL manually in Supabase SQL Editor:")
print("=" * 80)
print(schema_sql)
print("=" * 80)
print("\nMigration SQL printed above. Apply manually in Supabase dashboard.")
