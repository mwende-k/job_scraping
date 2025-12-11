import requests
from bs4 import BeautifulSoup
from .base import BaseScraper
from utils import random_sleep, get_random_headers
import logging

class MyJobMagScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.domains = {
            "Kenya": "https://www.myjobmag.co.ke",
            # "Uganda": "https://ug.myjobmag.com", # Domain does not exist
            # Add others if discovered
        }

    def scrape(self, search_term):
        title = search_term.get("title")
        location = search_term.get("location")
        
        base_url = self.domains.get(location)
        if not base_url:
            # MyJobMag might not have specific sites for all 12 countries
            return []

        search_url = f"{base_url}/search/jobs?q={title}"
        self.logger.info(f"Scraping {search_url}")
        
        headers = get_random_headers()
        try:
            response = requests.get(search_url, headers=headers, timeout=10)
            if response.status_code != 200:
                self.logger.error(f"Failed to fetch {search_url}: Status {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            jobs = []
            
            # Select job list items
            job_list = soup.find('ul', class_='job-list')
            if not job_list:
                return []
                
            items = job_list.find_all('li', class_='job-list-li')
            
            for item in items:
                try:
                    h2 = item.find('h2')
                    if not h2: continue
                    
                    a_tag = h2.find('a')
                    if not a_tag: continue
                    
                    job_title = a_tag.get_text(strip=True)
                    job_link =  base_url + a_tag['href'] if not a_tag['href'].startswith('http') else a_tag['href']
                    
                    # Company is often in a separate item or span
                    # Inspecting typical MyJobMag structure
                    # Usually: <li class="job-logo">...</li> <li class="job-info">...</li>
                    # But simpler view: look for 'job-item-image' which has alt text sometimes?
                    # Or look for listing-company
                    
                    # Fallback simple search in the item text
                    # Often structure: <h2>Title</h2> <div class="job-desc">...</div>
                    # Company name is not continually structured well in list view
                    # We might need to visit the link or guess.
                    # Actually, usually there is a param or checking 'li.job-logo img' alt
                    
                    company = "N/A"
                    img = item.find('img')
                    if img and img.get('alt'):
                        company = img.get('alt')
                    elif item.find('a', href=lambda x: x and '/company/' in x):
                         company = item.find('a', href=lambda x: x and '/company/' in x).get_text(strip=True)

                    date_elem = item.find('li', id='job-date')
                    date = date_elem.get_text(strip=True) if date_elem else "Recent"

                    jobs.append(self._format_job(
                        title=job_title,
                        company=company,
                        location=location,
                        date=date,
                        link=job_link,
                        source="MyJobMag"
                    ))
                except Exception as e:
                    continue
            
            random_sleep()
            return jobs

        except Exception as e:
            self.logger.error(f"Error scraping {base_url}: {e}")
            return []
