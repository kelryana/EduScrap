##backend/scraper_ciee.py

import logging
import os
import re
import time
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
)
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

from dotenv import load_dotenv

# Garante saída UTF-8 no terminal do Windows sem erro de charmap (cp1252)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from driver_factory import obter_driver
try:
    from src.normalizer.classifier import classificar_oportunidade
except Exception:
    classificar_oportunidade = None

load_dotenv(PROJECT_ROOT / ".env")

MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("MONGODB_DB", "hub_estudantes")
COLLECTION_NAME = os.getenv("CIEE_COLLECTION", "vagas_ciee")
CIDADE = os.getenv("CIEE_CIDADE", "Mossoró")
URL_CIEE = os.getenv("CIEE_URL", "https://portal.ciee.org.br/")
GECKODRIVER_PATH = os.getenv("GECKODRIVER_PATH", "")  # vazio => download automático

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(BACKEND_DIR / "scraper_ciee.log", encoding="utf-8"),
        logging.FileHandler(LOGS_DIR / "ciee.log", mode="a", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def _sem_acentos(texto: str) -> str:
    if not texto:
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", str(texto))
        if unicodedata.category(c) != "Mn"
    )


class ScraperCIEEHibrido:
    def __init__(self, cidade=CIDADE):
        self.cidade = cidade
        self.driver = None
        self.vagas = []
        self.colecao = None
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        logger.info(f"Sessão iniciada: {self.session_id}")
        logger.info(f"Buscando por: {cidade}")

    def conectar_mongodb(self):
        try:
            client = MongoClient(MONGO_URI)
            db = client[DB_NAME]
            self.colecao = db[COLLECTION_NAME]

            self.colecao.create_index("codigo", unique=True, sparse=True)
            self.colecao.create_index("link")
            self.colecao.create_index("coletado_em")
            self.colecao.create_index("cidade")

            logger.info("Conectado ao MongoDB com índices")
            return True

        except Exception as e:
            logger.error(f"Erro na conexão MongoDB: {e}")
            return False

    def configurar_driver(self):
        try:
            preferencia = os.getenv("SELENIUM_BROWSER", "auto")
            logger.info(f"Configurando driver Selenium (preferência: {preferencia})...")
            self.driver = obter_driver(
                preferencia=preferencia,
                headless=True,
                timeout_pagina=30,
                timeout_implicito=2,
                fallback=True,
            )
            logger.info(f"Navegador {self.driver.name} headless configurado com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao configurar driver: {e}")
            return False

    def _obter_resumo_dom_vagas(self):
        """Retorna lista rápida de códigos e locais dos cards atualmente renderizados no DOM."""
        try:
            res = self.driver.execute_script(
                """
                return Array.from(document.querySelectorAll('a.vaga-row')).map(el => ({
                    codigo: (el.querySelector('.cod-vaga')?.textContent || '').trim(),
                    local: (el.querySelector('.info-local')?.textContent || '').trim()
                }));
                """
            )
            return res if isinstance(res, list) else []
        except Exception:
            return []

    def buscar_cidade(self):
        try:
            logger.info(f"Buscando por '{self.cidade}'...")

            resumo_antes = self._obter_resumo_dom_vagas()
            primeiro_codigo_antes = resumo_antes[0]["codigo"] if resumo_antes else None

            campo = None
            seletores = [
                "//input[@id='CidadeVaga']",
                "//input[contains(@placeholder, 'cidade')]",
                "//input[contains(@placeholder, 'Cidade')]",
                "//input[@type='text']",
            ]

            for xpath in seletores:
                try:
                    campo = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
                    if campo and campo.is_enabled() and campo.is_displayed():
                        logger.info(f"Campo encontrado: {xpath}")
                        break
                except Exception:
                    continue

            if not campo:
                logger.error("Campo de busca não encontrado")
                return False

            # PASSO 1: Centralizar campo na tela (evita interceptação pelo menu fixo superior) e clicar
            try:
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", campo)
                time.sleep(0.2)
                campo.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", campo)
            time.sleep(0.2)

            # PASSO 2: Digitar a cidade e aguardar renderização do autocomplete
            campo.clear()
            campo.send_keys(self.cidade)
            logger.info(f"Digitado '{self.cidade}'")
            time.sleep(1.2)

            # PASSO 3: Clicar na sugestão do autocomplete de forma atômica via JS (à prova de StaleElement)
            texto_sugestao = f"{self.cidade.upper()} - RN"
            cidade_sem_acento = _sem_acentos(self.cidade).upper()
            logger.info(f"Procurando sugestão: '{texto_sugestao}'")

            sugestao_clicada = None
            fim_busca_sug = time.time() + 5.0
            while time.time() < fim_busca_sug:
                try:
                    sugestao_clicada = self.driver.execute_script(
                        """
                        const alvoExato = arguments[0];
                        const cidadeBase = arguments[1];
                        const norm = s => (s || '').normalize('NFD').replace(/[\\u0300-\\u036f]/g, '').toUpperCase().trim();

                        const candidatos = Array.from(document.querySelectorAll('#ComboCidade li, ul li'));
                        let item = candidatos.find(el => {
                            const t = (el.textContent || '').toUpperCase().trim();
                            return t === alvoExato || norm(t).includes(cidadeBase + ' - RN') || norm(t).startsWith(cidadeBase);
                        });
                        if (!item && cidadeBase === 'MOSSORO') {
                            item = document.getElementById('2408003');
                        }
                        if (item) {
                            item.scrollIntoView({block: 'center'});
                            item.click();
                            return (item.textContent || alvoExato).trim();
                        }
                        return null;
                        """,
                        texto_sugestao,
                        cidade_sem_acento,
                    )
                    if sugestao_clicada:
                        break
                except Exception:
                    pass
                time.sleep(0.25)

            if sugestao_clicada:
                logger.info(f"Sugestão '{sugestao_clicada}' clicada!")
                time.sleep(0.4)

                # PASSO 4: Clicar no botão "Aplicar" via JS (evita ElementClickInterceptedException pelo header)
                aplicar_clicado = False
                try:
                    aplicar_clicado = bool(
                        self.driver.execute_script(
                            """
                            const btn = document.querySelector('.btn-search.btn-purple')
                                || Array.from(document.querySelectorAll('.btn-search, button, div, a'))
                                    .find(el => (el.textContent || '').trim() === 'Aplicar');
                            if (btn) {
                                btn.scrollIntoView({block: 'center'});
                                btn.click();
                                return true;
                            }
                            return false;
                            """
                        )
                    )
                except Exception:
                    aplicar_clicado = False

                if aplicar_clicado:
                    logger.info("Botão 'Aplicar' clicado")
                else:
                    campo.send_keys(Keys.RETURN)

                # PASSO 5: Aguardar dinamicamente a atualização dos cards para a cidade filtrada
                fim_espera = time.time() + 8.0
                filtro_aplicado = False
                while time.time() < fim_espera:
                    resumo_atual = self._obter_resumo_dom_vagas()
                    if resumo_atual:
                        locais_texto = " ".join(r.get("local", "") for r in resumo_atual)
                        primeiro_atual = resumo_atual[0].get("codigo")
                        if (
                            cidade_sem_acento in _sem_acentos(locais_texto).upper()
                            or (primeiro_codigo_antes and primeiro_atual != primeiro_codigo_antes)
                        ):
                            filtro_aplicado = True
                            break
                    time.sleep(0.25)

                if not filtro_aplicado:
                    time.sleep(1.5)

                resumo_pos = self._obter_resumo_dom_vagas()
                if resumo_pos:
                    logger.info(f"Busca por '{self.cidade}' confirmada! ({len(resumo_pos)} vagas na 1ª página)")
                    return True

                pagina_texto = _sem_acentos(self.driver.page_source).lower()
                if _sem_acentos(self.cidade).lower() in pagina_texto:
                    logger.info(f"Busca por '{self.cidade}' confirmada!")
                    return True
                else:
                    logger.warning(f"'{self.cidade}' NÃO encontrado após clicar na sugestão")
                    return False
            else:
                logger.warning("Nenhuma sugestão encontrada, tentando Enter...")
                campo.send_keys(Keys.RETURN)
                time.sleep(1.5)
                return True

        except Exception as e:
            logger.error(f"Erro na busca: {e}")
            return False

    @staticmethod
    def _eh_linha_ignorada(linha: str) -> bool:
        ruido = ("00:00", "Compartilhar", "Ver detalhes", "Carregar mais", "Candidatar-se")
        if any(p in linha for p in ruido):
            return True
        # Ignora linhas de horário como "07:30:00 às 11:30:00" ou "13:30:00 às 17:30:00"
        if re.search(r"\b\d{2}:\d{2}(?::\d{2})?\s*(?:às|as|-)\s*\d{2}:\d{2}", linha, re.IGNORECASE):
            return True
        return False

    @staticmethod
    def _parece_empresa(linha: str, cidade: str) -> bool:
        padroes_empresa = [
            "LTDA", "S/A", "S.A.", "SS", "MEI", "EIRELI",
            "INDÚSTRIA", "COMÉRCIO", "SERVIÇOS", "CONSULTORIA",
            "ASSOCIADOS", "PARCEIROS", "GRUPO", "HOLDING",
        ]
        eh_empresa = any(p in linha.upper() for p in padroes_empresa)
        if not (eh_empresa and len(linha) < 50 and cidade.upper() not in linha.upper()):
            return False

        return " - RN" not in linha.upper() and "/" not in linha and not linha.upper().startswith("MOSSORÓ")

    @staticmethod
    def _parece_endereco(linha: str, cidade: str) -> bool:
        upper = _sem_acentos(linha).upper()
        cidade_upper = _sem_acentos(cidade).upper()
        if cidade_upper in upper or " - RN" in upper or "/RN" in upper:
            return True
        # Padrão geral de localidade nos cards do CIEE: "Bairro - Cidade - UF" ou "Cidade - UF"
        if re.search(r"-\s*[A-Z]{2}\s*$", upper):
            return True
        return False

    @staticmethod
    def _extrair_data_vencimento(texto_card: str):
        """Extracts date information from text using multiple formats"""
        if not texto_card:
            return None

        padroes = [
            r"\b(\d{2})/(\d{2})/(\d{4})\b",  # dd/mm/yyyy
            r"\b(\d{2})-(\d{2})-(\d{4})\b",  # dd-mm-yyyy
            r"\b(\d{2})/(\d{2})/(\d{2})\b",  # dd/mm/yy
            r"\b(\d{1,2}) de (\w+) de (\d{4})\b",  # d de month de yyyy
            r"\b(\d{1,2}) (\w+) (\d{4})\b",  # d month yyyy
            r"\b(\d{4})-(\d{2})-(\d{2})\b",  # yyyy-mm-dd
            r"\b(\d{2})\.(\d{2})\.(\d{4})\b",  # dd.mm.yyyy
        ]

        for padrao in padroes:
            match = re.search(padrao, texto_card)
            if match:
                try:
                    if any("/" in g for g in match.groups()):
                        dia, mes, ano = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    elif "de" in match.group(0).lower():
                        dia = int(match.group(1))
                        mes_texto = match.group(2).lower()
                        ano = int(match.group(3))

                        meses = {
                            "jan": 1, "january": 1, "janeiro": 1,
                            "fev": 2, "feb": 2, "february": 2, "fevereiro": 2,
                            "mar": 3, "março": 3, "marco": 3, "march": 3,
                            "abr": 4, "april": 4, "abril": 4,
                            "mai": 5, "may": 5, "maio": 5,
                            "jun": 6, "june": 6, "junho": 6,
                            "jul": 7, "july": 7, "julho": 7,
                            "ago": 8, "aug": 8, "agosto": 8,
                            "set": 9, "sep": 9, "september": 9, "setembro": 9,
                            "out": 10, "oct": 10, "october": 10, "outubro": 10,
                            "nov": 11, "november": 11, "novembro": 11,
                            "dez": 12, "dec": 12, "december": 12, "dezembro": 12,
                        }

                        mes = meses.get(mes_texto, None)
                        if not mes:
                            continue
                    else:
                        if len(match.group(3)) == 2:
                            ano = int("20" + match.group(3))
                        else:
                            ano = int(match.group(3))
                        dia, mes = int(match.group(1)), int(match.group(2))

                    if 1 <= mes <= 12:
                        try:
                            return datetime(ano, mes, dia)
                        except ValueError:
                            continue
                except (ValueError, IndexError):
                    continue

        return None

    def _montar_link(self, card, codigo_vaga: str) -> str:
        url_base_vagas = f"{URL_CIEE.rstrip('/')}/quero-uma-vaga/"
        if codigo_vaga and codigo_vaga != "N/A":
            return f"{url_base_vagas}?codigoVaga={codigo_vaga}"

        if card is not None:
            try:
                href_direto = (card.get_attribute("href") or "").strip()
                if href_direto and "codigoVaga=" in href_direto:
                    if href_direto.startswith("?"):
                        return f"{url_base_vagas}{href_direto}"
                    return href_direto
            except Exception:
                pass

            try:
                if self.driver:
                    self.driver.implicitly_wait(0)
                links = card.find_elements(By.TAG_NAME, "a")
                for elem in links:
                    href = (elem.get_attribute("href") or "").strip()
                    if not href or href in (URL_CIEE, f"{URL_CIEE.rstrip('/')}/", "#", "javascript:void(0)", "javascript:;"):
                        continue
                    if "vaga" in href.lower() or "detalhe" in href.lower():
                        return href
            except Exception:
                pass
            finally:
                try:
                    if self.driver:
                        self.driver.implicitly_wait(2)
                except Exception:
                    pass

        return url_base_vagas

    def _parse_card(self, texto_card: str, link: str) -> dict:
        linhas = [linha.strip() for linha in texto_card.split("\n") if linha.strip()]

        nome = "Vaga CIEE"
        categoria = "Estágio/Jovem Aprendiz"
        salario = "A combinar"
        area = "Área não especificada"
        codigo_vaga = "N/A"
        endereco = ""
        cidade_encontrada = ""
        empresa = ""
        area_encontrada = False
        modalidade_encontrada = False
        indice_categoria = -1

        for j, linha in enumerate(linhas):
            if j == indice_categoria:
                # Esta linha já foi atribuída como categoria (ramo de atividade logo abaixo do título)
                continue

            if self._eh_linha_ignorada(linha):
                continue

            if linha.isdigit() and len(linha) >= 5:
                codigo_vaga = linha
                continue

            linha_lower = _sem_acentos(linha).lower().strip()
            if not modalidade_encontrada and linha_lower in ("estagio", "aprendiz", "jovem aprendiz", "pcd"):
                if "aprendiz" in linha_lower:
                    nome = "Aprendiz"
                elif "pcd" in linha_lower:
                    nome = "PCD"
                else:
                    nome = "Estágio"
                modalidade_encontrada = True
                if j + 1 < len(linhas) and not self._eh_linha_ignorada(linhas[j + 1]):
                    categoria = linhas[j + 1].strip()
                    indice_categoria = j + 1
                continue

            if "R$" in linha:
                salario = re.sub(r"\s+", " ", linha).strip()
                continue

            if linha.lower() == "a combinar":
                continue

            if self._parece_endereco(linha, self.cidade):
                endereco = linha
                if _sem_acentos(self.cidade).upper() in _sem_acentos(linha).upper():
                    cidade_encontrada = self.cidade
                continue

            if self._parece_empresa(linha, self.cidade) and area_encontrada:
                empresa = linha
                continue

            if not area_encontrada and 2 < len(linha) < 85:
                area = linha
                area_encontrada = True
                continue

        prefixo_codigo = f"[{codigo_vaga}]" if codigo_vaga and codigo_vaga != "N/A" else "[CIEE]"
        salario_txt = f" ({salario})" if salario and salario != "A combinar" else ""
        nome_completo = f"{prefixo_codigo} {nome} - {area}{salario_txt}"

        vaga = {
            "codigo": codigo_vaga,
            "titulo": nome_completo,
            "nome": nome_completo,
            "categoria": categoria,
            "salario": salario,
            "area": area,
            "endereco": endereco,
            "cidade": cidade_encontrada if cidade_encontrada else self.cidade,
            "empresa": empresa,
            "nome_completo": nome_completo,
            "descricao": f"Oportunidade de {nome} na área {area} ({categoria}). Remuneração: {salario}. Local: {endereco or cidade_encontrada or self.cidade}.",
            "link": link,
            "fonte": "CIEE",
            "fonte_id": "ciee_agente",
            "status": "Aberto",
            "coletado_em": datetime.now(),
            "session_id": self.session_id,
        }

        data_vencimento = self._extrair_data_vencimento(texto_card)
        if data_vencimento:
            vaga["data_vencimento"] = data_vencimento

        return vaga

    def _construir_vaga_de_dom_item(self, item: dict) -> dict:
        """Constrói o dicionário padronizado da vaga diretamente dos seletores semânticos de a.vaga-row."""
        codigo_vaga = (item.get("codigo") or "").strip() or "N/A"
        tipo_bruto = (item.get("tipo") or "").strip()
        tipo_lower = _sem_acentos(tipo_bruto).lower()
        if "aprendiz" in tipo_lower:
            nome = "Aprendiz"
        elif "pcd" in tipo_lower:
            nome = "PCD"
        elif "estagio" in tipo_lower:
            nome = "Estágio"
        else:
            nome = tipo_bruto or "Estágio"

        categoria = re.sub(r"\s+", " ", (item.get("descricao") or "").strip()) or "Estágio/Jovem Aprendiz"
        area = re.sub(r"\s+", " ", (item.get("area") or "").strip()) or "Área não especificada"
        endereco = re.sub(r"\s+", " ", (item.get("local") or "").strip())
        horario = re.sub(r"\s+", " ", (item.get("horario") or "").strip())
        salario = re.sub(r"\s+", " ", (item.get("salario") or "").replace("\xa0", " ").strip()) or "A combinar"

        url_base_vagas = f"{URL_CIEE.rstrip('/')}/quero-uma-vaga/"
        if codigo_vaga != "N/A":
            link = f"{url_base_vagas}?codigoVaga={codigo_vaga}"
        else:
            link = url_base_vagas

        prefixo_codigo = f"[{codigo_vaga}]" if codigo_vaga != "N/A" else "[CIEE]"
        salario_txt = f" ({salario})" if salario and salario != "A combinar" else ""
        nome_completo = f"{prefixo_codigo} {nome} - {area}{salario_txt}"

        vaga = {
            "codigo": codigo_vaga,
            "titulo": nome_completo,
            "nome": nome_completo,
            "categoria": categoria,
            "salario": salario,
            "horario": horario,
            "area": area,
            "endereco": endereco,
            "cidade": self.cidade if _sem_acentos(self.cidade).upper() in _sem_acentos(endereco).upper() else (endereco or self.cidade),
            "empresa": "",
            "nome_completo": nome_completo,
            "descricao": f"Oportunidade de {nome} na área {area} ({categoria}). Remuneração: {salario}. Horário: {horario or 'A combinar'}. Local: {endereco or self.cidade}.",
            "link": link,
            "fonte": "CIEE",
            "fonte_id": "ciee_agente",
            "status": "Aberto",
            "coletado_em": datetime.now(),
            "session_id": self.session_id,
        }

        data_vencimento = self._extrair_data_vencimento(item.get("texto") or "")
        if data_vencimento:
            vaga["data_vencimento"] = data_vencimento

        return vaga

    def _carregar_paginacao(self, max_cliques: int = 10):
        cliques = 0
        try:
            self.driver.implicitly_wait(0)
            while cliques < max_cliques:
                try:
                    botoes = self.driver.find_elements(
                        By.XPATH, "//*[contains(text(), 'Carregar mais')]"
                    )
                    visiveis = [b for b in botoes if b.is_displayed()]
                    if not visiveis:
                        break

                    alvo = visiveis[-1]
                    qtd_antes = len(self.driver.find_elements(By.CSS_SELECTOR, "a.vaga-row"))
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", alvo)
                    self.driver.execute_script("arguments[0].click();", alvo)
                    cliques += 1
                    logger.info(f"Paginação: clique {cliques} em 'Carregar mais'")

                    # Aguarda os novos cards serem inseridos no DOM (máx 2.5s)
                    fim = time.time() + 2.5
                    carregou_novos = False
                    while time.time() < fim:
                        qtd_atual = len(self.driver.find_elements(By.CSS_SELECTOR, "a.vaga-row"))
                        if qtd_atual > qtd_antes:
                            carregou_novos = True
                            break
                        time.sleep(0.2)
                    if not carregou_novos:
                        break
                except Exception:
                    break
        finally:
            try:
                self.driver.implicitly_wait(2)
            except Exception:
                pass
        return cliques

    def _localizar_botoes_detalhe(self):
        try:
            cards = self.driver.find_elements(By.CSS_SELECTOR, "a.vaga-row")
            if cards:
                logger.info(f"Encontrados {len(cards)} cards de vagas ('a.vaga-row')")
                return cards

            botoes = WebDriverWait(self.driver, 8).until(
                EC.presence_of_all_elements_located((By.XPATH, "//*[contains(text(), 'Ver detalhes')]"))
            )
            logger.info(f"Encontrados {len(botoes)} botões 'Ver detalhes'")
            return botoes
        except Exception:
            return []

    def extrair_vagas(self):
        try:
            logger.info("Extraindo vagas...")

            # Aguardar presença inicial dos cards
            try:
                WebDriverWait(self.driver, 8).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a.vaga-row"))
                )
            except Exception:
                time.sleep(1)

            # PASSO 1: tratar paginação (Carregar mais)
            self._carregar_paginacao()

            # PASSO 2: extração estruturada ultrarrápida via JS de todos os cards a.vaga-row
            itens_dom = []
            try:
                itens_dom = self.driver.execute_script(
                    """
                    return Array.from(document.querySelectorAll('a.vaga-row')).map(card => ({
                        codigo: (card.querySelector('.cod-vaga')?.textContent || '').trim(),
                        tipo: (card.querySelector('.tipo-vaga')?.textContent || '').trim(),
                        descricao: (card.querySelector('.descricao')?.textContent || '').trim(),
                        area: (card.querySelector('.info-area')?.textContent || '').trim(),
                        local: (card.querySelector('.info-local')?.textContent || '').trim(),
                        horario: (card.querySelector('.info-horario')?.textContent || '').trim(),
                        salario: (card.querySelector('.info-salario')?.textContent || '').trim(),
                        href: card.getAttribute('href') || '',
                        texto: card.innerText || card.textContent || ''
                    }));
                    """
                )
            except Exception:
                itens_dom = []

            vagas_temp = []
            codigos_processados = set()

            if isinstance(itens_dom, list) and len(itens_dom) > 0:
                logger.info(f"Encontrados {len(itens_dom)} cards de vagas na página")
                for i, item in enumerate(itens_dom):
                    codigo = (item.get("codigo") or "").strip()
                    chave_unica = codigo if codigo else (item.get("texto") or "").strip()
                    if not chave_unica or chave_unica in codigos_processados:
                        continue
                    codigos_processados.add(chave_unica)

                    if item.get("area") or item.get("local") or item.get("tipo"):
                        vaga = self._construir_vaga_de_dom_item(item)
                    else:
                        link_inicial = self._montar_link(None, codigo_vaga=codigo or "N/A")
                        vaga = self._parse_card(item.get("texto") or "", link_inicial)
                        vaga["link"] = self._montar_link(None, vaga["codigo"])

                    vagas_temp.append(vaga)
                    endereco_log = vaga["endereco"] if vaga["endereco"] else "sem endereço"
                    logger.info(f" Vaga {i+1}: {vaga['titulo']} | Local: {endereco_log}")
            else:
                # Fallback para WebElements tradicionais (ex.: mocks de testes)
                botoes = self._localizar_botoes_detalhe()
                if not botoes:
                    logger.warning("Nenhum botão 'Ver detalhes' encontrado")
                    self.driver.save_screenshot(f"ciee_sem_botoes_{self.session_id}.png")
                    return False

                cards_processados = set()
                for i, elem in enumerate(botoes):
                    try:
                        tag = (getattr(elem, "tag_name", "") or "").lower()
                        if tag == "a":
                            card = elem
                        else:
                            try:
                                card = elem.find_element(By.XPATH, "./ancestor::a[contains(@class, 'vaga-row')][1]")
                            except Exception:
                                card = elem.find_element(By.XPATH, "./ancestor::*[contains(., 'Compartilhar')][1]")

                        texto_card = card.text
                        if not texto_card or texto_card in cards_processados:
                            continue
                        cards_processados.add(texto_card)

                        vaga = self._parse_card(texto_card, "")
                        vaga["link"] = self._montar_link(card, vaga["codigo"])
                        vagas_temp.append(vaga)

                        endereco_log = vaga["endereco"] if vaga["endereco"] else "sem endereço"
                        logger.info(f" Vaga {i+1}: {vaga['titulo']} | Local: {endereco_log}")
                    except Exception as e:
                        logger.debug(f"Erro no card {i}: {e}")
                        continue

            # PASSO 4: filtrar por endereço que contém a cidade/UF
            self.vagas = self._filtrar_por_cidade(vagas_temp)

            if not self.vagas:
                logger.warning(f"Nenhuma vaga de {self.cidade} encontrada!")
                self.driver.save_screenshot(f"ciee_sem_vagas_{self.cidade}_{self.session_id}.png")
                return False

            logger.info(f"Total extraído: {len(self.vagas)} vagas de {self.cidade}")
            return True

        except Exception as e:
            logger.error(f"Erro na extração: {e}")
            return False

    def _filtrar_por_cidade(self, vagas: list) -> list:
        """Mantém apenas as vagas cujo texto/endereço contenha a cidade ou a UF RN."""
        filtradas = []
        cidade_norm = _sem_acentos(self.cidade).upper()
        for vaga in vagas:
            texto_completo = _sem_acentos(
                f"{vaga.get('nome_completo', '')} {vaga.get('area', '')} {vaga.get('endereco', '')}"
            ).upper()
            if cidade_norm in texto_completo or " - RN" in texto_completo or "/RN" in texto_completo or "RN" in vaga.get("endereco", ""):
                vaga["cidade"] = self.cidade
                filtradas.append(vaga)
                logger.info(f"Vaga de {self.cidade}: {vaga['titulo']} | Local: {vaga.get('endereco', '')}")
        return filtradas

    def salvar_mongodb(self):
        """Salva as vagas no MongoDB com deduplicação, classificação semântica e limpeza de vagas expiradas."""
        if not self.vagas:
            logger.warning(" Nenhuma vaga para salvar")
            return 0

        logger.info(f"Salvando {len(self.vagas)} vagas no MongoDB...")

        salvos = 0
        atualizados = 0
        erros = 0
        codigos_ativos = []

        for vaga in self.vagas:
            try:
                # Enriquecimento automático de cursos e áreas para o feed e filtros
                if classificar_oportunidade is not None:
                    try:
                        cls = classificar_oportunidade(
                            vaga.get("titulo", ""),
                            f"{vaga.get('area', '')} {vaga.get('categoria', '')} {vaga.get('descricao', '')}",
                        )
                        vaga["cursos"] = cls.get("cursos", [])
                        vaga["areas"] = cls.get("areas") or ["Mercado", "Estágio"]
                        vaga["geral"] = cls.get("geral", False)
                    except Exception:
                        vaga.setdefault("areas", ["Mercado", "Estágio"])

                if vaga.get("codigo") and vaga["codigo"] != "N/A":
                    filtro = {"codigo": vaga["codigo"]}
                    codigos_ativos.append(vaga["codigo"])
                else:
                    filtro = {"nome_completo": vaga["nome_completo"]}

                resultado = self.colecao.update_one(
                    filtro,
                    {"$set": vaga},
                    upsert=True,
                )

                if resultado.upserted_id:
                    salvos += 1
                elif resultado.modified_count:
                    atualizados += 1

            except Exception as e:
                logger.warning(f"Erro ao salvar vaga: {e}")
                erros += 1

        # Remove da coleção vagas antigas/encerradas que não estão mais ativas no portal CIEE
        if codigos_ativos:
            try:
                removidos = self.colecao.delete_many({"codigo": {"$nin": codigos_ativos}})
                if getattr(removidos, "deleted_count", 0) > 0:
                    logger.info(f"Removidas {removidos.deleted_count} vagas antigas/encerradas do banco.")
            except Exception as e:
                logger.debug(f"Aviso ao limpar vagas antigas: {e}")

        total_processado = salvos + atualizados
        logger.info(f"{salvos} novas vagas salvas, {atualizados} atualizadas (Itens na base: {len(self.vagas)})")
        if erros > 0:
            logger.warning(f"{erros} vagas com erro")

        return total_processado if total_processado > 0 else len(self.vagas)

    def gerar_relatorio(self):
        logger.info("=" * 60)
        logger.info("RELATÓRIO DE EXECUÇÃO")
        logger.info("=" * 60)
        logger.info(f"Sessão: {self.session_id}")
        logger.info(f"Cidade: {self.cidade}")
        logger.info(f"Vagas extraídas: {len(self.vagas)}")
        logger.info("=" * 60)

        for i, vaga in enumerate(self.vagas, 1):
            logger.info(f"{i}. {vaga.get('titulo', 'Sem título')}")
            logger.info(f"   Ramo/Categoria: {vaga.get('categoria', 'N/E')}")
            logger.info(f"   Área: {vaga.get('area', 'N/E')}")
            logger.info(f"   Local: {vaga.get('endereco', 'N/I')}")
            logger.info(f"   Salário: {vaga.get('salario', 'N/I')}")
            if vaga.get("data_vencimento"):
                logger.info(f"   Vence: {vaga['data_vencimento']}")
            logger.info("   ---")

    def executar(self):
        inicio_exec = time.time()
        logger.info("=== INÍCIO DA VARREDURA: CIEE (Estágios Comerciais) ===")
        logger.info(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
        logger.info("SCRAPER CIEE HÍBRIDO")
        logger.info("=" * 60)
        logger.info(f"Busca por: {self.cidade}")
        logger.info(f"URL: {URL_CIEE}")
        logger.info("=" * 60)

        if not self.conectar_mongodb():
            return False

        if not self.configurar_driver():
            return False

        try:
            logger.info("Acessando CIEE...")
            self.driver.get(URL_CIEE)
            time.sleep(1.5)

            if not self.buscar_cidade():
                logger.error("Falha na busca")
                return False

            if not self.extrair_vagas():
                logger.warning("Nenhuma vaga extraída")
                return False

            salvos = self.salvar_mongodb()
            self.gerar_relatorio()
            duracao = round(time.time() - inicio_exec, 1)

            logger.info("=" * 60)
            logger.info("SCRAPER CONCLUÍDO COM SUCESSO!")
            logger.info(f"Concluído em {duracao}s")
            logger.info(f"  {len(self.vagas)} vagas extraídas")
            logger.info(f"  vagas salvas: {len(self.vagas)} (novas/atualizadas: {salvos})")
            logger.info(f"  Itens na base: {len(self.vagas)}")
            logger.info("=" * 60)

            return True

        except Exception as e:
            logger.error(f"Erro durante execução: {e}")
            try:
                self.driver.save_screenshot(f"ciee_erro_{self.session_id}.png")
            except Exception:
                pass
            return False
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Navegador fechado")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Scraper CIEE Híbrido")
    parser.add_argument(
        "--cidade",
        default="Mossoró",
        help="Cidade para buscar (padrão: Mossoró)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Ativa modo debug",
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Limpa o arquivo logs/ciee.log ao iniciar diretamente para manter o log da última sessão limpo para o dashboard
    try:
        (LOGS_DIR / "ciee.log").write_text("", encoding="utf-8")
    except Exception:
        pass

    scraper = ScraperCIEEHibrido(cidade=args.cidade)
    sucesso = scraper.executar()

    return 0 if sucesso else 1


if __name__ == "__main__":
    exit(main())
