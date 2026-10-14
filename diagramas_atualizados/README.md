# Diagramas Atualizados – EduScrap (Projeto Integrador)

Esta pasta contém o conjunto completo de diagramas arquiteturais e comportamentais atualizados do projeto **EduScrap**, refletindo fielmente a implementação real do software.

---

## 📁 Conteúdo da Pasta

Para cada diagrama, foram disponibilizados três formatos:
1. **`.png`**: Imagem renderizada em alta definição (pronta para uso em relatórios e apresentações);
2. **`.svg`**: Gráfico vetorial escalável (qualidade infinita e edição visual);
3. **`.puml`**: Código-fonte PlantUML (para versionamento e modificações futuras no PlantUML ou VS Code).

---

## 📊 Lista dos Diagramas Gerados

### 1. Diagrama de Casos de Uso (Atualizado)
- **Arquivos:** `diagrama_01_casos_de_uso.png`, `.svg`, `.puml`
- **O que modela:**
  - Atores: `Estudante` e `Administrador / DevOps`.
  - Casos de uso do Estudante: `UC01: Consultar Feed`, `UC02: Pesquisar por Palavra-Chave`, `UC03: Filtrar por Curso/Área`, `UC04: Filtrar por Fonte`, `UC05: Monitorar Prazos (Gráfico Donut)`, `UC06: Favoritar`, `UC07: Visualizar Edital`, `UC08: Alternar Tema (Dark/Light)`, `UC09: Autenticar-se`.
  - Casos de uso do Administrador: `UC10: Disparar Coleta Concorrente`, `UC11: Monitorar Logs Isolados`, `UC12: Gerenciar Regras/URLs`, `UC13: Consultar Swagger API`.

### 2. Diagrama de Classes de Software (Arquitetura Real)
- **Arquivos:** `diagrama_02_classes_software.png`, `.svg`, `.puml`
- **O que modela:**
  - Módulos da API FastAPI: `FastAPIApplication` (`backend/main.py`), modelos Pydantic `OportunidadeModel` e `EstatisticasPrazos`;
  - Engine de Coleta: `ScraperRunner` (`run_scrapers.py`), `BaseScraper`, e os scrapers concretos `ScraperPRAE`, `ScraperPortalUERN`, `ScraperUFERSA`, `ScraperCIEE`;
  - Processamento: `Normalizer` (Regex Engine) e `PDFUtils` (`pdfplumber` / `PyPDF2`);
  - Persistência: `MongoDatabase` (`backend/database_setup.py`).

### 3. Diagrama de Sequência: Coleta Concorrente Paralela
- **Arquivos:** `diagrama_03_sequencia_coleta_paralela.png`, `.svg`, `.puml`
- **O que modela:**
  - Disparo de `run_scrapers.py` pelo Admin/Cron;
  - Criação da `ThreadPoolExecutor` com workers concorrentes;
  - Extração simultânea em múltiplas fontes (PRAE via Requests/BS4, CIEE via Selenium Headless);
  - Normalização temporal com Expressões Regulares;
  - Persistência em lote no MongoDB (`hub_estudantes`) e isolamento de logs individuais em `logs/<fonte>.log`.

### 4. Diagrama de Sequência: Consulta Interativa e Donut Chart
- **Arquivos:** `diagrama_04_sequencia_consulta_donut.png`, `.svg`, `.puml`
- **O que modela:**
  - Interação do estudante no Frontend SPA selecionando filtros ou área acadêmica;
  - Requisição assíncrona `GET /api/oportunidades?categoria=...`;
  - Consulta indexada sub-segundo no MongoDB;
  - Retorno JSON e processamento local das datas de vigência;
  - Injeção dinâmica do gráfico de rosca (Donut Chart SVG) e renderização dos cards no DOM.

### 5. Diagrama de Implantação e Infraestrutura Real
- **Arquivos:** `diagrama_05_implantacao_arquitetura.png`, `.svg`, `.puml`
- **O que modela:**
  - `Dispositivo do Discente`: Navegador Web executando a SPA (:3000);
  - `Servidor Host Linux (EduScrap)`: Processo Web Frontend (:3000), Processo API FastAPI/Uvicorn (:8000), Processo Batch Concorrente (`run_scrapers.py`), Storage local (`logs/` e `config/`);
  - `Servidor MongoDB`: Cluster local/remoto (:27017) com coleções `oportunidades` e `usuarios`;
  - `Fontes Externas`: Portais UERN, PRAE, PROEX, JOUERN, UFERSA e CIEE.

### 6. Diagrama de Componentes do Sistema (Visão Modular)
- **Arquivos:** `diagrama_06_componentes_sistema.png`, `.svg`, `.puml`
- **O que modela:**
  - Arquitetura desacoplada em 4 camadas:
    1. *Camada de Apresentação:* UI Controller, Donut Chart Renderer, Filter & Search Engine, Theme Switcher;
    2. *Camada de Serviços:* API Routers, Pydantic Schemas, CORS & OpenAPI Docs;
    3. *Camada de Ingestão e Processamento:* Scraper Orchestrator, Scrapers Estáticos/Dinâmicos, Normalizer & PDF Engine;
    4. *Camada de Persistência:* MongoDB Connection Pool, Coleção Oportunidades e Database Setup.

### 7. Diagrama de Estados do Objeto Edital / Oportunidade
- **Arquivos:** `diagrama_07_estados_edital.png`, `.svg`, `.puml`
- **O que modela:**
  - Ciclo de vida: `Descoberto` ➔ `Em Extração (Download HTML/PDF)` ➔ `Em Normalização (Regex)` ➔ `Aberto / Vigente (Prazo ativo)` ➔ `Prazo Crítico (Alerta <= 3 dias)` ➔ `Encerrado (Expirado)` ou `Inválido / Erro de Leitura`.
