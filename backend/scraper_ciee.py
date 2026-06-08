from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from pymongo import MongoClient
import time

def conectar_banco():
    client = MongoClient("mongodb://localhost:27017/")
    db = client["hub_estudantes"]
    return db["vagas_ciee"]

def raspar_ciee():
    print("Iniciando robô do CIEE...")
    print("ATENÇÃO: O navegador vai abrir. Você terá 20 SEGUNDOS para digitar 'Mossoró', apertar Enter e esperar as vagas carregarem!")
    
    chrome_options = Options()
    # ==========================================
    # TIRAMOS A VENDA DO ROBÔ (Removemos o --headless)
    # Agora você vai ver o Brave abrindo e sendo controlado
    # ==========================================
    chrome_options.binary_location = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    
    servico = Service(ChromeDriverManager().install())
    navegador = webdriver.Chrome(service=servico, options=chrome_options)
    
    # URL da Vitrine (Você pode colocar a exata que você usa aqui)
    navegador.get("https://portal.ciee.org.br/")
    
    # Pausa dramática para o "Humano" interagir com a tela
    print("\n[TEMPO] O relógio está correndo! Faça a pesquisa por Mossoró no navegador agora...")
    time.sleep(20) 
    print("[ROBO] O robô acordou! Extraindo os dados da tela atual...")
    
    colecao_bd = conectar_banco()
    vagas_inseridas = 0
    
    try:
        # 1. Caça especificamente os botões de "Ver detalhes"
        botoes = navegador.find_elements(By.XPATH, "//*[contains(text(), 'Ver detalhes')]")
        print(f"-> O robô visualizou {len(botoes)} vagas na tela. Iniciando extração...")
        
        cards_processados = set() # Para evitar duplicatas caso o site tenha botões duplos
        
        for botao in botoes:
            try:
                # 2. A MÁGICA: Sobe no HTML a partir do botão até achar a caixa do Card (que tem a palavra Compartilhar)
                card = botao.find_element(By.XPATH, "./ancestor::*[contains(., 'Compartilhar')][1]")
                
                texto_card = card.text
                
                # Prevenção de duplicatas de leitura
                if texto_card in cards_processados:
                    continue
                cards_processados.add(texto_card)
                
                # Quebra o texto do card isolado em linhas
                linhas = [linha.strip() for linha in texto_card.split('\n') if linha.strip()]
                
                # Valores padrão
                nome = "Vaga CIEE"
                categoria = "Estágio/Jovem Aprendiz"
                salario = "A combinar"
                area = "Área não especificada"
                codigo_vaga = "N/A"
                
                # Extrai os dados linha por linha do card isolado
                for i, linha in enumerate(linhas):
                    if linha.isdigit() and len(linha) >= 5:
                        codigo_vaga = linha
                    elif linha in ["Estágio", "Aprendiz"]:
                        nome = linha
                        if i + 1 < len(linhas):
                            categoria = linhas[i+1]
                    elif "R$" in linha:
                        salario = linha
                    elif "00:00" not in linha and "Mossoró" not in linha and "Compartilhar" not in linha and "Ver detalhes" not in linha:
                        if linha != nome and linha != categoria and len(linha) > 4 and not linha.isdigit():
                            area = linha

                documento = {
                    "nome": f"[{codigo_vaga}] {nome} - {area} ({salario})", 
                    "link": "https://portal.ciee.org.br/", 
                    "categoria": categoria,
                    "fonte": "CIEE"
                }
                
                # Salva no Mongo
                colecao_bd.update_one(
                    {"nome": documento["nome"]}, 
                    {"$set": documento},
                    upsert=True
                )
                vagas_inseridas += 1
                
            except Exception as erro_card:
                # Se um card específico der erro, ignora ele e vai para o próximo
                continue
                
    except Exception as e:
        print(f"Erro principal: {e}")
            
    print(f"\nSucesso! {vagas_inseridas} vagas do CIEE inseridas.")
    
    # Fecha o navegador automaticamente no final da missão
    navegador.quit()

if __name__ == "__main__":
    raspar_ciee()