# Relatório Técnico Completo — EduScrap (TechHub UERN)

> Documento **gerado automaticamente** pelo script `tools/gerar_relatorio.py`, a partir da análise estática do código-fonte do repositório (AST do Python, regex sobre JS/HTML, leitura dos diagramas PlantUML, requirements, configs e Git).
> Data de geração: **08/10/2026 06:58** · Raiz analisada: `/home/ana/projetos/EduScrap`

---

## Sumário

1. [Visão Geral e Intuito](#1-visão-geral-e-intuito)
2. [Stack Tecnológica](#2-stack-tecnológica)
3. [Arquitetura do Sistema](#3-arquitetura-do-sistema)
4. [Estrutura de Pastas e Métricas](#4-estrutura-de-pastas-e-métricas)
5. [Camada de Coleta (Web Scraping)](#5-camada-de-coleta-web-scraping)
6. [Camada de Normalização (Pipeline de Dados)](#6-camada-de-normalização-pipeline-de-dados)
7. [Camada de Persistência (MongoDB)](#7-camada-de-persistência-mongodb)
8. [Camada de API (FastAPI e Flask)](#8-camada-de-api-fastapi-e-flask)
9. [Frontend (Dashboard)](#9-frontend-dashboard)
10. [Configurações Externas (JSON)](#10-configurações-externas-json)
11. [Diagramas de Arquitetura](#11-diagramas-de-arquitetura)
12. [Ferramentas e Infraestrutura](#12-ferramentas-e-infraestrutura)
13. [Testes Automatizados](#13-testes-automatizados)
14. [Fluxo Ponta a Ponta](#14-fluxo-ponta-a-ponta)
15. [Decisões de Projeto e Riscos](#15-decisões-de-projeto-e-riscos)
16. [Como Executar](#16-como-executar)
17. [Conclusão](#17-conclusão)

---

## 1. Visão Geral e Intuito

O **EduScrap** (também chamado de *TechHub UERN*) é uma plataforma de **agregação automatizada de oportunidades acadêmicas e profissionais** voltada a estudantes da **UERN (Universidade do Estado do Rio Grande do Norte)** — com foco em Mossoró e região — e de instituições vizinhas como a **UFERSA**.

**Problema que resolve:** editais de estágio, bolsa, PNAES, monitoria, residência e processos seletivos são publicados espalhados em diversos portais institucionais (PRAE, PROEX, Portal UERN, UFERSA, CIEE), muitas vezes protegidos por Cloudflare e com prazos curtos. O estudante precisa visitar vários sites manualmente e frequentemente perde inscrições.

**Solução implementada (verificada no código):**
- **Robôs de coleta (scrapers)** independentes por fonte, com técnicas distintas (HTTP estático, Selenium headless anti-detecção, mineração de texto com palavras-chave);
- **Normalização heurística**: extração de datas por regex, deduplicação via `upsert`, vinculação de metadados da instituição (`fonte_id`) e cálculo de vigência;
- 🗄️ Armazenamento **NoSQL (MongoDB)** com índices de texto, índices compostos e validação por JSON Schema;
- **API REST** (FastAPI como principal + variante Flask modular em `backend/api/`) com paginação, filtro de vigentes, busca unificada, estatísticas e auditoria do banco;
- **Frontend estático** (HTML/CSS/JS puro, tema *Memphis Design*) que consome a API e exibe cards, dashboard analítico e um *inspector* de infraestrutura.

### Funcionalidades declaradas no README
- Web scraping automatizado multi-fonte;
- Monitoramento de notícias/editais com atualização automática;
- API moderna com CORS; dashboard responsivo; filtragem inteligente por área (Tecnologia, Saúde, Humanas, Exatas, Direito, Comunicação).

---

## 2. Stack Tecnológica

### 2.1 Dependências declaradas (`requirements.txt`)

| Pacote | Versão mínima | Papel no projeto |
|---|---|---|
| `requests` | `>=2.31.0` | Cliente HTTP síncrono para coleta de páginas estáticas (HTML) dos portais. |
| `beautifulsoup4` | `>=4.12.0` | Parser de HTML/XML; transforma o corpo das respostas em árvore navegável (BeautifulSoup) para extração de editais. |
| `selenium` | `>=4.15.0` | Automação de navegador real (Chrome/Firefox headless) para contornar proteção Cloudflare e páginas dinâmicas (Portal UERN, CIEE). |
| `pdfplumber` | `>=0.10.0` | Extração precisa de texto e tabelas de PDFs (editais/Diário Oficial) na esteira de normalização. |
| `PyPDF2` | `>=3.0.0` | Leitura/manipulação leve de PDFs (metadados e divisão de páginas) como alternativa ao pdfplumber. |
| `lxml` | `>=4.9.0` | Backend de parser rápido usado pelo BeautifulSoup para documentos grandes. |
| `fastapi` | `>=0.109.1` | Framework web assíncrono moderno que serve a API principal (backend/main.py) com documentação Swagger automática. |
| `uvicorn` | `>=0.20.0` | Servidor ASGI que executa a aplicação FastAPI (porta 8000). |
| `flask` | `>=3.0.0` | Microframework usado pela segunda interface REST (backend/api/app.py), baseada em Blueprints. |
| `flask-cors` | `>=4.0.0` | Extensão Flask que habilita CORS para as rotas /api/* consumidas pelo frontend. |
| `pymongo` | `>=4.5.0` | Driver oficial MongoDB — persistência de vagas, editais, notícias, fontes e logs de auditoria. |
| `schedule` | `>=1.2.0` | Agendador leve em Python (Scheduler) para varreduras periódicas e atualização de status. |
| `python-dotenv` | `>=1.0.0` | Carregamento de variáveis de ambiente (.env), ex.: MONGODB_URI. |
| `logging` | `>=0.4.9` | Registro estruturado de eventos dos scrapers (console + arquivos .log). |

### 2.2 Bibliotecas detectadas no código além do requirements
| Módulo | Onde é usado | Observação |
|---|---|---|
| `webdriver-manager` | `scraper_ciee.py`, `scraper_portal_uern.py` | ⚠️ Importado mas **não listado no requirements.txt** |
| `pdfminer.six` | `pdf_utils.py` | ⚠️ Usado com *graceful degradation*; **ausente no requirements.txt** |
| `pytest` | `tests/test_regex.py`, `tests/test_scraper.py` | ⚠️ Framework de teste não pinned no requirements |

### 2.3 Stack de apresentação
- **Frontend:** JavaScript puro (349 linhas), CSS autoral (694 linhas) e HTML (102 linhas); única dependência externa: `https://unpkg.com/@phosphor-icons/web` para ícones.
- **Paleta de design (variáveis CSS):** `--azul-escuro` `#09184D`, `--azul-claro` `#79D3E6`, `--laranja` `#F27A18`, `--fundo` `#FFFFFF`, `--branco` `#FFFFFF`, `--verde-forte` `#2E8B57`, `--purpura` `#9C27B0`

### 2.4 Banco e infraestrutura
- **MongoDB 4.4+** (standalone local, `mongodb://localhost:27017/`, database `hub_estudantes`);
- Diagramas modelados em **PlantUML** com biblioteca **C4-PlantUML**;
- Versionamento **Git** (branch atual: `main`).

---

## 3. Arquitetura do Sistema

O sistema segue uma **arquitetura em camadas orientada a pipeline de dados**, coerente com os diagramas C4 encontrados em `diagrams/`:

```text
┌─────────────────────────────────────────────────────────────────────┐
│ FONTES EXTERNAS   PRAE · PROEX · Portal UERN · UFERSA · CIEE · G1…   │
└───────────────┬─────────────────────────────────────────────────────┘
               │ HTTP/HTML · PDF · Navegador automatizado (Selenium)
┌───────────────▼───────────────┐     ┌──────────────────────────────┐
│  ENGINE DE COLETA (scrapers)  │────▶│ NORMALIZADOR                 │
│  requests+bs4 / selenium      │     │ RegexEngine → DataValidator  │
│  pdf_utils (pdfminer)         │     │ → JSONBuilder → Scheduler    │
└───────────────┬───────────────┘     └──────────────┬───────────────┘
                │ upsert (deduplicação)              │ schema v1.0
┌───────────────▼─────────────────────────────────────▼──────────────┐
│                     MONGODB  (banco: hub_estudantes)               │
│  vagas_estagio · vagas_bolsa · vagas_ufersa · vagas_ciee ·         │
│  vagas_portal_uern · vagas_noticias · fontes_provedores ·          │
│  historico_varreduras · controle_cache · editais/vagas/noticias    │
└───────────────┬────────────────────────────────────────────────────┘
                │ PyMongo
┌───────────────▼───────────────────────────┐
│ API REST  (FastAPI :8000 / Flask :5000)   │
│ paginação · vigência · busca $text · stats│
└───────────────┬───────────────────────────┘
                │ fetch()/JSON + CORS
┌───────────────▼───────────────────────────┐
│ FRONTEND ESTÁTICO (dashboard Memphis)     │
└───────────────────────────────────────────┘
```

### Princípios arquitetônicos observados no código
1. **Desacoplamento por fonte**: cada portal tem seu scraper independente — a queda de um não derruba os demais (try/except isolado por fonte em `scraper_noticias.py`).
2. **Produção e consumo assíncronos** (ver `diagrama_sequencia`): o scraping acontece em segundo plano (*fire-and-forget*); o usuário consulta dados **já normalizados** no banco, garantindo resposta rápida (< 2s).
3. **Abordagem híbrida NoSQL com referência manual**: a coleção `fontes_provedores` guarda a governança (nome oficial, URL, frequência, foco); os documentos de vaga carregam apenas `fonte_id`, e o join lógico é resolvido em runtime por `resolver_vinculo_fonte()` — equivalente a um *DBRef* leve.
4. **Idempotência**: scrapers gravam com `update_one(..., upsert=True)` chaveado por `link`/`codigo`/`nome`, evitando duplicatas em reexecuções.
5. **Cache TTL embutido**: `/api/noticias` só re-raspa se `controle_cache` indicar mais de 10 minutos desde a última execução.
6. **Auditoria**: toda *Varredura Global* grava em `historico_varreduras` duração, status, erro e contagem de documentos por coleção.
7. **Dualidade de APIs**: existe uma API FastAPI monolítica madura (`backend/main.py`, consumida pelo frontend) e uma API Flask modular experimental (`backend/api/` + `backend/src/normalizer/`) que opera sobre coleções padronizadas (`editais`, `vagas`, `noticias`).

---

## 4. Estrutura de Pastas e Métricas

```text
EduScrap-UERN/
├── backend/
│   ├── main.py                  # API FastAPI principal
│   ├── database_setup.py        # Índices + JSON Schema do MongoDB
│   ├── pdf_utils.py             # Extração de datas/PDF com cache
│   ├── scraper_*.py             # Robôs de coleta por fonte
│   ├── check_portal.sh          # Watchdog do portal UERN (loop curl)
│   ├── testar_uern.py           # Protótipo de análise de relevância
│   ├── api/                     # API alternativa Flask (app factory + blueprint)
│   └── src/normalizer/          # Esteira de normalização modular
│       ├── collectors/          # html_scraper, pdf_scraper, scheduler
│       ├── regex_engine.py      # Extração de datas/editais/valores/status
│       ├── validator.py         # Regras de vigência (Aberto/Urgente/Encerrado)
│       ├── json_builder.py      # Schema JSON v1.0 padronizado
│       └── database.py          # MongoDBHandler (CRUD + índices + update_status)
├── frontend/                    # Dashboard estático (index.html, script.js, style.css)
├── config/                      # course_mapping.json, patterns.json
├── diagrams/                    # Diagramas PlantUML/C4
├── tests/                       # Suítes pytest (regex, scraper)
├── tools/gerar_relatorio.py     # Este gerador de relatório
├── requirements.txt
└── README.md / LICENSE / .gitignore
```

### Métricas calculadas do repositório

- Arquivos de código/documentação analisados: **32**
- Linhas totais: **6.719**

| Tipo | Linhas |
|---|---|
| `.py` | 4.768 |
| `.css` | 694 |
| `.md` | 550 |
| `.js` | 349 |
| `(sem extensão)` | 169 |
| `.html` | 102 |
| `.json` | 66 |
| `.sh` | 21 |

### Principais módulos Python (extraídos via AST)

| Arquivo | Linhas | Classes | Funções de módulo |
|---|---|---|---|
| `gerar_relatorio.py` | 1121 | — | 17 função(ões) |
| `backend/scraper_ciee.py` | 527 | `ScraperCIEEHibrido` | 1 função(ões) |
| `backend/main.py` | 474 | — | 14 função(ões) |
| `backend/pdf_utils.py` | 335 | — | 10 função(ões) |
| `backend/scraper_portal_uern.py` | 269 | — | 5 função(ões) |
| `backend/src/normalizer/database.py` | 265 | — | — |
| `backend/src/normalizer/json_builder.py` | 198 | — | — |
| `backend/api/routes.py` | 197 | — | — |
| `backend/src/normalizer/regex_engine.py` | 158 | `RegexEngine` | — |
| `backend/src/normalizer/validator.py` | 150 | `DataValidator` | — |
| `backend/scraper_prae.py` | 115 | — | 3 função(ões) |
| `backend/scraper_proex.py` | 115 | — | 3 função(ões) |
| `backend/src/normalizer/collectors/scheduler.py` | 114 | `Scheduler` | — |
| `backend/scraper_ufersa.py` | 107 | — | 3 função(ões) |

**Git:** branch `main` · 62 commit(s) · autores: 52	Ana Kelry ·      9	PatoDesoxigenado · último: fe1c022 — Update project title in README.md (Ana Kelry, 2026-09-02)

---

## 5. Camada de Coleta (Web Scraping)

Cada scraper é um script autônomo executável (`python scraper_x.py`) que conecta ao MongoDB, raspa sua fonte e grava documentos no formato `{nome, link, categoria, fonte[, data_vencimento]}`.

### `scraper_ciee.py` — CIEE  (527 linhas)
**Foco:** Estágio comercial e Jovem Aprendiz (Mossoró)  
**Técnicas:** Selenium (navegador headless), webdriver-manager, upsert idempotente (deduplicação)  
**Coleção de destino:** `vagas_ciee`  
**URLs raspadas:** https://portal.ciee.org.br/ · https://portal.ciee.org.br/quero-uma-vaga/?codigoVaga={codigo_vaga}

### `scraper_noticias.py` — G1 / Canaltech  (81 linhas)
**Foco:** Notícias de tecnologia (feed agregado)  
**Técnicas:** BeautifulSoup, requests, limpeza prévia da coleção  
**Coleção de destino:** —  
**URLs raspadas:** https://canaltech.com.br · https://canaltech.com.br/ultimas/ · https://g1.globo.com/tecnologia/

### `scraper_portal_uern.py` — Portal UERN  (269 linhas)
**Foco:** Text mining de notícias relevantes (anti-Cloudflare)  
**Técnicas:** Selenium (navegador headless), webdriver-manager, BeautifulSoup, limpeza prévia da coleção  
**Coleção de destino:** `vagas_portal_uern`  
**URLs raspadas:** https://portal.uern.br/todas-as-noticias/

### `scraper_prae.py` — PRAE/UERN  (115 linhas)
**Foco:** Estágios acadêmicos, residência e auxílios  
**Técnicas:** BeautifulSoup, requests, upsert idempotente (deduplicação)  
**Coleção de destino:** `vagas_estagio`  
**URLs raspadas:** https://portal.uern.br/prae/2026-2/

### `scraper_proex.py` — PROEX/UERN  (115 linhas)
**Foco:** Bolsas de extensão, cultura e pesquisa  
**Técnicas:** BeautifulSoup, requests, upsert idempotente (deduplicação)  
**Coleção de destino:** `vagas_bolsa`  
**URLs raspadas:** https://portal.uern.br/proex/2026-2/

### `scraper_ufersa.py` — UFERSA  (107 linhas)
**Foco:** Editais de assistência estudantil e concursos  
**Técnicas:** BeautifulSoup, requests, upsert idempotente (deduplicação)  
**Coleção de destino:** `vagas_ufersa`  
**URLs raspadas:** https://proae.ufersa.edu.br/2026-2/

### Destaques técnicos identificados
- **Anti-Cloudflare / stealth** (`scraper_portal_uern.py`): Chrome `--headless=new`, user-agent falso, remoção de `navigator.webdriver` via CDP e espera do challenge; após carregar, aplica **análise de relevância por palavras-chave** (estágio, bolsa, edital, PNAES, monitoria…) antes de salvar em `vagas_portal_uern`.
- **Scraper híbrido CIEE** (`scraper_ciee.py`, classe `ScraperCIEEHibrido`): Firefox + GeckoDriver gerenciado pelo webdriver-manager, filtra pela cidade *Mossoró*, captura os cards por XPath (`Ver detalhes`/`Compartilhar`), salva com deduplicação por `codigo`, gera relatório de execução em log estruturado e screenshot em caso de falha.
- **Heurística de data** repetida nos scrapers simples: regex `dd/mm/aaaa` e variantes `dd-mm-aaaa`; sem prazo detectado, o documento fica sem `data_vencimento` (a API trata como vigência desconhecida).
- **Agregador de notícias** (`scraper_noticias.py`): limpa a coleção e insere ~10 itens de G1 Tecnologia e Canaltech, com isolamento de falha por fonte.
- **Utilitário PDF** (`pdf_utils.py`): download com cache em memória limitado a 50 PDFs, extração via pdfminer (até 10 páginas), regex multiformato de datas e **estratégia híbrida HTML→PDF** (`extrair_data_vencimento_hibrido`) para prazos que só existem dentro do PDF do edital.
- **Watchdog shell** (`check_portal.sh`): loop `curl` a cada 60s até o portal voltar ao ar (HTTP 200); então dispara os scrapers PRAE/PROEX automaticamente.

---

## 6. Camada de Normalização (Pipeline de Dados)

Localizada em `backend/src/normalizer/`, é a materialização do componente *Normalizador* do diagrama de componentes C4. Pipeline: **Coletor → RegexEngine → DataValidator → JSONBuilder → MongoDBHandler**, orquestrado periodicamente pelo `Scheduler`.

### ⚙️ `backend/src/normalizer/collectors/html_scraper.py` (58 linhas)
- **Classe `HTMLScraper`**:
  - Métodos: `__init__`, `fetch_page`, `parse_html`, `scrape`, `close`

### ⚙️ `backend/src/normalizer/collectors/pdf_scraper.py` (95 linhas)
- **Classe `PDFScraper`**:
  - Métodos: `__init__`, `extract_text_from_file`, `extract_text_from_url`, `extract_tables`, `extract_metadata`

### ⚙️ `backend/src/normalizer/collectors/scheduler.py` (114 linhas)
- **Classe `Scheduler`**:
  - Métodos: `__init__`, `add_task`, `_run_tasks`, `setup_schedule`, `run_once`, `run_continuous`, `stop`, `get_interval_from_env`

### ⚙️ `backend/src/normalizer/database.py` (265 linhas)

### ⚙️ `backend/src/normalizer/json_builder.py` (198 linhas)

### ⚙️ `backend/src/normalizer/regex_engine.py` (158 linhas)
- **Classe `RegexEngine`**:
  - Métodos: `__init__`, `_load_default_patterns`, `_load_custom_patterns`, `_compile_all`, `extract_dates`, `extract_edital_number`, `extract_title`, `extract_currency_values`, `detect_status`, `extract_all`

### ⚙️ `backend/src/normalizer/validator.py` (150 linhas)
- **Classe `DataValidator`**:
  - Métodos: `__init__`, `parse_date_string`, `validate_deadline`, `validate_required_fields`, `validate_edital`

### Regras de negócio codificadas
- **Status por vigência** (`DataValidator.validate_deadline`): `dias < 0 → Encerrado`, `= 0 → Encerra Hoje`, `≤ 3 → Urgente`, `senão → Aberto`;
- **Atualização em massa** (`MongoDBHandler.update_status`): marca `Encerrado`/`Aberto` comparando `data_limite` com hoje, pulando documentos já corretos;
- **Schema JSON v1.0** (`JSONBuilder`): campos obrigatórios `tipo, titulo, fonte, url` + carimbos `criado_em`/`atualizado_em` e `validate_schema()`;
- **Regex padrão** (idêntica a `config/patterns.json`): datas BR por extenso, numéricas e ISO; número de edital `Edital n° NN/AAAA`; valores monetários; keywords de status;
- **Scheduler**: executa tarefas a cada N horas (padrão 6h) **e** diariamente às 03:00 (horário de baixa demanda), sempre atualizando o status antes de coletar.

---

## 7. Camada de Persistência (MongoDB)

- **Host/URI:** `mongodb://localhost:27017/` (sobrescritível via `MONGODB_URI` no handler do normalizador);
- **Database:** `hub_estudantes`;
- **Timeouts de conexão** (MongoDBHandler): serverSelection 5s, socket 45s, connect 20s.

### Coleções detectadas no código

| Coleção | Propósito |
|---|---|
| `controle_cache` | Carimbo de tempo da última execução de cada robô (controle de cache TTL). |
| `editais` | Coleção padronizada da esteira de normalização (src/normalizer/database.py). |
| `fontes_provedores` | Governança/metadados das instituições (nome oficial, URL, frequência, foco). |
| `historico_varreduras` | Log de auditoria de cada 'Varredura Global' (duração, status, contagens). |
| `noticias` | Coleção padronizada da esteira de normalização (src/normalizer/database.py). |
| `ollectio` | Coleção auxiliar identificada no código. |
| `vagas` | Coleção padronizada da esteira de normalização (src/normalizer/database.py). |
| `vagas_bolsa` | Editais de bolsas de extensão coletados da PROEX/UERN. |
| `vagas_ciee` | Vagas de estágio e Jovem Aprendiz do CIEE (Mossoró), via Selenium. |
| `vagas_estagio` | Editais de estágio acadêmico coletados da PRAE/UERN. |
| `vagas_noticias` | Notícias tech agregadas (G1, Canaltech) — refresh a cada 10 min. |
| `vagas_portal_uern` | Notícias do Portal UERN filtradas por mineração de palavras-chave (text mining). |
| `vagas_ufersa` | Editais de assistência estudantil/concursos da UFERSA. |

### Otimizações aplicadas por `database_setup.py`
1. **Índice de texto** `idx_busca_nome_text` sobre `nome` nas coleções principais → alimenta a busca `$text` de `/api/pesquisar`;
2. **Índice composto** `idx_categoria_fonte` (`categoria`+`fonte`) → acelera os filtros combinados do dashboard;
3. **Validador JSON Schema** (`validationAction: warn`) em `vagas_noticias`: exige `nome`, `link` (pattern `^https?://`), `fonte` e `categoria`;
4. Índices adicionais do normalizador: `idx_status` e `idx_status_areas_composto` na coleção `editais`.

### Modelo de documento típico (scrapers legados)
```json
{
  "nome": "Edital 012/2026 - Programa de Monitoria",
  "link": "https://portal.uern.br/prae/.../edital-012.pdf",
  "categoria": "Monitoria",
  "fonte": "PRAE/UERN",
  "data_vencimento": "2026-10-30T00:00:00Z",
  "fonte_id": "prae_uern"
}
```

Documento enriquecido retornado pela API inclui `data_vencimento_formatada` (`dd/mm/aaaa`) e `meta_fonte` (nome oficial, URL e frequência do portal).

---

## 8. Camada de API (FastAPI e Flask)

### 8.1 API principal — FastAPI (`backend/main.py`, porta 8000) — 11 endpoints

Swagger/openAPI automático em `http://localhost:8000/docs`. CORS liberado (`allow_origins=["*"]`). Na subida do servidor, `garantir_metadados_fontes()` faz upsert das fontes mestre em `fontes_provedores`.

| Método | Endpoint | Função | Parâmetros | Descrição |
|---|---|---|---|---|
| GET | `/` | `raiz` | — | Raiz — mensagem de boas-vindas e pointer para /docs. |
| GET | `/api/estagios` | `listar_estagios` | pagina, ge | Lista paginada de estágios (PRAE) com filtro de vigência. |
| GET | `/api/bolsas` | `listar_bolsas` | pagina, ge | Lista paginada de bolsas (PROEX) com filtro de vigência. |
| GET | `/api/ufersa` | `listar_ufersa` | pagina, ge | Lista paginada de editais da UFERSA. |
| GET | `/api/ciee` | `listar_ciee` | pagina, ge | Lista paginada de vagas do CIEE (normaliza campo 'nome'). |
| GET | `/api/portal_uern` | `listar_portal_uern` | pagina, ge | Lista paginada de notícias mineradas do Portal UERN. |
| GET | `/api/noticias` | `listar_noticias` | pagina, ge | Notícias tech com cache TTL de 10 minutos (dispara scraper se expirado). |
| GET | `/api/pesquisar` | `pesquisar_unificado` | termo, min_length | Pesquisa unificada $text (fallback $regex) em todas as coleções. |
| GET | `/api/estatisticas` | `obter_estatisticas` | — | Dashboard analítico: totais, reta final (7 dias) e distribuição por categoria. |
| GET | `/api/db-status` | `obter_status_do_banco` | — | Auditoria física do MongoDB: documentos, KB, índices e validadores por coleção. |
| GET | `/api/buscar-tudo` | `acionar_todos_os_robos` | — | Orquestra TODOS os robôs de coleta + normalização heurística + log de auditoria. |

Padrão de resposta paginada: `{pagina_atual, limite_por_pagina, total_documentos, dados[]}`.

### 8.2 API alternativa — Flask (`backend/api/`, porta 5000) — 5 endpoints

Factory pattern (`create_app`) + Blueprint `api_routes` com prefixo `/api`, resposta JSON padrão `{success, count|error, data}`, **fallback gracioso (HTTP 503)** quando o MongoDB está indisponível e error handlers para 404/500.

| Método | Endpoint | Função | Origem | Descrição |
|---|---|---|---|---|
| GET | `/api/oportunidades` | `get_oportunidades` | routes.py (Blueprint) | Lista oportunidades (editais+vagas) com filtros area/status/tipo. |
| GET | `/api/editais` | `get_editais` | routes.py (Blueprint) | Lista editais normalizados com filtros status/fonte. |
| GET | `/api/vagas` | `get_vagas` | routes.py (Blueprint) | Lista vagas com filtros area/fonte. |
| GET | `/api/noticias` | `get_noticias` | routes.py (Blueprint) | Lista notícias com filtro por categoria. |
| GET | `/api/oportunidades/<int:id>` | `get_oportunidade_by_id` | routes.py (Blueprint) | Busca uma oportunidade por ID em editais/vagas/noticias. |

---

## 9. Frontend (Dashboard)

- **Título da página:** *TechHub UERN - Dashboard de Oportunidades*
- **Alvo da API:** `const API_URL = "http://localhost:8000/api"`;
- **Endpoints consumidos:** /buscar-tudo, /db-status, /estatisticas, /pesquisar;
- **Funções JavaScript:** `toggleFiltroVigentes`, `carregarDados`, `renderizarControlesPaginacao`, `realizarPesquisa`, `carregarEstatisticas`, `renderizarCards`, `carregarInspector`, `acionarTodosOsRobos`.

### Navegação (botões detectados no HTML)

| Elemento | Rótulo | Ação |
|---|---|---|
| `#btn-pesquisar` | Buscar | realizarPesquisa() — busca unificada ($text) |
| `#btn-buscar-tudo` |  | acionarTodosOsRobos() — dispara a Varredura Global (/api/buscar-tudo) |
| `#btn-estagios` | Estágios (PRAE) | carregarDados('estagios') — aba Estágios (PRAE) |
| `#btn-bolsas` | Bolsas (PROEX) | carregarDados('bolsas') — aba Bolsas (PROEX) |
| `#btn-ufersa` | Editais (UFERSA) | carregarDados('ufersa') — aba Editais (UFERSA) |
| `#btn-ciee` | Vagas (CIEE) | carregarDados('ciee') — aba Vagas (CIEE) |
| `#btn-portal_uern` | Portal UERN | carregarDados('portal_uern') — aba Portal UERN |
| `#btn-noticias` | Notícias Tech | carregarDados('noticias') — aba Notícias Tech |
| `#btn-analises` | Indicadores | carregarEstatisticas() — dashboard de indicadores |

### Comportamentos verificados em `script.js`
- Paginação dinâmica calculada a partir de `total_documentos`/`limite_por_pagina`;
- Checkbox **filtroVigentes** adiciona `&apenas_vigentes=true` às requisições (filtro `data_vencimento >= now` no backend);
- Cards exibem a **badge “ Inscrições até dd/mm/aaaa”** quando há `data_vencimento_formatada` (ou seja, quando a regex do backend detectou prazo);
- O link da fonte usa `meta_fonte.url_oficial` com tooltip mostrando o portal mestre e o ciclo do robô (frequência de monitoramento);
- **Indicadores** (`/api/estatisticas`): contadores por fonte, alerta de *reta final* (prazos ≤ 7 dias) e distribuição por categoria PRAE;
- **Inspector de infraestrutura** (`/api/db-status`): nº de documentos, alocação em KB, badges de índices e selo *VALIDADOR ATIVO* por coleção;
- Tratamento de erro amigável: *“Erro ao conectar com a API. O FastAPI está rodando?”*.

### Estilo
- Tema visual **Memphis Design**: formas geométricas absolutas (rosca laranja, zigue-zague, triângulos listrados, cruzes), sombras duras `box-shadow: Npx Npx 0 cor`, bordas grossas e grade de fundo desenhada com gradientes lineares em `body::before`;
- Tipografia `Segoe UI/Tahoma/Verdana`; grid responsivo `.grid-vagas` (`repeat(auto-fit, minmax(...))`) e animações de entrada (`surgimento`).

---

## 10. Configurações Externas (JSON)

### `config/course_mapping.json`
- Define **6 áreas** de conhecimento: Tecnologia, Saúde, Humanas, Exatas, Direito, Comunicação;
- Mapeia **25 cursos** de graduação às áreas (ex.: Tecnologia → Ciência da Computação, Sistemas de Informação, Engenharia de Software, Ciência de Dados, TI);
- Bloco `keywords` por área presente: **True** (heurística de classificação textual).

### `config/patterns.json`
- Espelha os padrões compilados de `RegexEngine`: grupos ['dates', 'edital', 'status_keywords'];
- Permite evoluir regras de extração **sem tocar no código** (injeção via `RegexEngine(patterns_path=...)`).

### Variáveis de ambiente suportadas (README + código)
```dotenv
MONGODB_URI=mongodb://localhost:27017/
DATABASE_NAME=hub_estudantes
DEBUG=True
SECRET_KEY=...
API_HOST=0.0.0.0            # Flask
FLASK_PORT=5000             # Flask
FLASK_ENV=production|development
```

---

## 11. Diagramas de Arquitetura

6 artefatos **PlantUML** (incluindo a stdlib **C4-PlantUML**) documentam o sistema em níveis crescentes de detalhe — Container → Componentes → Sequência:

### `componente_diagrama.jpeg` — componente_diagrama.jpeg

### `container_diagrama.jpeg` — container_diagrama.jpeg

### `diagrama_componentes` — Detalhamento Interno: Normalizador de Dados
*Nível Componente: detalhamento interno do Normalizador (Leitor de PDF → Motor Regex → Validador → Construtor JSON, com fallback opcional de NLP/spaCy e base de padrões por fonte).*

**Elementos nomeados:** Leitor de PDF; Motor Regex; Módulo NLP; Validador de Regras; Construtor JSON; Base de Padrões

| Componente | Para | Mensagem |
|---|---|---|
| `pdf_reader` | `regex_engine` | Texto Bruto |
| `regex_engine` | `regex_db` | Consulta Padrões |
| `regex_engine` | `validator` | Dados Extraídos |
| `regex_engine` | `nlp_module` | Fallback |
| `nlp_module` | `validator` | Dados Enriquecidos |
| `validator` | `json_builder` | Dados Validados |

### `diagrama_container` — EduScrap - Arquitetura de Containers
*Nível Container: visão macro da plataforma EduScrap, seus containers (Engine de Coleta, Normalizador, Serviço de Alertas, API REST, MongoDB, Redis) e sistemas externos (portais, JOUERN, CIEE).*

**Elementos nomeados:** Administrador; Estudante; Portais UERN/UFERSA; JOUERN; CIEE & Outros; Plataforma EduScrap; Engine de Coleta; Normalizador; Serviço de Alertas; API REST; MongoDB; Redis Cache
**Atores humanos detectados:** 4 (Administrador, Estudante)

| Origem | Destino | Interação |
|---|---|---|
| `engine` | `portais` | Web scraping[HTTP/HTML] |
| `engine` | `jouern` | Download[HTTP/PDF] |
| `engine` | `ciee` | Integração[REST/JSON] |
| `engine` | `normalizador` | Raw data[Message Queue] |
| `normalizador` | `alertas` | Novas vagas[Event] |
| `normalizador` | `mongodb` | Persistência[Insert/Update] |
| `api` | `mongodb` | CRUD[MongoDB] |
| `api` | `redis` | Cache[Redis] |
| `admin` | `api` | Configura[HTTPS] |
| `estudante` | `api` | Busca/filtra[HTTPS] |
| `alertas` | `estudante` | Alertas[SMTP] |

### `diagrama_sequencia` — Sequência: Coleta Assíncrona e Consulta do Usuário
*Sequência temporal: Fase 1 (coleta assíncrona disparada por Cron, fire-and-forget, persistência no MongoDB) e Fase 2 (consulta do estudante via API REST com query filtrada — o usuário nunca espera o scraping).*


| Origem | Destino | Interação |
|---|---|---|
| `Cron` | `Scraper` | Job Enfileirado |
| `Scraper` | `Scraper` | Pronto para próxima tarefa |
| `DB` | `Norm` | Ack (Confirmação de Escrita) |
| `DB` | `API` | Retorna Lista JSON (Dados Normalizados) |
| `API` | `Stud` | Exibe Feed Instantâneo (< 2s) |

### `sequencia_diagrama.jpeg` — sequencia_diagrama.jpeg

**Nota de governança do diagrama de componentes:** a *Regra de Vigência* (Data Extraída vs Data Atual → `Aberto`/`Encerrado`) está formalizada tanto no modelo quanto no código (`validator.py` e `database.update_status`).

> Para renderizar: instale o PlantUML e rode `plantuml diagrams/diagrama_container` (ou use o plugin PlantUML da IDE). O diagrama de componentes importa a lib remota C4-PlantUML, exigindo internet na primeira renderização.

---

## 12. Ferramentas e Infraestrutura

- Shell scripts de monitoramento: backend/check_portal.sh
- Git com `.gitignore` robusto (ignora venv, dumps do MongoDB, logs, screenshots *.png/*.html gerados pelos scrapers)
- pip gerenciando dependências via `requirements.txt` (versionamento mínimo `>=`)
- pytest (suítes em `tests/`) + smoke test manual (`teste.py`)
- PlantUML + biblioteca C4-PlantUML (modelagem de arquitetura em `diagrams/`)
- MongoDB local (mongosh / MongoDB Compass para inspeção do banco `hub_estudantes`)
- Documentação viva da API: Swagger UI e ReDoc geradas pelo FastAPI

### Scripts operacionais disponíveis

| Comando | Efeito |
|---|---|
| `uvicorn main:app --reload --host 0.0.0.0 --port 8000` | Sobe a API FastAPI (a partir de `backend/`) |
| `python database_setup.py` | Cria índices e aplica JSON Schema no MongoDB |
| `python scraper_prae.py` (idem proex/ufersa/ciee/noticias/portal_uern) | Executa um robô específico |
| `bash check_portal.sh` | Watchdog: aguarda o portal voltar e roda PRAE+PROEX |
| `python -m http.server 3000` (em `frontend/`) | Serve o dashboard |
| `pytest` (em `tests/`) | Roda as suítes unitárias |
| `GET /api/buscar-tudo` | Aciona todos os robôs pela API + normalização + auditoria |
| `python tools/gerar_relatorio.py` | Regenera este relatório técnico |

---

## 13. Testes Automatizados

### `test_regex.py`
- Suite **TestRegexEngine** (6 casos):
  - `test_extract_edital_number`
  - `test_extract_date_br_numeric`
  - `test_extract_date_br_full`
  - `test_detect_status_open`
  - `test_detect_status_closed`
  - `test_extract_currency`
- Suite **TestDataValidator** (4 casos):
  - `test_parse_date_numeric`
  - `test_parse_date_full`
  - `test_validate_deadline_future`
  - `test_validate_deadline_past`

### `test_scraper.py`
- Suite **TestHTMLScraper** (2 casos):
  - `test_scraper_initialization`
  - `test_parse_html_basic`
- Suite **TestPDFScraper** (1 casos):
  - `test_scraper_initialization`

**Total: 13 casos de teste**, cobrindo: extração regex de datas numéricas e por extenso, número de edital, detecção de status (Aberto/Encerrado), valores monetários, parsing de datas do validador, cálculo de deadline futuro/passado e o parser de seletores CSS do `HTMLScraper`. Existe também o smoke test manual `teste.py` (inserção de documento de exemplo no MongoDB).

> ⚠️ Os testes fazem `sys.path.insert(0, <raiz>/src)`, mas os módulos vivem em `backend/src/...` — ajuste o path (ou execute `pytest` com `PYTHONPATH=backend`) para que as importações resolvam.

---

## 14. Fluxo Ponta a Ponta (como uma vaga chega à tela)

1. **Gatilho** — agendamento (Scheduler: a cada 6h e às 03:00), `check_portal.sh`, botão global `/api/buscar-tudo` ou CLI manual;
2. **Coleta** — o scraper acessa o portal (requests/Selenium), isola os links de editais (`<li>` cujo texto inicia com “edital”, fora de nav/footer) e resolve os PDFs anexos;
3. **Enriquecimento** — regex extrai `data_vencimento` do título/categoria; quando o prazo só existe no PDF, `pdf_utils.extrair_data_vencimento_hibrido` baixa e varre o documento (cache de até 50 PDFs);
4. **Persistência** — `update_one(chave, {"$set": ...}, upsert=True)` grava sem duplicar; a varredura global ainda injeta `fonte_id` em todos os documentos (migração heurística) e registra a auditoria em `historico_varreduras`;
5. **Exposição** — a FastAPI pagina, formata datas, resolve `meta_fonte` via join lógico e filtra vigentes (`data_vencimento >= now`);
6. **Consumo** — o dashboard renderiza cards com badge de prazo, link oficial da fonte e indicadores (totais, reta final de 7 dias, distribuição por categoria);
7. **Transparência** — `/api/db-status` expõe a saúde física das coleções (documentos, KB, índices, validadores) no modo *Inspector*.

---

## 15. Decisões de Projeto e Riscos

### Decisões conscientes
- **Sem ORM / sem framework frontend**: máxima leveza e controle (vanilla JS + PyMongo cru);
- **Upsert como estratégia de deduplicação** — simples e suficiente para o volume regional;
- **Cache TTL no próprio banco** (`controle_cache`) em vez de Redis — coerente com o escopo (Redis aparece nos diagramas como evolução planejada);
- **Validação `warn` em vez de `strict`** no JSON Schema — não quebra ingestões antigas;
- **Duas APIs conviviendo**: FastAPI para produção imediata; Flask + `src/normalizer` como arquitetura-alvo modular (visível nos diagramas C4).

### Riscos / dívidas técnicas identificados automaticamente
1. **Dependências implícitas**: `webdriver-manager`, `pdfminer.six` e `pytest` são importados no código mas faltam no `requirements.txt`;
2. **Segurança**: CORS `allow_origins=["*"]` + endpoint `buscar-tudo` via GET que apaga e re-raspa coleções inteiras (`delete_many`) — proteger (POST + autenticação) antes de publicar fora de localhost;
3. **Configuração hardcoded**: URI do Mongo e caminhos de chromedriver (`/usr/local/bin/chromedriver`) fixos em vários scrapers — migrar para `.env`/webdriver-manager;
4. **Acoplamento a layouts de terceiros**: seletores CSS/XPath de G1, Canaltech, CIEE e portais UERN quebram quando os sites mudarem (mitigar com testes de contrato);
5. **Paths dos testes incorretos** (ver §13) — a suíte pode falhar por ImportError;
6. **Frontend aponta para `localhost:8000`** — externalizar `API_URL` para deploy;
7. **Artefatos binários na árvore de trabalho**: `backend/__pycache__/*.pyc` presentes — o `.gitignore` cobre `__pycache__/`; recomenda-se `git rm -r --cached backend/__pycache__`.

---

## 16. Como Executar (resumo operacional)

```bash
# 0) Pré-requisitos: Python 3.8+, MongoDB 4.4+ rodando em localhost:27017
python -m venv venv && source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install pdfminer.six webdriver-manager pytest   # complementos detectados

cd backend
python database_setup.py                 # 1) índices + validadores
uvicorn main:app --reload --port 8000    # 2) API FastAPI
python scraper_prae.py                   # 3) coleta (ou GET /api/buscar-tudo)

cd ../frontend
python -m http.server 3000               # 4) dashboard em http://localhost:3000
```

Docs interativos da API: `http://localhost:8000/docs` (Swagger) e `/redoc`.

---

## 17. Conclusão

O EduScrap demonstra. com **6.719 linhas** distribuídas em 32 arquivos. um pipeline ETL completo e funcional — *Extract* (6 scrapers multi-técnica). *Transform* (motor regex. validador de vigência e schema JSON v1.0) e *Load* (MongoDB indexado e auditado) — servido por API REST documentada e consumido por um dashboard autoexplicativo. O diferencial do projeto é a **resiliência pragmática**: fallbacks em cascata (HTML→PDF. `$text`→`$regex`. live-scrape→cache TTL. strict→warn) que mantêm o serviço útil mesmo com portais instáveis ou protegidos por anti-bot. Como próximos passos naturais: fechar as lacunas de dependências/paths apontadas em §15. autenticar a varredura global e promover a esteira modular (`src/normalizer`) a caminho principal. conforme projetado nos diagramas C4.

---

*Fim do relatório — rerode `python tools/gerar_relatorio.py` sempre que o código mudar para manter este documento sincronizado com a realidade do repositório.*