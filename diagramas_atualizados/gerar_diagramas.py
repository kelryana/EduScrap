import os
import subprocess

DIAGRAMS_DIR = "/home/ana/projetos/EduScrap/diagramas_atualizados"
os.makedirs(DIAGRAMS_DIR, exist_ok=True)

# ==============================================================================
# 1. PLANTUML SOURCES
# ==============================================================================

puml_01 = """@startuml CasosDeUso_EduScrap_Atualizado
left to right direction
skinparam packageStyle rectangle
skinparam backgroundColor #FFFFFF
skinparam defaultFontName "Arial"
skinparam actor {
    BorderColor #003366
    BackgroundColor #E6F0FA
}
skinparam usecase {
    BorderColor #2B6CB0
    BackgroundColor #F7FAFC
    BorderThickness 1.5
}

actor "Estudante\\n(Discente UERN/UFERSA)" as est
actor "Administrador /\\nDesenvolvedor" as adm

rectangle "Sistema EduScrap (Dashboard & Backend)" {
    
    usecase "UC01: Consultar Feed de Oportunidades" as UC_Feed
    usecase "UC02: Pesquisar por Palavra-Chave\\n(Busca Textual em Tempo Real)" as UC_Busca
    usecase "UC03: Filtrar por Área e Curso\\n(Seletor Dinâmico de Graduação)" as UC_Cursos
    usecase "UC04: Filtrar por Fonte Oficial\\n(PRAE, PROEX, UFERSA, CIEE, UERN)" as UC_Fontes
    usecase "UC05: Monitorar Prazos e Vigência\\n(Painel com Gráfico Donut)" as UC_Donut
    usecase "UC06: Favoritar / Salvar Oportunidade" as UC_Fav
    usecase "UC07: Visualizar Edital Oficial / Detalhes" as UC_Detalhes
    usecase "UC08: Alternar Tema Visual\\n(Modo Claro / Modo Escuro)" as UC_Theme
    usecase "UC09: Autenticar-se / Cadastrar Perfil" as UC_Auth
    
    usecase "UC10: Disparar Coleta Concorrente\\n(Paralela Multi-Worker)" as UC_RunScraper
    usecase "UC11: Monitorar Logs Isolados por Robô\\n(logs/<fonte>.log)" as UC_Logs
    usecase "UC12: Gerenciar Regras de Extração e URLs" as UC_Regras
    usecase "UC13: Consultar Documentação da API\\n(Swagger / OpenAPI /docs)" as UC_Swagger
}

' Relações Estudante
est --> UC_Feed
est --> UC_Theme
est --> UC_Auth

' Extensões do Feed
UC_Busca .> UC_Feed : <<extend>>
UC_Cursos .> UC_Feed : <<extend>>
UC_Fontes .> UC_Feed : <<extend>>
UC_Donut .> UC_Feed : <<extend>>
UC_Fav .> UC_Feed : <<extend>>
UC_Detalhes .> UC_Feed : <<extend>>

' Relações Administrador / DevOps
adm --> UC_RunScraper
adm --> UC_Logs
adm --> UC_Regras
adm --> UC_Swagger

@enduml
"""

