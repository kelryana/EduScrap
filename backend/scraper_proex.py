import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient

def conectar_banco():
    client = MongoClient("mongodb://localhost:27017/")
    db = client["hub_estudantes"]
    return db["vagas_bolsa"]

def raspar_pagina_proex(url, colecao_bd):
    print(f"Acessando a página da PROEX: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    resposta = requests.get(url, headers=headers)
    
    if resposta.status_code != 200:
        print(f"Erro ao acessar a página. Código: {resposta.status_code}")
        return

    soup = BeautifulSoup(resposta.text, 'html.parser')
    editais_inseridos = 0

    # Estratégia PROEX: Procura diretamente os links <a>
    for tag_link in soup.find_all('a'):
        # Ignora menus laterais, cabeçalhos e rodapés
        if tag_link.find_parent(['nav', 'aside', 'footer', 'header']):
            continue

        texto_link = tag_link.get_text(strip=True).upper()

        # Verifica se o link é literalmente a palavra "EDITAL" (como na imagem em rosa)
        if texto_link == "EDITAL":
            link_pdf = tag_link.get('href')
            
            # Validação básica do link
            if not link_pdf or link_pdf == "#" or not link_pdf.startswith("http"):
                continue

            # Descobre o elemento "container" do link. 
            # Pode ser o item da lista (<li>) ou apenas o parágrafo (<p>)
            parent = tag_link.parent
            container = parent.parent if parent.name == 'li' else parent

            # Procura o título do edital "olhando para cima" (elementos anteriores)
            # Usamos um while para pular parágrafos vazios ou quebras de linha (<br>)
            irmao = container.find_previous_sibling()
            texto_titulo = ""
            
            while irmao:
                texto_temp = irmao.get_text(strip=True)
                if texto_temp: # Achou o primeiro elemento acima que tem algum texto
                    texto_titulo = texto_temp
                    break
                irmao = irmao.find_previous_sibling()

            # ==========================================
            # FILTRO: Só aceita se o TÍTULO começar com "EDITAL"
            # Isso ignora coisas como "CHAMAMENTO..." ou "NORMAS..."
            # ==========================================
            if not texto_titulo.upper().startswith("EDITAL"):
                continue

            nome_edital = texto_titulo.strip()

            # Monta o documento conforme as suas restrições
            documento = {
                "nome": nome_edital,
                "link": link_pdf,
                "categoria": "Bolsa", # Valor fixo para a PROEX conforme solicitado
                "fonte": "PROEX/UERN"
            }
            
            # Salva no banco de dados
            colecao_bd.update_one(
                {"link": link_pdf},
                {"$set": documento},
                upsert=True
            )
            editais_inseridos += 1

    print(f"Sucesso! {editais_inseridos} editais de Bolsa (PROEX) processados.\n")

if __name__ == "__main__":
    colecao = conectar_banco()
    
    # Lista de páginas alvo da PROEX
    paginas_alvo_proex = [
        "https://portal.uern.br/proex/2026-2/",
        "https://portal.uern.br/proex/2025-2/"
    ]
    
    for pagina in paginas_alvo_proex:
        raspar_pagina_proex(pagina, colecao)
        
    print("Finalizado! Verifique o MongoDB Compass.")