import streamlit as st
import pandas as pd
import logging
from datetime import datetime, timedelta
from config import LOCATIONS, JOB_TITLES
from utils import setup_logger, parse_relative_date, normalize_url
from db import SupabaseHandler
from auth import init_session, login_form, signup_form, logout

# Configure Streamlit
st.set_page_config(page_title="Eastern Africa Data Job Scraper", layout="wide", page_icon="🐯")

# Initialize Session
init_session()

def landing_page():
    st.markdown("""
    <div style="text-align: center; padding: 50px 0;">
        <h1>🐯 Eastern Africa Data Jobs</h1>
        <p style="font-size: 1.2em; color: #666;">
            The premier platform for Data Analysts, Engineers, and Scientists 
            finding work in Kenya, Tanzania, Uganda, and beyond.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.markdown("### 🚀 Why Join?")
        st.markdown("""
        - **Aggregated Listings**: Jobs from LinkedIn, BrighterMonday, MyJobMag in one place.
        - **Smart Filtering**: Filter by role, country, and date.
        - **Daily Updates**: Fresh jobs added every 24 hours.
        - **Excel/CSV Export**: Download data for your own analysis.
        """)
        
    with col2:
        if st.session_state.auth_view == "login":
            login_form()
        else:
            signup_form()

    st.markdown("---")
    st.subheader("Pricing Plans")
    
    p_col1, p_col2 = st.columns(2)
    
    with p_col1:
        st.info("### Monthly\n**$10 / month**\n\n- Full Access\n- Daily Updates\n- Cancel Anytime")
        
    with p_col2:
        st.success("### Yearly\n**$100 / year**\n\n- **Save 16%**\n- Priority Support\n- Early Access Features")

def dashboard():
    st.sidebar.title("🐯 Dashboard")
    st.sidebar.write(f"Logged in as: {st.session_state.user.email}")
    if st.sidebar.button("Log Out"):
        logout()
        
    st.title("Search Jobs")
    
    # Sidebar Controls
    st.sidebar.header("Filters")
    
    # Countries filter with Select All
    select_all_locations = st.sidebar.checkbox("Select All Countries", value=False)
    if select_all_locations:
        selected_locations = LOCATIONS
    else:
        selected_locations = st.sidebar.multiselect(
            "Select Countries", 
            LOCATIONS,
            default=["Kenya", "Tanzania", "Uganda", "Rwanda"]
        )
    
    # Job Titles filter with Select All
    select_all_titles = st.sidebar.checkbox("Select All Job Titles", value=False)
    if select_all_titles:
        selected_titles = JOB_TITLES
    else:
        selected_titles = st.sidebar.multiselect(
            "Select Job Titles",
            JOB_TITLES,
            default=["data analyst", "data engineer", "BI developer"]
        )
    
    days_lookback = st.sidebar.slider("Date Filter (Last X Days)", 1, 60, 30)
    
    if st.button("🔄 Refresh Data"):
        st.rerun()

    # Fetch Data from Supabase
    try:
        db = SupabaseHandler()
        # Fetching raw for now, ideally we filter in DB request
        raw_jobs = db.fetch_jobs(limit=2000)
        
        if not raw_jobs:
            st.info("No jobs found in the database. Run the scraper to populate data.")
            return

        df = pd.DataFrame(raw_jobs)
        
        # Client-side filtering (for simplicity vs building complex SQL queries)
        # 1. Title Filter
        if selected_titles:
            # Flexible match
            mask = df['title'].str.contains('|'.join(selected_titles), case=False, na=False)
            df = df[mask]
            
        # 2. Location Filter
        if selected_locations:
            mask = df['location'].str.contains('|'.join(selected_locations), case=False, na=False)
            df = df[mask]
            
        # 3. Date Filter
        cutoff = datetime.now() - timedelta(days=days_lookback)
        df['parsed_date'] = pd.to_datetime(df['posted_date'], errors='coerce') # Supabase returns ISO usually?
        # If stored as string/text in varied formats, we might need our parser.
        # Assuming we store decent ISO or strings.
        # If 'posted_date' is the raw string "2 days ago", we re-parse.
        # Let's rely on our parser
        
        df['parsed_date_obj'] = df['posted_date'].apply(parse_relative_date)
        df = df[df['parsed_date_obj'] >= cutoff]
        
        # Display Metrics
        st.metric("Jobs Found", len(df))
        
        # Show Data
        display_cols = ['title', 'company', 'location', 'posted_date', 'link', 'source']
        # filter valid cols
        valid_cols = [c for c in display_cols if c in df.columns]
        
        st.dataframe(
            df[valid_cols],
            column_config={
                "link": st.column_config.LinkColumn("Apply Link")
            },
            use_container_width=True
        )
        
    except Exception as e:
        st.error(f"Error loading dashboard: {e}")

def main():
    # Check if user is authenticated AND has a valid profile
    if st.session_state.user:
        # Double-check profile exists
        if not st.session_state.get("profile"):
            st.error("Access denied. No profile found.")
            st.session_state.user = None
            st.rerun()
        else:
            dashboard()
    else:
        landing_page()

if __name__ == "__main__":
    main()