puml_02 = """@startuml DiagramaClasses_EduScrap_Software
skinparam classAttributeIconSize 0
skinparam packageStyle frame
skinparam backgroundColor #FFFFFF
skinparam defaultFontName "Arial"

package "API & Controllers (FastAPI)" {
    class FastAPIApplication {
        + app: FastAPI
        + router: APIRouter
        + listar_oportunidades(categoria, fonte, busca): List[OportunidadeModel]
        + listar_editais(status): List[OportunidadeModel]
        + listar_vagas(): List[OportunidadeModel]
        + listar_noticias(): List[OportunidadeModel]
        + obter_estatisticas_prazos(): EstatisticasPrazos
        + health_check(): dict
    }

    class OportunidadeModel <<Pydantic>> {
        + id: str
        + titulo: str
        + link: str
        + data_publicacao: datetime
        + data_limite: Optional[datetime]
        + status_vigencia: str
        + categoria: str
        + fonte: str
        + tags: List[str]
        + extra_info: dict
    }

    class EstatisticasPrazos <<Pydantic>> {
        + total: int
        + vigentes: int
        + encerrados: int
        + sem_prazo: int
        + percentual_vigentes: float
    }
}

package "Engine de Scraping Concorrente" {
    class ScraperRunner {
        - FONTES_DISPONIVEIS: List[str]
        - max_workers: int
        + executar_paralelo(fontes_selecionadas: List[str]): void
        + executar_serial(): void
        + configurar_logger_isolado(nome_fonte: str): Logger
    }

    abstract class BaseScraper {
        # nome_fonte: str
        # url_base: str
        # logger: Logger
        + {abstract} coletar(): List[dict]
        + salvar_no_banco(oportunidades: List[dict]): int
        + limpar_texto(texto: str): str
    }

    class ScraperPRAE {
        + coletar(): List[dict]
        + extrair_editais_permanencia(): void
    }

    class ScraperPortalUERN {
        - driver: WebDriver
        + coletar(): List[dict]
        + navegar_paginacao(): void
    }

    class ScraperUFERSA {
        + coletar(): List[dict]
    }

    class ScraperCIEE {
        - driver: WebDriver
        + coletar(): List[dict]
        + aplicar_filtro_mossoro(): void
    }
}

package "Processamento & Normalização" {
    class Normalizer {
        - PADROES_REGEX: dict
        + extrair_datas(texto: str): Optional[datetime]
        + validar_vigencia(data_limite: datetime): str
        + associar_curso_area(texto: str): List[str]
    }

    class PDFUtils {
        + extrair_texto_pdf(caminho_ou_bytes): str
        + ler_tabelas_jouern(pdf): List[str]
    }
}

package "Persistência (MongoDB)" {
    class MongoDatabase {
        - client: MongoClient
        - db: Database
        + oportunidades: Collection
        + database_setup(): void
        + criar_indices_busca(): void
        + upsert_oportunidade(filtro: dict, doc: dict): void
    }
}

' Relacionamentos
FastAPIApplication ..> OportunidadeModel : retorna
FastAPIApplication ..> EstatisticasPrazos : calcula
FastAPIApplication --> MongoDatabase : consulta

ScraperRunner --> BaseScraper : orquestra
BaseScraper <|-- ScraperPRAE
BaseScraper <|-- ScraperPortalUERN
BaseScraper <|-- ScraperUFERSA
BaseScraper <|-- ScraperCIEE

BaseScraper --> Normalizer : higieniza dados
BaseScraper --> MongoDatabase : persiste
Normalizer --> PDFUtils : processa PDFs

@enduml
"""

puml_03 = """@startuml Sequencia_Coleta_Paralela
autonumber
skinparam backgroundColor #FFFFFF
skinparam defaultFontName "Arial"

actor "Admin / Cron Job" as Admin
participant "ScraperRunner\\n[run_scrapers.py]" as Runner
participant "ThreadPoolExecutor\\n(Workers Paralelos)" as Pool
participant "ScraperPRAE\\n[Worker 1]" as PRAE
participant "ScraperCIEE\\n[Worker 2]" as CIEE
participant "Normalizer\\n[Regex + Validação]" as Norm
database "MongoDB\\n[hub_estudantes]" as DB
entity "File System\\n[logs/<fonte>.log]" as LogFile

Admin -> Runner: Executa "python run_scrapers.py"
activate Runner

Runner -> LogFile: Inicializa logs isolados para cada fonte
Runner -> Pool: Cria pool de threads concorrentes
activate Pool

par Execução Concorrente em Paralelo
    Pool -> PRAE: Inicia coleta PRAE / UERN
    activate PRAE
    PRAE -> PRAE: HTTP GET (Requests) + Parse BeautifulSoup
    PRAE -> Norm: Envia texto e PDFs brutos
    activate Norm
    Norm -> Norm: Executa Expressões Regulares (extrai prazos)
    Norm --> PRAE: Metadados normalizados
    deactivate Norm
    PRAE -> DB: bulkWrite / upsert na coleção "oportunidades"
    PRAE -> LogFile: Registra status em logs/prae.log
    PRAE --> Pool: 15 editais processados
    deactivate PRAE
else
    Pool -> CIEE: Inicia coleta CIEE (Vagas de Estágio)
    activate CIEE
    CIEE -> CIEE: Inicializa Firefox Headless (Selenium)
    CIEE -> CIEE: Interage com DOM dinâmico
    CIEE -> Norm: Envia dados de vagas extraídas
    activate Norm
    Norm -> Norm: Normaliza remuneração e área
    Norm --> CIEE: Vagas padronizadas
    deactivate Norm
    CIEE -> DB: bulkWrite / upsert na coleção "oportunidades"
    CIEE -> LogFile: Registra status em logs/ciee.log
    CIEE --> Pool: 8 vagas processadas
    deactivate CIEE
end

Pool --> Runner: Todas as threads concluídas
deactivate Pool

Runner --> Admin: Relatório final: Sucesso em paralelo
deactivate Runner
@enduml
"""

