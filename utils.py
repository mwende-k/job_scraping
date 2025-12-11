import logging
import time
import random
from fake_useragent import UserAgent
import dateparser
from datetime import datetime
from urllib.parse import urlparse, urlunparse

def setup_logger(name="JobScraper"):
    """Sets up a console logger"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

def random_sleep(min_seconds=2, max_seconds=5):
    """Sleeps for a random duration to behave more human-like"""
    duration = random.uniform(min_seconds, max_seconds)
    time.sleep(duration)

def get_random_headers():
    """Generates random headers with a rotating User-Agent"""
    try:
        ua = UserAgent()
        user_agent = ua.random
    except:
        user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
    return {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

def parse_relative_date(date_str):
    """
    Parses a relative date string (e.g., '2 days ago', 'Just now') into a datetime object.
    Returns datetime.now() if parsing fails to ensure we don't crash, 
    but effectively treats unknown dates as 'recent'.
    """
    if not date_str or date_str.lower() in ["recent", "n/a", "today", "just now"]:
        return datetime.now()
        
    try:
        dt = dateparser.parse(date_str)
        return dt if dt else datetime.now()
    except:
        return datetime.now()

def normalize_url(url):
    """
    Normalizes a URL by stripping query parameters to improve deduplication.
    """
    if not url or url == "N/A":
        return url
        
    try:
        parsed = urlparse(url)
        clean_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
        return clean_url
    except:
        return url
