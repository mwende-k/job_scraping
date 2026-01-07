"""
Verify if the database trigger exists and check auth users
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

supabase = create_client(url, key)

print("=" * 70)
print("DIAGNOSTIC: Checking Database Trigger and Auth Users")
print("=" * 70)

# Check if there are any users in auth
print("\n1. Checking for users in auth system...")
try:
    # Use admin API to list users
    users = supabase.auth.admin.list_users()
    if users:
        print(f"   ✅ Found {len(users)} users in auth system:")
        for user in users[:5]:  # Show first 5
            print(f"      - {user.email} (ID: {user.id[:8]}...)")
            print(f"        Confirmed: {user.email_confirmed_at is not None}")
            print(f"        Created: {user.created_at}")
    else:
        print("   ⚠️  No users found in auth system")
except Exception as e:
    print(f"   ❌ Error listing users: {e}")

# Check profiles table
print("\n2. Checking profiles table...")
try:
    profiles = supabase.table("profiles").select("*").execute()
    if profiles.data:
        print(f"   ✅ Found {len(profiles.data)} profiles:")
        for profile in profiles.data[:5]:
            print(f"      - {profile}")
    else:
        print("   ⚠️  No profiles found in database")
        print("   This means the trigger is NOT working or wasn't created")
except Exception as e:
    print(f"   ❌ Error querying profiles: {e}")

print("\n" + "=" * 70)
print("DIAGNOSIS")
print("=" * 70)

print("""
If you see users but NO profiles, it means:
→ The database trigger was NOT created or is not working

SOLUTION:
1. Go to Supabase Dashboard → SQL Editor
2. Run the trigger creation SQL from TRIGGER_SOLUTION.md
3. Try signing up with a NEW email again

---

If you see NO users at all:
→ Signups might not be completing due to email confirmation

SOLUTION:
1. Go to Supabase Dashboard → Authentication → Settings
2. Temporarily DISABLE "Enable email confirmations"
3. Try signing up again

---

Email verification not working:
→ Check Supabase Dashboard → Authentication → Email Templates
→ Verify SMTP settings are configured
→ Check spam folder
""")
