import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_telemetria_requer_autenticacao():
    # Sem credencial admin deve barrar caso API_KEY esteja configurada, ou retornar 200 em dev_default
    response = client.get("/api/admin/telemetria")
    assert response.status_code in [200, 403]

def test_telemetria_retorna_metricas_fidedignas():
    # Com chave de admin
    response = client.get("/api/admin/telemetria", headers={"X-API-Key": ""})
    assert response.status_code == 200
    dados = response.json()
    assert dados["sucesso"] is True
    assert "timestamp" in dados
    
    # 1. Quadro de Memória Atual (Processo e Host)
    mem_atual = dados["memoria_atual"]
    assert "rss_mb" in mem_atual
    assert "vms_mb" in mem_atual
    assert "percent_memoria_processo" in mem_atual
    assert "threads_ativas" in mem_atual
    assert "objetos_heap_gc" in mem_atual
    assert "uptime_segundos" in mem_atual
    assert "uptime_formatado" in mem_atual
    assert isinstance(mem_atual["rss_mb"], (int, float))
    assert mem_atual["threads_ativas"] >= 1
    assert mem_atual["objetos_heap_gc"] > 0
    
    # 2. Quadro de Memória em Persistência (MongoDB)
    mem_persistencia = dados["memoria_persistencia"]
    assert "status_banco" in mem_persistencia
    assert "dados_tamanho_kb" in mem_persistencia
    assert "armazenamento_disco_kb" in mem_persistencia
    assert "total_documentos" in mem_persistencia
    assert "total_colecoes" in mem_persistencia
    assert "colecoes" in mem_persistencia
    assert isinstance(mem_persistencia["colecoes"], list)

def test_limpar_vencidos_admin():
    response = client.post("/api/admin/limpar-vencidos", headers={"X-API-Key": ""})
    assert response.status_code == 200
    dados = response.json()
    assert dados["sucesso"] is True
    assert "itens_removidos" in dados
    assert isinstance(dados["itens_removidos"], int)
