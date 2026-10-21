#--- src/collectors/pdf_scraper.py 

import pdfplumber
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFScraper:
    def __init__(self):
        self.extracted_text = []

    @staticmethod
    def is_obj_in_bbox(obj: Any, bbox: Tuple[float, float, float, float], page_height: Optional[float] = None) -> bool:
        """
        Verifica se um elemento ou suas coordenadas intersectam o bounding box de uma tabela.
        Abordagem inspirada no artigo de Khadija Mahanga para isolamento de texto e tabelas.
        """
        try:
            if isinstance(obj, dict):
                ox0 = float(obj.get("x0", 0))
                otop = float(obj.get("top", obj.get("y0", 0)))
                ox1 = float(obj.get("x1", 0))
                obottom = float(obj.get("bottom", obj.get("y1", 0)))
            elif hasattr(obj, "bbox"):
                bx0, by0, bx1, by1 = obj.bbox
                if page_height is not None:
                    otop = page_height - by1
                    obottom = page_height - by0
                else:
                    otop, obottom = by0, by1
                ox0, ox1 = bx0, bx1
            elif isinstance(obj, (tuple, list)) and len(obj) == 4:
                ox0, otop, ox1, obottom = [float(v) for v in obj]
            else:
                return False

            tx0, ttop, tx1, tbottom = bbox
            # Verifica se o centro ou área do objeto está contido na tabela
            return (ox0 >= tx0 - 2) and (ox1 <= tx1 + 2) and (otop >= ttop - 2) and (obottom <= tbottom + 2)
        except Exception:
            return False

    @staticmethod
    def format_table_to_text(table_matrix: List[List[Optional[str]]]) -> str:
        """
        Formata uma matriz de tabela em linhas delimitadas por ' | ',
        preservando a legibilidade semântica de datas e cronogramas para o Regex.
        """
        if not table_matrix:
            return ""
        linhas = []
        for row in table_matrix:
            if not row:
                continue
            celulas = [str(c).strip().replace("\n", " ") for c in row if c is not None and str(c).strip()]
            if celulas:
                linhas.append(" | ".join(celulas))
        return "\n".join(linhas)

    def extract_page_hybrid(self, page) -> str:
        """
        Extrai o conteúdo de uma página isolando tabelas de cronograma do texto corrente,
        preservando a hierarquia de leitura e evitando colisão de colunas.
        """
        try:
            tables = page.find_tables()
            if not tables:
                return page.extract_text() or ""

            # Extrai e formata as tabelas encontradas
            tabelas_formatadas = []
            table_bboxes = []
            for t in tables:
                t_data = t.extract()
                t_txt = self.format_table_to_text(t_data)
                if t_txt:
                    tabelas_formatadas.append(t_txt)
                table_bboxes.append(t.bbox)

            # Filtra elementos que estão fora dos bounding boxes das tabelas
            try:
                page_sem_tabelas = page.filter(
                    lambda obj: not any(self.is_obj_in_bbox(obj, bbox) for bbox in table_bboxes)
                )
                texto_livre = page_sem_tabelas.extract_text() or ""
            except Exception:
                # Fallback seguro caso filter() não suporte os objetos da página
                texto_livre = page.extract_text() or ""

            partes = []
            if texto_livre.strip():
                partes.append(texto_livre.strip())
            if tabelas_formatadas:
                partes.append("\n[TABELA DE CRONOGRAMA / DADOS]\n" + "\n\n".join(tabelas_formatadas))

            return "\n\n".join(partes)
        except Exception as e:
            logger.warning(f"Erro na extração híbrida da página, usando padrão: {e}")
            return page.extract_text() or ""

    def extract_text_from_file(self, file_path: str, use_hybrid: bool = True) -> Optional[str]:
        try:
            full_text = []
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    if use_hybrid:
                        text = self.extract_page_hybrid(page)
                    else:
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

    def extract_text_from_url(self, url: str, save_path: Optional[str] = None, use_hybrid: bool = True) -> Optional[str]:
        import requests

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            if save_path:
                Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return self.extract_text_from_file(save_path, use_hybrid=use_hybrid)
            else:
                from io import BytesIO
                pdf_file = BytesIO(response.content)
                full_text = []
                with pdfplumber.open(pdf_file) as pdf:
                    for page in pdf.pages:
                        if use_hybrid:
                            text = self.extract_page_hybrid(page)
                        else:
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