puml_04 = """@startuml Sequencia_Consulta_Donut
autonumber
skinparam backgroundColor #FFFFFF
skinparam defaultFontName "Arial"

actor "Estudante" as User
boundary "Frontend SPA\\n[Dashboard Web]" as UI
control "API REST\\n[FastAPI / Uvicorn]" as API
database "MongoDB\\n[oportunidades]" as DB
participant "DonutRenderer\\n[SVG Chart Engine]" as Donut

User -> UI: Acessa Dashboard ou seleciona Área / Curso
activate UI

UI -> API: GET /api/oportunidades?categoria=tecnologia
activate API

API -> DB: find({ categoria: "tecnologia" }).sort({ data_limite: 1 })
activate DB
DB --> API: Retorna documentos JSON estruturados
deactivate DB

API --> UI: HTTP 200 OK [JSON com editais e metadados]
deactivate API

UI -> UI: Itera sobre lista de oportunidades\\n(calcula vigentes vs. encerrados)

UI -> Donut: renderizarGraficoDonut(vigentes, encerrados, total)
activate Donut
Donut -> Donut: Calcula porcentagens e arcos SVG
Donut --> UI: Insere gráfico Donut interativo no DOM
deactivate Donut

UI -> UI: Renderiza cards responsivos com badges de status
UI --> User: Exibe tela atualizada em menos de 1 segundo!
deactivate UI
@enduml
"""

puml_05 = """@startuml Implantacao_EduScrap_Real
skinparam node {
    BorderColor #2B6CB0
    BackgroundColor #F7FAFC
}
skinparam component {
    BorderColor #333333
    BackgroundColor #FFFFFF
}

node "Dispositivo do Discente / Usuário" as ClientNode {
    artifact "Navegador Web\\n[Chrome / Firefox / Edge]" as Browser
}

node "Servidor Local / Nuvem Linux (Host EduScrap)" as ServerNode {
    
    node "Processo Frontend (Porta 3000)" {
        component "Servidor Web HTTP\\n[Vanilla JS + CSS3 + SVG]" as WebServer
    }

    node "Processo Backend (Porta 8000)" {
        component "FastAPI Framework\\n[ASGI Uvicorn Server]" as ApiServer
        component "OpenAPI / Swagger\\n[/docs Interativo]" as Swagger
    }
    
    node "Processo em Background (Batch)" {
        component "Orquestrador Concorrente\\n[run_scrapers.py]" as Runner
        component "Módulos de Scraping\\n[Requests + Selenium Headless]" as Scrapers
    }
    
    folder "Armazenamento Local" {
        file "logs/*.log\\n(Logs isolados por robô)" as Logs
        file "config/*.json\\n(Mapeamento de Cursos)" as Configs
    }
}

node "Servidor de Banco de Dados" as DBNode {
    database "MongoDB 7.0 (Porta 27017)\\n[Database: hub_estudantes]" as Mongo {
        collections "oportunidades"
        collections "usuarios"
    }
}

cloud "Fontes Externas (Internet)" as ExternalCloud {
    component "Portais Institucionais UERN" as UernSites
    component "Diários Oficiais (JOUERN)" as Jouern
    component "Portal UFERSA" as Ufersa
    component "Plataforma CIEE" as Ciee
}

' Comunicações
Browser --> WebServer : HTTP / GET :3000
Browser --> ApiServer : REST / JSON :8000
ApiServer --> Mongo : TCP / Driver PyMongo :27017
ApiServer ..> Swagger : Disponibiliza documentação

Runner --> Scrapers : Dispara threads paralelas
Scrapers --> ExternalCloud : Web Scraping (HTTP/HTTPS)
Scrapers --> Mongo : Persiste dados normalizados
Scrapers --> Logs : Grava execuções e erros
Scrapers ..> Configs : Lê mapeamento de áreas
@enduml
"""

