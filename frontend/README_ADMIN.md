# Painel de Governança Técnica e Administração (`admin.html`)

O Painel de Governança Técnica é o subsistema de operação e auditoria do **EduScrap UERN**. Ele centraliza o monitoramento de robôs de coleta, visualização de logs, edição de padrões regex e segurança via MFA.

---

## 1. Como Acessar

1. Certifique-se de que o backend e o frontend estão rodando (`./start.sh` ou `docker-compose up`).
2. Acesse no navegador:
   ```text
   http://localhost:3000/admin.html
   ```
3. Digite sua **Chave Mestre de Governança**:
   * **Em desenvolvimento (padrão):** `admin123`
   * **Em produção:** O valor definido na variável `API_KEY` do seu arquivo `.env` (quando configurada, a chave padrão `admin123` é automaticamente revogada por segurança).

---

## 2. Funcionalidades Disponíveis

### A. Dashboard de Monitorização dos Scrapers (UC11)
* Lista em tempo real os **13 robôs de coleta** (PRAE, PROEX, UFERSA, CIEE, MPRN, UERN, IEL, etc.).
* Exibe:
  * **Status:** `Sucesso` (verde), `Alerta` (amarelo), `Falha` (vermelho) ou `Pendente`.
  * **Data/Hora:** Última execução registrada.
  * **Duração:** Tempo total em segundos de cada scraping.
  * **Itens Coletados:** Volume de editais minerados e armazenados no banco.
  * **Contagem de Erros:** Erros HTTP, seletores quebrados ou exceções capturadas.
* Botão **"Ver Log"**: Abre instantaneamente as últimas 200 linhas de execução daquele robô específico.

### B. Inspeção Rápida de Logs Técnicos
* Permite escolher o arquivo de log direto de um menu suspenso.
* Renderiza no terminal embutido as mensagens de rastreamento do coletor para identificar portais fora do ar ou mudanças de layout.

###  C. Editor de Padrões Regex Dinâmicos (UC12 / RF12)
* Permite alterar o arquivo `patterns.json` em tempo de execução sem necessidade de recompilar a aplicação nem reiniciar o backend.
* **Proteção MFA:** Qualquer alteração e salvamento de regras exige validação de token TOTP de 6 dígitos gerado via autenticador (Google Authenticator / Authy / Bitwarden).

###  D. Fontes e Robôs Cadastrados (UC10)
* Visão dos scripts executáveis cadastrados no orquestrador `run_scrapers.py`.

---

## 3. Boas Práticas de Segurança

1. **Nunca versione credenciais:** Nunca comite arquivos `.env` ou logs em repositórios públicos.
2. **Ative o MFA no primeiro acesso:** Clique no botão **"Configurar MFA (pyotp)"**, escaneie o QR Code com seu app autenticador e confirme com o código de 6 dígitos.
3. **Defina uma `API_KEY` forte:** No ambiente de produção, crie uma chave com pelo menos 32 caracteres alfanuméricos no `.env`.
