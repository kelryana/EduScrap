#tests/test_scraper.py 

import pytest
import sys
from pathlib import Path

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from collectors.html_scraper import HTMLScraper
from collectors.pdf_scraper import PDFScraper

class TestHTMLScraper:
    @pytest.fixture
    def scraper(self):
        return HTMLScraper(base_url="https://example.com")

    def test_scraper_initialization(self, scraper):
        assert scraper.base_url == "https://example.com"
        assert scraper.session is not None

    def test_parse_html_basic(self, scraper):
        html = """
        <html>
            <div class="edital">
                <h2 class="titulo">Edital 001/2026</h2>
                <p class="data">30/09/2026</p>
            </div>
        </html>
        """
        selectors = {
            'container': '.edital',
            'titulo': '.titulo',
            'data': '.data'
        }

        results = scraper.parse_html(html, selectors)
        assert len(results) == 1
        assert results[0]['titulo'] == "Edital 001/2026"
        assert results[0]['data'] == "30/09/2026"


class TestPDFScraper:
    @pytest.fixture
    def scraper(self):
        return PDFScraper()

    def test_scraper_initialization(self, scraper):
        assert scraper.extracted_text == []

    # Teste de integração com arquivo PDF real seria adicionado aqui
    # Por enquanto, testa apenas a inicialização e estrutura

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
