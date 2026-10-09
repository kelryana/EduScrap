##backend/pdf_utils.py 

import logging
import os
import re
import hashlib
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

try:
    from pdfminer.high_level import extract_text
    PDFMINER_AVAILABLE = True
except ImportError:
    PDFMINER_AVAILABLE = False
    logger.warning("pdfminer.six não disponível. Instale com: pip install pdfminer.six")


_CACHE_PDF = {}
_MAX_CACHE = 50  

def _cache_pdf(url: str, conteudo: BytesIO) -> None:
    """Armazena conteúdo PDF no cache"""
    if len(_CACHE_PDF) >= _MAX_CACHE:
        # Remove o mais antigo FIFO
        _CACHE_PDF.pop(next(iter(_CACHE_PDF)))
    _CACHE_PDF[url] = conteudo


def _obter_cache_pdf(url: str) -> Optional[BytesIO]:
    """Recupera conteúdo PDF do cache"""
    if url in _CACHE_PDF:
        # Retorna cópia seek(0)
        _CACHE_PDF[url].seek(0)
        return _CACHE_PDF[url]
    return None


def baixar_pdf(url: str, timeout: int = 15, usar_cache: bool = True) -> Optional[BytesIO]:
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

   
    if usar_cache:
        cacheado = _obter_cache_pdf(url)
        if cacheado:
            logger.debug(f"PDF do cache: {url[:80]}...")
            return cacheado

    try:
        logger.info(f"Baixando PDF: {url[:80]}...")
        resposta = requests.get(url, headers=headers, timeout=timeout, stream=True)

        if resposta.status_code == 200:
           
            content_type = resposta.headers.get('Content-Type', '').lower()
            primeiros_bytes = resposta.content[:10]
            if 'application/pdf' in content_type or url.lower().endswith('.pdf') or b'%PDF' in primeiros_bytes:
                conteudo = BytesIO(resposta.content)

                if usar_cache:
                    _cache_pdf(url, BytesIO(resposta.content))

                logger.info(f"PDF baixado com sucesso ({len(resposta.content)} bytes)")
                return conteudo
            else:
                logger.warning(f"URL não retorna PDF (Content-Type: {content_type})")
                return None
        else:
            logger.error(f"Erro ao baixar PDF: Status {resposta.status_code}")
            return None

    except requests.exceptions.Timeout:
        logger.warning(f"Timeout ao baixar PDF ({timeout}s)")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de rede ao baixar PDF: {e}")
        return None
    except Exception as e:
        logger.error(f"Erro inesperado ao baixar PDF: {e}", exc_info=True)
        return None


def extrair_texto_pdf(arquivo_pdf_bytes: BytesIO, max_paginas: int = 10) -> str:
    """Extrai texto de um PDF usando pdfminer com fallback para pypdf/PyPDF2."""
    if not arquivo_pdf_bytes:
        return ""

    arquivo_pdf_bytes.seek(0)
    texto = ""

    # Método 1: pdfminer.high_level.extract_text
    if PDFMINER_AVAILABLE:
        try:
            page_numbers = list(range(max_paginas)) if max_paginas > 0 else None
            texto = extract_text(arquivo_pdf_bytes, page_numbers=page_numbers)
            if texto and len(texto.strip()) > 10:
                logger.info(f"Texto extraído via pdfminer: {len(texto)} caracteres")
                return texto
        except Exception as e:
            logger.warning(f"pdfminer falhou ({e}); tentando leitor alternativo...")

    # Método 2: pypdf / PyPDF2
    try:
        arquivo_pdf_bytes.seek(0)
        try:
            from pypdf import PdfReader
        except ImportError:
            from PyPDF2 import PdfReader
        reader = PdfReader(arquivo_pdf_bytes)
        paginas_total = len(reader.pages)
        limite = min(paginas_total, max_paginas) if max_paginas > 0 else paginas_total
        partes = []
        for i in range(limite):
            txt = reader.pages[i].extract_text() or ""
            partes.append(txt)
        texto = "\n".join(partes)
        if texto and len(texto.strip()) > 10:
            logger.info(f"Texto extraído via PdfReader: {len(texto)} caracteres")
            return texto
    except Exception as e:
        logger.error(f"Erro ao extrair texto do PDF via PdfReader: {e}")

    return texto

