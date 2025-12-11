from abc import ABC, abstractmethod
import logging
from typing import List, Dict

class BaseScraper(ABC):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.results: List[Dict] = []

    @abstractmethod
    def scrape(self, search_term: Dict) -> List[Dict]:
        """
        Main scraping method to be implemented by child classes.
        
        Args:
            search_term (Dict): {'title': '...', 'location': '...'}
            
        Returns:
            List[Dict]: List of job dictionaries matches standard schema
        """
        pass

    def _format_job(self, title, company, location, date, link, source):
        """Standardizes job data structure"""
        return {
            "title": title.strip() if title else "N/A",
            "company": company.strip() if company else "N/A",
            "location": location.strip() if location else "N/A",
            "posted_date": date.strip() if date else "N/A",
            "link": link.strip() if link else "N/A",
            "source": source
        }
