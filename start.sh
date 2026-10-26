#!/usr/bin/env bash

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "============================================================"
echo "          INICIALIZANDO PROJETO EDUSCRAP UERN            "
echo "============================================================"

kill_port_processes() {
    local port=$1
    echo "  -> Verificando e liberando processos na porta $port..."
    if [ "$port" = "8000" ]; then
        pkill -9 -f "uvicorn.*8000" 2>/dev/null || true
    elif [ "$port" = "3000" ]; then
        pkill -9 -f "http\.server.*3000" 2>/dev/null || true
    fi
    if command -v fuser >/dev/null 2>&1; then
        fuser -k -9 "${port}/tcp" 2>/dev/null || true
    fi
    if command -v lsof >/dev/null 2>&1; then
        local pids=$(lsof -ti:$port 2>/dev/null || true)
        if [ ! -z "$pids" ]; then
            echo "  -> Matando processos na porta $port (PID: $pids)..."
            kill -9 $pids 2>/dev/null || true
        fi
    fi
    sleep 1
}

if [ -f ".venv/Scripts/activate" ]; then
    echo "[1/5] Ativando ambiente virtual (.venv)..."
    source .venv/Scripts/activate
elif [ -f ".venv/bin/activate" ]; then
    echo "[1/5] Ativando ambiente virtual (.venv)..."
    source .venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    echo "[1/5] Ativando ambiente virtual (venv)..."
    source venv/Scripts/activate
elif [ -f "venv/bin/activate" ]; then
    echo "[1/5] Ativando ambiente virtual (venv)..."
    source venv/bin/activate
elif [ -f "../venv/bin/activate" ]; then
    source ../venv/bin/activate
else
    echo "⚠️ Ambiente virtual 'venv' não encontrado na raiz."
    echo "Recomendado criar com: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
fi

# Detecta executável Python funcional (compatível com Linux e Git Bash no Windows)
if command -v python >/dev/null 2>&1 && python -c "import sys" >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    PYTHON_CMD="python3"
fi

echo "[2/5] Verificando status do MongoDB (porta 27017)..."
if command -v nc >/dev/null 2>&1 && nc -z 127.0.0.1 27017 2>/dev/null; then
    echo "  -> MongoDB já está em execução!"
elif "$PYTHON_CMD" -c "import pymongo; pymongo.MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=1000).server_info()" 2>/dev/null; then
    echo "  -> MongoDB conectado com sucesso!"
else
    echo "  -> Tentando inicializar o serviço do MongoDB..."
    if command -v systemctl >/dev/null 2>&1 && systemctl status mongod >/dev/null 2>&1; then
        sudo systemctl start mongod || true
    elif command -v service >/dev/null 2>&1; then
        sudo service mongod start 2>/dev/null || sudo service mongodb start 2>/dev/null || true
    fi

    # Se ainda não estiver rodando, tenta iniciar processo local do mongod
    if ! "$PYTHON_CMD" -c "import pymongo; pymongo.MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=1000).server_info()" 2>/dev/null; then
        echo "  ℹ️ Iniciando instância local do mongod em segundo plano..."
        mkdir -p /tmp/mongodb_eduscrap_data
        mongod --dbpath /tmp/mongodb_eduscrap_data --nounixsocket --logpath /tmp/mongodb_eduscrap_data/mongod.log --fork 2>/dev/null || true
    fi
fi

# 3. Inicializar coleções e índices do banco
echo "[3/5] Garantindo índices e coleções no MongoDB..."
"$PYTHON_CMD" backend/database_setup.py || echo "Aviso: Configuração de banco falhou (verifique se o MongoDB está rodando)."

# 3.2 Disparar varredura de todos os scrapers em segundo plano (atualizando logs/*.log e MongoDB)
mkdir -p "$PROJECT_ROOT/logs"
echo "[3.2/5] Executando scrapers em segundo plano (atualizando base e logs/*.log)..."
"$PYTHON_CMD" -u "$PROJECT_ROOT/run_scrapers.py" &
SCRAPER_PID=$!

# Kill any existing processes on our target ports
echo "[3.5/5] Liberando portas 8000 (Backend) e 3000 (Frontend)..."
kill_port_processes 8000
kill_port_processes 3000

# Trap para encerrar todos os processos ao pressionar Ctrl+C
cleanup() {
    echo ""
    echo "Encerrando servidores..."
    if [ -n "$SCRAPER_PID" ]; then
        kill "$SCRAPER_PID" 2>/dev/null || true
    fi
    if [ -n "$BACKEND_PID" ]; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
    kill_port_processes 8000
    kill_port_processes 3000
    echo "Todos os serviços foram finalizados. Até a próxima!"
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

echo "[4/5] Iniciando Backend FastAPI (Porta 8000)..."
sleep 1
(cd "$PROJECT_ROOT/backend" && "$PYTHON_CMD" -m uvicorn main:app --reload --host 0.0.0.0 --port 8000) &
BACKEND_PID=$!

sleep 2

echo "[5/5] Iniciando Servidor Frontend (Porta 3000)..."
sleep 1
(cd "$PROJECT_ROOT/frontend" && "$PYTHON_CMD" -m http.server 3000) &
FRONTEND_PID=$!

sleep 1

echo ""
echo "============================================================"
echo "          EDUSCRAP RODANDO COM SUCESSO!                 "
echo "============================================================"
echo "   Frontend:          http://localhost:3000"
echo "   API Backend:       http://localhost:8000"
echo "   Documentação (API): http://localhost:8000/docs"
echo "   Logs dos Scrapers: $PROJECT_ROOT/logs/"
echo "============================================================"
echo "Pressione [Ctrl + C] a qualquer momento para parar tudo."
echo ""

# Abrir automaticamente no navegador se houver interface gráfica
if command -v xdg-open >/dev/null 2>&1 && [ -n "$DISPLAY" ]; then
    xdg-open "http://localhost:3000" 2>/dev/null || true
fi

# Manter o script ativo monitorando os processos dos servidores
wait "$BACKEND_PID" "$FRONTEND_PID"
