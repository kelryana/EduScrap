import os
import base64
import subprocess

def get_base64_image(image_path):
    if not os.path.exists(image_path):
        print(f"Aviso: imagem não encontrada: {image_path}")
        return ""
    with open(image_path, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode("utf-8")
        ext = os.path.splitext(image_path)[1].lower()
        mime = "image/png"
        if ext in [".jpg", ".jpeg"]:
            mime = "image/jpeg"
        elif ext == ".svg":
            mime = "image/svg+xml"
        return f"data:{mime};base64,{encoded}"

# Carregar todas as 15 imagens em Base64
img_caso_uso = get_base64_image("diagrams/caso_de_uso_diagrama.png")
img_conceitual = get_base64_image("diagrams/diagrama_conceitual.png")
img_seq1 = get_base64_image("diagrams/diagrama_sequencia.png")
img_seq2 = get_base64_image("diagrams/diagrama_sequencia2.png")
img_est_edital = get_base64_image("diagrams/diagrama_estado_edital.png")
img_est_job = get_base64_image("diagrams/diagrama_estado_job.png")
img_der = get_base64_image("diagrams/diagrama_entidade.png")
img_norm = get_base64_image("diagrams/diagrama_normalizador.png")
img_classes = get_base64_image("diagrams/diagrama_classes.png")
img_tela_hero = get_base64_image("diagrams/tela_principal_hero.png")
img_tela_donut = get_base64_image("diagrams/tela_prazos_donut.png")
img_tela_cards = get_base64_image("diagrams/tela_cards_oportunidades.png")
img_tela_dark = get_base64_image("diagrams/tela_tema_escuro.png")
img_tela_login = get_base64_image("diagrams/tela_login_estudante.png")
img_impl = get_base64_image("diagrams/implantasao.png")

html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Documento de Modelagem UML - EduScrap</title>
<style>
    @page {{
        size: A4;
        margin: 2.5cm 2.5cm 2.5cm 2.5cm;
        @bottom-right {{
            content: counter(page);
        }}
    }}
    body {{
        font-family: 'Times New Roman', Times, serif;
        font-size: 12pt;
        line-height: 1.5;
        color: #111;
        text-align: justify;
        margin: 0;
        padding: 0;
    }}
    .cover {{
        text-align: center;
        padding-top: 100px;
        height: 800px;
        page-break-after: always;
    }}
    .cover-title {{
        font-size: 16pt;
        font-weight: bold;
        line-height: 1.4;
        margin-bottom: 25px;
        text-transform: uppercase;
    }}
    .cover-project {{
        font-size: 20pt;
        font-weight: bold;
        color: #003366;
        margin-bottom: 10px;
    }}
    .cover-version {{
        font-size: 13pt;
        font-style: italic;
        margin-bottom: 250px;
    }}
    .cover-team {{
        font-size: 12pt;
        line-height: 1.6;
    }}
    .cover-leader {{
        margin-top: 20px;
        font-size: 12pt;
        font-weight: bold;
    }}
    .cover-email {{
        color: #003366;
        text-decoration: underline;
    }}
    h1 {{
        font-size: 14pt;
        font-weight: bold;
        margin-top: 30px;
        margin-bottom: 12px;
        color: #000;
        border-bottom: 1px solid #ddd;
        padding-bottom: 4px;
    }}
    h2 {{
        font-size: 12pt;
        font-weight: bold;
        margin-top: 22px;
        margin-bottom: 8px;
        color: #222;
    }}
    h3 {{
        font-size: 11pt;
        font-weight: bold;
        margin-top: 16px;
        margin-bottom: 6px;
    }}
    p {{
        margin-top: 0;
        margin-bottom: 10px;
        text-indent: 1.25cm;
    }}
    p.no-indent {{
        text-indent: 0;
    }}
    .figure-container {{
        text-align: center;
        margin: 20px 0;
        page-break-inside: avoid;
    }}
    .figure-container img {{
        max-width: 95%;
        max-height: 480px;
        height: auto;
        border: 1px solid #ccc;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        border-radius: 4px;
        padding: 4px;
        background: #fff;
    }}
    .figure-caption {{
        font-size: 10.5pt;
        font-weight: bold;
        margin-top: 8px;
        color: #333;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 15px 0 20px 0;
        font-size: 10pt;
    }}
    table, th, td {{
        border: 1px solid #444;
    }}
    th {{
        background-color: #f2f2f2;
        font-weight: bold;
        text-align: center;
        padding: 6px;
    }}
    td {{
        padding: 6px;
        vertical-align: top;
    }}
    td.center {{
        text-align: center;
        vertical-align: middle;
    }}
    ul, ol {{
        margin-top: 4px;
        margin-bottom: 10px;
        padding-left: 30px;
    }}
    li {{
        margin-bottom: 4px;
    }}
    .page-break {{
        page-break-before: always;
    }}
    .toc-item {{
        display: flex;
        justify-content: space-between;
        margin-bottom: 5px;
        font-size: 11pt;
    }}
    .note-box {{
        background-color: #f9f9f9;
        border-left: 4px solid #003366;
        padding: 8px 12px;
        margin: 12px 0;
        font-size: 10.5pt;
        font-style: italic;
    }}
</style>
</head>
<body>

<!-- CAPA -->
<div class="cover">
    <div class="cover-title">
        Universidade do Estado do Rio Grande do Norte – UERN<br>
        Faculdade de Ciências Exatas e Naturais – FANAT<br>
        Departamento de Informática – DI<br><br>
        Documento de Modelagem de Análise e Projeto<br>Orientado a Objetos usando UML
    </div>
    <div class="cover-project">&lt;EduScrap&gt;</div>
    <div class="cover-version">Versão 1.2 (Atualizada)</div>
    
    <div class="cover-team">
        <strong>Equipe:</strong><br>
        Ana Kelry Fernandes Cabral do Nascimento – Matrícula / DI<br>
        Luiz Fernando Santos Teixeira – Matrícula / DI
    </div>
    
    <div class="cover-leader">
        Líder da Equipe: Ana Kelry<br>
        <span class="cover-email">kelryana930@gmail.com</span>
    </div>
</div>

<!-- HISTÓRICO DA REVISÃO -->
<h1>Histórico da Revisão</h1>
<table>
    <thead>
        <tr>
            <th style="width: 15%;">Data</th>
            <th style="width: 12%;">Versão</th>
            <th style="width: 48%;">Descrição</th>
            <th style="width: 25%;">Autor</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td class="center">30/08/2026</td>
            <td class="center">1.0</td>
            <td>Criação dos diagramas iniciais do projeto (Casos de Uso, Conceitual, Classes e Implantação preliminar).</td>
            <td class="center">Ana Kelry e Luiz Fernando</td>
        </tr>
        <tr>
            <td class="center">08/10/2026</td>
            <td class="center">1.1</td>
            <td>Prototipação visual das telas do sistema e detalhamento do fluxo de leitura de editais.</td>
            <td class="center">Ana Kelry</td>
        </tr>
        <tr>
            <td class="center">14/10/2026</td>
            <td class="center">1.2</td>
            <td><strong>Versão Completa e Atualizada do Sistema:</strong><br>
            - Expansão dos Casos de Uso com detalhamento formal (UC01 a UC09);<br>
            - Alinhamento pleno do Modelo Conceitual, Diagramas de Sequência e Estados ao domínio real do EduScrap;<br>
            - Documentação do orquestrador paralelo de scrapers (concorrência e logs isolados);<br>
            - Inclusão dos prints reais em alta resolução da interface atual (incluindo o novo gráfico Donut de vigência, seletor dinâmico de cursos e suporte nativo a Tema Escuro);<br>
            - Atualização da arquitetura de implantação em containers Docker e FastAPI.</td>
            <td class="center">Ana Kelry e Luiz Fernando</td>
        </tr>
    </tbody>
</table>

<div class="note-box">
    <strong>Registro de Ajustes Realizados na Versão 1.2:</strong>
    <ul>
        <li><strong>Personalização e Filtros Avançados:</strong> Inclusão do fluxo completo de filtragem por áreas de conhecimento e cursos de graduação no feed.</li>
        <li><strong>Expansão dos Casos de Uso:</strong> Adição dos cenários de autenticação de discente, salvamento de oportunidades favoritas, alertas e monitoramento de scrapers.</li>
        <li><strong>Substituição de Imagens:</strong> Atualização integral das capturas de tela com a versão mais recente em execução no repositório, apresentando os botões com nova paleta e o gráfico analítico de prazos em formato Donut.</li>
        <li><strong>Padronização Acadêmica:</strong> Correção e realinhamento de todos os títulos, legendas e numerações de figuras em consonância com as normas da ABNT e do DI/UERN.</li>
    </ul>
</div>

<div class="page-break"></div>

<!-- ÍNDICE ANALÍTICO -->
<h1>Índice Analítico</h1>
<div class="no-indent">
    <div class="toc-item"><span>1. Introdução</span><span>4</span></div>
    <div class="toc-item"><span>2. Diagrama de Casos de Uso do Sistema</span><span>5</span></div>
    <div class="toc-item"><span>&nbsp;&nbsp;&nbsp;&nbsp;2.1 Especificação Textual dos Casos de Uso</span><span>6</span></div>
    <div class="toc-item"><span>3. Modelo Conceitual do Sistema</span><span>8</span></div>
    <div class="toc-item"><span>&nbsp;&nbsp;&nbsp;&nbsp;3.1 Identificação dos Conceitos Candidatos</span><span>8</span></div>
    <div class="toc-item"><span>&nbsp;&nbsp;&nbsp;&nbsp;3.2 Diagrama do Modelo Conceitual</span><span>9</span></div>
    <div class="toc-item"><span>4. Diagramas de Sequência do Sistema</span><span>10</span></div>
    <div class="toc-item"><span>&nbsp;&nbsp;&nbsp;&nbsp;4.1 Caso de Uso – Favoritar Oportunidade</span><span>10</span></div>
    <div class="toc-item"><span>&nbsp;&nbsp;&nbsp;&nbsp;4.2 Caso de Uso – Coleta Assíncrona e Disparo de Alertas</span><span>11</span></div>
    <div class="toc-item"><span>5. Diagramas de Estado de Objeto</span><span>12</span></div>
    <div class="toc-item"><span>&nbsp;&nbsp;&nbsp;&nbsp;5.1 Objeto Edital / Oportunidade</span><span>12</span></div>
    <div class="toc-item"><span>&nbsp;&nbsp;&nbsp;&nbsp;5.2 Objeto Job de Coleta</span><span>13</span></div>
    <div class="toc-item"><span>6. Modelo de Dados do Sistema</span><span>14</span></div>
    <div class="toc-item"><span>&nbsp;&nbsp;&nbsp;&nbsp;6.1 Mapeamento NoSQL (MongoDB) e Justificativa</span><span>14</span></div>
    <div class="toc-item"><span>&nbsp;&nbsp;&nbsp;&nbsp;6.2 Arquitetura Interna do Normalizador de Dados</span><span>15</span></div>
    <div class="toc-item"><span>7. Diagrama de Classes do Sistema</span><span>16</span></div>
    <div class="toc-item"><span>&nbsp;&nbsp;&nbsp;&nbsp;7.1 Especificação Detalhada das Classes e Relacionamentos</span><span>17</span></div>
    <div class="toc-item"><span>8. Protótipos de Interface do Sistema (Telas Reais Atualizadas)</span><span>18</span></div>
    <div class="toc-item"><span>&nbsp;&nbsp;&nbsp;&nbsp;8.1 Dashboard Principal e Pesquisa (Tema Claro)</span><span>18</span></div>
    <div class="toc-item"><span>&nbsp;&nbsp;&nbsp;&nbsp;8.2 Painel de Monitoramento de Prazos (Gráfico Donut)</span><span>19</span></div>
    <div class="toc-item"><span>&nbsp;&nbsp;&nbsp;&nbsp;8.3 Listagem de Oportunidades e Filtros por Curso</span><span>20</span></div>
    <div class="toc-item"><span>&nbsp;&nbsp;&nbsp;&nbsp;8.4 Modo Escuro (Dark Mode) e Acessibilidade Visual</span><span>21</span></div>
    <div class="toc-item"><span>&nbsp;&nbsp;&nbsp;&nbsp;8.5 Interface de Autenticação do Usuário</span><span>22</span></div>
    <div class="toc-item"><span>&nbsp;&nbsp;&nbsp;&nbsp;8.6 Análise de Usabilidade e Heurísticas de Nielsen</span><span>23</span></div>
    <div class="toc-item"><span>9. Diagramas de Implantação do Sistema</span><span>24</span></div>
    <div class="toc-item"><span>&nbsp;&nbsp;&nbsp;&nbsp;9.1 Arquitetura de Software em Containers Docker</span><span>24</span></div>
</div>

<h1 style="margin-top: 30px;">Lista de Figuras</h1>
<div class="no-indent">
    <div class="toc-item"><span>Figura 1 – Diagrama de Casos de Uso do Sistema</span><span>5</span></div>
    <div class="toc-item"><span>Figura 2 – Modelo Conceitual do Domínio EduScrap</span><span>9</span></div>
    <div class="toc-item"><span>Figura 3 – Diagrama de Sequência: Favoritar Oportunidade</span><span>10</span></div>
    <div class="toc-item"><span>Figura 4 – Diagrama de Sequência: Coleta Assíncrona e Alertas</span><span>11</span></div>
    <div class="toc-item"><span>Figura 5 – Diagrama de Estado do Objeto: Edital</span><span>12</span></div>
    <div class="toc-item"><span>Figura 6 – Diagrama de Estado do Objeto: Job de Coleta</span><span>13</span></div>
    <div class="toc-item"><span>Figura 7 – Diagrama de Entidade e Relacionamento (NoSQL)</span><span>14</span></div>
    <div class="toc-item"><span>Figura 8 – Arquitetura do Normalizador de Dados</span><span>15</span></div>
    <div class="toc-item"><span>Figura 9 – Diagrama de Classes do Sistema</span><span>16</span></div>
    <div class="toc-item"><span>Figura 10 – Interface Principal do Sistema (Dashboard em Tema Claro)</span><span>18</span></div>
    <div class="toc-item"><span>Figura 11 – Painel de Prazos com Gráfico Donut de Vigência</span><span>19</span></div>
    <div class="toc-item"><span>Figura 12 – Listagem Compacta com Filtros de Áreas e Cursos</span><span>20</span></div>
    <div class="toc-item"><span>Figura 13 – Interface do Sistema com Tema Escuro (Dark Mode)</span><span>21</span></div>
    <div class="toc-item"><span>Figura 14 – Interface de Autenticação / Login</span><span>22</span></div>
    <div class="toc-item"><span>Figura 15 – Diagrama de Implantação e Arquitetura de Containers</span><span>24</span></div>
</div>

<div class="page-break"></div>

<!-- 1. INTRODUÇÃO -->
<h1>1. Introdução</h1>
<p>
    O presente documento formaliza a modelagem de análise e projeto orientado a objetos da plataforma <strong>EduScrap</strong>, em conformidade com as diretrizes do Processo Unificado e as notações formais da Unified Modeling Language (UML). O EduScrap consiste em uma solução de software concebida para mitigar o problema crônico da dispersão de informações institucionais no meio universitário da Universidade do Estado do Rio Grande do Norte (UERN) e instituições de ensino superior do semiárido potiguar.
</p>
<p>
    O ecossistema universitário produz continuamente atos administrativos, editais de assistência estudantil, chamadas de iniciação científica, processos seletivos e oportunidades de estágio. Entretanto, a inexistência de um canal centralizado e padronizado resulta em desinformação sistemática e na perda de prazos regulamentares por parte dos estudantes. Para superar esse desafio, o EduScrap implementa uma arquitetura baseada em microsserviços desacoplados, combinando web scraping concorrente, higienização documental via Expressões Regulares (Regex), persistência NoSQL em MongoDB e uma API RESTful de alta performance construída em FastAPI.
</p>
<p>
    Nas seções subsequentes, são apresentados os modelos comportamentais e estruturais do sistema, detalhando os casos de uso, o modelo conceitual de domínio, os fluxos temporais de sequência, as máquinas de estados dos objetos críticos, o modelo de persistência, as especificações de classes, os protótipos de tela reais capturados da versão atual do software e o diagrama de implantação em infraestrutura conteinerizada.
</p>

<!-- 2. DIAGRAMA DE CASOS DE USO -->
<h1>2. Diagrama de Caso de Uso do Sistema</h1>
<p>
    O Diagrama de Casos de Uso sintetiza as interações funcionais entre os atores externos e a fronteira do sistema EduScrap. Foram modelados dois atores essenciais:
</p>
<ul>
    <li><strong>Estudante:</strong> Usuário final da plataforma, interessado em pesquisar, filtrar, favoritar oportunidades acadêmicas e receber notificações preditivas de prazos.</li>
    <li><strong>Administrador:</strong> Responsável pela governança do sistema, manutenção das fontes de extração web (URLs, seletores CSS/XPath) e monitoramento dos logs isolados de execução dos scrapers.</li>
</ul>

<div class="figure-container">
    <img src="{img_caso_uso}" alt="Diagrama de Caso de Uso">
    <div class="figure-caption">Figura 1 – Diagrama de Caso de Uso do Sistema</div>
</div>

<p>
    Observa-se que a coleta automatizada de dados (web scraping) é propositalmente dissociada das ações síncronas do estudante. Os robôs operam em segundo plano (background) sob controle do orquestrador concorrente, garantindo que as consultas efetuadas pelos alunos na interface web obtenham respostas em tempo sub-segundo diretamente da base indexada no MongoDB.
</p>

<h2>2.1 Especificação Textual dos Casos de Uso</h2>
<table>
    <thead>
        <tr>
            <th style="width: 15%;">Código / Nome</th>
            <th style="width: 15%;">Atores</th>
            <th style="width: 35%;">Fluxo Principal</th>
            <th style="width: 35%;">Regras / Extensões</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>UC01 – Consultar Feed</strong></td>
            <td>Estudante</td>
            <td>1. Discente acessa o sistema.<br>2. Sistema requisita à API os registros ativos.<br>3. Cards são renderizados com dados consolidados.</td>
            <td>Resposta sub-segundo; ordenação cronológica decrescente.</td>
        </tr>
        <tr>
            <td><strong>UC02 – Filtrar por Curso / Área</strong></td>
            <td>Estudante</td>
            <td>1. Usuário seleciona sua Área ou Curso.<br>2. Sistema filtra os dados instantaneamente.<br>3. Feed exibe apenas itens pertinentes.</td>
            <td>Mapeamento semântico de palavras-chave definido em <code>course_mapping.json</code>.</td>
        </tr>
        <tr>
            <td><strong>UC03 – Visualizar Vigência</strong></td>
            <td>Estudante</td>
            <td>1. Usuário analisa o card ou painel Donut.<br>2. Badges indicam status ("Vigente", "Encerrado").</td>
            <td>Estende UC01 (&laquo;extend&raquo;). Cálculo automático de data limite vs. data do servidor.</td>
        </tr>
        <tr>
            <td><strong>UC04 – Favoritar Oportunidade</strong></td>
            <td>Estudante</td>
            <td>1. Usuário clica no ícone de estrela.<br>2. API atualiza o vetor de favoritos no MongoDB.<br>3. Feedback visual é exibido em tela.</td>
            <td>Estende UC01 (&laquo;extend&raquo;). Requer identificação do usuário.</td>
        </tr>
        <tr>
            <td><strong>UC05 – Cadastrar / Autenticar-se</strong></td>
            <td>Estudante</td>
            <td>1. Usuário informa e-mail e senha.<br>2. Sistema valida credenciais e gera sessão segura.</td>
            <td>Senha armazenada em hash criptográfico; permissão de navegação anônima no feed.</td>
        </tr>
        <tr>
            <td><strong>UC06 – Gerenciar Fontes</strong></td>
            <td>Administrador</td>
            <td>1. Administrador acessa painel restrito.<br>2. Adiciona ou ajusta regras de extração de portais.</td>
            <td>Permite incluir novas URLs sem recompilar a aplicação.</td>
        </tr>
        <tr>
            <td><strong>UC07 – Monitorar Coleta</strong></td>
            <td>Administrador</td>
            <td>1. Administrador consulta os logs em <code>logs/</code>.<br>2. Avalia taxas de sucesso e falhas por robô.</td>
            <td>Isolamento por arquivo de log (ex: <code>logs/prae.log</code>, <code>logs/ciee.log</code>).</td>
        </tr>
    </tbody>
</table>

<div class="page-break"></div>

<!-- 3. MODELO CONCEITUAL -->
<h1>3. Modelo Conceitual do Sistema</h1>

<h2>3.1 Identificação dos Conceitos Candidatos do Sistema</h2>
<p>
    A partir da extração substantiva das necessidades do domínio e dos fluxos operacionais, foram identificadas as entidades conceituais basilares para o modelo de domínio do EduScrap:
</p>
<ul>
    <li><strong>Usuário:</strong> Especializado em <em>Estudante</em> (com atributos de matrícula, cursos de interesse e favoritos) e <em>Administrador</em> (responsável pela governança técnica das fontes).</li>
    <li><strong>Oportunidade:</strong> Superclasse abstrata que consolida os atributos comuns a qualquer publicação (identificador único, título descritivo, link canônico, data de publicação, fonte emissora e status de vigência).</li>
    <li><strong>Edital:</strong> Especialização de Oportunidade, agregando número do edital, órgão promotor e data de encerramento das inscrições.</li>
    <li><strong>VagaEstágio:</strong> Especialização de Oportunidade voltada a anúncios corporativos, contendo empresa contratante e bolsa/remuneração.</li>
    <li><strong>Notícia:</strong> Comunicados e informes acadêmicos classificados por categoria e resumo.</li>
    <li><strong>Fonte:</strong> Portal de origem (ex.: Portal UERN, PRAE, JOUERN, UFERSA, CIEE).</li>
    <li><strong>MotorScraping e Normalizador:</strong> Mecanismos de software encarregados da captura concorrente, higienização com expressões regulares e persistência estruturada.</li>
</ul>

<h2>3.2 Modelo Conceitual</h2>
<div class="figure-container">
    <img src="{img_conceitual}" alt="Modelo Conceitual do Sistema">
    <div class="figure-caption">Figura 2 – Modelo Conceitual do Domínio EduScrap</div>
</div>
<p>
    O modelo conceitual demonstra a navegabilidade e o relacionamento entre os conceitos. Um Estudante pode possuir múltiplos interesses em cursos e manter uma lista de oportunidades favoritas. As oportunidades são catalogadas a partir das fontes externas e sofrem triagem contínua quanto à sua validade temporal.
</p>

<div class="page-break"></div>

<!-- 4. DIAGRAMAS DE SEQUÊNCIA -->
<h1>4. Diagramas de Sequência do Sistema</h1>
<p>
    O comportamento dinâmico do EduScrap é estruturado sobre o desacoplamento temporal:
</p>
<ol>
    <li><strong>Ciclo Assíncrono de Ingestão:</strong> Executado de forma paralela e em horários programados, onde os robôs consultam as fontes externas, extraem dados brutos, passam pelo normalizador de expressões regulares e gravam no MongoDB.</li>
    <li><strong>Ciclo Síncrono de Consulta:</strong> Ocorre quando o estudante interage com a interface web, realizando requisições leves à API FastAPI que consulta diretamente os índices do MongoDB em poucos milissegundos.</li>
</ol>

<h2>4.1 Caso de Uso – Favoritar Oportunidade</h2>
<p>
    Ilustra o fluxo onde o aluno decide salvar um edital para acompanhamento posterior. A requisição HTTP do tipo PATCH é encaminhada da SPA para a API REST, que executa um operador atômico (<code>$addToSet</code>) na base de dados, garantindo idempotência e retornando feedback visual imediato.
</p>

<div class="figure-container">
    <img src="{img_seq1}" alt="Diagrama de Sequência: Favoritar Oportunidade">
    <div class="figure-caption">Figura 3 – Diagrama de Sequência: Favoritar / Salvar Oportunidade</div>
</div>

<h2>4.2 Caso de Uso – Coleta Assíncrona e Disparo de Alertas</h2>
<p>
    Mapeia a interação entre a Engine de Coleta, o Normalizador de dados brutos e o módulo de alertas. Quando um edital novo é validado com status "Aberto", os usuários cadastrados com afinidade para aquele curso são identificados para recebimento de notificação.
</p>

<div class="figure-container">
    <img src="{img_seq2}" alt="Diagrama de Sequência: Coleta Assíncrona e Alertas">
    <div class="figure-caption">Figura 4 – Diagrama de Sequência: Coleta Assíncrona e Alertas aos Estudantes</div>
</div>

<div class="page-break"></div>

<!-- 5. DIAGRAMAS DE ESTADO -->
<h1>5. Diagramas de Estado de Objeto</h1>
<p>
    Os diagramas de estado modelam as transições de ciclo de vida das duas entidades mais dinâmicas do EduScrap: o documento de <strong>Edital</strong> e o <strong>Job de Coleta</strong> em background.
</p>

<h2>5.1 Objeto Edital / Oportunidade</h2>
<p>
    Descreve os estados assumidos pelo edital desde o instante em que sua URL é descoberta pelo robô de extração. O documento transita para <em>Em Processamento</em> enquanto tem seu conteúdo em texto/PDF lido e filtrado por Regex. Caso o arquivo esteja corrompido ou inacessível, transita para <em>Inválido</em>. Se validado com data limite superior à data atual, é persistido como <em>Aberto (Vigente)</em>. No momento em que o relógio do sistema ultrapassa a data limite, o edital é automaticamente comutado para <em>Encerrado</em>.
</p>

<div class="figure-container">
    <img src="{img_est_edital}" alt="Diagrama de Estado: Edital">
    <div class="figure-caption">Figura 5 – Diagrama de Estado do Objeto: Edital / Oportunidade</div>
</div>

<h2>5.2 Objeto Job de Coleta</h2>
<p>
    Rastreia o ciclo de vida da tarefa agendada disparada pelo cron ou orquestrador concorrente (<code>run_scrapers.py</code>). A tarefa parte do estado <em>Agendado</em> para <em>Executando</em>. Em caso de timeout de conexão ou indisponibilidade do portal externo, a rotina de retry entra em ação; persistindo a falha, o job transita para <em>Falha</em> (registrando o erro em seu respectivo arquivo de log). Havendo êxito na leitura dos metadados, passa para <em>Persistindo</em> e finaliza em <em>Concluído</em>.
</p>

<div class="figure-container">
    <img src="{img_est_job}" alt="Diagrama de Estado: Job de Coleta">
    <div class="figure-caption">Figura 6 – Diagrama de Estado do Objeto: Job de Coleta</div>
</div>

<div class="page-break"></div>

<!-- 6. MODELO DE DADOS -->
<h1>6. Modelo de Dados do Sistema</h1>

<h2>6.1 Mapeamento NoSQL (MongoDB) e Justificativa Arquitetural</h2>
<p>
    Dada a heterogeneidade intrínseca das informações publicadas por portais públicos e agentes de integração, optou-se tecnicamente pelo modelo NoSQL orientado a documentos (<strong>MongoDB</strong>). Em bancos de dados relacionais tradicionais (SQL), a coexistência de um edital de monitoria acadêmica (com dezenas de anexos, números de portarias e comissões avaliadoras) com uma vaga de estágio do CIEE (com dados de valor de bolsa-auxílio e carga horária semanal) exigiria esquemas com elevado número de tabelas intermediárias e junções caras (JOINs), ou campos nulos em abundância.
</p>
<p>
    No MongoDB, a coleção <code>oportunidades</code> armazena objetos polimórficos de maneira limpa, enquanto a validação de schema (implementada no script <code>database_setup.py</code>) garante a presença dos campos essenciais comuns (<code>titulo</code>, <code>link</code>, <code>data_coleta</code>, <code>status</code>). Foram criados índices compostos de busca textual e temporal para garantir respostas imediatas.
</p>

<div class="figure-container">
    <img src="{img_der}" alt="Diagrama de Entidade e Relacionamento">
    <div class="figure-caption">Figura 7 – Diagrama de Entidade e Relacionamento (Mapeamento Lógico NoSQL)</div>
</div>

<h2>6.2 Arquitetura Interna do Normalizador de Dados</h2>
<p>
    O Normalizador é o coração da higienização dos dados do EduScrap. Ao receber o texto bruto capturado das páginas web ou extraído dos arquivos em PDF via <code>pdfplumber</code>, o componente submete o fluxo ao motor de Expressões Regulares (Regex).
</p>

<div class="figure-container">
    <img src="{img_norm}" alt="Normalizador de Dados">
    <div class="figure-caption">Figura 8 – Arquitetura do Normalizador de Dados</div>
</div>

<p>
    Caso os padrões Regex apresentem confiança estrita, as datas e números são extraídos diretamente; em situações ambíguas, o fluxo recorre a heurísticas complementares de validação. O validador compara a data de encerramento com a data do servidor (<code>Hoje</code>), definindo o status binário e gerando um payload JSON padronizado pronto para inserção no MongoDB.
</p>

<div class="page-break"></div>

<!-- 7. DIAGRAMA DE CLASSES -->
<h1>7. Diagrama de Classe do Sistema</h1>
<p>
    O Diagrama de Classes representa a estrutura lógica estática do software, formalizando a orientação a objetos utilizada tanto no backend Python (FastAPI/Pydantic) quanto no mapeamento de domínio.
</p>

<div class="figure-container">
    <img src="{img_classes}" alt="Diagrama de Classes">
    <div class="figure-caption">Figura 9 – Diagrama de Classes do Sistema</div>
</div>

<h2>7.1 Especificação Detalhada das Classes e Relacionamentos</h2>
<ul>
    <li><strong>Usuario (Classe Abstrata):</strong> Superclasse que concentra credenciais e identificação:
        <ul>
            <li><code>id: String</code> – Identificador único do usuário.</li>
            <li><code>nome: String</code> – Nome completo.</li>
            <li><code>email: String</code> – E-mail institucional ou pessoal.</li>
            <li><code>senhaHash: String</code> – Hash seguro da credencial de autenticação.</li>
        </ul>
    </li>
    <li><strong>Estudante (Subclasse de Usuario):</strong> Especialização do discente:
        <ul>
            <li><code>matricula: String</code> – Identificador de vínculo acadêmico.</li>
            <li><code>cursosInteresse: List&lt;String&gt;</code> – Cursos seguidos pelo aluno.</li>
            <li><code>areasInteresse: List&lt;String&gt;</code> – Áreas temáticas cadastradas.</li>
            <li><code>favoritos: List&lt;String&gt;</code> – Lista de IDs de oportunidades salvas.</li>
            <li><code>+atualizarPreferencias()</code>, <code>+alternarFavorito()</code>, <code>+consultarFeed()</code>.</li>
        </ul>
    </li>
    <li><strong>Administrador (Subclasse de Usuario):</strong> Especialização do gestor técnico:
        <ul>
            <li><code>setor: String</code> – Lotação administrativa.</li>
            <li><code>+gerenciarFontes()</code>, <code>+monitorarScraping()</code>.</li>
        </ul>
    </li>
    <li><strong>Oportunidade (Classe Abstrata):</strong> Superclasse dos itens coletados:
        <ul>
            <li><code>id</code>, <code>titulo</code>, <code>link</code>, <code>dataPublicacao</code>, <code>statusVigencia</code>, <code>fonte</code>.</li>
            <li><code>+verificarStatus(): boolean</code> – Avalia validade temporal em tempo de execução.</li>
        </ul>
    </li>
    <li><strong>Edital, VagaEstagio e Noticia:</strong> Especializações concretas contendo metadados pertinentes (número de portaria, empresa promotora e categoria textual, respectivamente).</li>
</ul>

<div class="page-break"></div>

<!-- 8. PROTÓTIPOS DE INTERFACE DO SISTEMA -->
<h1>8. Protótipos de Interface do Sistema (Telas Reais Atualizadas)</h1>
<p>
    A interface do usuário do EduScrap foi desenvolvida sob os preceitos de Design Centrado no Usuário (UCD), visando clareza de navegação, resposta imediata e acessibilidade. A versão atual conta com novo design system, paleta de cores institucional enriquecida (destaque para o botão de ação rápida em <code>#FF5C00</code>), cards compactos e o recém-implementado <strong>painel de monitoramento temporal com gráfico Donut</strong>.
</p>

<h2>8.1 Dashboard Principal e Pesquisa (Tema Claro)</h2>
<p>
    A tela inicial apresenta o cabeçalho moderno com logo institucional, barra de busca centralizada e atalhos rápidos para as principais fontes integradas (PRAE, PROEX, UFERSA, CIEE, Portal UERN).
</p>

<div class="figure-container">
    <img src="{img_tela_hero}" alt="Interface Principal - Dashboard">
    <div class="figure-caption">Figura 10 – Interface Principal do Sistema (Dashboard em Tema Claro)</div>
</div>

<h2>8.2 Painel de Monitoramento de Prazos (Gráfico Donut)</h2>
<p>
    Componente analítico inovador que sintetiza a situação dos editais coletados. O gráfico Donut (gráfico de rosca) exibe visualmente a proporção de certames com inscrições <em>Vigentes</em> em contraste com certames <em>Encerrados</em>, permitindo ao aluno identificar com um bater de olhos a disponibilidade de novos processos seletivos.
</p>

<div class="figure-container">
    <img src="{img_tela_donut}" alt="Painel de Prazos com Gráfico Donut">
    <div class="figure-caption">Figura 11 – Painel de Monitoramento de Prazos com Gráfico Donut de Vigência</div>
</div>

<div class="page-break"></div>

<h2>8.3 Listagem de Oportunidades e Filtros por Curso</h2>
<p>
    A listagem de cards organiza as oportunidades com badges de identificação de fonte, tags temáticas (Inclusão Digital, Informática, Saúde), datas de publicação e botões diretos de "Ver Edital Oficial" e "Salvar / Favoritar".
</p>

<div class="figure-container">
    <img src="{img_tela_cards}" alt="Listagem de Cards de Oportunidades">
    <div class="figure-caption">Figura 12 – Listagem Compacta de Oportunidades com Filtros por Área do Conhecimento</div>
</div>

<h2>8.4 Modo Escuro (Dark Mode) e Acessibilidade Visual</h2>
<p>
    O sistema conta com suporte nativo a Tema Escuro através do módulo <code>theme.js</code>. Ao alternar o tema, a aplicação aplica a classe <code>dark</code> no documento, ajusta automaticamente as cores de fundo para tons profundos de alto contraste e substitui o logotipo da aplicação pelo asset específico <code>assets/logo_temaescuro.png</code>, reduzindo o cansaço visual em sessões noturnas de estudo.
</p>

<div class="figure-container">
    <img src="{img_tela_dark}" alt="Tema Escuro - Dark Mode">
    <div class="figure-caption">Figura 13 – Interface do Sistema com Tema Escuro (Dark Mode) e Logo Temático</div>
</div>

<div class="page-break"></div>

<h2>8.5 Interface de Autenticação do Usuário</h2>
<p>
    Tela minimalista para cadastro e login do estudante (<code>frontend/login.html</code>), permitindo vinculação de matrícula, curso de graduação e preferências de alertas por e-mail.
</p>

<div class="figure-container">
    <img src="{img_tela_login}" alt="Interface de Login">
    <div class="figure-caption">Figura 14 – Interface de Autenticação / Login do Estudante</div>
</div>

<h2>8.6 Análise de Usabilidade e Heurísticas de Nielsen</h2>
<ul>
    <li><strong>Visibilidade do Estado do Sistema:</strong> As badges coloridas informam imediatamente se o edital está aberto ou encerrado, reforçadas pela métrica visual do gráfico Donut.</li>
    <li><strong>Correspondência entre o Sistema e o Mundo Real:</strong> Nomenclaturas acadêmicas autênticas utilizadas na UERN (PRAE, PROEX, Edital de Permanência, Auxílio Inclusão Digital).</li>
    <li><strong>Controle e Liberdade do Usuário:</strong> Facilidade para desmarcar filtros e alternar instantaneamente entre temas claro e escuro sem recarregar a página.</li>
    <li><strong>Design Estético e Minimalista:</strong> Informações secundárias e burocráticas são omitidas do feed principal, mantendo apenas título, prazo limite e link para o documento original.</li>
</ul>

<div class="page-break"></div>

<!-- 9. DIAGRAMA DE IMPLANTAÇÃO -->
<h1>9. Diagramas de Implantação do Sistema</h1>

<h2>9.1 Arquitetura de Software em Containers Docker</h2>
<p>
    A infraestrutura do EduScrap foi concebida para operar sob arquitetura de microsserviços conteinerizada (<strong>Docker</strong>), garantindo isolamento de dependências, facilidade de deploy contínuo e escalabilidade horizontal.
</p>

<div class="figure-container">
    <img src="{img_impl}" alt="Diagrama de Implantação e Containers">
    <div class="figure-caption">Figura 15 – Diagrama de Implantação e Arquitetura de Containers (Docker)</div>
</div>

<p>
    A topologia de rede é segmentada em camadas de segurança e responsabilidade:
</p>
<ol>
    <li><strong>Dispositivo do Usuário:</strong> O cliente final consome a Single Page Application (SPA) através de navegadores modernos (Chrome, Firefox, Safari) e recebe eventuais alertas informativos via cliente de e-mail.</li>
    <li><strong>Camada de Entrada (Nginx Reverse Proxy):</strong> Recebe tráfego criptografado via HTTPS (porta 443), realiza terminação SSL/TLS, serve arquivos estáticos do frontend e encaminha requisições dinâmicas de API para o backend FastAPI.</li>
    <li><strong>Camada de Aplicação (API FastAPI / Uvicorn):</strong> Executa em container assíncrono, processando endpoints RESTful e controlando autenticação de sessão.</li>
    <li><strong>Camada de Fila e Cache (Redis Queue):</strong> Atua como broker de mensagens entre o agendador de tarefas (Cron / Scheduler) e os workers de execução pesada.</li>
    <li><strong>Workers Concorrentes Assíncronos:</strong>
        <ul>
            <li><code>scraper-worker</code>: Executa as rotinas de coleta (Requests para HTML estático e Selenium Headless para portais com JavaScript complexo);</li>
            <li><code>parser-worker</code>: Executa a leitura de diários em PDF e a normalização via Expressões Regulares;</li>
            <li><code>alert-worker</code>: Filtra discentes inscritos e dispara e-mails informativos via protocolo SMTP.</li>
        </ul>
    </li>
    <li><strong>Servidor de Banco de Dados:</strong> Instância isolada do <strong>MongoDB</strong> (porta 27017), gerenciando as coleções de usuários e oportunidades com replicação e índices otimizados.</li>
    <li><strong>Sistemas Externos Integrados:</strong> Portais institucionais da UERN, UFERSA, acervo de Diários Oficiais (JOUERN), API CIEE e servidores SMTP.</li>
</ol>

</body>
</html>
"""

output_html = "/home/ana/projetos/EduScrap/documentos_finais/Documento_Modelagem_UML_EduScrap.html"
with open(output_html, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"HTML do Documento UML gerado com sucesso em: {output_html}")

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
print("PDF do Documento UML gerado com sucesso!")

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
print("DOCX do Documento UML gerado com sucesso!")
