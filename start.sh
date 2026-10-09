#!/usr/bin/env bash

# ==============================================================================
# Script de Inicialização Automatizada - EduScrap UERN
# ==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "============================================================"
echo "          🚀 INICIALIZANDO PROJETO EDUSCRAP UERN            "
echo "============================================================"

# Função para matar processos em uma porta específica
kill_port_processes() {
    local port=$1
    echo "  -> Verificando processos na porta $port..."
    local pids=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pids" ]; then
        echo "  -> Matando processos na porta $port (PID: $pids)..."
        kill -9 $pids 2>/dev/null || true
        sleep 2  # Aguarda um pouco para liberar a porta
    fi
}

# 1. Verificar ambiente virtual
if [ -d "venv" ]; then
    echo "[1/4] Ativando ambiente virtual (venv)..."
    source venv/bin/activate
elif [ -d "../venv" ]; then
    source ../venv/bin/activate
else
    echo "⚠️ Ambiente virtual 'venv' não encontrado na raiz."
    echo "Recomendado criar com: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
fi

# 2. Verificar MongoDB
echo "[2/4] Verificando status do MongoDB (porta 27017)..."
if command -v nc >/dev/null 2>&1 && nc -z 127.0.0.1 27017 2>/dev/null; then
    echo "  -> MongoDB já está em execução!"
elif python3 -c "import pymongo; pymongo.MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=1000).server_info()" 2>/dev/null; then
    echo "  -> MongoDB conectado com sucesso!"
else
    echo "  -> Tentando inicializar o serviço do MongoDB..."
    if command -v systemctl >/dev/null 2>&1 && systemctl status mongod >/dev/null 2>&1; then
        sudo systemctl start mongod || true
    elif command -v service >/dev/null 2>&1; then
        sudo service mongod start 2>/dev/null || sudo service mongodb start 2>/dev/null || true
    fi

    # Se ainda não estiver rodando, tenta iniciar processo local do mongod
    if ! python3 -c "import pymongo; pymongo.MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=1000).server_info()" 2>/dev/null; then
        echo "  ℹ️ Iniciando instância local do mongod em segundo plano..."
        mkdir -p /tmp/mongodb_eduscrap_data
        mongod --dbpath /tmp/mongodb_eduscrap_data --nounixsocket --logpath /tmp/mongodb_eduscrap_data/mongod.log --fork 2>/dev/null || true
    fi
fi

# 3. Inicializar coleções e índices do banco
echo "[3/4] Garantindo índices e coleções no MongoDB..."
python3 backend/database_setup.py || echo "⚠️ Aviso: Configuração de banco falhou (verifique se o MongoDB está rodando)."

# Kill any existing processes on our target ports
echo "[3.5/4] Liberando portas 8000 (Backend) e 3000 (Frontend)..."
kill_port_processes 8000
kill_port_processes 3000

# Trap para encerrar todos os processos ao pressionar Ctrl+C
cleanup() {
    echo ""
    echo "🛑 Encerrando servidores..."
    if [ -n "$BACKEND_PID" ]; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
    # Certificar-se de que nenhuma instância permanece
    kill_port_processes 8000
    kill_port_processes 3000
    echo "✔️ Todos os serviços foram finalizados. Até a próxima!"
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# 4. Iniciar Backend FastAPI
echo "[4/4] Iniciando Backend FastAPI (Porta 8000)..."
sleep 1  # Pequena pausa para garantir que a porta esteja liberada
(cd "$PROJECT_ROOT/backend" && uvicorn main:app --reload --host 0.0.0.0 --port 8000) &
BACKEND_PID=$!

# Aguardar 2s para a API subir
sleep 2

# 5. Iniciar Servidor Frontend
echo "[5/4] Iniciando Servidor Frontend (Porta 3000)..."
sleep 1  # Pequena pausa para garantir que a porta esteja liberada
(cd "$PROJECT_ROOT/frontend" && python3 -m http.server 3000) &
FRONTEND_PID=$!

sleep 1

echo ""
echo "============================================================"
echo "          🎉 EDUSCRAP RODANDO COM SUCESSO!                 "
echo "============================================================"
echo "  🌐 Frontend:          http://localhost:3000"
echo "  🚀 API Backend:       http://localhost:8000"
echo "  📚 Documentação (API): http://localhost:8000/docs"
echo "============================================================"
echo "Pressione [Ctrl + C] a qualquer momento para parar tudo."
echo ""

# Abrir automaticamente no navegador se houver interface gráfica
if command -v xdg-open >/dev/null 2>&1 && [ -n "$DISPLAY" ]; then
    xdg-open "http://localhost:3000" 2>/dev/null || true
fi

# Manter o script ativo monitorando os processos
wait "$BACKEND_PID" "$FRONTEND_PID"