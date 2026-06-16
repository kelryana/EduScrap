from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

PALAVRAS_CHAVE = [
    "estágio", "estágios", "bolsa", "bolsas", "vaga", "vagas", 
    "seleção", "edital", "pnaes", "auxílio", "residência", "monitoria"
]

def criar_navegador_real():
    """Configura e inicializa o Chrome de forma nativa para o Python 3.14."""
    opcoes = Options()
    opcoes.add_argument("--headless")  # Executa oculto em segundo plano
    opcoes.add_argument("--no-sandbox")
    opcoes.add_argument("--disable-dev-shm-usage")
    opcoes.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # NATIVO: Sem usar ChromeDriverManager para não quebrar no Python 3.14
    return webdriver.Chrome(options=opcoes)

def minerar_com_selenium():
    print("\n🌐 [BROWSER AUTOMATION] Inicializando Google Chrome legítimo nativo...")
    driver = criar_navegador_real()
    
    try:
        # --- ALVO 1: PORTAL DE NOTÍCIAS ---
        print("\n🕵️‍♂️ Navegando até o Portal de Notícias da UERN...")
        driver.get("https://portal.uern.br/todas-as-noticias/")
        
        print("⏳ Aguardando renderização da página...")
        time.sleep(8)
        
        soup_noticias = BeautifulSoup(driver.page_source, "html.parser")
        links_ancora = soup_noticias.find_all("a")
        
        print(f"✅ Conexão bem-sucedida! Encontradas {len(links_ancora)} tags de link na página.")
        
        links_processados = set()
        for ancora in links_ancora:
            titulo = ancora.get_text().strip()
            link = ancora.get("href", "")
            
            if link.startswith("https://portal.uern.br/") and len(titulo) > 15:
                if any(pula in link.lower() for pula in ["/wp-content/", "/category/", "/tag/", "/todas-as-noticias/"]):
                    continue
                    
                if link not in links_processados:
                    links_processados.add(link)
                    print(f"   📌 Manchete Mapeada: '{titulo}'")
                    print(f"   🔗 Link: {link}")

        # --- ALVO 2: JOUERN ---
        print("\n🕵️‍♂️ Navegando até a listagem de edições do JOUERN...")
        driver.get("https://portal.uern.br/jouern/todas-as-edicoes/")
        print("⏳ Aguardando renderização do JOUERN...")
        time.sleep(8)
        
        soup_jouern = BeautifulSoup(driver.page_source, "html.parser")
        links_jouern = soup_jouern.find_all("a")
        
        for link in links_jouern:
            href = link.get("href", "")
            texto = link.get_text().strip()
            
            if href.endswith(".pdf") or ("jouern" in href.lower() and any(c.isdigit() for c in texto)):
                if len(texto) > 4:
                    print(f"   📰 Edição do Diário Oficial Encontrada: '{texto}'")
                    print(f"   🔗 Link do Arquivo: {href}")

    except Exception as e:
        print(f"❌ Erro durante a simulação do navegador: {e}")
    finally:
        driver.quit()
        print("\n🔒 Instância do navegador encerrada com segurança.")

if __name__ == "__main__":
    print("🤖=== INICIANDO PROTOCOLO SELENIUM NATIVO BYPASS ===")
    minerar_com_selenium()
    print("🤖=== PROTOCOLO FINALIZADO ===")