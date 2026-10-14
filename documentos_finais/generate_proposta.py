import os
import subprocess

html_content = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Proposta do Projeto - EduScrap</title>
<style>
    @page {
        size: A4;
        margin: 2.5cm 2.5cm 2.5cm 2.5cm;
    }
    body {
        font-family: 'Times New Roman', Times, serif;
        font-size: 12pt;
        line-height: 1.5;
        color: #111;
        text-align: justify;
        margin: 0;
        padding: 0;
    }
    .header-box {
        text-align: center;
        font-weight: bold;
        text-transform: uppercase;
        margin-bottom: 25px;
        line-height: 1.3;
    }
    .header-box .institution {
        font-size: 12pt;
    }
    .header-box .department {
        font-size: 11pt;
        margin-top: 4px;
    }
    .header-box .project-title {
        font-size: 13pt;
        margin-top: 15px;
    }
    .header-box .template-type {
        font-size: 11pt;
        margin-top: 10px;
        font-weight: bold;
    }
    .team-box {
        border: 1.5px solid #000;
        padding: 12px;
        text-align: center;
        margin: 20px 0 25px 0;
        background-color: #fcfcfc;
    }
    .team-box .team-title {
        font-weight: bold;
        font-size: 12pt;
        margin-bottom: 6px;
    }
    .team-box .members {
        font-size: 11pt;
    }
    h2 {
        font-size: 12pt;
        font-weight: bold;
        margin-top: 25px;
        margin-bottom: 8px;
        color: #000;
        text-transform: none;
    }
    p.instruction {
        font-style: italic;
        color: #444;
        margin-top: 0;
        margin-bottom: 12px;
        font-size: 11pt;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 15px 0 25px 0;
        font-size: 10.5pt;
    }
    table, th, td {
        border: 1px solid #000;
    }
    th {
        background-color: #f0f0f0;
        font-weight: bold;
        text-align: center;
        padding: 8px;
    }
    td {
        padding: 8px;
        vertical-align: top;
    }
    td.center {
        text-align: center;
        vertical-align: middle;
    }
    ul {
        margin-top: 6px;
        margin-bottom: 12px;
        padding-left: 25px;
    }
    li {
        margin-bottom: 6px;
    }
    .activity-item {
        margin-bottom: 16px;
    }
    .activity-title {
        font-weight: bold;
        margin-bottom: 4px;
    }
    .activity-desc {
        margin-bottom: 4px;
    }
    .activity-res {
        font-style: normal;
    }
    .page-break {
        page-break-before: always;
    }
</style>
</head>
<body>

<div class="header-box">
    <div class="institution">UNIVERSIDADE DO ESTADO DO RIO GRANDE DO NORTE – UERN</div>
    <div class="institution">FACULDADE DE CIÊNCIAS EXATAS E NATURAIS – FANAT</div>
    <div class="department">DEPARTAMENTO DE INFORMÁTICA – DI</div>
    <div class="project-title">PROJETO INTEGRADOR</div>
    <div class="template-type">TEMPLATE DO PROJETO<br>PROPOSTA DO PROJETO (X) Versão inicial (X) Versão Atualizada</div>
</div>

<div class="team-box">
    <div class="team-title">NOME DA EQUIPE: EduScrap / EstudanteHUB (Evolução do projeto TECHHUB)</div>
    <div class="members"><strong>Equipe:</strong> Ana Kelry Fernandes Cabral do Nascimento &nbsp;|&nbsp; Luiz Fernando Santos Teixeira</div>
</div>

<h2>1. Metodologia de execução/Cronograma:</h2>
<p class="instruction">Crie uma tabela contendo todas as atividades que serão desenvolvidas e as datas de execução para todas elas.</p>

