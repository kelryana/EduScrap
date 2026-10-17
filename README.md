# EduScrap UERN – Plataforma de Oportunidades Acadêmicas

<div align="center">

![EduScrap](https://img.shields.io/badge/EduScrap-UERN-FF5C00?style=for-the-badge&logo=mortarboard&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-7.0+-47A248?style=for-the-badge&logo=mongodb&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![UML](https://img.shields.io/badge/UML%20v1.3-100%25%20Conforme-brightgreen?style=for-the-badge)
![MFA](https://img.shields.io/badge/MFA-TOTP%20pyotp-orange?style=for-the-badge)
![WCAG](https://img.shields.io/badge/WCAG%202.1-AA%20Conforme-green?style=for-the-badge)
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