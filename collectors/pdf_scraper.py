#--- src/collectors/pdf_scraper.py 

import pdfplumber
from typing import List, Dict, Optional
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFScraper:
    def __init__(self):
        self.extracted_text = []

    def extract_text_from_file(self, file_path: str) -> Optional[str]:
    
        try:
            full_text = []
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        full_text.append(text)
                    logger.info(f"Página {page_num} processada: {file_path}")

            result = "\n".join(full_text)
            logger.info(f"Texto extraído com sucesso: {len(result)} caracteres")
            return result
        except Exception as e:
            logger.error(f"Erro ao extrair PDF {file_path}: {str(e)}")
            return None

    def extract_text_from_url(self, url: str, save_path: Optional[str] = None) -> Optional[str]:
     
        import requests

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Salva temporariamente se necessário
            if save_path:
                Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return self.extract_text_from_file(save_path)
            else:
                # Extrai diretamente da memória
                from io import BytesIO
                pdf_file = BytesIO(response.content)
                full_text = []
                with pdfplumber.open(pdf_file) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            full_text.append(text)

                result = "\n".join(full_text)
                logger.info(f"Texto extraído da URL: {len(result)} caracteres")
                return result

        except Exception as e:
            logger.error(f"Erro ao baixar/extrair PDF de {url}: {str(e)}")
            return None

    def extract_tables(self, file_path: str) -> List[List[List[str]]]:
     
        try:
            tables = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)

            logger.info(f"{len(tables)} tabelas extraídas de {file_path}")
            return tables
        except Exception as e:
            logger.error(f"Erro ao extrair tabelas: {str(e)}")
            return []

    def extract_metadata(self, file_path: str) -> Dict:
       
        try:
            with pdfplumber.open(file_path) as pdf:
                metadata = pdf.metadata or {}
                return {
                    'author': metadata.get('Author', ''),
                    'title': metadata.get('Title', ''),
                    'creation_date': metadata.get('CreationDate', ''),
                    'pages_count': len(pdf.pages)
                }
        except Exception as e:
            logger.error(f"Erro ao extrair metadados: {str(e)}")
            return {}
