import os
import subprocess

OUT_DIR = "/home/ana/projetos/EduScrap/diagramas_atualizados"
os.makedirs(OUT_DIR, exist_ok=True)

svgs = {}

# ==============================================================================
# DIAGRAMA 1: CASOS DE USO ATUALIZADO
# ==============================================================================
svgs["diagrama_01_casos_de_uso"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 850" width="100%" height="100%">
  <defs>
    <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="2" dy="2" stdDeviation="3" flood-opacity="0.12"/>
    </filter>
    <marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#2B6CB0"/>
    </marker>
    <marker id="arrow-dash" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#718096"/>
    </marker>
  </defs>

  <rect width="1100" height="850" fill="#FFFFFF"/>
  <text x="550" y="38" font-family="Arial, sans-serif" font-size="20" font-weight="bold" fill="#003366" text-anchor="middle">
    Diagrama de Casos de Uso – Plataforma EduScrap (Atualizado)
  </text>
  <text x="550" y="58" font-family="Arial, sans-serif" font-size="12" fill="#718096" text-anchor="middle">
    Modelagem funcional completa incluindo: Busca Textual, Filtro de Cursos, Filtro por Fontes e Gráfico Donut de Prazos
  </text>

  <rect x="230" y="80" width="640" height="740" rx="12" fill="#F8FAFC" stroke="#CBD5E0" stroke-width="2" filter="url(#shadow)"/>
  <rect x="230" y="80" width="640" height="35" rx="12" fill="#EDF2F7"/>
  <text x="550" y="103" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="#2D3748" text-anchor="middle">
    Sistema EduScrap (Frontend SPA + API FastAPI)
  </text>

  <!-- ATOR: ESTUDANTE -->
  <g transform="translate(100, 360)">
    <circle cx="0" cy="-35" r="16" fill="#EBF8FF" stroke="#2B6CB0" stroke-width="2.5"/>
    <line x1="0" y1="-19" x2="0" y2="25" stroke="#2B6CB0" stroke-width="2.5"/>
    <line x1="-25" y1="-5" x2="25" y2="-5" stroke="#2B6CB0" stroke-width="2.5"/>
    <line x1="0" y1="25" x2="-20" y2="65" stroke="#2B6CB0" stroke-width="2.5"/>
    <line x1="0" y1="25" x2="20" y2="65" stroke="#2B6CB0" stroke-width="2.5"/>
    <text x="0" y="88" font-family="Arial, sans-serif" font-size="13" font-weight="bold" fill="#1A365D" text-anchor="middle">Estudante</text>
    <text x="0" y="104" font-family="Arial, sans-serif" font-size="10" fill="#4A5568" text-anchor="middle">(Discente UERN / UFERSA)</text>
  </g>

  <!-- ATOR: ADMINISTRADOR -->
  <g transform="translate(1000, 360)">
    <circle cx="0" cy="-35" r="16" fill="#FEFCBF" stroke="#D69E2E" stroke-width="2.5"/>
    <line x1="0" y1="-19" x2="0" y2="25" stroke="#D69E2E" stroke-width="2.5"/>
    <line x1="-25" y1="-5" x2="25" y2="-5" stroke="#D69E2E" stroke-width="2.5"/>
    <line x1="0" y1="25" x2="-20" y2="65" stroke="#D69E2E" stroke-width="2.5"/>
    <line x1="0" y1="25" x2="20" y2="65" stroke="#D69E2E" stroke-width="2.5"/>
    <text x="0" y="88" font-family="Arial, sans-serif" font-size="13" font-weight="bold" fill="#744210" text-anchor="middle">Administrador</text>
    <text x="0" y="104" font-family="Arial, sans-serif" font-size="10" fill="#4A5568" text-anchor="middle">(DevOps / Gestor)</text>
  </g>

  <!-- UC01 -->
  <g transform="translate(390, 230)">
    <ellipse cx="160" cy="0" rx="155" ry="32" fill="#EBF8FF" stroke="#3182CE" stroke-width="2.5" filter="url(#shadow)"/>
    <text x="160" y="-5" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#1A365D" text-anchor="middle">UC01: Consultar Feed de Oportunidades</text>
    <text x="160" y="14" font-family="Arial, sans-serif" font-size="10.5" fill="#4A5568" text-anchor="middle">(Visualização agregada de editais e vagas)</text>
  </g>
  <line x1="125" y1="360" x2="395" y2="235" stroke="#2B6CB0" stroke-width="2"/>

  <!-- UC02 -->
  <g transform="translate(250, 140)">
    <ellipse cx="120" cy="0" rx="115" ry="24" fill="#FFFFFF" stroke="#4A5568" stroke-width="1.5" stroke-dasharray="3,3"/>
    <text x="120" y="-3" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#2D3748" text-anchor="middle">UC02: Pesquisar por Palavra</text>
    <text x="120" y="12" font-family="Arial, sans-serif" font-size="9.5" fill="#718096" text-anchor="middle">(Busca instantânea em tempo real)</text>
  </g>
  <path d="M 370 140 L 470 200" fill="none" stroke="#718096" stroke-width="1.5" stroke-dasharray="4,4" marker-end="url(#arrow-dash)"/>
  <text x="440" y="165" font-family="Arial, sans-serif" font-size="10" fill="#4A5568">&lt;&lt;extend&gt;&gt;</text>

  <!-- UC03 -->
  <g transform="translate(630, 140)">
    <ellipse cx="120" cy="0" rx="115" ry="24" fill="#FFFFFF" stroke="#4A5568" stroke-width="1.5" stroke-dasharray="3,3"/>
    <text x="120" y="-3" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#2D3748" text-anchor="middle">UC03: Filtrar por Curso / Área</text>
    <text x="120" y="12" font-family="Arial, sans-serif" font-size="9.5" fill="#718096" text-anchor="middle">(Seletor dinâmico de graduação)</text>
  </g>
  <path d="M 730 164 L 620 205" fill="none" stroke="#718096" stroke-width="1.5" stroke-dasharray="4,4" marker-end="url(#arrow-dash)"/>
  <text x="680" y="195" font-family="Arial, sans-serif" font-size="10" fill="#4A5568">&lt;&lt;extend&gt;&gt;</text>

  <!-- UC04 -->
  <g transform="translate(250, 320)">
    <ellipse cx="120" cy="0" rx="115" ry="24" fill="#FFFFFF" stroke="#4A5568" stroke-width="1.5" stroke-dasharray="3,3"/>
    <text x="120" y="-3" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#2D3748" text-anchor="middle">UC04: Filtrar por Fonte Oficial</text>
    <text x="120" y="12" font-family="Arial, sans-serif" font-size="9.5" fill="#718096" text-anchor="middle">(PRAE, PROEX, UFERSA, CIEE, UERN)</text>
  </g>
  <path d="M 370 320 L 460 260" fill="none" stroke="#718096" stroke-width="1.5" stroke-dasharray="4,4" marker-end="url(#arrow-dash)"/>
  <text x="390" y="280" font-family="Arial, sans-serif" font-size="10" fill="#4A5568">&lt;&lt;extend&gt;&gt;</text>

  <!-- UC05 (Donut) -->
  <g transform="translate(630, 320)">
    <ellipse cx="120" cy="0" rx="115" ry="24" fill="#FFF5F5" stroke="#E53E3E" stroke-width="2"/>
    <text x="120" y="-3" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#9B2C2C" text-anchor="middle">UC05: Monitorar Prazos (Donut)</text>
    <text x="120" y="12" font-family="Arial, sans-serif" font-size="9.5" fill="#C53030" text-anchor="middle">(Métricas de editais vigentes/encerrados)</text>
  </g>
  <path d="M 720 320 L 610 260" fill="none" stroke="#718096" stroke-width="1.5" stroke-dasharray="4,4" marker-end="url(#arrow-dash)"/>
  <text x="670" y="285" font-family="Arial, sans-serif" font-size="10" fill="#4A5568">&lt;&lt;extend&gt;&gt;</text>

  <!-- UC06 -->
  <g transform="translate(390, 400)">
    <ellipse cx="160" cy="0" rx="135" ry="24" fill="#FFFFFF" stroke="#4A5568" stroke-width="1.5" stroke-dasharray="3,3"/>
    <text x="160" y="-3" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#2D3748" text-anchor="middle">UC06: Favoritar / Salvar Oportunidade</text>
    <text x="160" y="12" font-family="Arial, sans-serif" font-size="9.5" fill="#718096" text-anchor="middle">(Armazenamento no perfil local/remoto)</text>
  </g>
  <path d="M 550 376 L 550 265" fill="none" stroke="#718096" stroke-width="1.5" stroke-dasharray="4,4" marker-end="url(#arrow-dash)"/>
  <text x="555" y="330" font-family="Arial, sans-serif" font-size="10" fill="#4A5568">&lt;&lt;extend&gt;&gt;</text>

  <!-- UC07 -->
  <g transform="translate(390, 480)">
    <ellipse cx="160" cy="0" rx="135" ry="24" fill="#FFFFFF" stroke="#4A5568" stroke-width="1.5" stroke-dasharray="3,3"/>
    <text x="160" y="-3" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#2D3748" text-anchor="middle">UC07: Visualizar Edital / Detalhes</text>
    <text x="160" y="12" font-family="Arial, sans-serif" font-size="9.5" fill="#718096" text-anchor="middle">(Redirecionamento para PDF canônico)</text>
  </g>
  <path d="M 550 456 L 550 425" fill="none" stroke="#718096" stroke-width="1.5" stroke-dasharray="4,4" marker-end="url(#arrow-dash)"/>

  <!-- UC08 -->
  <g transform="translate(250, 560)">
    <ellipse cx="120" cy="0" rx="115" ry="24" fill="#EDF2F7" stroke="#4A5568" stroke-width="1.5"/>
    <text x="120" y="-3" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#2D3748" text-anchor="middle">UC08: Alternar Tema Visual</text>
    <text x="120" y="12" font-family="Arial, sans-serif" font-size="9.5" fill="#718096" text-anchor="middle">(Modo Claro / Modo Escuro)</text>
  </g>
  <line x1="125" y1="380" x2="260" y2="550" stroke="#2B6CB0" stroke-width="2"/>

  <!-- UC09 -->
  <g transform="translate(250, 640)">
    <ellipse cx="120" cy="0" rx="115" ry="24" fill="#EDF2F7" stroke="#4A5568" stroke-width="1.5"/>
    <text x="120" y="-3" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#2D3748" text-anchor="middle">UC09: Autenticar-se / Cadastrar</text>
    <text x="120" y="12" font-family="Arial, sans-serif" font-size="9.5" fill="#718096" text-anchor="middle">(Login discente e preferências)</text>
  </g>
  <line x1="125" y1="400" x2="260" y2="630" stroke="#2B6CB0" stroke-width="2"/>

  <!-- UC10 a UC13 -->
  <g transform="translate(630, 480)">
    <ellipse cx="130" cy="0" rx="125" ry="26" fill="#FEFCBF" stroke="#D69E2E" stroke-width="2"/>
    <text x="130" y="-3" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#744210" text-anchor="middle">UC10: Disparar Coleta Concorrente</text>
    <text x="130" y="12" font-family="Arial, sans-serif" font-size="9.5" fill="#975A16" text-anchor="middle">(Execução paralela via run_scrapers.py)</text>
  </g>
  <line x1="975" y1="360" x2="880" y2="470" stroke="#D69E2E" stroke-width="2"/>

  <g transform="translate(630, 560)">
    <ellipse cx="130" cy="0" rx="125" ry="26" fill="#FEFCBF" stroke="#D69E2E" stroke-width="2"/>
    <text x="130" y="-3" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#744210" text-anchor="middle">UC11: Monitorar Logs Isolados</text>
    <text x="130" y="12" font-family="Arial, sans-serif" font-size="9.5" fill="#975A16" text-anchor="middle">(Auditoria em logs/&lt;fonte&gt;.log)</text>
  </g>
  <line x1="975" y1="380" x2="880" y2="550" stroke="#D69E2E" stroke-width="2"/>

  <g transform="translate(630, 640)">
    <ellipse cx="130" cy="0" rx="125" ry="26" fill="#FEFCBF" stroke="#D69E2E" stroke-width="2"/>
    <text x="130" y="-3" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#744210" text-anchor="middle">UC12: Gerenciar Regras e URLs</text>
    <text x="130" y="12" font-family="Arial, sans-serif" font-size="9.5" fill="#975A16" text-anchor="middle">(Ajuste de seletores CSS/Regex)</text>
  </g>
  <line x1="975" y1="400" x2="880" y2="630" stroke="#D69E2E" stroke-width="2"/>

  <g transform="translate(630, 720)">
    <ellipse cx="130" cy="0" rx="125" ry="26" fill="#FEFCBF" stroke="#D69E2E" stroke-width="2"/>
    <text x="130" y="-3" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#744210" text-anchor="middle">UC13: Consultar Documentação API</text>
    <text x="130" y="12" font-family="Arial, sans-serif" font-size="9.5" fill="#975A16" text-anchor="middle">(Swagger interativo em /docs)</text>
  </g>
  <line x1="975" y1="420" x2="880" y2="710" stroke="#D69E2E" stroke-width="2"/>

  <!-- Legenda -->
  <g transform="translate(250, 770)">
    <rect x="0" y="0" width="600" height="38" rx="6" fill="#FFFFFF" stroke="#E2E8F0"/>
    <text x="15" y="23" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#4A5568">Legenda:</text>
    <circle cx="85" cy="19" r="6" fill="#EBF8FF" stroke="#3182CE"/>
    <text x="96" y="23" font-family="Arial, sans-serif" font-size="10" fill="#4A5568">Caso de Uso Central</text>
    <circle cx="230" cy="19" r="6" fill="#FFF5F5" stroke="#E53E3E"/>
    <text x="241" y="23" font-family="Arial, sans-serif" font-size="10" fill="#4A5568">Nova Funcionalidade (Donut)</text>
    <circle cx="410" cy="19" r="6" fill="#FEFCBF" stroke="#D69E2E"/>
    <text x="421" y="23" font-family="Arial, sans-serif" font-size="10" fill="#4A5568">Casos de Uso de DevOps / Admin</text>
  </g>
</svg>
"""

# ==============================================================================
# DIAGRAMA 2: CLASSES DE SOFTWARE (ARQUITETURA REAL)
# ==============================================================================
svgs["diagrama_02_classes_software"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1150 900" width="100%" height="100%">
  <defs>
    <filter id="shadow2" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="2" dy="2" stdDeviation="3" flood-opacity="0.12"/>
    </filter>
  </defs>

  <rect width="1150" height="900" fill="#FFFFFF"/>
  <text x="575" y="38" font-family="Arial, sans-serif" font-size="20" font-weight="bold" fill="#003366" text-anchor="middle">
    Diagrama de Classes de Software – Arquitetura do Sistema EduScrap
  </text>
  <text x="575" y="58" font-family="Arial, sans-serif" font-size="12" fill="#718096" text-anchor="middle">
    Estrutura de classes orientada a objetos: API FastAPI, Ingestão Concorrente, Modelos Pydantic e Persistência NoSQL
  </text>

  <!-- PACOTE API -->
  <rect x="40" y="80" width="480" height="340" rx="8" fill="#F0F9FF" stroke="#0284C7" stroke-width="1.5" filter="url(#shadow2)"/>
  <rect x="40" y="80" width="180" height="25" rx="8" fill="#BAE6FD"/>
  <text x="50" y="97" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#0369A1">API &amp; Controllers (FastAPI)</text>

  <!-- Classe FastAPIApplication -->
  <g transform="translate(60, 115)">
    <rect width="440" height="150" fill="#FFFFFF" stroke="#0284C7" stroke-width="1.5" rx="4"/>
    <rect width="440" height="26" fill="#E0F2FE" rx="4"/>
    <text x="220" y="18" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#0369A1" text-anchor="middle">FastAPIApplication (main.py)</text>
    <line x1="0" y1="26" x2="440" y2="26" stroke="#0284C7"/>
    <text x="10" y="44" font-family="monospace" font-size="10" fill="#333">+ app: FastAPI</text>
    <text x="10" y="58" font-family="monospace" font-size="10" fill="#333">+ router: APIRouter</text>
    <line x1="0" y1="66" x2="440" y2="66" stroke="#E2E8F0"/>
    <text x="10" y="82" font-family="monospace" font-size="10" fill="#333">+ listar_oportunidades(categoria, busca): List[OportunidadeModel]</text>
    <text x="10" y="96" font-family="monospace" font-size="10" fill="#333">+ listar_editais(status): List[OportunidadeModel]</text>
    <text x="10" y="110" font-family="monospace" font-size="10" fill="#333">+ listar_vagas(): List[OportunidadeModel]</text>
    <text x="10" y="124" font-family="monospace" font-size="10" fill="#333">+ obter_estatisticas_prazos(): EstatisticasPrazos</text>
    <text x="10" y="138" font-family="monospace" font-size="10" fill="#333">+ health_check(): dict</text>
  </g>

  <!-- Classe EstatisticasPrazos -->
  <g transform="translate(60, 280)">
    <rect width="210" height="120" fill="#FFFFFF" stroke="#0284C7" stroke-width="1.5" rx="4"/>
    <rect width="210" height="24" fill="#E0F2FE" rx="4"/>
    <text x="105" y="16" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#0369A1" text-anchor="middle">&lt;&lt;Pydantic&gt;&gt; EstatisticasPrazos</text>
    <line x1="0" y1="24" x2="210" y2="24" stroke="#0284C7"/>
    <text x="8" y="40" font-family="monospace" font-size="9.5" fill="#333">+ total: int</text>
    <text x="8" y="54" font-family="monospace" font-size="9.5" fill="#333">+ vigentes: int</text>
    <text x="8" y="68" font-family="monospace" font-size="9.5" fill="#333">+ encerrados: int</text>
    <text x="8" y="82" font-family="monospace" font-size="9.5" fill="#333">+ sem_prazo: int</text>
    <line x1="0" y1="90" x2="210" y2="90" stroke="#E2E8F0"/>
    <text x="8" y="105" font-family="monospace" font-size="9.5" fill="#333">+ calcular_metricas_donut()</text>
  </g>

  <!-- Classe OportunidadeModel -->
  <g transform="translate(290, 280)">
    <rect width="210" height="120" fill="#FFFFFF" stroke="#0284C7" stroke-width="1.5" rx="4"/>
    <rect width="210" height="24" fill="#E0F2FE" rx="4"/>
    <text x="105" y="16" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#0369A1" text-anchor="middle">&lt;&lt;Pydantic&gt;&gt; OportunidadeModel</text>
    <line x1="0" y1="24" x2="210" y2="24" stroke="#0284C7"/>
    <text x="8" y="40" font-family="monospace" font-size="9.5" fill="#333">+ id: str</text>
    <text x="8" y="54" font-family="monospace" font-size="9.5" fill="#333">+ titulo: str</text>
    <text x="8" y="68" font-family="monospace" font-size="9.5" fill="#333">+ link: str</text>
    <text x="8" y="82" font-family="monospace" font-size="9.5" fill="#333">+ data_publicacao: datetime</text>
    <text x="8" y="96" font-family="monospace" font-size="9.5" fill="#333">+ data_limite: Optional[datetime]</text>
    <text x="8" y="110" font-family="monospace" font-size="9.5" fill="#333">+ status_vigencia: str</text>
  </g>

  <!-- PACOTE SCRAPING -->
  <rect x="560" y="80" width="550" height="480" rx="8" fill="#FDF8F6" stroke="#EA580C" stroke-width="1.5" filter="url(#shadow2)"/>
  <rect x="560" y="80" width="230" height="25" rx="8" fill="#FFEDD5"/>
  <text x="570" y="97" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#C2410C">Engine de Scraping Concorrente</text>

  <!-- ScraperRunner -->
  <g transform="translate(580, 115)">
    <rect width="510" height="110" fill="#FFFFFF" stroke="#EA580C" stroke-width="1.5" rx="4"/>
    <rect width="510" height="26" fill="#FFEDD5" rx="4"/>
    <text x="255" y="18" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#C2410C" text-anchor="middle">ScraperRunner (run_scrapers.py)</text>
    <line x1="0" y1="26" x2="510" y2="26" stroke="#EA580C"/>
    <text x="10" y="44" font-family="monospace" font-size="10" fill="#333">- FONTES_DISPONIVEIS: List[str] = ['prae', 'proex', 'portal_uern', 'ufersa', 'ciee']</text>
    <text x="10" y="58" font-family="monospace" font-size="10" fill="#333">- max_workers: int = 5</text>
    <line x1="0" y1="66" x2="510" y2="66" stroke="#E2E8F0"/>
    <text x="10" y="82" font-family="monospace" font-size="10" fill="#333">+ executar_paralelo(fontes_selecionadas: List[str]): void</text>
    <text x="10" y="96" font-family="monospace" font-size="10" fill="#333">+ executar_serial(): void</text>
    <text x="10" y="106" font-family="monospace" font-size="10" fill="#333">+ configurar_logger_isolado(nome_fonte: str): Logger</text>
  </g>

  <!-- BaseScraper -->
  <g transform="translate(710, 245)">
    <rect width="250" height="100" fill="#FFFFFF" stroke="#EA580C" stroke-width="1.5" rx="4"/>
    <rect width="250" height="24" fill="#FFEDD5" rx="4"/>
    <text x="125" y="16" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#C2410C" text-anchor="middle">&lt;&lt;Abstract&gt;&gt; BaseScraper</text>
    <line x1="0" y1="24" x2="250" y2="24" stroke="#EA580C"/>
    <text x="8" y="40" font-family="monospace" font-size="9.5" fill="#333"># nome_fonte: str</text>
    <text x="8" y="54" font-family="monospace" font-size="9.5" fill="#333"># url_base: str</text>
    <line x1="0" y1="62" x2="250" y2="62" stroke="#E2E8F0"/>
    <text x="8" y="78" font-family="monospace" font-size="9.5" fill="#333">+ {abstract} coletar(): List[dict]</text>
    <text x="8" y="92" font-family="monospace" font-size="9.5" fill="#333">+ salvar_no_banco(dados): int</text>
  </g>

  <!-- Especializações -->
  <g transform="translate(580, 375)">
    <rect width="115" height="75" fill="#FFFFFF" stroke="#EA580C" rx="4"/>
    <rect width="115" height="20" fill="#FFEDD5" rx="4"/>
    <text x="57" y="14" font-family="Arial, sans-serif" font-size="10" font-weight="bold" fill="#C2410C" text-anchor="middle">ScraperPRAE</text>
    <line x1="0" y1="20" x2="115" y2="20" stroke="#EA580C"/>
    <text x="5" y="36" font-family="monospace" font-size="8.5" fill="#333">+ coletar(): List</text>
    <text x="5" y="50" font-family="monospace" font-size="8.5" fill="#333">+ ler_editais_html()</text>
    <text x="5" y="64" font-family="monospace" font-size="8.5" fill="#333">+ extrair_bolsas()</text>
  </g>

  <g transform="translate(710, 375)">
    <rect width="115" height="75" fill="#FFFFFF" stroke="#EA580C" rx="4"/>
    <rect width="115" height="20" fill="#FFEDD5" rx="4"/>
    <text x="57" y="14" font-family="Arial, sans-serif" font-size="10" font-weight="bold" fill="#C2410C" text-anchor="middle">ScraperUERN</text>
    <line x1="0" y1="20" x2="115" y2="20" stroke="#EA580C"/>
    <text x="5" y="36" font-family="monospace" font-size="8.5" fill="#333">- driver: WebDriver</text>
    <text x="5" y="50" font-family="monospace" font-size="8.5" fill="#333">+ coletar(): List</text>
    <text x="5" y="64" font-family="monospace" font-size="8.5" fill="#333">+ paginar_portal()</text>
  </g>

  <g transform="translate(840, 375)">
    <rect width="115" height="75" fill="#FFFFFF" stroke="#EA580C" rx="4"/>
    <rect width="115" height="20" fill="#FFEDD5" rx="4"/>
    <text x="57" y="14" font-family="Arial, sans-serif" font-size="10" font-weight="bold" fill="#C2410C" text-anchor="middle">ScraperUFERSA</text>
    <line x1="0" y1="20" x2="115" y2="20" stroke="#EA580C"/>
    <text x="5" y="36" font-family="monospace" font-size="8.5" fill="#333">+ coletar(): List</text>
    <text x="5" y="50" font-family="monospace" font-size="8.5" fill="#333">+ parse_editais()</text>
  </g>

  <g transform="translate(970, 375)">
    <rect width="120" height="75" fill="#FFFFFF" stroke="#EA580C" rx="4"/>
    <rect width="120" height="20" fill="#FFEDD5" rx="4"/>
    <text x="60" y="14" font-family="Arial, sans-serif" font-size="10" font-weight="bold" fill="#C2410C" text-anchor="middle">ScraperCIEE</text>
    <line x1="0" y1="20" x2="120" y2="20" stroke="#EA580C"/>
    <text x="5" y="36" font-family="monospace" font-size="8.5" fill="#333">- driver: Firefox</text>
    <text x="5" y="50" font-family="monospace" font-size="8.5" fill="#333">+ coletar(): List</text>
    <text x="5" y="64" font-family="monospace" font-size="8.5" fill="#333">+ filtrar_vagas()</text>
  </g>

  <!-- Linhas herança scrapers -->
  <path d="M 637 375 L 637 355 L 835 355 L 835 345" fill="none" stroke="#EA580C" stroke-width="1.5"/>
  <path d="M 767 375 L 767 355" fill="none" stroke="#EA580C" stroke-width="1.5"/>
  <path d="M 897 375 L 897 355" fill="none" stroke="#EA580C" stroke-width="1.5"/>
  <path d="M 1030 375 L 1030 355 L 835 355" fill="none" stroke="#EA580C" stroke-width="1.5"/>

  <!-- PACOTE NORMALIZAÇÃO -->
  <rect x="40" y="460" width="480" height="240" rx="8" fill="#F0FDF4" stroke="#16A34A" stroke-width="1.5" filter="url(#shadow2)"/>
  <rect x="40" y="460" width="220" height="25" rx="8" fill="#DCFCE7"/>
  <text x="50" y="477" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#15803D">Processamento &amp; Normalização</text>

  <!-- Normalizer -->
  <g transform="translate(60, 495)">
    <rect width="210" height="185" fill="#FFFFFF" stroke="#16A34A" stroke-width="1.5" rx="4"/>
    <rect width="210" height="24" fill="#DCFCE7" rx="4"/>
    <text x="105" y="16" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#15803D" text-anchor="middle">Normalizer (Regex Engine)</text>
    <line x1="0" y1="24" x2="210" y2="24" stroke="#16A34A"/>
    <text x="8" y="40" font-family="monospace" font-size="9.5" fill="#333">- PADROES_REGEX: dict</text>
    <text x="8" y="54" font-family="monospace" font-size="9.5" fill="#333">- FORMATOS_DATA: List</text>
    <line x1="0" y1="62" x2="210" y2="62" stroke="#E2E8F0"/>
    <text x="8" y="78" font-family="monospace" font-size="9.5" fill="#333">+ extrair_datas(texto)</text>
    <text x="8" y="94" font-family="monospace" font-size="9.5" fill="#333">+ validar_vigencia(data)</text>
    <text x="8" y="110" font-family="monospace" font-size="9.5" fill="#333">+ mapear_area_curso(txt)</text>
    <text x="8" y="126" font-family="monospace" font-size="9.5" fill="#333">+ limpar_html(bruto)</text>
    <text x="8" y="142" font-family="monospace" font-size="9.5" fill="#333">+ padronizar_json(): dict</text>
  </g>

  <!-- PDFUtils -->
  <g transform="translate(290, 495)">
    <rect width="210" height="185" fill="#FFFFFF" stroke="#16A34A" stroke-width="1.5" rx="4"/>
    <rect width="210" height="24" fill="#DCFCE7" rx="4"/>
    <text x="105" y="16" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#15803D" text-anchor="middle">PDFUtils (Leitor JOUERN)</text>
    <line x1="0" y1="24" x2="210" y2="24" stroke="#16A34A"/>
    <text x="8" y="40" font-family="monospace" font-size="9.5" fill="#333">- engine_pdf: pdfplumber</text>
    <text x="8" y="54" font-family="monospace" font-size="9.5" fill="#333">- fallback: PyPDF2</text>
    <line x1="0" y1="62" x2="210" y2="62" stroke="#E2E8F0"/>
    <text x="8" y="78" font-family="monospace" font-size="9.5" fill="#333">+ extrair_texto_pdf(path)</text>
    <text x="8" y="94" font-family="monospace" font-size="9.5" fill="#333">+ ler_tabelas_jouern()</text>
    <text x="8" y="110" font-family="monospace" font-size="9.5" fill="#333">+ extrair_metadados_doc()</text>
  </g>

  <!-- PACOTE PERSISTÊNCIA -->
  <rect x="560" y="590" width="550" height="250" rx="8" fill="#F8FAFC" stroke="#475569" stroke-width="1.5" filter="url(#shadow2)"/>
  <rect x="560" y="590" width="180" height="25" rx="8" fill="#E2E8F0"/>
  <text x="570" y="607" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#334155">Persistência (MongoDB)</text>

  <!-- MongoDatabase -->
  <g transform="translate(580, 625)">
    <rect width="510" height="195" fill="#FFFFFF" stroke="#475569" stroke-width="1.5" rx="4"/>
    <rect width="510" height="24" fill="#E2E8F0" rx="4"/>
    <text x="255" y="16" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#334155" text-anchor="middle">MongoDatabase (database_setup.py)</text>
    <line x1="0" y1="24" x2="510" y2="24" stroke="#475569"/>
    <text x="8" y="40" font-family="monospace" font-size="9.5" fill="#333">- client: MongoClient</text>
    <text x="8" y="54" font-family="monospace" font-size="9.5" fill="#333">- db: Database = 'hub_estudantes'</text>
    <text x="8" y="68" font-family="monospace" font-size="9.5" fill="#333">+ col_oportunidades: Collection</text>
    <text x="8" y="82" font-family="monospace" font-size="9.5" fill="#333">+ col_usuarios: Collection</text>
    <line x1="0" y1="90" x2="510" y2="90" stroke="#CBD5E1"/>
    <text x="8" y="106" font-family="monospace" font-size="9.5" fill="#333">+ database_setup(): void (Aplica JSON Schema validation)</text>
    <text x="8" y="122" font-family="monospace" font-size="9.5" fill="#333">+ criar_indices_busca(): void (Índice de texto em titulo/tags + índice data_limite)</text>
    <text x="8" y="138" font-family="monospace" font-size="9.5" fill="#333">+ upsert_oportunidade(filtro: dict, doc: dict): UpdateResult</text>
    <text x="8" y="154" font-family="monospace" font-size="9.5" fill="#333">+ buscar_por_filtros(categoria, busca, status): Cursor</text>
  </g>

  <!-- LIGAÇÕES ENTRE PACOTES -->
  <path d="M 280 265 L 280 440 L 600 440 L 600 625" fill="none" stroke="#2B6CB0" stroke-width="1.5" stroke-dasharray="4,4"/>
  <text x="380" y="435" font-family="Arial, sans-serif" font-size="10" fill="#2B6CB0">&lt;&lt;consulta e agrega&gt;&gt;</text>

  <path d="M 835 450 L 835 590" fill="none" stroke="#EA580C" stroke-width="1.5"/>
  <text x="840" y="520" font-family="Arial, sans-serif" font-size="10" fill="#EA580C">&lt;&lt;persiste dados higienizados&gt;&gt;</text>

  <path d="M 580 400 L 520 400 L 520 500 L 270 500" fill="none" stroke="#16A34A" stroke-width="1.5" stroke-dasharray="4,4"/>
  <text x="370" y="495" font-family="Arial, sans-serif" font-size="10" fill="#16A34A">&lt;&lt;normaliza dados brutos&gt;&gt;</text>
</svg>
"""

# Salvar SVGs no disco
for name, content in svgs.items():
    svg_path = os.path.join(OUT_DIR, f"{name}.svg")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"SVG salvo: {svg_path}")

