import pandas as pd
import logging
import argparse
from datetime import datetime
from config import LOCATIONS, JOB_TITLES, OUTPUT_FILE, CSV_COLUMNS
from utils import setup_logger
from scrapers.brightermonday import BrighterMondayScraper
from scrapers.myjobmag import MyJobMagScraper
from scrapers.linkedin import LinkedinScraper

from utils import setup_logger, parse_relative_date, is_within_days

def run_scraper(limit=None, days=None):
    logger = setup_logger()
    logger.info("Starting Eastern Africa Data Job Scraper...")
    
    if days:
        logger.info(f"Filtering jobs from the last {days} days.")
    
    # Check for .env
    from dotenv import load_dotenv
    import os
    if not os.path.exists(".env"):
        logger.warning("No .env file found. Credentials might be missing.")
    else:
        load_dotenv()

    # Initialize Scrapers
    scrapers = [
        BrighterMondayScraper(),
        MyJobMagScraper(),
        LinkedinScraper()
    ]

    all_jobs = []
    
    total_searches = len(LOCATIONS) * len(JOB_TITLES) * len(scrapers)
    if limit:
        logger.info(f"Limit set to {limit} searches per scraper.")
    else:
        logger.info(f"Planned searches: {total_searches}")
    
    for scraper in scrapers:
        scraper_name = scraper.__class__.__name__
        logger.info(f"--- Starting {scraper_name} ---")
        
        search_count = 0
        
        for location in LOCATIONS:
            if limit and search_count >= limit:
                break
                
            for title in JOB_TITLES:
                if limit and search_count >= limit:
                    break
                    
                search_term = {
                    "title": title, 
                    "location": location,
                    "days": days # Pass to scraper if it supports pre-filtering
                }
                
                try:
                    jobs = scraper.scrape(search_term)
                    
                    if jobs:
                        logger.info(f"Found {len(jobs)} jobs for '{title}' in '{location}' on {scraper_name}")
                        all_jobs.extend(jobs)
                    else:
                        logger.info(f"No jobs found for '{title}' in '{location}' on {scraper_name}")
                        
                except Exception as e:
                    logger.error(f"Failed search for '{title}' in '{location}' on {scraper_name}: {e}")
                finally:
                    search_count += 1
                    
    # Process Results
    if not all_jobs:
        logger.warning("No jobs found in this run.")
        return

    df = pd.DataFrame(all_jobs)
    
    # Deduplicate
    initial_count = len(df)
    df.drop_duplicates(subset=['link'], keep='first', inplace=True)
    dedupa_count = len(df)
    logger.info(f"Deduplication: {initial_count} -> {dedupa_count} jobs")
    
    # Date Filtering (Post-processing)
    if days:
        logger.info("Applying date filter...")
        
        def check_date(row):
            date_obj = parse_relative_date(row['posted_date'])
            # If date extraction failed (None) or is "Recent", we typically keep it
            # But if strict filtering is needed, user might want to drop "N/A" dates.
            # For now, let's keep "Recent" (returns Now) and drop actual old dates
            if not date_obj:
                # If date is N/A, we can't be sure.
                # Policy: If we can't parse, maybe keep? Or drop? 
                # Let's keep to be safe, but log.
                return True
            return is_within_days(date_obj, days)
            
        df = df[df.apply(check_date, axis=1)]
        filtered_count = len(df)
        logger.info(f"Date Filter: {dedupa_count} -> {filtered_count} jobs (Last {days} days)")
        dedupa_count = filtered_count
    
    # Ensure all columns exist
    for col in CSV_COLUMNS:
        if col not in df.columns:
            df[col] = "N/A"
            
    df = df[CSV_COLUMNS]
    
    try:
        # Write summary to file first
        with open(OUTPUT_FILE, 'w') as f:
            f.write(f"# Total Jobs Found: {dedupa_count}, Scrape Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Append DataFrame
        df.to_csv(OUTPUT_FILE, mode='a', index=False)
        logger.info(f"Data saved to {OUTPUT_FILE}")
        
        # Preview
        print("\n--- Preview ---")
        print(df.head(10))
        print(f"\nTotal: {dedupa_count} jobs saved.")
        
    except Exception as e:
        logger.error(f"Error saving to CSV: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="scrape jobs")
    parser.add_argument("--location", help="Filter by specific location (e.g. Kenya)")
    parser.add_argument("--title", help="Filter by specific job title (e.g. 'data analyst')")
    parser.add_argument("--limit", type=int, help="Limit number of searches per scraper for testing")
    parser.add_argument("--days", type=int, help="Filter jobs posted in the last N days")
    args = parser.parse_args()
    
    # Apply filters
    if args.location:
        filtered_locs = [l for l in LOCATIONS if args.location.lower() in l.lower()]
        if filtered_locs:
            LOCATIONS[:] = filtered_locs
        else:
            print(f"Warning: Location '{args.location}' not found in supported countries.")
            
    if args.title:
        filtered_titles = [t for t in JOB_TITLES if args.title.lower() in t.lower()]
        if filtered_titles:
            JOB_TITLES[:] = filtered_titles
            
    run_scraper(limit=args.limit, days=args.days)
