# Diretrizes de Design de Interface, Ferramentas Base e Qualidade de Frontend (EduScrap)

Este documento define as regras mandatórias, ferramentas e princípios de design de interface injetados no escopo deste repositório. Toda geração de interface, refatoração de frontend ou teste automatizado deve estritamente validar e cumprir estes padrões.

---

## 1. As 5 Ferramentas e Diretrizes Base

### 1.1. Taste Skill (`tasteskill.dev`)
* **Critério Estético e Refinamento:** Rejeitar visuais genéricos de templates pré-fabricados. Aplicar hierarquia visual intencional, ritmo vertical coerente e precisão nos detalhes de acabamento.
* **Espaçamento e Tipografia:** Uso de escalas tipográficas modulares e harmoniosas, respeitando line-heights legíveis e espaçamento proporcional (grid de 4px/8px).
* **Harmonia Cromática e Texturas:** Cores aplicadas com semântica e contraste rigoroso, preservando a identidade Neobrutalista do EduScrap com toques modernos.

### 1.2. Web Design Guidelines (`skills.sh`)
* **Semântica e Acessibilidade (WCAG):** Elementos HTML semânticos obrigatórios (`<header>`, `<main>`, `<nav>`, `<section>`, `<article>`, `<button>`).
* **Contraste e Legibilidade:** Relação mínima de contraste de 4.5:1 para texto normal e 3:1 para textos grandes/elementos gráficos, tanto em Tema Claro quanto Escuro.
* **Estados Interativos:** Todo elemento interativo deve ter estados explícitos e distintos para: `hover`, `focus-visible`, `active`, `disabled` e `loading`.
* **Responsividade:** Layouts fluidos adaptados de mobile (320px) até ultra-wide (1920px+), sem overflow horizontal indesejado.

### 1.3. Awesome Design (`getdesign.md`)
* **Arquitetura de Componentes:** Componentes modulares, desacoplados e reutilizáveis (cards, badges, modals, toolbars).
* **Design Tokens:** Centralização de variáveis para paleta de cores, elevação/sombras sólidas (`shadow-brutal`), espessuras de borda e raios de canto (`rounded-*`).
* **Iconografia Coesa:** Conjunto padronizado com Phosphor Icons (`ph-bold`), alinhamento visual e proporção balanceada em todos os botões e títulos.

### 1.4. Image to Code (`github.com`)
* **Fidelidade Visual Pixel-Conscious:** Ao traduzir wireframes, mockups ou prints de referência, reproduzir a estrutura visual com fidelidade exata.
* **Transposição para Código Limpo:** Código CSS/Tailwind organizado, evitando hacks de alinhamento e priorizando Flexbox e CSS Grid sem duplicidade.

### 1.5. Playwright CLI (`playwright.dev`)
* **Validação Automatizada de UI:** Testes de regressão visual, fluxos end-to-end (E2E), navegação de usuário e validação de acessibilidade.
* **Inspeção de Estados Reais:** Assegurar que componentes interativos (dropdowns, abas, modais, filtros e botões) respondam sem quebras de layout.

---

## 2. As 8 Regras de Ouro do Design de Interface de Ben Shneiderman

### Regra 1: Buscar Consistência (Strive for Consistency)
* Manter paleta de cores idêntica em todas as telas (`#FF5C00`, `#FACC15`, `#0F172A`, gradientes de status).
* Uniformidade nos nomes de ações, ícones e formatação de datas/horários em todas as páginas (`index.html`, `admin.html`, `login.html`).
* Consistência nos padrões de layout: cabeçalhos, footers e grades seguem a mesma métrica geométrica.

### Regra 2: Permitir Atalhos para Usuários Frequentes (Enable Frequent Users to Use Shortcuts)
* Atalhos de teclado para ações centrais (ex.: `Enter` para disparar busca, `Esc` para fechar modais e sidebars).
* Filtros rápidos em um clique (chips de tags, botões de abas ativas, filtros de editais vigentes).
* Navegação acessível via teclado (`Tab` / `Shift+Tab`) com anel de foco bem delineado.

### Regra 3: Oferecer Feedback Informativo (Offer Informative Feedback)
* Para cada ação do usuário (clique, busca, cadastro, salvamento, cópia), exibir resposta visual imediata.
* Skeletons durante carregamento assíncrono de dados (`renderizarSkeletonDashboard`).
* Toasts flutuantes e badges de status para confirmações e notificações de sucesso/erro.

### Regra 4: Projetar Diálogos que Fechem Fluxos (Design Dialogs to Yield Closure)
* Fluxos de tarefas organizados em início, meio e conclusão nítida (ex.: cadastro -> feedback -> redirecionamento).
* Mensagens explícitas de conclusão quando uma operação for realizada (ex.: limpeza de dados, salvamento de perfil).

### Regra 5: Prevenção de Erros e Tratamento Simples (Prevent Errors & Simple Error Handling)
* Validação de campos antes de submeter formulários (ex.: senhas coincidentes, email válido, campus preenchido).
* Tratamento gracioso de indisponibilidade de rede ou falha de scraper, exibindo mensagens amigáveis e botões de "Tentar Novamente" em vez de telas quebradas.

### Regra 6: Permitir Reversão Fácil de Ações (Permit Easy Reversal of Actions - Undo)
* Confirmação explícita para ações destrutivas (ex.: logout, exclusão, expurgo de dados).
* Botão claro de "Limpar Busca" que restaura a listagem completa original instantaneamente.
* Possibilidade de alterar ou reverter opções personalizadas na sidebar de perfil a qualquer momento.

### Regra 7: Apoiar o Controle Interno (Support Internal Locus of Control)
* O usuário deve estar no comando: navegação previsível, sem surpresas ou redirecionamentos involuntários.
* Abertura e fechamento de painéis sob comando explícito do usuário, sem pop-ups invasivos não solicitados.
* Alternância de Tema (Claro/Escuro) sob controle total do usuário, respeitando a persistência em `localStorage`.

### Regra 8: Reduzir a Carga de Memória de Curto Prazo (Reduce Short-Term Memory Load)
* Não forçar o usuário a memorizar informações de uma tela para outra: os cards exibem contexto completo (órgão, prazo, link direto, salário, carga horária).
* Paginação clara e indicadores numéricos explícitos no topo do dashboard (ex.: total consolidado e divisão por fontes).
* Visões consolidadas e consolidação de estatísticas limpas e intuitivas.

---

## 3. Checklist Obrigatório para Modificações de Frontend

Antes de concluir qualquer tarefa de interface no EduScrap:
1. [ ] A consistência visual com o Neobrutalismo do projeto foi preservada?
2. [ ] O contraste de texto e elementos gráficos está nítido no tema Claro e no tema Escuro?
3. [ ] Há feedback visual (loading/toast/mensagem) para cada clique ou requisição?
4. [ ] O fluxo de navegação ou fechamento da ação está evidente para o estudante?
5. [ ] O teclado permite operar o fluxo básico (Enter, Esc, Tab)?
6. [ ] A reversão (voltar/cancelar/limpar) é fácil e imediata?
7. [ ] A interface reduziu ou minimizou a necessidade de memorização do usuário?