def extrair_data_de_texto(texto: str) -> Optional[str]:

    if not texto or len(texto) < 5:
        return None

    
    texto = str(texto)

    # Lista de padrões em ordem de prioridade
    padroes = [
        # Padrão 1: "até DD/MM/AAAA" - muito comum para prazos
        (r"(?:até|data\s*limite|prazo\s*(?:final|máximo)?|vencimento|inscrições?\s*(?:até|para))\.?\s*:?[\s]*(\d{1,2})/(\d{1,2})/(\d{4})", "normal"),

        # Padrão 2: "DD/MM/AAAA a DD/MM/AAAA" - período, pega a segunda data
        (r"(\d{1,2})/(\d{1,2})/(\d{4})\s*(?:a|até|-)\s*(\d{1,2})/(\d{1,2})/(\d{4})", "periodo"),

        # Padrão 3: "período DD/MM/AAAA a DD/MM/AAAA"
        (r"(?:período|periodo).*?(\d{1,2})/(\d{1,2})/(\d{4}).*?(\d{1,2})/(\d{1,2})/(\d{4})", "periodo"),

        # Padrão 4: "DD/MM/AA" (ano com 2 dígitos)
        (r"(?:até|prazo|vencimento)[\s:]*(\d{1,2})/(\d{1,2})/(\d{2})", "normal_curto"),

        # Padrão 5: "DD de Mês de AAAA" (formato textual)
        (r"(\d{1,2})\s+de\s+(janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\s+de\s+(\d{4})", "textual"),

        # Padrão 6: Data simples isolada (menos prioritário)
        (r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", "normal"),
    ]

    for padrao, tipo in padroes:
        resultado = re.search(padrao, texto, re.IGNORECASE | re.DOTALL)
        if resultado:
            grupos = resultado.groups()

            if tipo == "periodo":
                
                try:
                    dia, mes, ano = int(grupos[3]), int(grupos[4]), int(grupos[5])
                except:
                    continue
            elif tipo == "textual":
                
                meses = {
                    'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4,
                    'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
                    'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
                }
                try:
                    dia, mes_nome, ano = int(grupos[0]), grupos[1].lower(), int(grupos[2])
                    mes = meses.get(mes_nome, 0)
                    if mes == 0:
                        continue
                except:
                    continue
            elif tipo == "normal_curto":
                
                try:
                    dia, mes, ano = int(grupos[0]), int(grupos[1]), int(grupos[2])
                    
                    ano_completo = 2000 + ano if ano < 50 else 1900 + ano
                except:
                    continue
            else:
                
                try:
                    dia, mes, ano = int(grupos[0]), int(grupos[1]), int(grupos[2])
                except:
                    continue

            try:
                # Validar data
                data_encontrada = datetime(ano, mes, dia)

                # Validação: ano entre 2020 e 2035
                if not (2020 <= ano <= 2035):
                    continue

                data_encontrada.strftime('%Y-%m-%d')

                data_str = data_encontrada.strftime('%Y-%m-%d')
                logger.info(f"Data encontrada: {data_str}")
                return data_str

            except (ValueError, TypeError):
                continue

    # Se nenhum padrão funcionou, tenta encontrar datas genéricas
    # mas apenas para conteúdo que não seja de notícias tecnológicas
    if 'notícia tech' not in texto.lower() and 'g1' not in texto.lower() and 'canaltech' not in texto.lower():
        # Procurar por qualquer data no texto para outros tipos de conteúdo
        generic_date_pattern = r'\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})\b'
        generic_match = re.search(generic_date_pattern, texto, re.IGNORECASE)
        if generic_match:
            try:
                dia, mes, ano = int(generic_match.group(1)), int(generic_match.group(2)), int(generic_match.group(3))
                if 2020 <= ano <= 2035:
                    data_encontrada = datetime(ano, mes, dia)
                    data_str = data_encontrada.strftime('%Y-%m-%d')
                    logger.info(f"Data genérica encontrada: {data_str}")
                    return data_str
            except (ValueError, IndexError):
                pass
    
    return None
def extrair_data_vencimento_pdf(url_pdf: str, timeout: int = 15) -> Optional[str]:

    logger.info("Extraindo data do PDF...")

   
    pdf_bytes = baixar_pdf(url_pdf, timeout)
    if not pdf_bytes:
        return None

    
    texto = extrair_texto_pdf(pdf_bytes, max_paginas=5)
    if not texto:
        return None

    # Extrai a data do texto
    data = extrair_data_de_texto(texto)

    if data:
        return data
    else:
        logger.warning("Nenhuma data encontrada no PDF")
        return None


def extrair_data_vencimento_hibrido(texto_html: str, url_pdf: str) -> Optional[str]:

    # Passo 1: Tentar no HTML
    if texto_html:
        data_html = extrair_data_de_texto(texto_html)
        if data_html:
            logger.info(f"Data encontrada no HTML: {data_html}")
            return data_html

    # Passo 2: Tentar no PDF
    if url_pdf:
        logger.info("Data não encontrada no HTML, usando PDF...")
        data_pdf = extrair_data_vencimento_pdf(url_pdf)
        if data_pdf:
            logger.info(f"Data encontrada no PDF: {data_pdf}")
            return data_pdf

    logger.warning("Nenhuma data encontrada (HTML + PDF)")
    return None


def extrair_data_vencimento_datetime(texto_html: str, url_pdf: str) -> Optional[datetime]:
    """
    Versão para os scrapers: busca o prazo no texto (HTML) e, se não achar, no PDF do edital.
    Retorna datetime (formato salvo no MongoDB) ou None. Nunca lança exceção.
    """
    try:
        data_str = extrair_data_vencimento_hibrido(texto_html, url_pdf)
        return datetime.strptime(data_str, "%Y-%m-%d") if data_str else None
    except Exception as e:
        logger.warning(f"Falha ao extrair prazo de {url_pdf}: {e}")
        return None


def verificar_status(data_vencimento: Optional[str]) -> str:

    if not data_vencimento:
        return "vigente"  # Fallback

    try:
        hoje = datetime.now().date()
        data_limite = datetime.strptime(data_vencimento, '%Y-%m-%d').date()

        if data_limite >= hoje:
            return "vigente"
        else:
            return "vencido"
    except (ValueError, TypeError):
        return "vigente"

def extrair_e_validar_data(texto_html: str, url_pdf: str) -> Tuple[Optional[str], str]:

    data = extrair_data_vencimento_hibrido(texto_html, url_pdf)
    status = verificar_status(data)
    return data, status

def limpar_cache_pdf():
    """Limpa o cache de PDFs"""
    global _CACHE_PDF
    _CACHE_PDF = {}
    logger.info("Cache de PDFs limpo")


if __name__ == "__main__":
    # Teste rápido
    print("="*60)
    print("🧪 TESTANDO PDF UTILS")
    print("="*60)

    # Teste com texto HTML
    texto_teste = """
    EDITAL Nº 001/2026
    Período de inscrições: 10/01/2026 a 15/02/2026
    Prazo final: 20/02/2026
    """

    print("\n🔍 Teste com texto HTML:")
    data = extrair_data_de_texto(texto_teste)
    print(f"   Data extraída: {data}")

    # Teste de status
    print("\n🔍 Teste de verificação de status:")
    data_teste = "2024-12-31"
    status = verificar_status(data_teste)
    print(f"   Data {data_teste} -> {status}")

    data_teste = "2027-01-01"
    status = verificar_status(data_teste)
    print(f"   Data {data_teste} -> {status}")

    print("\n" + "="*60)
    print("✅ Testes concluídos")