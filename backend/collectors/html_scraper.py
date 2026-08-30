#--- src/collectors/html_scraper.py

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HTMLScraper:
    def __init__(self, base_url: str, headers: Optional[Dict] = None):
        self.base_url = base_url
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (EduScrap Bot)'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def fetch_page(self, url: str) -> Optional[str]:
      
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            logger.info(f"Sucesso ao coletar: {url}")
            return response.text
        except requests.RequestException as e:
            logger.error(f"Erro ao coletar {url}: {str(e)}")
            return None

    def parse_html(self, html_content: str, selectors: Dict) -> List[Dict]:
     
        soup = BeautifulSoup(html_content, 'html.parser')
        results = []

        # Implementação genérica - será especializada por fonte
        items = soup.select(selectors.get('container', 'body'))

        for item in items:
            data = {}
            for field, selector in selectors.items():
                if field != 'container':
                    element = item.select_one(selector)
                    data[field] = element.get_text(strip=True) if element else ''
            results.append(data)

        return results

    def scrape(self, url: str, selectors: Dict) -> List[Dict]:
        
        html = self.fetch_page(url)
        if html:
            return self.parse_html(html, selectors)
        return []

    def close(self):
        """Fecha a sessão HTTP"""
        self.session.close()
