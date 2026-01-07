#!/usr/bin/env python3
"""
Test script to verify Supabase authentication and database setup
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def test_connection():
    """Test basic Supabase connection"""
    print("=" * 50)
    print("Testing Supabase Connection")
    print("=" * 50)
    
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        print("❌ SUPABASE_URL or SUPABASE_KEY not found in environment")
        return False
    
    print(f"✅ URL found: {url[:20]}...")
    print(f"✅ Key found: {key[:20]}...")
    
    try:
        supabase = create_client(url, key)
        print("✅ Supabase client created successfully")
        return supabase
    except Exception as e:
        print(f"❌ Failed to create Supabase client: {e}")
        return None

def test_profiles_table(supabase):
    """Test if profiles table exists and is accessible"""
    print("\n" + "=" * 50)
    print("Testing Profiles Table")
    print("=" * 50)
    
    try:
        # Try to query the profiles table
        response = supabase.table("profiles").select("*").limit(1).execute()
        print(f"✅ Profiles table exists and is accessible")
        print(f"   Current row count: {len(response.data)}")
        if response.data:
            print(f"   Sample data: {response.data[0]}")
        return True
    except Exception as e:
        print(f"❌ Error accessing profiles table: {e}")
        print("\n⚠️  You may need to create the profiles table in Supabase")
        print("   Run this SQL in your Supabase SQL Editor:")
        print("""
        CREATE TABLE IF NOT EXISTS profiles (
            id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
            email TEXT NOT NULL,
            tier TEXT DEFAULT 'monthly',
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        -- Enable Row Level Security
        ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
        
        -- Allow users to read their own profile
        CREATE POLICY "Users can view own profile" ON profiles
            FOR SELECT USING (auth.uid() = id);
        
        -- Allow users to insert their own profile
        CREATE POLICY "Users can insert own profile" ON profiles
            FOR INSERT WITH CHECK (auth.uid() = id);
        
        -- Allow service role to do anything (for your backend)
        CREATE POLICY "Service role can do anything" ON profiles
            FOR ALL USING (auth.role() = 'service_role');
        """)
        return False

def test_email_settings(supabase):
    """Check email configuration"""
    print("\n" + "=" * 50)
    print("Email Configuration Check")
    print("=" * 50)
    
    print("⚠️  To enable email verification:")
    print("   1. Go to Supabase Dashboard → Authentication → Email Templates")
    print("   2. Customize your confirmation email template")
    print("   3. Go to Authentication → Settings")
    print("   4. Check 'Enable email confirmations' setting")
    print("   5. Configure SMTP settings if using custom email provider")
    print("\n   By default, Supabase sends emails from their domain.")
    print("   Check your spam folder if emails aren't arriving.")

def test_signup(supabase):
    """Test a signup flow"""
    print("\n" + "=" * 50)
    print("Testing Signup Flow")
    print("=" * 50)
    
    test_email = input("\nEnter a test email (or press Enter to skip): ").strip()
    if not test_email:
        print("Skipping signup test")
        return
    
    test_password = "TestPassword123!"
    
    try:
        print(f"\n📝 Attempting to sign up: {test_email}")
        response = supabase.auth.sign_up({
            "email": test_email,
            "password": test_password
        })
        
        print(f"✅ Signup response received")
        print(f"   User ID: {response.user.id if response.user else 'None'}")
        print(f"   Email: {response.user.email if response.user else 'None'}")
        print(f"   Session: {'Yes' if response.session else 'No (email confirmation required)'}")
        
        if response.user:
            # Try to create profile
            print(f"\n📝 Creating profile for user {response.user.id}")
            profile_data = {
                "id": response.user.id,
                "email": test_email,
                "tier": "monthly"
            }
            
            profile_response = supabase.table("profiles").upsert(profile_data).execute()
            print(f"✅ Profile created: {profile_response.data}")
            
    except Exception as e:
        print(f"❌ Signup test failed: {e}")

if __name__ == "__main__":
    supabase = test_connection()
    
    if supabase:
        test_profiles_table(supabase)
        test_email_settings(supabase)
        test_signup(supabase)
    
    print("\n" + "=" * 50)
    print("Test Complete")
    print("=" * 50)
