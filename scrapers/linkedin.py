import logging
import os
import time
import random
from .base import BaseScraper
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.chrome.service import Service
from dotenv import load_dotenv

load_dotenv()

class LinkedinScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.cookie = os.getenv("LINKEDIN_LI_AT")
        self.base_url = "https://www.linkedin.com"

    def _setup_driver(self):
        options = Options()
        # options.add_argument("--headless")  # Comment out for debugging if needed
        # Headless often detected by LinkedIn, so be careful. 
        # For public search headless is okay-ish, for auth it's better.
        # Let's try headless first but with user-agent spoofing
        options.add_argument("--headless=new") 
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Selenium 4.6+ has built-in Selenium Manager, so we don't need webdriver_manager
        driver = webdriver.Chrome(options=options)
        return driver

    def scrape(self, search_term):
        title = search_term.get("title")
        location = search_term.get("location")
        days = search_term.get("days")
        
        driver = self._setup_driver()
        jobs = []
        
        try:
            # Login if cookie present
            if self.cookie:
                self.logger.info("Using LinkedIn cookie for authentication...")
                driver.get(self.base_url)
                driver.add_cookie({
                    'name': 'li_at',
                    'value': self.cookie,
                    'domain': '.linkedin.com'
                })
                driver.refresh()
                time.sleep(3)
            
            # Construct Search URL
            # f_TPR=r2592000 roughly 30 days, r604800 is 1 week. 
            # If days is 10, closest valid param for public search is usually r2592000 (month) or we filter post-scrape.
            # But we can try passing seconds: 10 * 24 * 3600 = 864000
            
            time_param = ""
            if days:
                seconds = int(days) * 24 * 3600
                time_param = f"&f_TPR=r{seconds}"

            search_url = f"{self.base_url}/jobs/search/?keywords={title}&location={location}{time_param}"
            self.logger.info(f"Scraping {search_url}")
            
            driver.get(search_url)
            time.sleep(random.uniform(3, 6)) # Wait for load
            
            # Scroll to load more
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            # Parse Results
            if self.cookie:
                job_cards = driver.find_elements(By.CLASS_NAME, "jobs-search-results__list-item")
            else:
                # Public search selectors
                job_cards = driver.find_elements(By.CSS_SELECTOR, "div.base-search-card") or \
                            driver.find_elements(By.CSS_SELECTOR, "div.job-search-card") or \
                            driver.find_elements(By.CSS_SELECTOR, "li.jobs-search__results-list__item")

            self.logger.info(f"Found {len(job_cards)} potential job cards")
            
            for card in job_cards[:20]:
                try:
                    # Helper to get text safe
                    def get_text(elem, selector):
                        try:
                            return elem.find_element(By.CSS_SELECTOR, selector).get_attribute("innerText").strip()
                        except:
                            return None

                    # Extract title
                    job_title = get_text(card, ".base-search-card__title") or \
                                get_text(card, "h3.base-search-card__title") or \
                                get_text(card, "a.job-card-list__title") or \
                                get_text(card, "h3")

                    # Company
                    company = get_text(card, ".base-search-card__subtitle") or \
                              get_text(card, "h4.base-search-card__subtitle") or \
                              get_text(card, "h4") or \
                              get_text(card, "a.job-card-container__company-name")

                    # Location
                    job_loc = get_text(card, ".job-search-card__location") or \
                              get_text(card, ".job-card-container__metadata-item") or \
                              location
                    
                    # Link
                    try:
                        link_elem = card.find_element(By.TAG_NAME, "a")
                        link = link_elem.get_attribute("href")
                    except:
                        link = "N/A"
                        
                    # Date
                    try:
                        date_elem = card.find_element(By.CSS_SELECTOR, "time")
                        date = date_elem.get_attribute("datetime") or date_elem.get_attribute("innerText")
                    except:
                        date = "Recent"

                    jobs.append(self._format_job(
                        title=job_title,
                        company=company,
                        location=job_loc,
                        date=date,
                        link=link,
                        source="LinkedIn"
                    ))
                except Exception as e:
                    # self.logger.debug(f"Error parsing card: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"LinkedIn scrape error: {e}")
        finally:
            driver.quit()
            
        return jobs
