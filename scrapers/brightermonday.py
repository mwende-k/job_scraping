import requests
from bs4 import BeautifulSoup
from .base import BaseScraper
from utils import random_sleep, get_random_headers
import logging

class BrighterMondayScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.domains = {
            "Kenya": "https://www.brightermonday.co.ke",
            "Tanzania": "https://www.brightermonday.co.tz",
            "Uganda": "https://www.brightermonday.co.ug"
        }

    def scrape(self, search_term):
        """
        Scrapes BrighterMonday for a specific term and location.
        """
        title = search_term.get("title")
        location = search_term.get("location")
        
        base_url = self.domains.get(location)
        if not base_url:
            self.logger.debug(f"BrighterMonday does not support location: {location}")
            return []

        search_url = f"{base_url}/jobs?q={title}"
        self.logger.info(f"Scraping {search_url}")
        
        headers = get_random_headers()
        try:
            response = requests.get(search_url, headers=headers, timeout=10)
            if response.status_code != 200:
                self.logger.error(f"Failed to fetch {search_url}: Status {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            jobs = []
            
            # This selector is based on common structure, might need adjustment
            # BrighterMonday usually uses flex containers for job cards
            # Look for div with class matching job card patterns
            job_cards = soup.find_all('div', class_='flex-1') 
            
            if not job_cards:
                 # Fallback/Alternative selector if site structure changed
                job_cards = soup.select('div[data-cy="listing-cards-components"] > div')

            for card in job_cards:
                try:
                    # Extract Data
                    title_elem = card.find('p', class_='text-lg') or card.find('a', class_='text-base')
                    if not title_elem:
                        continue
                        
                    job_title = title_elem.get_text(strip=True)
                    job_link = title_elem.find_parent('a')['href'] if title_elem.find_parent('a') else title_elem.get('href')
                    
                    if job_link and not job_link.startswith('http'):
                        job_link = base_url + job_link

                    company_elem = card.find('p', class_='text-sm')
                    company = company_elem.get_text(strip=True) if company_elem else "Confidential"
                    
                    # Date/Location might be in other tags
                    # Creating a simple extraction for now
                    jobs.append(self._format_job(
                        title=job_title,
                        company=company,
                        location=location,
                        date="Recent", # BrighterMonday dates are varying relative strings
                        link=job_link,
                        source="BrighterMonday"
                    ))
                except Exception as e:
                    continue
            
            random_sleep()
            return jobs

        except Exception as e:
            self.logger.error(f"Error scraping {base_url}: {e}")
            return []
