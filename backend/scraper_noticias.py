import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient

def conectar_banco():
    client = MongoClient("mongodb://localhost:27017/")
    return client["hub_estudantes"]["vagas_noticias"]

def atualizar_noticias_agora():
    print("\nIniciando raspagem ao vivo de múltiplas fontes...")
    colecao = conectar_banco()
    
    # Apaga as notícias antigas para mostrar os dados fresquinhos na apresentação
    colecao.delete_many({})
    noticias_inseridas = 0
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # ==========================================
    # FONTE 1: G1 TECNOLOGIA
    # ==========================================
    try:
        print("-> Buscando no G1 Tecnologia...")
        resposta_g1 = requests.get("https://g1.globo.com/tecnologia/", headers=headers)
        soup_g1 = BeautifulSoup(resposta_g1.text, 'html.parser')
        
        for post in soup_g1.find_all('div', class_='feed-post-body')[:10]: # Pegando as 6 primeiras
            titulo_tag = post.find('a', class_='gui-color-hover')
            if not titulo_tag:
                continue
                
            documento = {
                "nome": titulo_tag.text.strip(),
                "link": titulo_tag.get('href'),
                "categoria": "Notícia Tech",
                "fonte": "G1"
            }
            colecao.insert_one(documento)
            noticias_inseridas += 1
    except Exception as e:
        print(f"Erro no G1: {e}")

    # ==========================================
    # FONTE 2: CANALTECH (Últimas Notícias)
    # ==========================================
    try:
        print("-> Buscando no Canaltech...")
        resposta_ct = requests.get("https://canaltech.com.br/ultimas/", headers=headers)
        soup_ct = BeautifulSoup(resposta_ct.text, 'html.parser')
        
        # No Canaltech, os títulos das notícias geralmente ficam em tags <h3> ou <h2>
        # Vamos procurar os títulos e "subir" para achar o link principal
        titulos = soup_ct.find_all(['h3', 'h2'])
        
        # Contador para limitar a 6 notícias também
        ct_count = 0 
        
        for titulo_tag in titulos:
            if ct_count >= 10:
                break
                
            # Procura a tag <a> (link) que envolve o título
            link_tag = titulo_tag.find_parent('a')
            if not link_tag:
                continue
                
            link = link_tag.get('href', '')
            # O Canaltech costuma usar links relativos (ex: /noticia/...), precisamos colocar o domínio antes
            if link.startswith('/'):
                link = "https://canaltech.com.br" + link
                
            documento = {
                "nome": titulo_tag.text.strip(),
                "link": link,
                "categoria": "Notícia Tech",
                "fonte": "Canaltech"
            }
            colecao.insert_one(documento)
            noticias_inseridas += 1
            ct_count += 1
            
    except Exception as e:
        print(f"Erro no Canaltech: {e}")
        
    print(f"Sucesso! {noticias_inseridas} notícias salvas no banco neste exato segundo.")
    return True

# Teste local
if __name__ == "__main__":
    atualizar_noticias_agora()