puml_06 = """@startuml Componentes_EduScrap_Modular
skinparam componentStyle uml2
skinparam backgroundColor #FFFFFF

package "Frontend SPA" {
    [UI Controller & Router] as UI_Ctrl
    [Theme Switcher (Dark/Light)] as Theme_Mod
    [Donut Chart Engine (SVG)] as Donut_Mod
    [Filter & Search Engine] as Filter_Mod
}

package "Backend REST API (FastAPI)" {
    [API Router & Endpoints] as Router_Mod
    [Pydantic Models & Schemas] as Schema_Mod
    [CORS & Security Middleware] as Sec_Mod
}

package "Engine de Ingestão & Processamento" {
    [Scraper Orchestrator] as Orch_Mod
    [Static Scrapers (BS4)] as Static_Mod
    [Dynamic Scrapers (Selenium)] as Dyn_Mod
    [Normalizer & Regex Engine] as Regex_Mod
    [PDF Processing (pdfplumber)] as PDF_Mod
}

package "Camada de Dados (MongoDB)" {
    [Database Connection Pool] as DB_Pool
    [Schema Validation & Indexes] as DB_Index
    database "MongoDB Cluster" as DB_Inst
}

cloud "Fontes Externas" as Ext_Sources

' Ligações Frontend
UI_Ctrl --> Filter_Mod
UI_Ctrl --> Donut_Mod
UI_Ctrl --> Theme_Mod
UI_Ctrl --> Router_Mod : HTTP / JSON (Porta 8000)

' Ligações Backend
Router_Mod --> Sec_Mod
Router_Mod --> Schema_Mod
Router_Mod --> DB_Pool : Consultas de leitura

' Ligações Ingestão
Orch_Mod --> Static_Mod
Orch_Mod --> Dyn_Mod
Static_Mod --> Regex_Mod
Dyn_Mod --> Regex_Mod
Regex_Mod --> PDF_Mod
Static_Mod --> Ext_Sources : Requisições HTTP
Dyn_Mod --> Ext_Sources : Automação Headless

Regex_Mod --> DB_Pool : Gravação de oportunidades
DB_Pool --> DB_Index
DB_Index --> DB_Inst
@enduml
"""

puml_07 = """@startuml Estados_Edital_EduScrap
skinparam backgroundColor #FFFFFF
skinparam state {
    BorderColor #2B6CB0
    BackgroundColor #F7FAFC
}

[*] --> Descoberto : Robô localiza URL na fonte

Descoberto --> EmExtracao : Download do HTML / PDF
EmExtracao --> EmNormalizacao : Texto enviado ao motor Regex

state EmNormalizacao {
    [*] --> AnalisandoTexto
    AnalisandoTexto --> ExtraindoDatas : Regex identifica padrões
    ExtraindoDatas --> ValidandoVigencia : Compara Data Limite vs Data Atual
}

EmNormalizacao --> Invalido : Erro de parse / PDF corrompido
EmNormalizacao --> AbertoVigente : Data Limite >= Data Atual
EmNormalizacao --> Encerrado : Data Limite < Data Atual

state AbertoVigente {
    [*] --> InscricoesAbertas
    InscricoesAbertas --> AlertaPrazoCritico : Faltando <= 3 dias
}

AbertoVigente --> Encerrado : Relógio do sistema ultrapassa Data Limite

Invalido --> [*] : Registrado em logs/erro.log
Encerrado --> [*] : Arquivado no histórico de oportunidades
@enduml
"""

# Salvar todos os arquivos .puml
with open(os.path.join(DIAGRAMS_DIR, "diagrama_01_casos_de_uso.puml"), "w") as f:
    f.write(puml_01)
with open(os.path.join(DIAGRAMS_DIR, "diagrama_02_classes_software.puml"), "w") as f:
    f.write(puml_02)
with open(os.path.join(DIAGRAMS_DIR, "diagrama_03_sequencia_coleta_paralela.puml"), "w") as f:
    f.write(puml_03)
with open(os.path.join(DIAGRAMS_DIR, "diagrama_04_sequencia_consulta_donut.puml"), "w") as f:
    f.write(puml_04)
with open(os.path.join(DIAGRAMS_DIR, "diagrama_05_implantacao_arquitetura.puml"), "w") as f:
    f.write(puml_05)
with open(os.path.join(DIAGRAMS_DIR, "diagrama_06_componentes_sistema.puml"), "w") as f:
    f.write(puml_06)
with open(os.path.join(DIAGRAMS_DIR, "diagrama_07_estados_edital.puml"), "w") as f:
    f.write(puml_07)

print("Fontes .puml salvos com sucesso!")
