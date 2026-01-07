#!/usr/bin/env python3
"""
Check the profiles table schema and foreign key constraints
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

supabase = create_client(url, key)

print("=" * 60)
print("Checking Profiles Table Schema")
print("=" * 60)

# Try to get table info using a SQL query
try:
    # Check if we can query the auth.users table
    print("\n1. Checking auth.users table...")
    result = supabase.rpc('exec_sql', {
        'query': 'SELECT id, email FROM auth.users LIMIT 5'
    }).execute()
    print(f"   Found {len(result.data)} users in auth.users")
    if result.data:
        for user in result.data:
            print(f"   - {user}")
except Exception as e:
    print(f"   ❌ Cannot query auth.users: {e}")

# Check profiles table
try:
    print("\n2. Checking profiles table...")
    result = supabase.table("profiles").select("*").limit(5).execute()
    print(f"   Found {len(result.data)} profiles")
    if result.data:
        for profile in result.data:
            print(f"   - {profile}")
except Exception as e:
    print(f"   ❌ Error querying profiles: {e}")

# Try to understand the foreign key constraint
print("\n3. Understanding the issue...")
print("   The error mentions: 'profiles_id_fkey'")
print("   This suggests the profiles.id column has a foreign key constraint")
print("   pointing to a 'users' table (not auth.users)")
print("\n   Possible issues:")
print("   a) The foreign key references 'public.users' instead of 'auth.users'")
print("   b) The user hasn't been committed to auth.users yet (timing)")
print("   c) Email confirmation is required before user appears in auth.users")

print("\n" + "=" * 60)
print("Recommended Fix")
print("=" * 60)
print("""
The profiles table foreign key should reference 'auth.users', not 'public.users'.

Run this SQL in Supabase SQL Editor to check the constraint:

SELECT
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_name = 'profiles';

If it shows 'public.users', you need to recreate the constraint to point to 'auth.users':

-- Drop the incorrect constraint
ALTER TABLE profiles DROP CONSTRAINT profiles_id_fkey;

-- Add the correct constraint
ALTER TABLE profiles
ADD CONSTRAINT profiles_id_fkey
FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE;
""")