<table>
    <thead>
        <tr>
            <th style="width: 58%;">Atividade</th>
            <th style="width: 17%;">Prazo</th>
            <th style="width: 25%;">Responsáveis</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>
                <strong>Semana 1: Modelagem de Dados, Arquitetura de Coleta e Infraestrutura</strong><br>
                Definição do schema flexível no MongoDB para suportar fontes heterogêneas (Editais, Vagas, Notícias). Configuração de regras de validação estrutural (JSON Schema) e criação de índices compostos e de busca textual. Implementação dos scripts base de extração web com <em>Requests</em> e <em>BeautifulSoup</em> para fontes estáticas. Estruturação do repositório, ambiente virtual e scripts de automação.
            </td>
            <td class="center">Semana 1</td>
            <td class="center">Luiz Fernando e<br>Ana Kelry</td>
        </tr>
        <tr>
            <td>
                <strong>Semana 2: Processamento de PDFs e Motor de Expressões Regulares (Regex)</strong><br>
                Implementação de módulos robustos de leitura de arquivos PDF (utilizando <code>pdfplumber</code> e <code>PyPDF2</code>), com foco nos Diários Oficiais (JOUERN) e repositórios institucionais da UERN. Desenvolvimento de padrões refinados de Expressões Regulares (Regex) para extração precisa de número de edital, datas de vigência/validade, valores de bolsas/remuneração e requisitos mínimos, mitigando a necessidade de processamento pesado de PLN no servidor.
            </td>
            <td class="center">Semana 2</td>
            <td class="center">Luiz Fernando e<br>Ana Kelry</td>
        </tr>
        <tr>
            <td>
                <strong>Semana 3: Lógica de Negócio, Validação Temporal e Scraping Paralelo Concorrente</strong><br>
                Desenvolvimento da camada de validação temporal no backend, comparando automaticamente a data limite extraída com a data atual para rotulação dinâmica do status ("Aberto / Vigente" ou "Encerrado"). Implementação da categorização automática por Áreas de Conhecimento (Tecnologia, Saúde, Humanas, Exatas, Sociais Aplicadas). Construção do orquestrador concorrente (<code>run_scrapers.py</code>) com isolamento de logs individuais por robô em <code>logs/</code> e mecanismo de retentativa (retry).
            </td>
            <td class="center">Semana 3</td>
            <td class="center">Luiz Fernando e<br>Ana Kelry</td>
        </tr>
        <tr>
            <td>
                <strong>Semana 4: Desenvolvimento da API RESTful (FastAPI) e Interface Web Responsiva</strong><br>
                Implementação do backend com <strong>FastAPI</strong> assíncrono e Uvicorn, disponibilizando rotas REST documentadas automaticamente via OpenAPI/Swagger (<code>/docs</code>) com suporte a CORS. Criação do Frontend SPA (Single Page Application) moderno e responsivo, dotado de seletor dinâmico de áreas e cursos, filtros instantâneos no lado do cliente e suporte a alternância dinâmica de Tema Claro e Tema Escuro (Dark Mode).
            </td>
            <td class="center">Semana 4</td>
            <td class="center">Luiz Fernando e<br>Ana Kelry</td>
        </tr>
        <tr>
            <td>
                <strong>Semana 5: Componente Analítico de Prazos (Gráfico Donut), Otimizações e Testes</strong><br>
                Implementação do painel de monitoramento temporal de prazos com componente gráfico interativo tipo <strong>Donut</strong> (gráfico de rosca) para exibição imediata do balanço entre editais abertos e encerrados. Realização de testes de carga simulando múltiplos acessos simultâneos, otimização das consultas no MongoDB com índices consolidados. Implementação de suíte de testes automatizados com <code>pytest</code> e automação de inicialização via <code>start.sh</code> e <code>Makefile</code>.
            </td>
            <td class="center">Semana 5</td>
            <td class="center">Luiz Fernando e<br>Ana Kelry</td>
        </tr>
        <tr>
            <td>
                <strong>Semana 6: Homologação Ponta a Ponta, Refinamento Visual e Entrega Final</strong><br>
                Validação integral do fluxo: coleta concorrente nas fontes reais (PRAE/UERN, Portal UERN, UFERSA, CIEE), normalização de metadados, persistência no MongoDB e renderização no frontend. Correção de bugs visuais, auditoria de contraste e acessibilidade, refinamento de mensagens de erro e finalização da documentação técnica e arquitetural UML.
            </td>
            <td class="center">Semana 6</td>
            <td class="center">Luiz Fernando e<br>Ana Kelry</td>
        </tr>
    </tbody>
