##backend/scraper_ciee.py

import logging
import os
import re
import time
import sys
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.firefox import GeckoDriverManager
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("MONGODB_DB", "hub_estudantes")
COLLECTION_NAME = os.getenv("CIEE_COLLECTION", "vagas_ciee")
CIDADE = os.getenv("CIEE_CIDADE", "Mossoró")
URL_CIEE = os.getenv("CIEE_URL", "https://portal.ciee.org.br/")
GECKODRIVER_PATH = os.getenv("GECKODRIVER_PATH", "")  # vazio => download automático

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('scraper_ciee.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

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
            logger.error(f"❌ Erro na conexão MongoDB: {e}")
            return False

    def configurar_driver(self):
     
        try:
            options = Options()

            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")

            options.set_preference("general.useragent.override",
                "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0")
            options.set_preference("permissions.default.image", 2)
        
            if GECKODRIVER_PATH and Path(GECKODRIVER_PATH).exists():
                service = Service(GECKODRIVER_PATH)
            else:
                service = Service(GeckoDriverManager().install())
            self.driver = webdriver.Firefox(service=service, options=options)

            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)

            logger.info("Firefox headless configurado")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao configurar driver: {e}")
            return False

    def buscar_cidade(self):
        
        try:
            logger.info(f"Buscando por '{self.cidade}'...")

            campo = None
            seletores = [
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
                except:
                    continue

            if not campo:
                logger.error("❌ Campo de busca não encontrado")
                return False

            # PASSO 1: CLICAR NO CAMPO (ativa o dropdown)
            campo.click()
            time.sleep(0.5)

            # PASSO 2: DIGITAR A CIDADE
            campo.clear()
            campo.send_keys(self.cidade)
            logger.info(f"Digitado '{self.cidade}'")
            time.sleep(2)

            # PASSO 3: CLICAR NA SUGESTÃO (CORRIGIDO!)
            try:
                sugestao = None

                texto_sugestao = f"{self.cidade.upper()} - RN"
                logger.info(f"🔍 Procurando sugestão: '{texto_sugestao}'")

                # Estratégia 1: Procurar por <li> com o texto EXATO
                sugestoes = self.driver.find_elements(By.XPATH,
                    f"//li[contains(text(), '{texto_sugestao}')]")
                for elem in sugestoes:
                    if elem.is_displayed() and elem.is_enabled():
                        sugestao = elem
                        logger.info("Sugestão encontrada (li)")
                        break

                # Estratégia 2: Procurar por ID específico
                if not sugestao:
                    try:
                        sugestao = self.driver.find_element(By.ID, "2408003")
                        logger.info("Sugestão encontrada por ID")
                    except:
                        pass

                # Estratégia 3: Procurar dentro do ComboCidade
                if not sugestao:
                    try:
                        sugestao = self.driver.find_element(By.CSS_SELECTOR, "#ComboCidade li")
                        logger.info("Sugestão encontrada por CSS")
                    except:
                        pass

                if sugestao:
                    
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", sugestao)
                    time.sleep(0.5)
                    sugestao.click()
                    logger.info(f"Sugestão '{texto_sugestao}' clicada!")
                    time.sleep(2)

                    # PASSO 4: CLICAR NO BOTÃO "Aplicar"
                    try:
                        aplicar = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Aplicar')]")
                        aplicar.click()
                        logger.info("Botão 'Aplicar' clicado")
                        time.sleep(2)
                    except:
                        pass

                    # PASSO 5: VERIFICAR SE O FILTRO FUNCIONOU
                    time.sleep(2)
                    pagina_texto = self.driver.page_source.lower()
                    if self.cidade.lower() in pagina_texto:
                        logger.info(f"Busca por '{self.cidade}' confirmada!")

                        
                        try:
                            botoes = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Ver detalhes')]")
                            logger.info(f"{len(botoes)} vagas encontradas")
                        except:
                            pass

                        return True
                    else:
                        logger.warning(f"⚠️ '{self.cidade}' NÃO encontrado após clicar na sugestão")
                        return False
                else:
                    logger.warning("⚠️ Nenhuma sugestão encontrada, tentando Enter...")
                    campo.send_keys(Keys.RETURN)
                    time.sleep(3)
                    return True

            except Exception as e:
                logger.error(f"❌ Erro ao clicar na sugestão: {e}")
                campo.send_keys(Keys.RETURN)
                time.sleep(3)
                return True

        except Exception as e:
            logger.error(f"❌ Erro na busca: {e}")
            return False

    
    @staticmethod
    def _eh_linha_ignorada(linha: str) -> bool:
       
        ruido = ("00:00", "Compartilhar", "Ver detalhes", "Carregar mais", "Candidatar-se")
        return any(p in linha for p in ruido)

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
       
        upper = linha.upper()
        return cidade.upper() in upper or " - RN" in upper or "/RN" in upper

    @staticmethod
    def _extrair_data_vencimento(texto_card: str):
        """Extracts date information from text using multiple formats"""
        if not texto_card:
            return None

        # Common date patterns
        padroes = [
            r"\b(\d{2})/(\d{2})/(\d{4})\b",  # dd/mm/yyyy
            r"\b(\d{2})-(\d{2})-(\d{4})\b",  # dd-mm-yyyy
            r"\b(\d{2})/(\d{2})/(\d{2})\b",  # dd/mm/yy
            r"\b(\d{1,2}) de (\w+) de (\d{4})\b",  # d de month de yyyy (Brazilian Portuguese)
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
                            "dez": 12, "dec": 12, "december": 12, "dezembro": 12
                        }
                        
                        mes = meses.get(mes_texto, None)
                        if not mes:
                            continue
                    else:
                        # For other formats without separators
                        if len(match.group(3)) == 2:  # yy format
                            ano = int("20" + match.group(3))  # Assume 21st century
                        else:
                            ano = int(match.group(3))
                        dia, mes = int(match.group(1)), int(match.group(2))
                    
                    # Validate date
                    if 1 <= mes <= 12:
                        try:
                            return datetime(ano, mes, dia)
                        except ValueError:
                            continue
                except (ValueError, IndexError):
                    continue
        
        return None

    def _montar_link(self, card, codigo_vaga: str) -> str:
      
        if codigo_vaga == "N/A":
            return URL_CIEE
        link_detalhe = f"{URL_CIEE.rstrip('/')}/quero-uma-vaga/?codigoVaga={codigo_vaga}"
        try:
            link_elem = card.find_element(By.TAG_NAME, "a")
            href = link_elem.get_attribute("href")
            if href:
                link_detalhe = href
        except Exception:
            pass
        return link_detalhe

    def _parse_card(self, texto_card: str, link: str) -> dict:
        
        linhas = [linha.strip() for linha in texto_card.split('\n') if linha.strip()]

        nome = "Vaga CIEE"
        categoria = "Estágio/Jovem Aprendiz"
        salario = "A combinar"
        area = "Área não especificada"
        codigo_vaga = "N/A"
        endereco = ""
        cidade_encontrada = ""
        empresa = ""
        area_encontrada = False

        for j, linha in enumerate(linhas):
            if self._eh_linha_ignorada(linha):
                continue

           
            if linha.isdigit() and len(linha) >= 6:
                codigo_vaga = linha
                continue

            if linha in ["Estágio", "Aprendiz"]:
                nome = linha
                if j + 1 < len(linhas):
                    categoria = linhas[j + 1]
                continue

            
            if "R$" in linha:
                salario = linha
                continue

            if self._parece_empresa(linha, self.cidade):
                empresa = linha
                continue

           
            if self._parece_endereco(linha, self.cidade):
                endereco = linha
                cidade_encontrada = self.cidade
                continue

            
            if not area_encontrada and 4 < len(linha) < 80:
                area = linha
                area_encontrada = True
                continue

        vaga = {
            "codigo": codigo_vaga,
            "titulo": nome,
            "categoria": categoria,
            "salario": salario,
            "area": area,
            "endereco": endereco,
            "cidade": cidade_encontrada if cidade_encontrada else self.cidade,
            "empresa": empresa,
            "nome_completo": f"[{codigo_vaga}] {nome} - {area} ({salario})",
            "link": link,
            "fonte": "CIEE",
            "coletado_em": datetime.now(),
            "session_id": self.session_id,
        }

        data_vencimento = self._extrair_data_vencimento(texto_card)
        if data_vencimento:
            vaga["data_vencimento"] = data_vencimento

        return vaga

    def _carregar_paginacao(self, max_cliques: int = 10):
      
        cliques = 0
        while cliques < max_cliques:
            try:
                botao = self.driver.find_element(
                    By.XPATH, "//*[contains(text(), 'Carregar mais')]"
                )
                if not botao.is_displayed():
                    break
                self.driver.execute_script("arguments[0].click();", botao)
                cliques += 1
                logger.info(f"📄 Paginação: clique {cliques} em 'Carregar mais'")
                time.sleep(2)
            except Exception:
                break  # não há mais paginação
        return cliques

    def _localizar_botoes_detalhe(self):
       
        try:
            botoes = WebDriverWait(self.driver, 20).until(
                EC.presence_of_all_elements_located((By.XPATH, "//*[contains(text(), 'Ver detalhes')]"))
            )
            logger.info(f"Encontrados {len(botoes)} botões 'Ver detalhes'")
            return botoes
        except Exception:
            return []

    def extrair_vagas(self):
       
        try:
            logger.info("Extraindo vagas...")

            # Aguardar carregamento inicial
            time.sleep(3)

            # PASSO 1: tratar paginação (infinite scroll)
            self._carregar_paginacao()

            # PASSO 2: localizar os botões "Ver detalhes"
            botoes = self._localizar_botoes_detalhe()
            if not botoes:
                logger.warning("⚠️ Nenhum botão 'Ver detalhes' encontrado")
                self.driver.save_screenshot(f"ciee_sem_botoes_{self.session_id}.png")
                return False

            # PASSO 3: extrair os dados de cada card (parsing puro)
            cards_processados = set()
            vagas_temp = []

            for i, botao in enumerate(botoes):
                try:
                    card = botao.find_element(
                        By.XPATH, "./ancestor::*[contains(., 'Compartilhar')][1]"
                    )

                    texto_card = card.text
                    if texto_card in cards_processados:
                        continue
                    cards_processados.add(texto_card)

                    link = self._montar_link(card, codigo_vaga="N/A")
                    # Reusa o parser puro; o código/link definitivo é recalculado
                    # a partir do texto extraído para manter consistência.
                    vaga = self._parse_card(texto_card, link)
                    vaga["link"] = self._montar_link(card, vaga["codigo"])

                    vagas_temp.append(vaga)

                    endereco_log = vaga['endereco'][:30] if vaga['endereco'] else 'sem endereço'
                    logger.info(f" Vaga {i+1}: [{vaga['codigo']}] {vaga['titulo'][:20]} - {endereco_log}")

                except Exception as e:
                    logger.debug(f"⚠️ Erro no card {i}: {e}")
                    continue

            # PASSO 4: filtrar por endereço que contém a cidade/UF
            self.vagas = self._filtrar_por_cidade(vagas_temp)

            if not self.vagas:
                logger.warning(f"⚠️ Nenhuma vaga de {self.cidade} encontrada!")
                self.driver.save_screenshot(f"ciee_sem_vagas_{self.cidade}_{self.session_id}.png")
                return False

            logger.info(f"Total extraído: {len(self.vagas)} vagas de {self.cidade}")
            return True

        except Exception as e:
            logger.error(f"❌ Erro na extração: {e}")
            return False

    def _filtrar_por_cidade(self, vagas: list) -> list:
        """Mantém apenas as vagas cujo texto contenha a cidade ou a UF RN."""
        filtradas = []
        for vaga in vagas:
            texto_completo = f"{vaga.get('nome_completo', '')} {vaga.get('area', '')} {vaga.get('endereco', '')}"
            if self.cidade in texto_completo or "RN" in texto_completo:
                vaga["cidade"] = self.cidade
                filtradas.append(vaga)
                logger.info(f"Vaga de {self.cidade}: [{vaga['codigo']}] {vaga['titulo'][:20]} - {vaga['endereco'][:30]}")
        return filtradas

    def salvar_mongodb(self):
        """Salva as vagas no MongoDB com deduplicação"""
        if not self.vagas:
            logger.warning(" Nenhuma vaga para salvar")
            return 0

        logger.info(f"Salvando {len(self.vagas)} vagas no MongoDB...")

        salvos = 0
        atualizados = 0
        erros = 0

        for vaga in self.vagas:
            try:
                if vaga.get("codigo") and vaga["codigo"] != "N/A":
                    filtro = {"codigo": vaga["codigo"]}
                else:
                    filtro = {"nome_completo": vaga["nome_completo"]}

                resultado = self.colecao.update_one(
                    filtro,
                    {"$set": vaga},
                    upsert=True
                )

                if resultado.upserted_id:
                    salvos += 1
                elif resultado.modified_count:
                    atualizados += 1

            except Exception as e:
                logger.warning(f"Erro ao salvar vaga: {e}")
                erros += 1

        logger.info(f"{salvos} novas vagas salvas, {atualizados} atualizadas")
        if erros > 0:
            logger.warning(f"{erros} vagas com erro")

        return salvos

    def gerar_relatorio(self):
       
        logger.info("=" * 60)
        logger.info("RELATÓRIO DE EXECUÇÃO")
        logger.info("=" * 60)
        logger.info(f"Sessão: {self.session_id}")
        logger.info(f"Cidade: {self.cidade}")
        logger.info(f"Vagas extraídas: {len(self.vagas)}")
        logger.info("=" * 60)

        for i, vaga in enumerate(self.vagas, 1):
            logger.info(f"{i}. [{vaga.get('codigo', 'N/A')}] {vaga.get('titulo', 'Sem título')}")
            logger.info(f"    Área: {vaga.get('area', 'N/E')}")
            logger.info(f"   Salário: {vaga.get('salario', 'N/I')}")
            if vaga.get('data_vencimento'):
                logger.info(f"   Vence: {vaga['data_vencimento']}")
            logger.info("   ---")

    def executar(self):
       
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
            logger.info("🌐 Acessando CIEE...")
            self.driver.get(URL_CIEE)
            time.sleep(2)

            if not self.buscar_cidade():
                logger.error("Falha na busca")
                return False

            if not self.extrair_vagas():
                logger.warning("Nenhuma vaga extraída")
                return False

            salvos = self.salvar_mongodb()
            self.gerar_relatorio()

            logger.info("=" * 60)
            logger.info(f"SCRAPER CONCLUÍDO COM SUCESSO!")
            logger.info(f"  {len(self.vagas)} vagas extraídas")
            logger.info(f"   {salvos} vagas salvas")
            logger.info("=" * 60)

            return True

        except Exception as e:
            logger.error(f"❌ Erro durante execução: {e}")
            try:
                self.driver.save_screenshot(f"ciee_erro_{self.session_id}.png")
            except:
                pass
            return False
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Navegador fechado")
def main():
    import argparse

    parser = argparse.ArgumentParser(description='Scraper CIEE Híbrido')
    parser.add_argument('--cidade', default='Mossoró',
                       help='Cidade para buscar (padrão: Mossoró)')
    parser.add_argument('--debug', action='store_true',
                       help='Ativa modo debug')

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = ScraperCIEEHibrido(cidade=args.cidade)
    sucesso = scraper.executar()

    return 0 if sucesso else 1

if __name__ == "__main__":
    exit(main())