"""
Test if users appear in auth.users immediately after signup
"""
import os
from dotenv import load_dotenv
from supabase import create_client
import time

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

supabase = create_client(url, key)

print("Testing user creation flow...")
print("=" * 60)

# Try to sign up a test user
test_email = f"test_{int(time.time())}@example.com"
test_password = "TestPassword123!"

print(f"\n1. Signing up: {test_email}")
try:
    response = supabase.auth.sign_up({
        "email": test_email,
        "password": test_password
    })
    
    if response.user:
        user_id = response.user.id
        print(f"   ✅ User created with ID: {user_id}")
        print(f"   Session exists: {response.session is not None}")
        print(f"   Email confirmed: {response.user.email_confirmed_at is not None}")
        
        # Wait a moment
        print("\n2. Waiting 2 seconds...")
        time.sleep(2)
        
        # Try to query auth.users using the admin API
        print("\n3. Checking if user exists in auth.users...")
        try:
            # Use the admin API to list users
            from supabase.lib.client_options import ClientOptions
            admin_client = create_client(
                url, 
                key,
                options=ClientOptions(
                    auto_refresh_token=False,
                    persist_session=False
                )
            )
            
            # Try to get user by ID
            user_response = admin_client.auth.admin.get_user_by_id(user_id)
            if user_response:
                print(f"   ✅ User found in auth.users!")
                print(f"   Email: {user_response.user.email}")
                print(f"   Confirmed: {user_response.user.email_confirmed_at is not None}")
            else:
                print(f"   ❌ User NOT found in auth.users")
                
        except Exception as e:
            print(f"   ⚠️  Cannot query auth.users: {e}")
        
        # Now try to create profile
        print("\n4. Attempting to create profile...")
        try:
            profile_data = {
                "id": user_id,
                "email": test_email,
                "tier": "monthly"
            }
            profile_response = supabase.table("profiles").upsert(profile_data).execute()
            print(f"   ✅ Profile created successfully!")
            print(f"   Data: {profile_response.data}")
        except Exception as e:
            print(f"   ❌ Profile creation failed: {e}")
            
            # Check what the actual error is
            error_str = str(e)
            if "foreign key" in error_str:
                print("\n   Analysis: Foreign key constraint is blocking profile creation")
                print("   This means the constraint is still pointing to wrong table")
                print("   OR email confirmation is required before user appears in auth.users")
            
    else:
        print("   ❌ Signup failed - no user returned")
        
except Exception as e:
    print(f"   ❌ Signup error: {e}")

print("\n" + "=" * 60)
print("Recommendation:")
print("If profile creation failed, the issue is likely:")
print("1. Email confirmation required (check Supabase Auth settings)")
print("2. Foreign key still pointing to wrong table")
print("\nTo disable email confirmation temporarily:")
print("Supabase Dashboard → Authentication → Settings")
print("→ Disable 'Enable email confirmations'")