</table>

<div class="page-break"></div>

<h2>2. Justificativa de aderência da proposta ao tema escolhido:</h2>
<p>
    A proposta do <strong>EduScrap</strong> ataca frontalmente o problema crônico da <strong>dispersão informacional de oportunidades</strong> no ambiente universitário e acadêmico regional. Atualmente, os discentes da Universidade do Estado do Rio Grande do Norte (UERN) enfrentam significativas barreiras de usabilidade e praticidade para descobrir editais de monitoria, pesquisa (PIBIC), extensão (PIBEX), bolsas de assistência estudantil (PRAE) e vagas de estágio supervisionado.
</p>
<p>
    As oportunidades encontram-se fragmentadas em múltiplos canais desarticulados: edições volumosas do Jornal Oficial da UERN (JOUERN) em formato PDF não estruturado, páginas esparsas do portal institucional, comunicados nas redes sociais de faculdades isoladas (como FANAT, FAFIC, FAED) e plataformas externas (como CIEE e portais de instituições parceiras, como a UFERSA). Como consequência direta dessa descentralização, alunos frequentemente perdem prazos cruciais de inscrição ou deixam de concorrer a auxílios por simples falta de conhecimento.
</p>
<p>
    O projeto se alinha rigorosamente às diretrizes da disciplina de Projeto Integrador do Departamento de Informática da UERN por conceber uma solução tecnológica que alia engenharia de software aplicada, automação de processos, extração de dados e design centrado no usuário. O EduScrap democratiza o acesso à informação pública, nivelando as oportunidades para estudantes de diferentes cursos e realidades socioeconômicas, estendendo seu benefício inclusive para discentes do ensino básico e comunidade externa interessados em processos seletivos públicos da região.
</p>

<h2>3. Descreva o objeto do projeto (proposta).</h2>
<p class="instruction">Apresente de maneira clara e detalhada o produto, processo ou serviço proposto.</p>
<p>
    O <strong>EduScrap</strong> é uma plataforma web centralizada e responsiva de agregação, higienização e curadoria de oportunidades acadêmicas e profissionais. Seu objetivo primordial é fornecer aos estudantes uma experiência ágil, consolidada e em poucos cliques para acompanhamento de certames, processos seletivos e notícias do seu interesse formativo.
</p>
<p>A solução integra de forma coesa os seguintes pilares funcionais:</p>
<ul>
    <li><strong>Coleta Automatizada de Editais Oficiais:</strong> Monitoramento contínuo de publicações de editais de bolsas de fomento, auxílios de permanência discente e certames abertos da UERN e instituições congêneres (ex.: UFERSA, IFRN), extraindo dados estruturados diretamente de páginas web e documentos em PDF.</li>
    <li><strong>Agregação de Vagas de Estágio e Trainee:</strong> Integração automatizada com agentes de integração e portais de vagas reconhecidos (como o CIEE), filtrando anúncios compatíveis com o perfil universitário local.</li>
    <li><strong>Curadoria de Notícias Acadêmicas e Tecnológicas:</strong> Extração e organização de comunicados e novidades setoriais, categorizadas por curso e área do conhecimento (Tecnologia, Saúde, Humanas, Exatas, Sociais Aplicadas).</li>
    <li><strong>Painel Analítico de Prazos e Vigência:</strong> Indicador visual sintetizado por meio de um gráfico Donut (gráfico de rosca) e badges coloridas que informam instantaneamente se o prazo de submissão está ativo, próximo do encerramento ou expirado.</li>
    <li><strong>Feed Personalizado e Busca Inteligente:</strong> Mecanismo que permite ao aluno filtrar simultaneamente por sua área acadêmica, seu curso específico ou palavras-chave livres, entregando resultados em tempo sub-segundo graças à pré-indexação no banco de dados.</li>
