# EduScrap UERN – Plataforma de Oportunidades Acadêmicas

<div align="center">

![EduScrap](https://img.shields.io/badge/EduScrap-UERN-FF5C00?style=for-the-badge&logo=mortarboard&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-7.0+-47A248?style=for-the-badge&logo=mongodb&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Pytest](https://img.shields.io/badge/Pytest-68%20Passed-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)
![UML](https://img.shields.io/badge/UML%20v1.3-100%25%20Conforme-brightgreen?style=for-the-badge)
![Licença](https://img.shields.io/badge/Licen%C3%A7a-MIT-yellow?style=for-the-badge)

<img width="1782" height="980" alt="Dashboard EduScrap" src="https://github.com/user-attachments/assets/0b8f6859-3fc3-409b-8c11-96956ca0a8de" />
<img width="1213" height="843" alt="Donut de Prazos e Vigência" src="https://github.com/user-attachments/assets/ec12ce21-4f4c-4302-ba32-57673db64070" />
<img width="1134" height="900" alt="Filtros e Cursos" src="https://github.com/user-attachments/assets/6a988c1f-3b23-441d-afd6-5c6e6767c731" />

<p align="center">
  <strong>Hub centralizado de mineração, curadoria e monitoramento de editais, bolsas, estágios e notícias acadêmicas para o ecossistema universitário potiguar.</strong>
</p>

</div>

---

## Sobre o Projeto

O **EduScrap** é uma plataforma completa desenvolvida no âmbito do Departamento de Informática (DI) da **Universidade do Estado do Rio Grande do Norte (UERN)**. O projeto adota o **Processo Unificado** e a **Modelagem Orientada a Objetos com UML (v1.3)** para resolver a dispersão de informações acadêmicas institucionais.

### A Problemática
No ambiente universitário regional, informações vitais para a permanência e formação discente encontram-se fragmentadas em múltiplos portais institucionais desarticulados (Jornal Oficial JOUERN em PDFs volumosos, sites da PRAE e PROEX, portais de faculdades isoladas, diários municipais, portais da UFERSA e plataformas corporativas como o CIEE). Essa descentralização provoca perda crônica de prazos regulamentares e impede que estudantes tenham acesso igualitário a bolsas e estágios.

### A Solução
O **EduScrap** resolve essa dor ao atuar como um agregador e minerador automatizado:
1. **Web Scraping Paralelo Concorrente:** Robôs orientados a objetos (`BaseScraper`) orquestrados via `ThreadPoolExecutor` (`ScraperRunner`);
2. **Normalização Textual & Leitura de PDFs:** Parsing híbrido com Expressões Regulares (`RegexEngine`) e `pdfplumber`/`pdfminer` para extração de prazos, categorias e valores;
3. **Persistência NoSQL Indexada:** Cluster **MongoDB 7.0** encapsulado pela classe `MongoDatabase` com índices textuais compostos e busca instantânea;
4. **API RESTful Assíncrona:** Backend de alta performance com **FastAPI**, modelos tipados com **Pydantic** (`OportunidadeModel`), documentação Swagger interativa e latência sub-segundo (RNF01);
5. **Dashboard SPA Moderno:** Interface visual com Tema Claro/Escuro (`theme.js`), gráfico Donut interativo em SVG, seletores por curso e **Painel Administrativo de Governança Técnica**.

---

##  Funcionalidades Principais

- ⚡ **Web Scraping Concorrente Multi-Worker (`run_scrapers.py`):** Coleta paralela em múltiplas fontes com isolamento de logs individuais por robô em `logs/<fonte>.log`.
-  **Validação Temporal Automática de Prazos (RN01 a RN03):** Cálculo dinâmico comparando a data do servidor com os prazos de inscrição, gerando badges de alerta para prazos críticos ($\le$ 3 dias) e marcação de certames vencidos.
-  **Painel Analítico com Gráfico Donut (UC05):** Visualização interativa em SVG que renderiza em tempo real a proporção de editais abertos, vencendo em até 7 dias e encerrados.
-  **Filtro Inteligente por Áreas e Cursos (UC03):** Seletor dinâmico baseado em `config/course_mapping.json` contemplando 15 cursos e áreas temáticas (Tecnologia, Saúde, Humanas, Exatas, etc.).
-  **Feed Unificado e Busca Textual (UC01 / UC02 / Figura 4):** Endpoint consolidado `GET /api/oportunidades` para busca por palavra-chave, categoria, fonte e vigência.
-  **Modo Escuro (Dark Mode) Nativo (UC08):** Alternância instantânea de tema sem recarregar a página, com persistência no `localStorage` e troca de logo.
-  **Área do Estudante e Favoritos (UC06 / UC09):** Cadastro com termo de consentimento LGPD, autenticação com hash criptográfico (PBKDF2/SHA256) e gerenciamento de favoritos.
-  **Painel Administrativo de Governança Técnica (UC11 / UC12 / RF12):** Interface web (`admin.html`) para monitoramento de logs de robôs e ajuste de URLs e expressões de extração (`patterns.json`) em tempo de execução sem recompilar, com proteção contra SSRF.
-  **Portabilidade Total com Docker (RNF08 / Seção 12):** Empacotamento completo com `Dockerfile.backend`, `Dockerfile.frontend` e `docker-compose.yml`.

---

## Arquitetura do Sistema

```mermaid
flowchart TD
    subgraph Fontes ["Fontes Oficiais Externas"]
        UERN["Portal UERN / JOUERN"]
        PRAE["PRAE - Estágios e Auxílios"]
        PROEX["PROEX - Bolsas e Projetos"]
        UFERSA["Portal Editais UFERSA"]
        CIEE["Plataforma CIEE"]
        OUTRAS["MPRN / IFRN / IEL / DOM"]
    end

    subgraph Ingestao ["Engine de Ingestão Concorrente - POO"]
        Runner["ScraperRunner - ThreadPoolExecutor"]
        Scrapers["Scrapers Concretos - herdam BaseScraper"]
        Norm["Normalizer - RegexEngine + PDF Extraction"]
    end

    subgraph Dados ["Camada de Persistência - NoSQL"]
        Mongo[("MongoDB 7.0 - hub_estudantes")]
        Logs["Logs Isolados por Robô"]
        Config["Regras Dinâmicas - patterns.json"]
    end

    subgraph Servicos ["Backend API - FastAPI"]
        FastAPI["FastAPI porta 8000\nEndpoints REST e Swagger /docs\nModels Pydantic - OportunidadeModel"]
    end

    subgraph Cliente ["Camada de Apresentação - Frontend"]
        SPA["Dashboard Discente porta 3000\nDonut SVG + Filtros + Dark Mode"]
        AdminUI["Painel de Governança admin.html\nGestão de Regras e Monitor de Logs"]
        User(["Estudante / Administrador"])
    end

    Fontes -->|Download HTML e PDF| Scrapers
    Runner --> Scrapers
    Scrapers --> Norm
    Config -.->|Leitura e Ajuste de Regras| Norm
    Norm -->|Upsert pelo Link Canônico - RN04| Mongo
    Scrapers -->|Gravação Isolada de Logs - UC11| Logs
    Mongo -->|Consultas Indexadas sub-segundo| FastAPI
    FastAPI -->|JSON REST| SPA
    FastAPI -->|APIs de Governança - UC12| AdminUI
    User <--> SPA
    User <--> AdminUI
```

---

## ⚡ Como Rodar o Projeto

Você pode iniciar o EduScrap de duas formas:

### Opção A: Via Docker Compose (Recomendado)

Sobe todos os serviços (MongoDB 7.0, API FastAPI e Frontend) em containers isolados:

```bash
docker compose up --build -d
```

Para verificar o status dos containers:
```bash
docker compose ps
```

Para parar os serviços:
```bash
docker compose down
```

---

### Opção B: Inicialização Local em 1 Comando (`start.sh`)

Garante a inicialização do MongoDB local, configuração dos índices de busca e execução paralela do Backend e Frontend:

```bash
./start.sh
```

> **Dica:** Você também pode utilizar o `Makefile`:
> ```bash
> make run
> ```

---

### URLs da Aplicação:

| Recurso | URL | Descrição |
| :--- | :--- | :--- |
| **Portal do Estudante** | [http://localhost:3000](http://localhost:3000) | Dashboard interativo, feed, Donut chart e modo escuro |
| **Painel de Governança** | [http://localhost:3000/admin.html](http://localhost:3000/admin.html) | Monitor de logs e editor de regras de extração (UC11/UC12) |
| **API Backend** | [http://localhost:8000](http://localhost:8000) | Servidor FastAPI sob Uvicorn |
| **Documentação Interativa (Swagger)** | [http://localhost:8000/docs](http://localhost:8000/docs) | Testador interativo de endpoints e esquemas OpenAPI |
| **Documentação Alternativa (ReDoc)** | [http://localhost:8000/redoc](http://localhost:8000/redoc) | Documentação formal da API REST |

---

## Coleta de Dados (Web Scraping Paralelo Concorrente)

O orquestrador `ScraperRunner` em `run_scrapers.py` dispara as varreduras em threads paralelas sem degradar a API:

```bash
# Executa todas as fontes em paralelo multi-worker (Recomendado):
python run_scrapers.py
# ou:
make scrape

# Executa apenas fontes específicas (ex.: PRAE e PROEX):
python run_scrapers.py prae proex

# Executa em modo sequencial:
python run_scrapers.py --serial
```

### Fontes Integradas:
| Chave | Nome da Fonte | Implementação POO | Coleção no Banco |
| :--- | :--- | :--- | :--- |
| `prae` | PRAE/UERN (Estágios e Auxílios) | `ScraperPRAE` (BaseScraper) | `vagas_estagio` |
| `proex` | PROEX/UERN (Bolsas e Projetos) | `ScraperPROEX` (BaseScraper) | `vagas_bolsa` |
| `ufersa` | UFERSA (Editais de Assistência) | `ScraperUFERSA` (BaseScraper) | `vagas_ufersa` |
| `ciee` | CIEE (Estágios Comerciais Mossoró) | `ScraperCIEEHibrido` | `vagas_ciee` |
| `portal_uern` | Portal Central UERN | Mineração textual e paginação | `vagas_portal_uern` |
| `noticias` | Notícias Tech & Inovação | Feed RSS / Mineração HTML | `vagas_noticias` |
| `cpps_ufersa` | CPPS UFERSA | Processos seletivos acadêmicos | `editais` |
| `assecom_ufersa` | ASSECOM UFERSA | Comunicados oficiais | `noticias` |
| `mprn` | MPRN | Estágios e residência jurídica | `vagas` |
| `iel_rn` | IEL/RN | Vagas corporativas e estágios | `vagas` |
| `ifrn` | IFRN | Processos seletivos e bolsas | `editais` |
| `dom_mossoro` | DOM Mossoró | Editais municipais oficiais | `editais` |

---

## Referência da API RESTful (FastAPI)

### Oportunidades & Editais
| Método | Endpoint | Parâmetros Principais | Descrição |
|:---:|:---|:---|:---|
| `GET` | `/` | — | Status da API e versão do EduScrap |
| `GET` | `/api/oportunidades` | `categoria`, `fonte`, `busca`, `apenas_vigentes`, `pagina`, `limite` | **Feed unificado e consolidado** com filtros e ordenação temporal (Figura 4) |
| `GET` | `/api/estagios` | `pagina`, `limite`, `apenas_vigentes` | Oportunidades de estágio |
| `GET` | `/api/bolsas` | `pagina`, `limite`, `apenas_vigentes` | Bolsas e auxílios acadêmicos |
| `GET` | `/api/ufersa` | `pagina`, `limite`, `apenas_vigentes` | Editais da UFERSA |
| `GET` | `/api/ciee` | `pagina`, `limite`, `apenas_vigentes` | Vagas corporativas CIEE |
| `GET` | `/api/pesquisar` | `termo` | Busca textual por Regex/Text index |
| `GET` | `/api/estatisticas`| — | Métricas de prazos e vigência para o Gráfico Donut |

### Autenticação & Favoritos (Estudante)
| Método | Endpoint | Header / Payload | Descrição |
|:---:|:---|:---|:---|
| `POST`| `/api/auth/register` | `{ nome, email, senha, matricula, curso }` | Cadastro discente com aceite de termos |
| `POST`| `/api/auth/login` | `{ email, senha }` | Autenticação e geração de token JWT |
| `GET` | `/api/auth/me` | `Bearer <token>` | Perfil do usuário autenticado |
| `GET` | `/api/favoritos` | `Bearer <token>` | Listagem de favoritos do estudante |
| `POST`| `/api/favoritos/{id}` | `Bearer <token>` | Adiciona oportunidade aos favoritos |
| `DELETE`| `/api/favoritos/{id}`| `Bearer <token>` | Remove oportunidade dos favoritos |
| `GET` | `/api/feed/personalizado`| `Bearer <token>` | Feed customizado por cursos de interesse |

### Governança Técnica & Administração (UC11 / UC12)
| Método | Endpoint | Header / Payload | Descrição |
|:---:|:---|:---|:---|
| `GET` | `/api/admin/regras` | `X-API-Key` ou `Bearer <token>` | Consulta regras de extração do `patterns.json` |
| `PUT` | `/api/admin/regras` | JSON com novos seletores/padrões | Atualiza regras em tempo de execução sem recompilar |
| `GET` | `/api/admin/fontes` | `X-API-Key` ou `Bearer <token>` | Lista parâmetros e fontes ativas |
| `GET` | `/api/admin/logs` | `X-API-Key` ou `Bearer <token>` | Lista arquivos de log dos robôs |
| `GET` | `/api/admin/logs/{arquivo}`| `X-API-Key` ou `Bearer <token>` | Lê as últimas linhas do log do robô |

---

## Testes Automatizados (Pytest)

A suíte de testes contempla testes unitários, de integração com `mongomock`, testes de API e teste de desempenho (< 1s):

```bash
# Executar toda a suíte:
pytest -v
# ou:
make test
```

**Resultado:** `68 passed, 0 failed`.

---

## Estrutura do Repositório

```
EduScrap/
├── backend/
│   ├── base_scraper.py           # Classe abstrata BaseScraper (RNF05 / Figura 11)
│   ├── models.py                 # Modelos Pydantic de domínio (OportunidadeModel, etc.)
│   ├── mongo_database.py         # Classe MongoDatabase para persistência NoSQL
│   ├── main.py                   # API RESTful FastAPI (porta 8000)
│   ├── database_setup.py         # Criação de índices e validação de schema
│   ├── scraper_*.py              # Classes e scripts dos robôs de coleta
│   └── pdf_utils.py              # Extração de datas e prazos de PDFs oficiais
├── frontend/
│   ├── index.html                # Interface principal do estudante (Dashboard SPA)
│   ├── admin.html                # Painel de governança técnica (UC11 / UC12)
│   ├── login.html                # Autenticação e cadastro
│   ├── script.js                 # Lógica do Donut Chart, filtros e consumo da API
│   ├── theme.js                  # Controle dinâmico de Modo Claro e Escuro
│   └── style.css                 # Estilização com Tailwind e custom CSS
├── config/
│   ├── course_mapping.json       # Mapeamento oficial de 15 cursos e áreas
│   └── patterns.json             # Regras compiladas de Regex para extração
├── tests/
│   ├── test_fastapi_endpoints.py # Testes dos endpoints FastAPI e admin
│   ├── test_performance.py       # Teste de latência do feed < 1s (RNF01)
│   ├── test_auth_favoritos.py    # Testes de autenticação e favoritos
│   ├── test_database_mongomock.py# Testes de persistência NoSQL
│   ├── test_pdf_utils.py         # Testes de extração de PDF e vigência
│   ├── test_regex.py             # Testes do motor de expressões regulares
│   └── test_scraper.py           # Testes dos coletores HTML e PDF
├── Dockerfile.backend            # Container para a API FastAPI
├── Dockerfile.frontend           # Container para o Frontend SPA
├── docker-compose.yml            # Orquestração de MongoDB + Backend + Frontend
├── run_scrapers.py               # Orquestrador ScraperRunner multi-worker
├── start.sh                      # Script de inicialização automática local
├── Makefile                      # Atalhos úteis de desenvolvimento
├── requirements.txt              # Dependências Python
└── README.md                     # Este documento
```

---

## Equipe e Autoria

Projeto acadêmico desenvolvido para a **Universidade do Estado do Rio Grande do Norte (UERN)**:

  GitHub: [@kelryana](https://github.com/kelryana)
  GitHub: [@PatoDesoxigenado](https://github.com/PatoDesoxigenado)

---

## Licença

Distribuído sob os termos da licença **MIT**. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.
