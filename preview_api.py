##preview_api.py
"""Servidor de preview: API /api/* com dados seedados em mongomock + estáticos do frontend.
Uso temporário para tirar screenshots do dashboard em navegador real (não faz parte do app)."""
import sys, os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

# Monkeypatch MongoClient ANTES de importar main
import mongomock
import pymongo
pymongo.MongoClient = mongomock.MongoClient

import main  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

db = main.db

agora = datetime.now()

def rnd(col, docs):
    db[col].insert_many(docs)

def vaga(nome, cat=None, venc_dias=10, criado_dias=2):
    d = {"nome": nome,
         "data_vencimento": agora + timedelta(days=venc_dias),
         "criado_em": agora - timedelta(days=criado_dias)}
    if cat: d["categoria"] = cat
    return d

rnd("vagas_estagio", [vaga(f"Estágio {i}", ["Engenharias", "Saúde", "Licenciaturas", "Administração", "TI", None][i % 6], criado_dias=i % 7) for i in range(132)])
rnd("vagas_bolsa", [vaga(f"Bolsa Proex {i}", criado_dias=i % 7) for i in range(58)])
rnd("vagas_ufersa", [vaga(f"Edital UFERSA {i}", criado_dias=i % 7) for i in range(37)])
rnd("vagas_ciee", [vaga(f"CIEE {i}") for i in range(29)])
rnd("vagas_mprn", [vaga(f"MPRN {i}") for i in range(14)])
rnd("vagas_iel", [vaga(f"IEL {i}") for i in range(21)])
rnd("vagas_ifrn", [vaga(f"IFRN {i}") for i in range(9)])
rnd("vagas_dom", [vaga(f"DOM Mossoró {i}", criado_dias=i % 7) for i in range(18)])
rnd("vagas_portal_uern", [{"nome": f"Portal UERN {i}"} for i in range(46)])
rnd("vagas_noticias", [{"tipo": "noticia", "nome": f"Notícia Tech {i}", "fonte": "ufersa", "criado_em": agora - timedelta(days=i % 7)} for i in range(64)])
rnd("noticias", [{"tipo": "capacitacao", "nome": f"Curso {i}", "criado_em": agora - timedelta(days=i % 7)} for i in range(25)] +
                [{"tipo": "bolsa_estudo", "nome": f"Bolsa Estudo {i}"} for i in range(12)] +
                [{"tipo": "artigo", "nome": f"Artigo {i}", "fonte": "edu", "criado_em": agora - timedelta(days=i % 7)} for i in range(15)])
rnd("historico_varreduras", [{"data_execucao": agora - timedelta(minutes=42), "status": "sucesso", "tempo_duracao_segundos": 87}])

print("Seed ok:", sum(db[c].count_documents({}) for c in db.list_collection_names()), "docs")

# Override da rota real (dependente de Mongo vivo) com a MESMA função, já que mongomock atende
# o enough? Se alguma operação falhar no mongomock, cai no mock simples abaixo.
try:
    r = main.obter_estatisticas()
    print("Rota real OK — totais:", r["totais"])
    USE_REAL = True
except Exception as e:
    print("Rota real falhou no mongomock:", e)
    USE_REAL = False

if not USE_REAL:
    @main.app.get("/api/estatisticas")
    def estatisticas_mock():
        nomes_dias = ["DOM", "SEG", "TER", "QUA", "QUI", "SEX", "SÁB"]
        cores = ["#10B981", "#FF5C00", "#0F172A", "#38BDF8", "#8B5CF6", "#FACC15", "#FB923C"]
        vals = [4, 9, 12, 7, 15, 11, 6]
        return {
            "totais": {"estagios": 132, "bolsas": 58, "ufersa": 37, "ciee": 29, "noticias": 79,
                       "noticias_ufersa": 40, "cursos_bolsas": 37, "portal_uern": 46, "mprn": 14,
                       "ifrn": 9, "iel": 21, "dom": 18},
            "total_geral": 483, "reta_final_urgente": 23, "vigentes": 268, "oportunidades_com_prazo": 318,
            "prae_categorias": [{"categoria": c, "total": t} for c, t in
                                [("Engenharias", 34), ("Saúde", 28), ("Licenciaturas", 22), ("TI", 19), ("Administração", 15), ("Geral / Não Especificada", 14)]],
            "fluxo_semanal": [{"dia": n, "valor": v, "cor": c} for n, v, c in zip(nomes_dias, vals, cores)],
            "tem_dados_fluxo": True,
            "ultima_varredura": {"data": (agora - timedelta(minutes=42)).isoformat(), "status": "sucesso", "duracao_segundos": 87},
            "ranking_fontes": sorted([{"origem": k, "total": v} for k, v in
                                      [("estagios", 132), ("bolsas", 58), ("noticias", 79), ("portal_uern", 46),
                                       ("ufersa", 37), ("ciee", 29), ("iel", 21), ("dom", 18), ("mprn", 14), ("ifrn", 9)]],
                                      key=lambda i: -i["total"]),
            "canais_monitorados": 12,
        }

from fastapi.staticfiles import StaticFiles

@main.app.get("/api/db-status")
def db_status_mock():
    return {"colecoes": [], "saudavel": True}

main.app.mount("/", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "frontend"), html=True), name="statics")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(main.app, host="127.0.0.1", port=8000, log_level="warning")