</ul>

<h2>4. Quais são as possíveis inovações da proposta e o grau de impacto deste projeto na sociedade?</h2>
<p class="instruction">Descreva quais são as ações inovadoras utilizadas no processo de desenvolvimento, como também qual seria o grupo de indivíduos ou setores beneficiados com a utilização da solução proposta.</p>
<p>
    A principal inovação do EduScrap reside na sua <strong>Curadoria Contextualizada e Arquitetura de Coleta Concorrente em Segundo Plano</strong>. Ao contrário de agregadores genéricos de emprego ou buscadores web convencionais, o EduScrap incorpora as regras de negócio e os padrões formais específicos dos atos administrativos da UERN e da administração pública regional.
</p>
<p>Destacam-se como ações e diferenciais inovadores no desenvolvimento:</p>
<ul>
    <li><strong>Orquestrador Concorrente Paralelo (Multi-Worker):</strong> Implementação do orquestrador <code>run_scrapers.py</code>, capaz de disparar múltiplos robôs de coleta simultaneamente de forma não bloqueante. Cada robô opera com isolamento de logs (gerando arquivos específicos em <code>logs/</code>) e rotinas de tolerância a falhas, garantindo que a instabilidade de uma fonte externa não comprometa a execução das demais.</li>
    <li><strong>Abordagem de Pré-Processamento Leve e Eficiente:</strong> Em vez de sobrecarregar a infraestrutura com modelos pesados de Inteligência Artificial generativa ou redes neurais densas para análise textual, o sistema implementa um pipeline baseado em <strong>Expressões Regulares Otimizadas (Regex)</strong> e heurísticas temporais. Isso assegura baixo consumo de memória RAM e processamento veloz em hardware modesto de hospedagem acadêmica.</li>
    <li><strong>Validação Temporal Heurística Automatizada:</strong> O normalizador compara as datas limite capturadas no texto do edital com o relógio do servidor, calculando automaticamente os estados de vigência ("Aberto / Vigente" vs. "Encerrado"), eliminando a necessidade de intervenção humana cotidiana para catalogação de status.</li>
    <li><strong>Visualização de Prazos com Gráfico Donut Integrado:</strong> Adoção de elementos visuais de alta densidade informativa na interface do discente, permitindo que o estudante compreenda a disponibilidade de oportunidades em frações de segundo.</li>
</ul>
<p>
    <strong>Impacto Social e Grupos Beneficiados:</strong> O público prioritário é composto pelos discentes de graduação e pós-graduação da UERN e universidades vizinhas. O impacto social é direto na permanência estudantil, pois a concessão de bolsas de auxílio-transporte, alimentação, moradia e iniciação científica depende estritamente do cumprimento de prazos rígidos. O EduScrap fecha o abismo informacional entre o edital publicado no diário oficial e o estudante em situação de vulnerabilidade, potencializando a empregabilidade acadêmica e a inserção profissional no mercado potiguar.
</p>

<div class="page-break"></div>

<h2>5. Descreva a viabilidade técnica da proposta.</h2>
<p class="instruction">Apresente aqui os possíveis instrumentos necessários para o desenvolvimento e utilização da solução proposta.</p>
<p>
    A viabilidade técnica foi comprovada pela implementação integral e harmoniosa de tecnologias maduras, abertas e de alto desempenho:
</p>

