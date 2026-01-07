import streamlit as st
from db import SupabaseHandler
import time

def init_session():
    if "user" not in st.session_state:
        st.session_state.user = None
    if "auth_view" not in st.session_state:
        st.session_state.auth_view = "login" # or 'signup'


def login_with_social(provider):
    try:
        db = SupabaseHandler()
        # Ensure your redirect URL is configured in Supabase Auth settings
        # Usually it's your Streamlit app URL, e.g., http://localhost:8501
        callback_url = "http://localhost:8501" # Update for production
        
        # Get the OAuth provider URL
        data = db.supabase.auth.sign_in_with_oauth({
            "provider": provider,
            "options": {
                "redirect_to": callback_url
            }
        })
        
        if data and data.url:
            st.markdown(f'<a href="{data.url}" target="_self"><button style="width: 100%; padding: 0.5rem; margin-bottom: 0.5rem; background-color: #f0f2f6; border: 1px solid #ccc; border-radius: 5px; cursor: pointer;">Sign in with {provider.capitalize()}</button></a>', unsafe_allow_html=True) 
    except Exception as e:
        st.error(f"Error initializing {provider} login: {e}")

def login_form():
    st.subheader("Sign In")
    
    # Social Login Section
    st.markdown("#### Social Login")
    login_with_social("google")
    login_with_social("linkedin")
    
    st.markdown("---")
    st.markdown("#### Email Login")
    
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")
    
    if st.button("Log In", type="primary"):
        try:
            db = SupabaseHandler()
            response = db.supabase.auth.sign_in_with_password({"email": email, "password": password})
            if response.user:
                # Fetch Profile - REQUIRED
                profile = db.get_profile(response.user.id)
                
                if not profile:
                    # User authenticated but no profile in database
                    st.error("Access denied. Your account is not authorized. Please contact support.")
                    # Sign out the user
                    db.supabase.auth.sign_out()
                    return
                
                st.session_state.user = response.user
                st.session_state.profile = profile
                
                st.success(f"Logged in successfully! Tier: {profile.get('tier', 'Unknown')}")
                time.sleep(1)
                st.rerun()
        except Exception as e:
            st.error(f"Login failed: {e}")
            
    if st.button("New user? Sign up here"):
        st.session_state.auth_view = "signup"
        st.rerun()

def signup_form():
    st.subheader("Create Account")
    
    # Social Login Section
    st.markdown("#### Quick Sign Up")
    login_with_social("google")
    login_with_social("linkedin")
    
    st.markdown("---")
    st.markdown("#### Email Sign Up")
    
    email = st.text_input("Email", key="signup_email")
    password = st.text_input("Password", type="password", key="signup_password")
    
    if st.button("Sign Up", type="primary"):
        if not email or not password:
            st.error("Please enter both email and password")
            return
            
        if len(password) < 6:
            st.error("Password must be at least 6 characters long")
            return
            
        try:
            db = SupabaseHandler()
            
            st.info("Creating your account...")
            response = db.supabase.auth.sign_up({
                "email": email, 
                "password": password
            })
            
            if response.user:
                # Profile is created automatically by the trigger!
                if response.session is None:
                    st.warning("📧 Please check your email to verify your account before logging in.")
                    st.info("Check your spam folder if you don't see the email within a few minutes.")
                else:
                    st.success("✅ Account created successfully! You can now log in.")
                
                time.sleep(2)
                st.session_state.auth_view = "login"
                st.rerun()
            else:
                st.error("Signup failed: No user returned from Supabase")
                
        except Exception as e:
            error_message = str(e)
            st.error(f"❌ Signup failed: {error_message}")
            
            if "already registered" in error_message.lower():
                st.info("This email is already registered. Try logging in instead.")
            elif "invalid email" in error_message.lower():
                st.info("Please enter a valid email address.")
            
    if st.button("Already have an account? Log in"):
        st.session_state.auth_view = "login"
        st.rerun()

def logout():
    try:
        db = SupabaseHandler()
        db.supabase.auth.sign_out()
    except:
        pass
    st.session_state.user = None
    st.rerun()