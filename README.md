# Eduscrap UERN - Dashboard de Oportunidades

![EduScrap](https://img.shields.io/badge/TechHub-UERN-orange)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)
![MongoDB](https://img.shields.io/badge/MongoDB-4.4+-brightgreen)

## 📖 Sobre o Projeto

O **EduScrap** é uma plataforma completa de agregação de oportunidades acadêmicas e profissionais para estudantes da UERN (Universidade do Estado do Rio Grande do Norte) e região. O sistema realiza web scraping de diversos portais institucionais e disponibiliza as informações em uma API REST moderna com frontend intuitivo.

### Funcionalidades Principais

- 🔍 **Web Scraping Automatizado**: Coleta dados de múltiplos portais (CIEE, UERN, UFERSA, etc.)
- 📰 **Monitoramento de Notícias**: Atualização automática de editais e vagas
- 🗄️ **Banco de Dados MongoDB**: Armazenamento otimizado com índices e validação de schema
- 🚀 **API FastAPI**: Backend moderno e performático com CORS habilitado
- 🎨 **Frontend Responsivo**: Dashboard interativo com design moderno
- 📊 **Filtragem Inteligente**: Organização por área (Tecnologia, Saúde, Humanas, Exatas, Direito, Comunicação)

---

## estrutura do Projeto

```
EduScrap-UERN/
├── backend/
│   ├── api/              # Módulos da API Flask/FastAPI
│   ├── src/              # Código fonte principal
│   ├── main.py           # Entry point da API FastAPI
│   ├── database_setup.py # Script de configuração do MongoDB
│   ├── scraper_*.py      # Scripts de web scraping
│   └── pdf_utils.py      # Utilitários para processamento de PDF
├── frontend/
│   ├── index.html        # Página principal
│   ├── style.css         # Estilização
│   └── script.js         # Lógica do frontend
├── config/
│   ├── course_mapping.json  # Mapeamento de cursos por área
│   └── patterns.json        # Padrões de busca
├── diagrams/             # Diagramas do sistema
├── tests/                # Testes automatizados
├── requirements.txt      # Dependências Python
└── README.md            # Este arquivo
```

---

## 🛠️ Pré-requisitos

Antes de começar, certifique-se de ter instalado:

### Obrigatórios
- **Python 3.8 ou superior**
- **MongoDB 4.4 ou superior**
- **Git** (para clonar o repositório)

### Recomendados
- **Node.js** (opcional, para ferramentas de desenvolvimento)
- **Navegador moderno** (Chrome, Firefox, Edge)

---

## 📦 Instalação e Configuração

### 1. Clonar o Repositório

```bash
git clone <url-do-repositorio>
cd EduScrap
```

---

## 🪟️ Tutorial para Windows

### Passo 1: Instalar Python

1. Acesse [python.org](https://www.python.org/downloads/)
2. Baixe a versão mais recente do Python 3.x
3. **Importante**: Marque a opção **"Add Python to PATH"** durante a instalação
4. Clique em "Install Now"

Verifique a instalação:
```cmd
python --version
pip --version
```

### Passo 2: Instalar MongoDB

1. Acesse [MongoDB Download Center](https://www.mongodb.com/try/download/community)
2. Selecione:
   - Version: Latest (7.0 ou superior)
   - Platform: Windows
   - Package: MSI
3. Baixe e execute o instalador
4. Escolha "Complete Installation"
5. **Importante**: Marque "Install MongoDB as a Service"
6. Marque "Run service as Network Service user"

Verifique se o MongoDB está rodando:
```cmd
sc query MongoDB
```

Ou inicie o serviço manualmente:
```cmd
net start MongoDB
```

### Passo 3: Configurar Ambiente Virtual

```cmd
# Navegue até a pasta do projeto
cd caminho\para\TechHub-UERN

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
venv\Scripts\activate
```

### Passo 4: Instalar Dependências

Com o ambiente virtual ativado:

```cmd
# Instalar todas as dependências
pip install -r requirements.txt

# Instalar FastAPI e uvicorn (se não estiverem no requirements.txt)
pip install fastapi uvicorn[standard]
```

### Passo 5: Configurar Banco de Dados

```cmd
# Navegue até a pasta backend
cd backend

# Executar script de configuração do MongoDB
python database_setup.py
```

### Passo 6: Iniciar o Backend

Na pasta `backend`, com o ambiente virtual ativado:

```cmd
# Opção 1: Usando FastAPI (recomendado)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Opção 2: Se houver um servidor Flask alternativo
python main.py
```

O servidor estará disponível em: `http://localhost:8000`

### Passo 7: Iniciar o Frontend

**Opção A: Usando Python HTTP Server (mais simples)**

Abra um novo terminal (mantenha o backend rodando):

```cmd
# Navegue até a pasta frontend
cd caminho\para\TechHub-UERN\frontend

# Iniciar servidor HTTP
python -m http.server 3000
```

**Opção B: Abrir diretamente no navegador**

Simplesmente abra o arquivo `index.html` em seu navegador:
```cmd
start frontend\index.html
```

⚠️ **Nota**: Algumas funcionalidades podem requerer um servidor HTTP devido a políticas de CORS.

### Passo 8: Acessar a Aplicação

- **Frontend**: `http://localhost:3000` (ou abra o index.html)
- **API**: `http://localhost:8000`
- **Documentação da API**: `http://localhost:8000/docs`

---

## 🐧 Tutorial para Linux

### Passo 1: Instalar Python

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv -y
```

**Fedora/RHEL:**
```bash
sudo dnf install python3 python3-pip python3-virtualenv -y
```

**Arch Linux:**
```bash
sudo pacman -S python python-pip
```

Verifique a instalação:
```bash
python3 --version
pip3 --version
```

### Passo 2: Instalar MongoDB

**Ubuntu/Debian:**
```bash
# Importar chave GPG do MongoDB
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor

# Adicionar repositório
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Instalar MongoDB
sudo apt update
sudo apt install mongodb-org -y

# Iniciar e habilitar serviço
sudo systemctl start mongod
sudo systemctl enable mongod
sudo systemctl status mongod
```

**Fedora:**
```bash
# Criar arquivo de repositório
sudo tee /etc/yum.repos.d/mongodb-org-7.0.repo << EOF
[mongodb-org-7.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/\$releasever/mongodb-org/7.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-7.0.asc
EOF

# Instalar
sudo dnf install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod
```

**Arch Linux (via AUR):**
```bash
yay -S mongodb-org-tools mongodb-compass
sudo systemctl start mongod
sudo systemctl enable mongod
```

### Passo 3: Configurar Ambiente Virtual

```bash
# Navegue até a pasta do projeto
cd ~/caminho/para/TechHub-UERN

# Criar ambiente virtual
python3 -m venv venv

# Ativar ambiente virtual
source venv/bin/activate
```

### Passo 4: Instalar Dependências

Com o ambiente virtual ativado:

```bash
# Instalar todas as dependências
pip install -r requirements.txt

# Instalar FastAPI e uvicorn
pip install fastapi uvicorn[standard]

# Dependências adicionais para web scraping
sudo apt install chromium-driver chromium -y  # Ubuntu/Debian
# ou
sudo dnf install chromedriver chromium -y     # Fedora
```

### Passo 5: Configurar Banco de Dados

```bash
# Navegue até a pasta backend
cd backend

# Executar script de configuração do MongoDB
python database_setup.py
```

### Passo 6: Iniciar o Backend

Na pasta `backend`, com o ambiente virtual ativado:

```bash
# Opção 1: Usando FastAPI (recomendado)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Opção 2: Em background (opcional)
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
```

### Passo 7: Iniciar o Frontend

**Opção A: Usando Python HTTP Server**

Abra um novo terminal:

```bash
# Navegue até a pasta frontend
cd ~/caminho/para/TechHub-UERN/frontend

# Iniciar servidor HTTP
python3 -m http.server 3000
```

**Opção B: Usando Node.js (se instalado)**

```bash
# Instalar serve globalmente
npm install -g serve

# Servir o frontend
serve frontend -l 3000
```

**Opção C: Abrir diretamente**

Alguns navegadores permitem abrir o arquivo diretamente:
```bash
xdg-open frontend/index.html
```

### Passo 8: Acessar a Aplicação

- **Frontend**: `http://localhost:3000`
- **API**: `http://localhost:8000`
- **Documentação da API**: `http://localhost:8000/docs`

---

## 🔌 Endpoints da API

A API fornece os seguintes endpoints principais:

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/` | Informações gerais da API |
| GET | `/health` | Health check do serviço |
| GET | `/api/oportunidades` | Lista todas as oportunidades |
| GET | `/api/editais` | Lista editais disponíveis |
| GET | `/api/vagas` | Lista vagas de estágio |
| GET | `/api/noticias` | Lista notícias atualizadas |

### Exemplo de Requisição

```bash
# Buscar todas as oportunidades
curl http://localhost:8000/api/oportunidades

# Filtrar por categoria
curl http://localhost:8000/api/vagas?categoria=tecnologia
```

---

## ⚙️ Comandos Úteis

### Gerenciar o MongoDB

**Windows:**
```cmd
# Verificar status
sc query MongoDB

# Iniciar serviço
net start MongoDB

# Parar serviço
net stop MongoDB
```

**Linux:**
```bash
# Verificar status
sudo systemctl status mongod

# Iniciar serviço
sudo systemctl start mongod

# Parar serviço
sudo systemctl stop mongod

# Reiniciar serviço
sudo systemctl restart mongod
```

### Gerenciar Ambiente Virtual

```bash
# Ativar (Linux/Mac)
source venv/bin/activate

# Ativar (Windows CMD)
venv\Scripts\activate

# Ativar (Windows PowerShell)
venv\Scripts\Activate.ps1

# Desativar
deactivate
```

### Rodar Scrapers Manualmente

```bash
cd backend

# Executar scraper específico
python scraper_ciee.py
python scraper_uern.py
python scraper_noticias.py
```

---

## 🧪 Testes

Para executar os testes automatizados:

```bash
cd tests
python -m pytest
# ou
python teste.py
```

---

## 🔧 Solução de Problemas

### Erro: MongoDB não conecta

**Windows:**
- Verifique se o serviço está rodando: `sc query MongoDB`
- Reinicie o serviço: `net stop MongoDB && net start MongoDB`

**Linux:**
- Verifique o status: `sudo systemctl status mongod`
- Veja os logs: `sudo journalctl -u mongod`
- Reinicie: `sudo systemctl restart mongod`

### Erro: Módulo não encontrado

Certifique-se de que o ambiente virtual está ativado:
```bash
# Windows
venv\Scripts\activate

# Linux
source venv/bin/activate
```

Reinstale as dependências:
```bash
pip install -r requirements.txt --force-reinstall
```

### Erro: Porta já em uso

Altere a porta no comando do uvicorn:
```bash
uvicorn main:app --reload --port 8001
```

Ou encerre o processo usando a porta:

**Windows:**
```cmd
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Linux:**
```bash
lsof -ti:8000 | xargs kill -9
```

### Erro: WebDriver não encontrado (Selenium)

**Windows:**
1. Baixe o ChromeDriver em [chromedriver.chromium.org](https://chromedriver.chromium.org/)
2. Extraia e coloque o `chromedriver.exe` na pasta do projeto ou no PATH

**Linux:**
```bash
sudo apt install chromium-chromedriver -y
# ou
sudo dnf install chromedriver -y
```

---

## 📝 Variáveis de Ambiente

Crie um arquivo `.env` na pasta `backend` se necessário:

```env
MONGODB_URI=mongodb://localhost:27017/
DATABASE_NAME=hub_estudantes
DEBUG=True
SECRET_KEY=sua_chave_secreta_aqui
```

---

## contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.


<div align="center">

**Feito com amor para a comunidade acadêmica...**

[⬆ Voltar ao topo](#techhub-uern---dashboard-de-oportunidades)

</div>