<ul>
    <li><strong>Linguagem e Backend:</strong>
        <ul>
            <li><strong>Python 3.12:</strong> Linguagem robusta, com ecossistema líder no mercado para web scraping, manipulação de dados e automação de serviços.</li>
            <li><strong>FastAPI & Uvicorn:</strong> Framework web assíncrono de altíssima performance (baseado em Starlette e Pydantic), responsável pela API RESTful, validação automática de dados, documentação interativa OpenAPI/Swagger (acessível em <code>/docs</code>) e controle de CORS para integração transparente com o cliente.</li>
        </ul>
    </li>
    <li><strong>Motores de Extração e Leitura de Documentos:</strong>
        <ul>
            <li><strong>Requests & BeautifulSoup4:</strong> Para extração rápida, leve e com baixíssimo consumo de memória de páginas institucionais baseadas em HTML estático.</li>
            <li><strong>Selenium WebDriver (Firefox Headless):</strong> Utilizado estritamente para portais dinâmicos que requerem renderização via JavaScript no cliente e interação simulada de navegador (ex.: portal CIEE), operando em modo headless para não saturar a memória do host.</li>
            <li><strong>pdfplumber & PyPDF2:</strong> Bibliotecas especializadas para ingestão e extração de texto estruturado de diários oficiais e editais em formato PDF.</li>
            <li><strong>Expressões Regulares (Módulo nativo <code>re</code>):</strong> Conjunto de padrões regex compilados para identificar datas de inscrição, valores de remuneração, órgãos emissores e números de portarias com precisão determinística.</li>
        </ul>
    </li>
    <li><strong>Persistência de Dados (MongoDB NoSQL):</strong>
        <ul>
            <li>Banco de dados orientado a documentos NoSQL (versão 7.0+). Sua flexibilidade de esquema (<em>schema-less</em>) permite armazenar registros com estruturas heterogêneas (um edital possui campos que não existem em uma notícia ou vaga de estágio) sob uma mesma coleção padronizada (<code>oportunidades</code>).</li>
            <li>Configuração automatizada via <code>database_setup.py</code>, com definição de validação de schema (JSON Schema) para campos obrigatórios (título, link, data de coleta) e criação de índices compostos (por data e status) e índices de busca textual para consultas rápidas.</li>
        </ul>
    </li>
    <li><strong>Frontend Responsivo (SPA):</strong>
        <ul>
            <li>Construído com tecnologias web fundamentais (HTML5, CSS3 moderno com variáveis semânticas, JavaScript Vanilla modular).</li>
            <li>Suporte dinâmico a <strong>Tema Claro e Escuro (Dark Mode)</strong> com chaveamento de logo temático em SVG/PNG, design responsivo com Tailwind CSS / Flexbox / Grid e renderização analítica via gráficos interativos.</li>
        </ul>
    </li>
    <li><strong>DevOps, Testes e Automação:</strong>
        <ul>
            <li>Pipeline completo de inicialização com um único comando através do script <code>./start.sh</code> ou do <code>Makefile</code> (com alvos <code>make run</code>, <code>make scrape</code>, <code>make test</code> e <code>make setup</code>).</li>
            <li>Suíte de testes automatizados com <code>pytest</code> e <code>mongomock</code> em <code>tests/</code> para garantir regressão zero nos parsers e nas rotas da API.</li>
        </ul>
    </li>
</ul>

<h2>6. Detalhe as atividades propostas e possíveis resultados.</h2>
<p class="instruction">Apresente detalhadamente as atividades que pretendem ser desenvolvidas, os possíveis resultados e os produtos finais de cada etapa do processo de desenvolvimento da solução proposta.</p>

<div class="activity-item">
    <div class="activity-title">Atividade 1: Modelagem Estrutural, Configuração de Banco e Scrapers Base</div>
    <div class="activity-desc"><strong>Descrição:</strong> Modelagem e inicialização do cluster MongoDB com validação de regras de integridade e índices textuais. Implementação dos robôs de extração de dados brutos para os portais da PRAE/UERN, Portal UERN e UFERSA. Estruturação do fluxo concorrente e isolamento de logs por robô.</div>
    <div class="activity-res"><strong>Resultado/Produto Final:</strong> Banco de dados configurado (<code>database_setup.py</code>) e populado com dezenas de oportunidades reais categorizadas; pipeline de scraping paralelo operacional.</div>
</div>

