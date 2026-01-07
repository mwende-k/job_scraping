import os
import time
import streamlit as st
from supabase import create_client, Client
from datetime import datetime
from dotenv import load_dotenv

# Load env variables from .env file if present
load_dotenv()

class SupabaseHandler:
    def __init__(self):
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        
        # Fallback to st.secrets if not in env
        if not url or not key:
            try:
                if hasattr(st, "secrets") and "SUPABASE_URL" in st.secrets:
                     url = st.secrets["SUPABASE_URL"]
                     key = st.secrets["SUPABASE_KEY"]
            except FileNotFoundError:
                # No secrets.toml found, generic error will be raised below if url/key still empty
                pass
            except Exception:
                pass
        
        if not url or not key:
            st.error("Supabase credentials not found. Please set SUPABASE_URL and SUPABASE_KEY in .env or secrets.toml")
            # Return or raise? Raising stops execution which is probably good here.
            raise ValueError("Supabase credentials not found.")
            
        self.supabase: Client = create_client(url, key)

    def fetch_jobs(self, limit=1000, days_lookback=30):
        """Fetch jobs from the 'jobs' table"""
        # Calculate cutoff date
        # Note: Supabase/Postgres filters might be more efficient
        try:
            response = self.supabase.table("jobs").select("*").order("posted_date", desc=True).limit(limit).execute()
            return response.data
        except Exception as e:
            print(f"Error fetching jobs: {e}")
            return []

    def upsert_jobs(self, jobs_data):
        """
        Upsert a list of job dictionaries.
        jobs_data elements should match table schema.
        Expected schema: title, company, location, link, source, posted_date, created_at
        """
        if not jobs_data:
            return
            
        try:
            # We assume 'link' or a composite key might be the unique constraint
            # Ideally, have a 'dedupe_id' in the table as primary key or unique index
            response = self.supabase.table("jobs").upsert(jobs_data).execute()
            return response
        except Exception as e:
            print(f"Error upserting jobs: {e}")
            raise e
            
    def subscribe_user(self, email, tier="monthly"):
        """Record a user subscription"""
        data = {
            "email": email,
            "tier": tier,
            "status": "active",
            "subscribed_at": datetime.now().isoformat()
        }
        try:
            return self.supabase.table("subscriptions").upsert(data).execute()
        except Exception as e:
            print(f"Error subscribing user: {e}")
            return None

    def create_profile(self, user_id, email, tier="monthly"):
        """Create a user profile in the public table"""
        data = {
            "id": user_id,
            "email": email,
            "tier": tier,
            "created_at": datetime.now().isoformat()
        }
        
        # Retry logic to handle timing issues with auth.users table
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                # Using upsert to be safe if it already exists (e.g. via trigger)
                response = self.supabase.table("profiles").upsert(data).execute()
                print(f"Profile created successfully for user {user_id}: {response.data}")
                return response
            except Exception as e:
                error_str = str(e)
                
                # Check if it's a foreign key constraint error
                if "foreign key constraint" in error_str and attempt < max_retries - 1:
                    print(f"Foreign key constraint error on attempt {attempt + 1}, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    continue
                
                # If it's the last attempt or a different error, raise it
                error_msg = f"Error creating profile for {email}: {str(e)}"
                print(error_msg)
                raise Exception(error_msg)

    def get_profile(self, user_id):
        """Fetch a user profile by ID"""
        try:
            response = self.supabase.table("profiles").select("*").eq("id", user_id).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Error fetching profile: {e}")
            return None