print("SVGs gerados com sucesso!")

# Continuação de svgs com os diagramas 3, 4, 5, 6 e 7
extra_svgs = {}

# ==============================================================================
# DIAGRAMA 3: SEQUÊNCIA - COLETA PARALELA
# ==============================================================================
extra_svgs["diagrama_03_sequencia_coleta_paralela"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1150 820" width="100%" height="100%">
  <defs>
    <filter id="sd3" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="2" dy="2" stdDeviation="3" flood-opacity="0.12"/>
    </filter>
    <marker id="m-arr" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#1A365D"/>
    </marker>
  </defs>

  <rect width="1150" height="820" fill="#FFFFFF"/>
  <text x="575" y="38" font-family="Arial, sans-serif" font-size="20" font-weight="bold" fill="#003366" text-anchor="middle">
    Diagrama de Sequência – Coleta Concorrente Paralela e Persistência
  </text>
  <text x="575" y="58" font-family="Arial, sans-serif" font-size="12" fill="#718096" text-anchor="middle">
    Orquestrador paralelo multi-worker (run_scrapers.py), isolamento de logs e processamento por expressões regulares
  </text>

  <!-- Lifelines Cabeçalhos -->
  <g transform="translate(70, 85)">
    <rect width="110" height="40" rx="6" fill="#EDF2F7" stroke="#4A5568" stroke-width="1.5"/>
    <text x="55" y="18" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#2D3748" text-anchor="middle">Admin / Cron</text>
    <text x="55" y="32" font-family="Arial, sans-serif" font-size="9.5" fill="#718096" text-anchor="middle">[Gatilho]</text>
  </g>
  <line x1="125" y1="125" x2="125" y2="760" stroke="#CBD5E0" stroke-width="1.5" stroke-dasharray="4,4"/>

  <g transform="translate(210, 85)">
    <rect width="130" height="40" rx="6" fill="#FFEDD5" stroke="#EA580C" stroke-width="1.5"/>
    <text x="65" y="18" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#C2410C" text-anchor="middle">ScraperRunner</text>
    <text x="65" y="32" font-family="Arial, sans-serif" font-size="9.5" fill="#C2410C" text-anchor="middle">[run_scrapers.py]</text>
  </g>
  <line x1="275" y1="125" x2="275" y2="760" stroke="#CBD5E0" stroke-width="1.5" stroke-dasharray="4,4"/>

  <g transform="translate(370, 85)">
    <rect width="140" height="40" rx="6" fill="#FFEDD5" stroke="#EA580C" stroke-width="1.5"/>
    <text x="70" y="18" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#C2410C" text-anchor="middle">ThreadPoolExecutor</text>
    <text x="70" y="32" font-family="Arial, sans-serif" font-size="9.5" fill="#C2410C" text-anchor="middle">[Multi-Worker]</text>
  </g>
  <line x1="440" y1="125" x2="440" y2="760" stroke="#CBD5E0" stroke-width="1.5" stroke-dasharray="4,4"/>

  <g transform="translate(540, 85)">
    <rect width="150" height="40" rx="6" fill="#E0F2FE" stroke="#0284C7" stroke-width="1.5"/>
    <text x="75" y="18" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#0369A1" text-anchor="middle">Scrapers Concorrentes</text>
    <text x="75" y="32" font-family="Arial, sans-serif" font-size="9.5" fill="#0369A1" text-anchor="middle">[PRAE, UFERSA, CIEE]</text>
  </g>
  <line x1="615" y1="125" x2="615" y2="760" stroke="#CBD5E0" stroke-width="1.5" stroke-dasharray="4,4"/>

  <g transform="translate(720, 85)">
    <rect width="130" height="40" rx="6" fill="#DCFCE7" stroke="#16A34A" stroke-width="1.5"/>
    <text x="65" y="18" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#15803D" text-anchor="middle">Normalizer</text>
    <text x="65" y="32" font-family="Arial, sans-serif" font-size="9.5" fill="#15803D" text-anchor="middle">[Regex + PDF Engine]</text>
  </g>
  <line x1="785" y1="125" x2="785" y2="760" stroke="#CBD5E0" stroke-width="1.5" stroke-dasharray="4,4"/>

  <g transform="translate(880, 85)">
    <rect width="110" height="40" rx="6" fill="#F1F5F9" stroke="#475569" stroke-width="1.5"/>
    <text x="55" y="18" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#334155" text-anchor="middle">MongoDB</text>
    <text x="55" y="32" font-family="Arial, sans-serif" font-size="9.5" fill="#334155" text-anchor="middle">[hub_estudantes]</text>
  </g>
  <line x1="935" y1="125" x2="935" y2="760" stroke="#CBD5E0" stroke-width="1.5" stroke-dasharray="4,4"/>

  <g transform="translate(1010, 85)">
    <rect width="100" height="40" rx="6" fill="#FEF3C7" stroke="#D97706" stroke-width="1.5"/>
    <text x="50" y="18" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#B45309" text-anchor="middle">logs/&lt;fonte&gt;.log</text>
    <text x="50" y="32" font-family="Arial, sans-serif" font-size="9.5" fill="#B45309" text-anchor="middle">[Isolamento]</text>
  </g>
  <line x1="1060" y1="125" x2="1060" y2="760" stroke="#CBD5E0" stroke-width="1.5" stroke-dasharray="4,4"/>

  <!-- MENSAGENS -->
  <line x1="125" y1="150" x2="270" y2="150" stroke="#1A365D" stroke-width="1.5" marker-end="url(#m-arr)"/>
  <text x="195" y="143" font-family="Arial, sans-serif" font-size="10.5" fill="#1A365D" text-anchor="middle">1. python run_scrapers.py</text>
  <rect x="270" y="150" width="10" height="570" fill="#EA580C"/>

  <line x1="280" y1="175" x2="1055" y2="175" stroke="#D97706" stroke-width="1.5" marker-end="url(#m-arr)"/>
  <text x="670" y="168" font-family="Arial, sans-serif" font-size="10" fill="#B45309" text-anchor="middle">2. Configura loggers isolados (logs/prae.log, logs/ciee.log, logs/ufersa.log...)</text>

  <line x1="280" y1="205" x2="435" y2="205" stroke="#EA580C" stroke-width="1.5" marker-end="url(#m-arr)"/>
  <text x="355" y="198" font-family="Arial, sans-serif" font-size="10.5" fill="#C2410C" text-anchor="middle">3. Inicializa ThreadPool(max_workers=5)</text>
  <rect x="435" y="205" width="10" height="470" fill="#EA580C"/>

  <!-- Caixa de Execução Paralela -->
  <rect x="390" y="235" width="690" height="410" rx="8" fill="#F8FAFC" stroke="#94A3B8" stroke-width="1.5" stroke-dasharray="6,4"/>
  <rect x="390" y="235" width="220" height="22" rx="6" fill="#E2E8F0"/>
  <text x="400" y="250" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#334155">par [Execução Concorrente Paralela]</text>

  <!-- Thread PRAE -->
  <line x1="445" y1="275" x2="610" y2="275" stroke="#0284C7" stroke-width="1.5" marker-end="url(#m-arr)"/>
  <text x="525" y="268" font-family="Arial, sans-serif" font-size="10" fill="#0369A1" text-anchor="middle">4a. Dispara Worker PRAE</text>
  <rect x="610" y="275" width="10" height="150" fill="#0284C7"/>

  <path d="M 620 295 C 660 295, 660 315, 620 315" fill="none" stroke="#0284C7" stroke-width="1.5" marker-end="url(#m-arr)"/>
  <text x="670" y="310" font-family="Arial, sans-serif" font-size="9.5" fill="#0369A1">Requests + BeautifulSoup (HTML)</text>

  <line x1="620" y1="335" x2="780" y2="335" stroke="#16A34A" stroke-width="1.5" marker-end="url(#m-arr)"/>
  <text x="700" y="328" font-family="Arial, sans-serif" font-size="9.5" fill="#15803D" text-anchor="middle">extrair_datas(texto) via Regex</text>
  <rect x="780" y="335" width="10" height="40" fill="#16A34A"/>

  <line x1="780" y1="365" x2="620" y2="365" stroke="#16A34A" stroke-width="1.5" stroke-dasharray="3,3" marker-end="url(#m-arr)"/>
  <text x="700" y="358" font-family="Arial, sans-serif" font-size="9" fill="#15803D" text-anchor="middle">retorna status="Aberto/Vigente"</text>

  <line x1="620" y1="395" x2="930" y2="395" stroke="#334155" stroke-width="1.5" marker-end="url(#m-arr)"/>
  <text x="775" y="388" font-family="Arial, sans-serif" font-size="9.5" fill="#334155" text-anchor="middle">bulk_upsert_oportunidades(dados)</text>

  <line x1="620" y1="415" x2="1055" y2="415" stroke="#D97706" stroke-width="1.5" marker-end="url(#m-arr)"/>
  <text x="840" y="410" font-family="Arial, sans-serif" font-size="9" fill="#B45309" text-anchor="middle">Grava log em logs/prae.log</text>

  <!-- Divisor Paralelo -->
  <line x1="390" y1="440" x2="1080" y2="440" stroke="#CBD5E0" stroke-width="1" stroke-dasharray="4,4"/>
  <text x="400" y="455" font-family="Arial, sans-serif" font-size="10" font-style="italic" fill="#64748B">also [Simultaneamente em outra Thread]</text>

  <!-- Thread CIEE -->
  <line x1="445" y1="480" x2="610" y2="480" stroke="#0284C7" stroke-width="1.5" marker-end="url(#m-arr)"/>
  <text x="525" y="473" font-family="Arial, sans-serif" font-size="10" fill="#0369A1" text-anchor="middle">4b. Dispara Worker CIEE</text>
  <rect x="610" y="480" width="10" height="145" fill="#0284C7"/>

  <path d="M 620 500 C 660 500, 660 520, 620 520" fill="none" stroke="#0284C7" stroke-width="1.5" marker-end="url(#m-arr)"/>
  <text x="670" y="515" font-family="Arial, sans-serif" font-size="9.5" fill="#0369A1">Firefox Headless (DOM Dinâmico)</text>

  <line x1="620" y1="540" x2="780" y2="540" stroke="#16A34A" stroke-width="1.5" marker-end="url(#m-arr)"/>
  <text x="700" y="533" font-family="Arial, sans-serif" font-size="9.5" fill="#15803D" text-anchor="middle">normalizar_vagas(Mossoró/RN)</text>
  <rect x="780" y="540" width="10" height="30" fill="#16A34A"/>

  <line x1="620" y1="585" x2="930" y2="585" stroke="#334155" stroke-width="1.5" marker-end="url(#m-arr)"/>
  <text x="775" y="578" font-family="Arial, sans-serif" font-size="9.5" fill="#334155" text-anchor="middle">bulk_upsert_oportunidades(vagas)</text>

  <line x1="620" y1="610" x2="1055" y2="610" stroke="#D97706" stroke-width="1.5" marker-end="url(#m-arr)"/>
  <text x="840" y="605" font-family="Arial, sans-serif" font-size="9" fill="#B45309" text-anchor="middle">Grava log em logs/ciee.log</text>

  <!-- Fim do Paralelo -->
  <line x1="445" y1="660" x2="280" y2="660" stroke="#EA580C" stroke-width="1.5" stroke-dasharray="3,3" marker-end="url(#m-arr)"/>
  <text x="360" y="653" font-family="Arial, sans-serif" font-size="10" fill="#C2410C" text-anchor="middle">Workers concluídos</text>

  <line x1="270" y1="710" x2="125" y2="710" stroke="#1A365D" stroke-width="1.5" stroke-dasharray="3,3" marker-end="url(#m-arr)"/>
  <text x="195" y="703" font-family="Arial, sans-serif" font-size="10.5" fill="#1A365D" text-anchor="middle">Relatório consolidado (Sucesso)</text>
</svg>
"""

# ==============================================================================
# DIAGRAMA 4: SEQUÊNCIA - CONSULTA E DONUT CHART
# ==============================================================================
extra_svgs["diagrama_04_sequencia_consulta_donut"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 780" width="100%" height="100%">
  <defs>
    <marker id="m4" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#1A365D"/>
    </marker>
  </defs>

  <rect width="1100" height="780" fill="#FFFFFF"/>
  <text x="550" y="38" font-family="Arial, sans-serif" font-size="20" font-weight="bold" fill="#003366" text-anchor="middle">
    Diagrama de Sequência – Consulta Interativa e Renderização do Gráfico Donut
  </text>
  <text x="550" y="58" font-family="Arial, sans-serif" font-size="12" fill="#718096" text-anchor="middle">
    Consumo de dados pré-processados da API FastAPI e agregação analítica de prazos no frontend
  </text>

  <!-- Lifelines -->
  <g transform="translate(60, 85)">
    <rect width="120" height="40" rx="6" fill="#EBF8FF" stroke="#3182CE" stroke-width="1.5"/>
    <text x="60" y="24" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#1A365D" text-anchor="middle">Estudante</text>
  </g>
  <line x1="120" y1="125" x2="120" y2="720" stroke="#CBD5E0" stroke-width="1.5" stroke-dasharray="4,4"/>

  <g transform="translate(260, 85)">
    <rect width="160" height="40" rx="6" fill="#F0F9FF" stroke="#0284C7" stroke-width="1.5"/>
    <text x="80" y="18" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#0369A1" text-anchor="middle">Frontend SPA</text>
    <text x="80" y="32" font-family="Arial, sans-serif" font-size="9.5" fill="#0369A1" text-anchor="middle">[index.html / script.js]</text>
  </g>
  <line x1="340" y1="125" x2="340" y2="720" stroke="#CBD5E0" stroke-width="1.5" stroke-dasharray="4,4"/>

  <g transform="translate(500, 85)">
    <rect width="160" height="40" rx="6" fill="#E0F2FE" stroke="#0284C7" stroke-width="1.5"/>
    <text x="80" y="18" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#0369A1" text-anchor="middle">API REST (FastAPI)</text>
    <text x="80" y="32" font-family="Arial, sans-serif" font-size="9.5" fill="#0369A1" text-anchor="middle">[Uvicorn :8000]</text>
  </g>
  <line x1="580" y1="125" x2="580" y2="720" stroke="#CBD5E0" stroke-width="1.5" stroke-dasharray="4,4"/>

  <g transform="translate(740, 85)">
    <rect width="140" height="40" rx="6" fill="#F1F5F9" stroke="#475569" stroke-width="1.5"/>
    <text x="70" y="18" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#334155" text-anchor="middle">MongoDB</text>
    <text x="70" y="32" font-family="Arial, sans-serif" font-size="9.5" fill="#334155" text-anchor="middle">[col_oportunidades]</text>
  </g>
  <line x1="810" y1="125" x2="810" y2="720" stroke="#CBD5E0" stroke-width="1.5" stroke-dasharray="4,4"/>

  <g transform="translate(940, 85)">
    <rect width="130" height="40" rx="6" fill="#FFF5F5" stroke="#E53E3E" stroke-width="1.5"/>
    <text x="65" y="18" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#9B2C2C" text-anchor="middle">Donut SVG Engine</text>
    <text x="65" y="32" font-family="Arial, sans-serif" font-size="9.5" fill="#9B2C2C" text-anchor="middle">[Módulo de Prazos]</text>
  </g>
  <line x1="1005" y1="125" x2="1005" y2="720" stroke="#CBD5E0" stroke-width="1.5" stroke-dasharray="4,4"/>

  <!-- Fluxo -->
  <line x1="120" y1="160" x2="335" y2="160" stroke="#1A365D" stroke-width="1.5" marker-end="url(#m4)"/>
  <text x="227" y="153" font-family="Arial, sans-serif" font-size="10.5" fill="#1A365D" text-anchor="middle">1. Seleciona Curso/Área ou clica em Filtro</text>
  <rect x="335" y="160" width="10" height="520" fill="#0284C7"/>

  <line x1="345" y1="200" x2="575" y2="200" stroke="#0284C7" stroke-width="1.5" marker-end="url(#m4)"/>
  <text x="460" y="193" font-family="Arial, sans-serif" font-size="10.5" fill="#0369A1" text-anchor="middle">2. GET /api/oportunidades?categoria=tecnologia</text>
  <rect x="575" y="200" width="10" height="150" fill="#0284C7"/>

  <line x1="585" y1="235" x2="805" y2="235" stroke="#475569" stroke-width="1.5" marker-end="url(#m4)"/>
  <text x="695" y="228" font-family="Arial, sans-serif" font-size="10" fill="#334155" text-anchor="middle">3. find({ categoria: 'tecnologia' }).sort(data_limite: 1)</text>
  <rect x="805" y="235" width="10" height="65" fill="#475569"/>

  <line x1="805" y1="290" x2="585" y2="290" stroke="#475569" stroke-width="1.5" stroke-dasharray="3,3" marker-end="url(#m4)"/>
  <text x="695" y="283" font-family="Arial, sans-serif" font-size="10" fill="#334155" text-anchor="middle">4. Documentos JSON indexados (&lt; 20ms)</text>

  <line x1="575" y1="340" x2="345" y2="340" stroke="#0284C7" stroke-width="1.5" stroke-dasharray="3,3" marker-end="url(#m4)"/>
  <text x="460" y="333" font-family="Arial, sans-serif" font-size="10.5" fill="#0369A1" text-anchor="middle">5. HTTP 200 OK [Array de Oportunidades]</text>

  <path d="M 345 375 C 390 375, 390 405, 345 405" fill="none" stroke="#0284C7" stroke-width="1.5" marker-end="url(#m4)"/>
  <text x="400" y="395" font-family="Arial, sans-serif" font-size="10" fill="#0369A1">6. Itera e contabiliza: Vigentes vs. Encerrados</text>

  <line x1="345" y1="440" x2="1000" y2="440" stroke="#E53E3E" stroke-width="1.5" marker-end="url(#m4)"/>
  <text x="670" y="433" font-family="Arial, sans-serif" font-size="10.5" fill="#9B2C2C" text-anchor="middle">7. renderizarDonutChart(vigentes, encerrados)</text>
  <rect x="1000" y="440" width="10" height="90" fill="#E53E3E"/>

  <path d="M 1010 465 C 1055 465, 1055 495, 1010 495" fill="none" stroke="#E53E3E" stroke-width="1.5" marker-end="url(#m4)"/>
  <text x="1060" y="485" font-family="Arial, sans-serif" font-size="9.5" fill="#9B2C2C">Calcula ângulos dos arcos SVG</text>

  <line x1="1000" y1="520" x2="345" y2="520" stroke="#E53E3E" stroke-width="1.5" stroke-dasharray="3,3" marker-end="url(#m4)"/>
  <text x="670" y="513" font-family="Arial, sans-serif" font-size="10" fill="#9B2C2C" text-anchor="middle">8. Injeta nó &lt;svg class="donut-chart"&gt; no DOM</text>

  <path d="M 345 560 C 390 560, 390 590, 345 590" fill="none" stroke="#0284C7" stroke-width="1.5" marker-end="url(#m4)"/>
  <text x="400" y="580" font-family="Arial, sans-serif" font-size="10" fill="#0369A1">9. Constrói cards com badges de vigência e links canônicos</text>

  <line x1="335" y1="640" x2="120" y2="640" stroke="#1A365D" stroke-width="1.5" stroke-dasharray="3,3" marker-end="url(#m4)"/>
  <text x="227" y="633" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#1A365D" text-anchor="middle">10. Interface renderizada (&lt; 0.3s)</text>
</svg>
"""

# ==============================================================================
# DIAGRAMA 5: IMPLANTAÇÃO E INFRAESTRUTURA REAL
# ==============================================================================
extra_svgs["diagrama_05_implantacao_arquitetura"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1150 820" width="100%" height="100%">
  <defs>
    <filter id="sd5" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="2" dy="2" stdDeviation="3" flood-opacity="0.12"/>
    </filter>
  </defs>

  <rect width="1150" height="820" fill="#FFFFFF"/>
  <text x="575" y="38" font-family="Arial, sans-serif" font-size="20" font-weight="bold" fill="#003366" text-anchor="middle">
    Diagrama de Implantação – Arquitetura de Execução do EduScrap
  </text>
  <text x="575" y="58" font-family="Arial, sans-serif" font-size="12" fill="#718096" text-anchor="middle">
    Mapeamento físico e lógico dos nós de processamento: Dispositivo Cliente, Host Linux, MongoDB e Fontes Externas
  </text>

  <!-- NÓ CLIENTE -->
  <g transform="translate(40, 100)">
    <polygon points="0,20 20,0 280,0 260,20" fill="#E2E8F0" stroke="#94A3B8"/>
    <polygon points="280,0 280,240 260,260 260,20" fill="#CBD5E1" stroke="#94A3B8"/>
    <rect x="0" y="20" width="260" height="240" fill="#F8FAFC" stroke="#94A3B8" stroke-width="1.5" filter="url(#sd5)"/>
    <text x="130" y="45" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#1E293B" text-anchor="middle">&lt;&lt;device&gt;&gt; Dispositivo do Discente</text>
    
    <rect x="25" y="70" width="210" height="160" rx="6" fill="#FFFFFF" stroke="#3B82F6" stroke-width="1.5"/>
    <rect x="25" y="70" width="210" height="24" rx="6" fill="#EFF6FF"/>
    <text x="130" y="86" font-family="Arial, sans-serif" font-size="10" font-weight="bold" fill="#1D4ED8" text-anchor="middle">&lt;&lt;artifact&gt;&gt; Navegador Web</text>
    <text x="35" y="115" font-family="Arial, sans-serif" font-size="9.5" fill="#333">• Single Page Application (SPA)</text>
    <text x="35" y="135" font-family="Arial, sans-serif" font-size="9.5" fill="#333">• HTML5 + CSS3 + Tailwind</text>
    <text x="35" y="155" font-family="Arial, sans-serif" font-size="9.5" fill="#333">• JavaScript Vanilla (script.js)</text>
    <text x="35" y="175" font-family="Arial, sans-serif" font-size="9.5" fill="#333">• Tema Dinâmico (theme.js)</text>
    <text x="35" y="195" font-family="Arial, sans-serif" font-size="9.5" fill="#333">• Donut Chart (SVG)</text>
    <text x="35" y="215" font-family="monospace" font-size="9" fill="#2563EB">Porta de Acesso: :3000</text>
  </g>

  <!-- NÓ SERVIDOR DE APLICAÇÃO -->
  <g transform="translate(360, 100)">
    <polygon points="0,20 20,0 470,0 450,20" fill="#BAE6FD" stroke="#0284C7"/>
    <polygon points="470,0 470,640 450,660 450,20" fill="#7DD3FC" stroke="#0284C7"/>
    <rect x="0" y="20" width="450" height="640" fill="#F0F9FF" stroke="#0284C7" stroke-width="1.5" filter="url(#sd5)"/>
    <text x="225" y="45" font-family="Arial, sans-serif" font-size="13" font-weight="bold" fill="#0369A1" text-anchor="middle">&lt;&lt;server&gt;&gt; Host Linux / Servidor EduScrap</text>

    <!-- Processo 1 -->
    <rect x="25" y="70" width="400" height="90" rx="6" fill="#FFFFFF" stroke="#0284C7" stroke-width="1.5"/>
    <text x="35" y="90" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#0369A1">Processo Web Frontend (Porta 3000)</text>
    <text x="35" y="110" font-family="Arial, sans-serif" font-size="9.5" fill="#475569">• Servidor HTTP Estático (Python http.server / Nginx)</text>
    <text x="35" y="128" font-family="Arial, sans-serif" font-size="9.5" fill="#475569">• Disponibiliza index.html, login.html, style.css e assets/</text>
    <text x="35" y="146" font-family="monospace" font-size="9" fill="#0284C7">start.sh -&gt; python -m http.server 3000</text>

    <!-- Processo 2 -->
    <rect x="25" y="180" width="400" height="150" rx="6" fill="#FFFFFF" stroke="#0284C7" stroke-width="1.5"/>
    <text x="35" y="200" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#0369A1">Processo Backend REST API (Porta 8000)</text>
    <text x="35" y="220" font-family="Arial, sans-serif" font-size="9.5" fill="#475569">• Framework FastAPI com Servidor ASGI Uvicorn</text>
    <text x="35" y="238" font-family="Arial, sans-serif" font-size="9.5" fill="#475569">• Middlewares: CORS habilitado (origem :3000 liberada)</text>
    <text x="35" y="256" font-family="Arial, sans-serif" font-size="9.5" fill="#475569">• Documentação OpenAPI/Swagger interativa em /docs</text>
    <text x="35" y="274" font-family="Arial, sans-serif" font-size="9.5" fill="#475569">• Driver PyMongo com pooling de conexões assíncronas</text>
    <text x="35" y="300" font-family="monospace" font-size="9" fill="#0284C7">uvicorn main:app --reload --host 0.0.0.0 --port 8000</text>

    <!-- Processo 3 -->
    <rect x="25" y="350" width="400" height="140" rx="6" fill="#FFFFFF" stroke="#EA580C" stroke-width="1.5"/>
    <text x="35" y="370" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#C2410C">Processo Batch Concorrente (run_scrapers.py)</text>
    <text x="35" y="390" font-family="Arial, sans-serif" font-size="9.5" fill="#475569">• Multi-threading paralelo (ThreadPoolExecutor)</text>
    <text x="35" y="408" font-family="Arial, sans-serif" font-size="9.5" fill="#475569">• Scrapers: PRAE, PROEX, Portal UERN, UFERSA, CIEE</text>
    <text x="35" y="426" font-family="Arial, sans-serif" font-size="9.5" fill="#475569">• Extração: Requests + BeautifulSoup + Selenium Headless</text>
    <text x="35" y="444" font-family="Arial, sans-serif" font-size="9.5" fill="#475569">• Normalização: pdfplumber, PyPDF2 e módulo Regex</text>
    <text x="35" y="470" font-family="monospace" font-size="9" fill="#EA580C">make scrape / python run_scrapers.py</text>

    <!-- Armazenamento Local -->
    <rect x="25" y="510" width="400" height="120" rx="6" fill="#FFFFFF" stroke="#475569" stroke-width="1.5"/>
    <text x="35" y="530" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#334155">Sistema de Arquivos Local (Storage)</text>
    <text x="35" y="550" font-family="Arial, sans-serif" font-size="9.5" fill="#475569">• logs/*.log (Logs isolados por robô de coleta)</text>
    <text x="35" y="568" font-family="Arial, sans-serif" font-size="9.5" fill="#475569">• config/course_mapping.json (Categorias por Área/Curso)</text>
    <text x="35" y="586" font-family="Arial, sans-serif" font-size="9.5" fill="#475569">• Makefile e start.sh (Automação de inicialização)</text>
  </g>

  <!-- NÓ BANCO DE DADOS -->
  <g transform="translate(870, 100)">
    <polygon points="0,20 20,0 240,0 220,20" fill="#CBD5E1" stroke="#475569"/>
    <polygon points="240,0 240,240 220,260 220,20" fill="#94A3B8" stroke="#475569"/>
    <rect x="0" y="20" width="220" height="240" fill="#F8FAFC" stroke="#475569" stroke-width="1.5" filter="url(#sd5)"/>
    <text x="110" y="45" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#1E293B" text-anchor="middle">&lt;&lt;database-server&gt;&gt;</text>
    <text x="110" y="60" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#334155" text-anchor="middle">MongoDB 7.0 (NoSQL)</text>

    <rect x="15" y="80" width="190" height="160" rx="6" fill="#FFFFFF" stroke="#475569" stroke-width="1.5"/>
    <text x="25" y="105" font-family="Arial, sans-serif" font-size="10" font-weight="bold" fill="#334155">Database: hub_estudantes</text>
    <text x="25" y="130" font-family="monospace" font-size="9" fill="#1E293B">• col: oportunidades</text>
    <text x="25" y="150" font-family="monospace" font-size="9" fill="#1E293B">• col: usuarios</text>
    <text x="25" y="175" font-family="Arial, sans-serif" font-size="8.5" fill="#64748B">Índices Textuais (titulo, tags)</text>
    <text x="25" y="195" font-family="Arial, sans-serif" font-size="8.5" fill="#64748B">Índices de Data (data_limite)</text>
    <text x="25" y="220" font-family="monospace" font-size="9" fill="#0284C7">Porta TCP: :27017</text>
  </g>

  <!-- NÓ FONTES EXTERNAS -->
  <g transform="translate(870, 420)">
    <rect x="0" y="0" width="230" height="220" rx="16" fill="#FEF3C7" stroke="#D97706" stroke-width="2" filter="url(#sd5)"/>
    <text x="115" y="28" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#B45309" text-anchor="middle">&lt;&lt;cloud&gt;&gt; Fontes Externas</text>

    <rect x="15" y="45" width="200" height="32" rx="4" fill="#FFFFFF" stroke="#D97706"/>
    <text x="25" y="66" font-family="Arial, sans-serif" font-size="9.5" fill="#78350F">Portal UERN &amp; Diários JOUERN</text>

    <rect x="15" y="85" width="200" height="32" rx="4" fill="#FFFFFF" stroke="#D97706"/>
    <text x="25" y="106" font-family="Arial, sans-serif" font-size="9.5" fill="#78350F">Pró-Reitorias PRAE &amp; PROEX</text>

    <rect x="15" y="125" width="200" height="32" rx="4" fill="#FFFFFF" stroke="#D97706"/>
    <text x="25" y="146" font-family="Arial, sans-serif" font-size="9.5" fill="#78350F">Portal de Editais UFERSA</text>

    <rect x="15" y="165" width="200" height="32" rx="4" fill="#FFFFFF" stroke="#D97706"/>
    <text x="25" y="186" font-family="Arial, sans-serif" font-size="9.5" fill="#78350F">Agente de Integração CIEE</text>
  </g>

  <!-- Linhas -->
  <line x1="300" y1="210" x2="385" y2="210" stroke="#3B82F6" stroke-width="2"/>
  <text x="340" y="200" font-family="Arial, sans-serif" font-size="9" fill="#1D4ED8" text-anchor="middle">HTTP :3000</text>

  <path d="M 275 250 L 320 250 L 320 330 L 385 330" fill="none" stroke="#0284C7" stroke-width="2"/>
  <text x="345" y="320" font-family="Arial, sans-serif" font-size="9" fill="#0284C7">REST :8000</text>

  <line x1="785" y1="230" x2="870" y2="230" stroke="#475569" stroke-width="2"/>
  <text x="825" y="220" font-family="Arial, sans-serif" font-size="9" fill="#334155" text-anchor="middle">PyMongo :27017</text>

  <line x1="785" y1="500" x2="870" y2="500" stroke="#EA580C" stroke-width="2"/>
  <text x="825" y="490" font-family="Arial, sans-serif" font-size="9" fill="#EA580C" text-anchor="middle">Scraping HTTP</text>

  <path d="M 785 460 L 830 460 L 830 260 L 870 260" fill="none" stroke="#EA580C" stroke-width="2"/>
  <text x="840" y="360" font-family="Arial, sans-serif" font-size="9" fill="#EA580C">Persistência</text>
</svg>
"""

# ==============================================================================
# DIAGRAMA 6: COMPONENTES MODULARES
# ==============================================================================
extra_svgs["diagrama_06_componentes_sistema"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 750" width="100%" height="100%">
  <defs>
    <filter id="sd6" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="2" dy="2" stdDeviation="3" flood-opacity="0.12"/>
    </filter>
  </defs>

  <rect width="1100" height="750" fill="#FFFFFF"/>
  <text x="550" y="38" font-family="Arial, sans-serif" font-size="20" font-weight="bold" fill="#003366" text-anchor="middle">
    Diagrama de Componentes – Visão Arquitetural Modular (EduScrap)
  </text>
  <text x="550" y="58" font-family="Arial, sans-serif" font-size="12" fill="#718096" text-anchor="middle">
    Desacoplamento em quatro camadas principais: Apresentação, Serviços de API, Ingestão e Persistência
  </text>

  <!-- CAMADA 1: FRONTEND -->
  <rect x="40" y="90" width="1020" height="120" rx="8" fill="#F0F9FF" stroke="#0284C7" stroke-width="1.5" filter="url(#sd6)"/>
  <text x="60" y="115" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#0369A1">Camada de Apresentação (Frontend SPA - Porta 3000)</text>

  <g transform="translate(60, 130)">
    <rect width="210" height="60" rx="4" fill="#FFFFFF" stroke="#0284C7"/>
    <text x="105" y="28" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#0369A1" text-anchor="middle">UI Controller</text>
    <text x="105" y="46" font-family="Arial, sans-serif" font-size="9" fill="#475569" text-anchor="middle">Gerenciador de Estado e Eventos</text>
  </g>

  <g transform="translate(300, 130)">
    <rect width="220" height="60" rx="4" fill="#FFFFFF" stroke="#0284C7"/>
    <text x="110" y="28" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#0369A1" text-anchor="middle">Donut Chart Renderer</text>
    <text x="110" y="46" font-family="Arial, sans-serif" font-size="9" fill="#475569" text-anchor="middle">Cálculo de Vigência &amp; Arcos SVG</text>
  </g>

  <g transform="translate(550, 130)">
    <rect width="230" height="60" rx="4" fill="#FFFFFF" stroke="#0284C7"/>
    <text x="115" y="28" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#0369A1" text-anchor="middle">Filter &amp; Search Engine</text>
    <text x="115" y="46" font-family="Arial, sans-serif" font-size="9" fill="#475569" text-anchor="middle">Filtros por Cursos, Áreas e Fontes</text>
  </g>

  <g transform="translate(810, 130)">
    <rect width="230" height="60" rx="4" fill="#FFFFFF" stroke="#0284C7"/>
    <text x="115" y="28" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#0369A1" text-anchor="middle">Theme Switcher</text>
    <text x="115" y="46" font-family="Arial, sans-serif" font-size="9" fill="#475569" text-anchor="middle">Dark Mode &amp; Logo Dinâmico</text>
  </g>

  <!-- CAMADA 2: BACKEND FASTAPI -->
  <rect x="40" y="250" width="1020" height="120" rx="8" fill="#F8FAFC" stroke="#334155" stroke-width="1.5" filter="url(#sd6)"/>
  <text x="60" y="275" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#1E293B">Camada de Serviços (FastAPI Backend - Porta 8000)</text>

  <g transform="translate(60, 290)">
    <rect width="290" height="60" rx="4" fill="#FFFFFF" stroke="#334155"/>
    <text x="145" y="28" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#1E293B" text-anchor="middle">REST Routers (/api/*)</text>
    <text x="145" y="46" font-family="Arial, sans-serif" font-size="9" fill="#475569" text-anchor="middle">/oportunidades, /editais, /vagas, /health</text>
  </g>

  <g transform="translate(380, 290)">
    <rect width="320" height="60" rx="4" fill="#FFFFFF" stroke="#334155"/>
    <text x="160" y="28" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#1E293B" text-anchor="middle">Pydantic Schemas &amp; Serializers</text>
    <text x="160" y="46" font-family="Arial, sans-serif" font-size="9" fill="#475569" text-anchor="middle">Validação Estrutural e Tipagem Estrita</text>
  </g>

  <g transform="translate(730, 290)">
    <rect width="310" height="60" rx="4" fill="#FFFFFF" stroke="#334155"/>
    <text x="155" y="28" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#1E293B" text-anchor="middle">CORS &amp; Docs Generator</text>
    <text x="155" y="46" font-family="Arial, sans-serif" font-size="9" fill="#475569" text-anchor="middle">Integração Segura &amp; Swagger (/docs)</text>
  </g>

  <!-- CAMADA 3: INGESTÃO E PROCESSAMENTO -->
  <rect x="40" y="410" width="1020" height="150" rx="8" fill="#FFFBEB" stroke="#D97706" stroke-width="1.5" filter="url(#sd6)"/>
  <text x="60" y="435" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#92400E">Camada de Ingestão e Processamento (Batch Concorrente)</text>

  <g transform="translate(60, 450)">
    <rect width="210" height="80" rx="4" fill="#FFFFFF" stroke="#D97706"/>
    <text x="105" y="26" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#92400E" text-anchor="middle">Scraper Orchestrator</text>
    <text x="105" y="44" font-family="Arial, sans-serif" font-size="9" fill="#475569" text-anchor="middle">run_scrapers.py Multi-Thread</text>
    <text x="105" y="62" font-family="monospace" font-size="8.5" fill="#B45309" text-anchor="middle">Isolamento de logs/</text>
  </g>

  <g transform="translate(290, 450)">
    <rect width="220" height="80" rx="4" fill="#FFFFFF" stroke="#D97706"/>
    <text x="110" y="26" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#92400E" text-anchor="middle">Scrapers Estáticos (BS4)</text>
    <text x="110" y="44" font-family="Arial, sans-serif" font-size="9" fill="#475569" text-anchor="middle">Requests + BeautifulSoup</text>
    <text x="110" y="62" font-family="Arial, sans-serif" font-size="8.5" fill="#78350F" text-anchor="middle">PRAE, PROEX, Portal UERN</text>
  </g>

  <g transform="translate(530, 450)">
    <rect width="230" height="80" rx="4" fill="#FFFFFF" stroke="#D97706"/>
    <text x="115" y="26" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#92400E" text-anchor="middle">Scrapers Dinâmicos</text>
    <text x="115" y="44" font-family="Arial, sans-serif" font-size="9" fill="#475569" text-anchor="middle">Selenium WebDriver Headless</text>
    <text x="115" y="62" font-family="Arial, sans-serif" font-size="8.5" fill="#78350F" text-anchor="middle">Portal de Vagas CIEE</text>
  </g>

  <g transform="translate(780, 450)">
    <rect width="260" height="80" rx="4" fill="#FFFFFF" stroke="#16A34A" stroke-width="1.5"/>
    <text x="130" y="26" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#15803D" text-anchor="middle">Normalizer &amp; PDF Engine</text>
    <text x="130" y="44" font-family="Arial, sans-serif" font-size="9" fill="#475569" text-anchor="middle">pdfplumber + Expressões Regulares</text>
    <text x="130" y="62" font-family="Arial, sans-serif" font-size="8.5" fill="#166534" text-anchor="middle">Validação Temporal Heurística</text>
  </g>

  <!-- CAMADA 4: PERSISTÊNCIA -->
  <rect x="40" y="600" width="1020" height="110" rx="8" fill="#F8FAFC" stroke="#475569" stroke-width="1.5" filter="url(#sd6)"/>
  <text x="60" y="625" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#1E293B">Camada de Persistência (MongoDB NoSQL - Porta 27017)</text>

  <g transform="translate(60, 640)">
    <rect width="450" height="50" rx="4" fill="#FFFFFF" stroke="#475569"/>
    <text x="225" y="24" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#334155" text-anchor="middle">Coleção: oportunidades</text>
    <text x="225" y="40" font-family="Arial, sans-serif" font-size="9" fill="#64748B" text-anchor="middle">Documentos polimórficos (editais, vagas, notícias) + Índices de texto e datas</text>
  </g>

  <g transform="translate(550, 640)">
    <rect width="490" height="50" rx="4" fill="#FFFFFF" stroke="#475569"/>
    <text x="245" y="24" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#334155" text-anchor="middle">Coleção: usuarios &amp; database_setup.py</text>
    <text x="245" y="40" font-family="Arial, sans-serif" font-size="9" fill="#64748B" text-anchor="middle">Preferências de cursos e validação de integridade estrutural (JSON Schema)</text>
  </g>

  <!-- Linhas conectoras -->
  <line x1="550" y1="210" x2="550" y2="250" stroke="#0284C7" stroke-width="2"/>
  <line x1="200" y1="370" x2="200" y2="600" stroke="#334155" stroke-width="2"/>
  <line x1="910" y1="530" x2="910" y2="600" stroke="#16A34A" stroke-width="2"/>
</svg>
"""

# ==============================================================================
# DIAGRAMA 7: ESTADOS DO EDITAL ATUALIZADO
# ==============================================================================
extra_svgs["diagrama_07_estados_edital"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 700" width="100%" height="100%">
  <defs>
    <filter id="sd7" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="2" dy="2" stdDeviation="3" flood-opacity="0.12"/>
    </filter>
    <marker id="m7" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#1A365D"/>
    </marker>
  </defs>

  <rect width="1000" height="700" fill="#FFFFFF"/>
  <text x="500" y="38" font-family="Arial, sans-serif" font-size="20" font-weight="bold" fill="#003366" text-anchor="middle">
    Diagrama de Estados – Ciclo de Vida do Objeto Edital / Oportunidade
  </text>
  <text x="500" y="58" font-family="Arial, sans-serif" font-size="12" fill="#718096" text-anchor="middle">
    Transições de estados desde a descoberta pelo robô até o encerramento do prazo regulamentar
  </text>

  <!-- Ponto Inicial -->
  <circle cx="80" cy="170" r="14" fill="#1A365D"/>
  <text x="80" y="205" font-family="Arial, sans-serif" font-size="10" fill="#64748B" text-anchor="middle">Início</text>

  <!-- Estado 1: Descoberto -->
  <g transform="translate(160, 140)">
    <rect width="160" height="60" rx="10" fill="#F8FAFC" stroke="#475569" stroke-width="2" filter="url(#sd7)"/>
    <text x="80" y="28" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#1E293B" text-anchor="middle">Descoberto</text>
    <text x="80" y="46" font-family="Arial, sans-serif" font-size="9.5" fill="#64748B" text-anchor="middle">URL identificada</text>
  </g>

  <!-- Transição Início -> Descoberto -->
  <line x1="94" y1="170" x2="150" y2="170" stroke="#1A365D" stroke-width="1.5" marker-end="url(#m7)"/>

  <!-- Estado 2: Em Extração -->
  <g transform="translate(410, 140)">
    <rect width="180" height="60" rx="10" fill="#F0F9FF" stroke="#0284C7" stroke-width="2" filter="url(#sd7)"/>
    <text x="90" y="28" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#0369A1" text-anchor="middle">Em Extração</text>
    <text x="90" y="46" font-family="Arial, sans-serif" font-size="9.5" fill="#0284C7" text-anchor="middle">Download HTML / PDF</text>
  </g>

  <!-- Transição Descoberto -> Em Extração -->
  <line x1="320" y1="170" x2="400" y2="170" stroke="#1A365D" stroke-width="1.5" marker-end="url(#m7)"/>
  <text x="365" y="160" font-family="Arial, sans-serif" font-size="9" fill="#475569" text-anchor="middle">Inicia coleta</text>

  <!-- Estado Composto: Em Normalização -->
  <g transform="translate(680, 100)">
    <rect width="280" height="140" rx="10" fill="#F0FDF4" stroke="#16A34A" stroke-width="2" filter="url(#sd7)"/>
    <text x="140" y="25" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#15803D" text-anchor="middle">Em Normalização (Regex Engine)</text>
    <rect x="20" y="40" width="240" height="35" rx="6" fill="#FFFFFF" stroke="#16A34A"/>
    <text x="140" y="62" font-family="Arial, sans-serif" font-size="10" fill="#15803D" text-anchor="middle">Extraindo Data Limite e Número</text>
    <rect x="20" y="85" width="240" height="35" rx="6" fill="#FFFFFF" stroke="#16A34A"/>
    <text x="140" y="107" font-family="Arial, sans-serif" font-size="10" fill="#15803D" text-anchor="middle">Comparando: Data Limite vs. Hoje</text>
  </g>

  <!-- Transição Em Extração -> Em Normalização -->
  <line x1="590" y1="170" x2="670" y2="170" stroke="#1A365D" stroke-width="1.5" marker-end="url(#m7)"/>
  <text x="635" y="160" font-family="Arial, sans-serif" font-size="9" fill="#475569" text-anchor="middle">Texto extraído</text>

  <!-- Estado: Inválido -->
  <g transform="translate(410, 290)">
    <rect width="180" height="60" rx="10" fill="#FEF2F2" stroke="#EF4444" stroke-width="2" filter="url(#sd7)"/>
    <text x="90" y="28" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#991B1B" text-anchor="middle">Inválido / Erro</text>
    <text x="90" y="46" font-family="Arial, sans-serif" font-size="9.5" fill="#DC2626" text-anchor="middle">Falha de parse / PDF ilegível</text>
  </g>

  <!-- Transição Normalização -> Inválido -->
  <path d="M 720 240 L 720 320 L 600 320" fill="none" stroke="#EF4444" stroke-width="1.5" marker-end="url(#m7)"/>
  <text x="660" y="310" font-family="Arial, sans-serif" font-size="9" fill="#EF4444">Erro de Regex / Timeout</text>

  <!-- Estado: Aberto (Vigente) -->
  <g transform="translate(720, 370)">
    <rect width="200" height="65" rx="10" fill="#ECFDF5" stroke="#059669" stroke-width="2.5" filter="url(#sd7)"/>
    <text x="100" y="28" font-family="Arial, sans-serif" font-size="13" font-weight="bold" fill="#065F46" text-anchor="middle">Aberto / Vigente</text>
    <text x="100" y="48" font-family="Arial, sans-serif" font-size="10" fill="#047857" text-anchor="middle">Data Limite &gt;= Data Atual</text>
  </g>

  <!-- Transição Normalização -> Aberto -->
  <line x1="820" y1="240" x2="820" y2="360" stroke="#059669" stroke-width="2" marker-end="url(#m7)"/>
  <text x="830" y="300" font-family="Arial, sans-serif" font-size="9.5" font-weight="bold" fill="#059669">Prazo ativo</text>

  <!-- Estado: Prazo Crítico (Alerta) -->
  <g transform="translate(720, 490)">
    <rect width="200" height="60" rx="10" fill="#FFFBEB" stroke="#D97706" stroke-width="2" filter="url(#sd7)"/>
    <text x="100" y="26" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#92400E" text-anchor="middle">Prazo Crítico (Alerta)</text>
    <text x="100" y="44" font-family="Arial, sans-serif" font-size="9.5" fill="#B45309" text-anchor="middle">Faltam &lt;= 3 dias para fechar</text>
  </g>

  <!-- Transição Aberto -> Prazo Crítico -->
  <line x1="820" y1="435" x2="820" y2="480" stroke="#D97706" stroke-width="1.5" marker-end="url(#m7)"/>
  <text x="830" y="460" font-family="Arial, sans-serif" font-size="9" fill="#D97706">Aproximação do fim</text>

  <!-- Estado: Encerrado -->
  <g transform="translate(410, 490)">
    <rect width="180" height="60" rx="10" fill="#F1F5F9" stroke="#64748B" stroke-width="2" filter="url(#sd7)"/>
    <text x="90" y="28" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#334155" text-anchor="middle">Encerrado</text>
    <text x="90" y="46" font-family="Arial, sans-serif" font-size="9.5" fill="#64748B" text-anchor="middle">Data Limite &lt; Data Atual</text>
  </g>

  <!-- Transição Prazo Crítico -> Encerrado -->
  <line x1="720" y1="520" x2="600" y2="520" stroke="#64748B" stroke-width="2" marker-end="url(#m7)"/>
  <text x="660" y="510" font-family="Arial, sans-serif" font-size="9" fill="#475569" text-anchor="middle">Data expirada</text>

  <!-- Transição Aberto -> Encerrado direto -->
  <path d="M 720 400 L 500 400 L 500 480" fill="none" stroke="#64748B" stroke-width="1.5" marker-end="url(#m7)"/>
  <text x="590" y="390" font-family="Arial, sans-serif" font-size="9" fill="#475569">Expira sem aviso</text>

  <!-- Ponto Final -->
  <g transform="translate(200, 520)">
    <circle cx="0" cy="0" r="14" fill="none" stroke="#1E293B" stroke-width="2"/>
    <circle cx="0" cy="0" r="8" fill="#1E293B"/>
  </g>
  <text x="200" y="550" font-family="Arial, sans-serif" font-size="10" fill="#64748B" text-anchor="middle">Fim do Ciclo</text>

  <line x1="410" y1="520" x2="225" y2="520" stroke="#1E293B" stroke-width="1.5" marker-end="url(#m7)"/>
  <path d="M 410 320 L 200 320 L 200 500" fill="none" stroke="#EF4444" stroke-width="1.5" marker-end="url(#m7)"/>
</svg>
"""

# Salvar todos os novos SVGs
for name, content in extra_svgs.items():
    svg_path = os.path.join(OUT_DIR, f"{name}.svg")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"SVG salvo: {svg_path}")

print("Todos os 7 SVGs foram salvos com sucesso!")
