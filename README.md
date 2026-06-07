# TechHub UERN 🎓

O **TechHub UERN** é um agregador automático de oportunidades acadêmicas, desenvolvido como projeto para a disciplina de Banco de Dados II. 

Ele automatiza a busca por editais de estágio, bolsas e auxílios espalhados pelos portais institucionais da Universidade do Estado do Rio Grande do Norte (PRAE e PROEX), centralizando-os em uma interface única, limpa e responsiva.

---

## 🛠️ Arquitetura e Tecnologias

O projeto adota uma arquitetura separada (Decoupled), dividida em três camadas principais:

1.  **Coleta de Dados (Web Scraping):** Scripts em **Python** utilizando `BeautifulSoup4` e `Requests` para varrer páginas HTML específicas da universidade, filtrar ruídos (menus e rodapés) e extrair dados estruturados.
2.  **Armazenamento (Banco de Dados):** **MongoDB** (NoSQL). Escolhido pela flexibilidade na inserção de documentos com esquemas variáveis (ex: editais da PRAE vs. PROEX). A integração é feita via `PyMongo`.
3.  **Disponibilização (API e Interface):**
    * **Back-end:** Uma API RESTful construída com **FastAPI**, servindo os dados em formato JSON.
    * **Front-end:** Interface estática desenvolvida com **HTML, CSS e Vanilla JavaScript** (fetch API), consumindo os dados do back-end de forma assíncrona.

---

## 🚀 Como Executar o Projeto Localmente

Siga os passos abaixo para rodar a aplicação em sua máquina.

### Pré-requisitos
* [Python 3.11](https://www.python.org/downloads/)
* [MongoDB Community Server](https://www.mongodb.com/try/download/community) rodando localmente (porta 27017).

### Passo 1: Clonar e Instalar Dependências
Abra o terminal, clone o repositório e instale as bibliotecas necessárias. É altamente recomendado o uso de um ambiente virtual (`venv`).

```bash
git clone [https://github.com/PatoDesoxigenado/TechHub---WebScrapping-de-Editais-para-Alunos.git](https://github.com/PatoDesoxigenado/TechHub---WebScrapping-de-Editais-para-Alunos.git)
cd TechHub---WebScrapping-de-Editais-para-Alunos

# Criar e ativar ambiente virtual (Windows)
python -m venv venv
venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

### Passo 2: Popular o Banco de Dados (Web Scraping)
Entre na pasta do backend e execute os scripts para buscar os editais nos portais da UERN:

```bash
cd backend
python scraper_prae.py
python scraper_proex.py

# Suba o servidor
fastapi dev main.py

A API estará rodando em http://localhost:8000. 
Você pode testar os endpoints interativamente acessando http://localhost:8000/docs.