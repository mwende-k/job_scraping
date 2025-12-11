# Configuration settings for Job Scraper

# Target Job Titles
JOB_TITLES = [
    "data analyst",
    "data engineer", 
    "data developer",
    "data manager",
    "head of data",
    "business intelligence consultant",
    "business intelligence developer",
    "business intelligence analyst",
    "business intelligence manager",
    "business intelligence head",
    "BI consultant",
    "BI developer",
    "BI analyst",
    "BI manager",
    "head of BI"
]

# Target Countries / Locations
LOCATIONS = [
    "Kenya",
    "Tanzania",
    "Uganda",
    "Rwanda",
    "Ethiopia",
    "Mauritius",
    "Seychelles",
    "Burundi",
    "South Sudan",
    "Djibouti",
    "Eritrea",
    "Somalia"
]

# Search queries generator (Title + Location)
# Note: Not all sites support complex queries, so this is a baseline
def get_search_queries():
    for title in JOB_TITLES:
        for location in LOCATIONS:
            yield {"title": title, "location": location}

# Output settings
OUTPUT_FILE = "eastern_africa_data_jobs.csv"
CSV_COLUMNS = ["title", "company", "location", "posted_date", "link", "source"]

# Scraper Settings
REQUEST_TIMEOUT = 10
RANDOM_DELAY_RANGE = (2, 5)  # Seconds
