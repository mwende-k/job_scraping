import streamlit as st
import pandas as pd
import logging
from datetime import datetime, timedelta
from config import LOCATIONS, JOB_TITLES, OUTPUT_FILE, CSV_COLUMNS
from utils import setup_logger, parse_relative_date, normalize_url
from scrapers.brightermonday import BrighterMondayScraper
from scrapers.myjobmag import MyJobMagScraper
from scrapers.linkedin import LinkedinScraper

# Configure Streamlit
st.set_page_config(page_title="Eastern Africa Job Scraper", layout="wide")

def get_scrapers():
    """Returns initialized scrapers"""
    return [
        BrighterMondayScraper(),
        MyJobMagScraper(),
        LinkedinScraper()
    ]

def filter_jobs_by_date(jobs, days_lookback):
    """Filters jobs based on parsed date"""
    cutoff_date = datetime.now() - timedelta(days=days_lookback)
    filtered = []
    
    for job in jobs:
        # Parse date if not already datetime
        posted = job.get('posted_date', 'Recent')
        job_dt = parse_relative_date(posted)
        
        # If parsing fails or implies older than cutoff (rough heuristic)
        # Note: parse_relative_date defaults to NOW if it fails or is 'recent', 
        # so 'recent' jobs will always pass.
        
        if job_dt >= cutoff_date:
            job['parsed_date'] = job_dt # Store for sorting
            filtered.append(job)
            
    return filtered

def main():
    st.title("🐯 Eastern Africa Data Job Scraper")
    
    # Sidebar Controls
    st.sidebar.header("Configuration")
    
    selected_locations = st.sidebar.multiselect(
        "Select Countries", 
        LOCATIONS,
        default=["Kenya", "Tanzania", "Uganda", "Rwanda"]
    )
    
    selected_titles = st.sidebar.multiselect(
        "Select Job Titles",
        JOB_TITLES,
        default=["data analyst", "data engineer", "BI developer"]
    )
    
    days_lookback = st.sidebar.slider("Date Filter (Last X Days)", 1, 30, 10)
    
    run_btn = st.sidebar.button("🚀 Start Scraping", type="primary")

    # Metrics Placeholder
    col1, col2, col3 = st.columns(3)
    metric_total = col1.empty()
    metric_new = col2.empty()
    status_text = st.empty()
    
    if run_btn:
        if not selected_locations or not selected_titles:
            st.error("Please select at least one location and one job title.")
            return
            
        scrapers = get_scrapers()
        all_jobs = []
        progress_bar = st.progress(0)
        
        total_steps = len(scrapers) * len(selected_locations) * len(selected_titles)
        step_count = 0
        
        status_text.info(f"Starting scrape for {len(selected_titles)} titles in {len(selected_locations)} countries...")
        
        # Scrape Loop
        for scraper in scrapers:
            scraper_name = scraper.__class__.__name__
            
            for location in selected_locations:
                for title in selected_titles:
                    status_text.text(f"Scraping {scraper_name}: {title} in {location}...")
                    
                    search_term = {"title": title, "location": location}
                    try:
                        jobs = scraper.scrape(search_term)
                        if jobs:
                            all_jobs.extend(jobs)
                    except Exception as e:
                        st.warning(f"Error on {scraper_name}: {e}")
                        
                    step_count += 1
                    progress_bar.progress(min(step_count / total_steps, 0.99))
        
        progress_bar.progress(1.0)
        status_text.success("Scraping completed!")
        
        # Processing
        if all_jobs:
            df = pd.DataFrame(all_jobs)
            
            # 1. Normalize URLs
            df['link_clean'] = df['link'].apply(normalize_url)
            
            # 2. Key Deduplication (Title + Company + Normalized Link)
            # Create a composite key to be safe
            df['dedupe_id'] = df['title'] + df['company'] + df['link_clean']
            
            initial_count = len(df)
            df.drop_duplicates(subset=['dedupe_id'], keep='first', inplace=True)
            unique_count = len(df)
            
            # 3. Date Filtering
            # We convert DF back to list of dicts for our helper, or apply on DF
            # Applying on DF using lambda with our util
            df['parsed_date'] = df['posted_date'].apply(parse_relative_date)
            cutoff = datetime.now() - timedelta(days=days_lookback)
            
            # Filter
            df_filtered = df[df['parsed_date'] >= cutoff].copy()
            filtered_count = len(df_filtered)
            
            # Display Metrics
            metric_total.metric("Jobs Found (Raw)", initial_count)
            metric_new.metric("After Dedupe", unique_count)
            col3.metric(f"Last {days_lookback} Days", filtered_count)
            
            # Clean up columns for display
            display_cols = ['title', 'company', 'location', 'posted_date', 'link', 'source']
            final_df = df_filtered[display_cols]
            
            st.dataframe(final_df, use_container_width=True)
            
            # CSV Download
            csv = final_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download CSV",
                csv,
                f"eastern_africa_jobs_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv",
                key='download-csv'
            )
            
        else:
            st.warning("No jobs found matching your criteria.")

if __name__ == "__main__":
    main()