<div class="activity-item">
    <div class="activity-title">Atividade 2: Processamento de Diários Oficiais e Extração de Metadados</div>
    <div class="activity-desc"><strong>Descrição:</strong> Desenvolvimento dos utilitários de processamento de documentos PDF (JOUERN) e integração com o motor de Expressões Regulares para decodificação precisa de datas de publicação, vigência de inscrições, valores de bolsas e categorias de certames.</div>
    <div class="activity-res"><strong>Resultado/Produto Final:</strong> Módulo de leitura e normalização documental capaz de converter publicações não estruturadas em coleções JSON padronizadas para consumo pelo sistema.</div>
</div>

<div class="activity-item">
    <div class="activity-title">Atividade 3: Lógica de Negócio Temporal e Categorização por Áreas</div>
    <div class="activity-desc"><strong>Descrição:</strong> Construção do algoritmo de validação de vigência (cálculo de dias restantes até o encerramento do edital) e mapeamento semântico dos cursos de graduação da universidade para suas respectivas áreas institucionais (Tecnologia, Saúde, Humanas, Exatas, Sociais Aplicadas).</div>
    <div class="activity-res"><strong>Resultado/Produto Final:</strong> Coleção de oportunidades enriquecida com status automatizado ("Aberto / Vigente", "Encerrado") e metadados de filtragem por afinidade acadêmica.</div>
</div>

<div class="activity-item">
    <div class="activity-title">Atividade 4: Implementação da API RESTful (FastAPI) e Interface SPA</div>
    <div class="activity-desc"><strong>Descrição:</strong> Criação dos endpoints da API no FastAPI (<code>/api/oportunidades</code>, <code>/api/editais</code>, <code>/api/vagas</code>, <code>/api/noticias</code>) e construção da interface web rica, incluindo barra de busca em tempo real, seletor visual de cursos, badges de vigência e alternância de tema claro/escuro.</div>
    <div class="activity-res"><strong>Resultado/Produto Final:</strong> Interface web interativa conectada à API RESTful assíncrona, operando com tempo de resposta sub-segundo e documentação interativa no Swagger.</div>
</div>

<div class="activity-item">
    <div class="activity-title">Atividade 5: Componente Analítico Donut, Homologação e Implantação</div>
    <div class="activity-desc"><strong>Descrição:</strong> Integração do componente analítico com gráfico Donut para visualização gráfica das métricas de prazos dos editais, bateria de testes com <code>pytest</code>, empacotamento com <code>start.sh</code>/<code>Makefile</code> e homologação ponta a ponta para uso piloto.</div>
    <div class="activity-res"><strong>Resultado/Produto Final:</strong> Plataforma EduScrap totalmente funcional, validada, robusta, documentada e pronta para apresentação perante a banca examinadora do Projeto Integrador.</div>
</div>

</body>
</html>
"""

output_html = "/home/ana/projetos/EduScrap/documentos_finais/Proposta_do_Projeto_EduScrap.html"
with open(output_html, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"HTML da Proposta gerado em: {output_html}")

# Converter para PDF via LibreOffice
cmd_pdf = [
    "libreoffice",
    "--headless",
    "-env:UserInstallation=file:///tmp/LibreOffice_Conversion",
    "--convert-to", "pdf",
    output_html,
    "--outdir", "/home/ana/projetos/EduScrap/documentos_finais"
]
subprocess.run(cmd_pdf, env={"HOME": "/tmp"}, check=True)
print("PDF da Proposta gerado com sucesso!")

# Converter para DOCX via LibreOffice
cmd_docx = [
    "libreoffice",
    "--headless",
    "-env:UserInstallation=file:///tmp/LibreOffice_Conversion",
    "--convert-to", "docx:MS Word 2007 XML",
    output_html,
    "--outdir", "/home/ana/projetos/EduScrap/documentos_finais"
]
subprocess.run(cmd_docx, env={"HOME": "/tmp"}, check=True)
print("DOCX da Proposta gerado com sucesso!")
