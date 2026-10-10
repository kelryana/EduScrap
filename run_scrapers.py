import sys
import os
import time
import argparse
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "backend"
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

SCRAPERS = {
    "prae": {
        "nome": "PRAE/UERN (Estágios e Auxílios)",
        "script": "scraper_prae.py",
        "colecao": "vagas_estagio",
        "icone": "🎓"
    },
    "proex": {
        "nome": "PROEX/UERN (Bolsas e Projetos)",
        "script": "scraper_proex.py",
        "colecao": "vagas_bolsa",
        "icone": "💰"
    },
    "ufersa": {
        "nome": "UFERSA (Editais e Assistência)",
        "script": "scraper_ufersa.py",
        "colecao": "vagas_ufersa",
        "icone": "🏛️"
    },
    "noticias": {
        "nome": "Notícias Tech (G1 e Canaltech)",
        "script": "scraper_noticias.py",
        "colecao": "vagas_noticias",
        "icone": "⚡"
    },
    "portal_uern": {
        "nome": "Portal UERN (Mineração Textual)",
        "script": "scraper_portal_uern.py",
        "colecao": "vagas_portal_uern",
        "icone": "📰"
    },
    "ciee": {
        "nome": "CIEE (Estágios Comerciais)",
        "script": "scraper_ciee.py",
        "colecao": "vagas_ciee",
        "icone": "💼"
    },
    "cpps_ufersa": {
        "nome": "UFERSA (CPPS Processos Seletivos)",
        "script": "scraper_cpps_ufersa.py",
        "colecao": "editais",
        "icone": "📝"
    },
    "assecom_ufersa": {
        "nome": "UFERSA (ASSECOM Notícias e Editais)",
        "script": "scraper_assecom_ufersa.py",
        "colecao": "noticias",
        "icone": "📢"
    },
    "mprn": {
        "nome": "MPRN (Processos Seletivos e Residências)",
        "script": "scraper_mprn.py",
        "colecao": "vagas",
        "icone": "⚖️"
    },
    "ifrn": {
        "nome": "IFRN (Bolsas e Editais de Ensino)",
        "script": "scraper_ifrn.py",
        "colecao": "editais",
        "icone": "🌿"
    },
    "iel_rn": {
        "nome": "IEL/RN (Estágios e Oportunidades)",
        "script": "scraper_iel_rn.py",
        "colecao": "vagas",
        "icone": "🏭"
    },
    "capacitacao_bolsas": {
        "nome": "Capacitação, DIO e Bolsas de Estudo",
        "script": "scraper_capacitacao_bolsas.py",
        "colecao": "noticias",
        "icone": "💡"
    },
    "dom_mossoro": {
        "nome": "DOM Mossoró (Editais e Processos Seletivos)",
        "script": "scraper_dom_mossoro.py",
        "colecao": "editais",
        "icone": "🏛️"
    }
}

def obter_python_bin():
   
    venv_python = PROJECT_ROOT / "venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable

def obter_contagem_colecao(nome_colecao):
   
    try:
        from pymongo import MongoClient
        uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        db_name = os.getenv("MONGODB_DB", "hub_estudantes")
        client = MongoClient(uri, serverSelectionTimeoutMS=800)
        return client[db_name][nome_colecao].count_documents({})
    except Exception:
        return None

def executar_scraper(chave, info):
   
    python_bin = obter_python_bin()
    script_path = BACKEND_DIR / info["script"]
    log_file_path = LOGS_DIR / f"{chave}.log"

    contagem_antes = obter_contagem_colecao(info["colecao"])
    inicio = time.time()

    if not script_path.exists():
        return {
            "chave": chave,
            "info": info,
            "sucesso": False,
            "erro": f"Arquivo não encontrado: {script_path}",
            "duracao": 0,
            "log": str(log_file_path),
            "itens": 0
        }

    with open(log_file_path, "w", encoding="utf-8") as f_log:
        f_log.write(f"=== INÍCIO DA VARREDURA: {info['nome']} ===\n")
        f_log.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f_log.write(f"Comando: {python_bin} {script_path.name}\n\n")
        f_log.flush()

        try:
            # Executa com cwd no diretório backend para resolver imports relativos
            processo = subprocess.run(
                [python_bin, str(script_path)],
                cwd=str(BACKEND_DIR),
                stdout=f_log,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=300  # Limite máximo de 5 minutos por scraper para evitar travamentos
            )
            sucesso = (processo.returncode == 0)
            erro = None if sucesso else f"Código de saída: {processo.returncode}"
        except subprocess.TimeoutExpired:
            sucesso = False
            erro = "Tempo limite excedido (5 minutos)"
            f_log.write("\n[ERRO] Processo interrompido por timeout de 5 minutos.\n")
        except Exception as e:
            sucesso = False
            erro = str(e)
            f_log.write(f"\n[ERRO] Exceção na execução: {e}\n")

    duracao = round(time.time() - inicio, 1)
    contagem_depois = obter_contagem_colecao(info["colecao"])

    itens = 0
    if contagem_antes is not None and contagem_depois is not None:
        itens = max(0, contagem_depois)

    return {
        "chave": chave,
        "info": info,
        "sucesso": sucesso,
        "erro": erro,
        "duracao": duracao,
        "log": str(log_file_path),
        "total_itens": itens
    }

def main():
    parser = argparse.ArgumentParser(
        description="EduScrap - Orquestrador Paralelo de Coleta de Dados",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Exemplos:\n"
               "  python run_scrapers.py              # Executa todos os scrapers em paralelo\n"
               "  python run_scrapers.py prae proex   # Executa apenas PRAE e PROEX simultaneamente\n"
               "  python run_scrapers.py --serial     # Executa um por vez sequencialmente\n"
    )
    parser.add_argument(
        "fontes",
        nargs="*",
        help=f"Fontes específicas a executar (opções: {', '.join(SCRAPERS.keys())})"
    )
    parser.add_argument(
        "--serial",
        action="store_true",
        help="Executa sequencialmente em vez de em paralelo"
    )

    args = parser.parse_args()

    # Determina quais scrapers serão executados
    if args.fontes:
        selecionados = {}
        for f in args.fontes:
            f_lower = f.lower()
            if f_lower in SCRAPERS:
                selecionados[f_lower] = SCRAPERS[f_lower]
            else:
                print(f"⚠️ Fonte desconhecida ignorada: '{f}' (Disponíveis: {', '.join(SCRAPERS.keys())})")
        if not selecionados:
            print("❌ Nenhuma fonte válida selecionada.")
            return 1
    else:
        selecionados = SCRAPERS

    total = len(selecionados)
    modo = "SEQUENCIAL" if args.serial else "PARALELO CONCORRENTE"

    print("\n" + "=" * 65)
    print("      EDUSCRAP - VARREDURA AUTOMATIZADA DE DADOS")
    print("=" * 65)
    print(f"  Modo de Execução: {modo}")
    print(f"  Fontes Ativas:    {total} ({', '.join(selecionados.keys())})")
    print(f"   Pasta de Logs:    {LOGS_DIR}/")
    print("=" * 65 + "\n")

    inicio_global = time.time()
    resultados = []

    if args.serial or total == 1:
        # Modo sequencial
        for chave, info in selecionados.items():
            print(f"  {info['icone']} Executando: {info['nome']}...")
            res = executar_scraper(chave, info)
            resultados.append(res)
            if res["sucesso"]:
                print(f"     Concluído em {res['duracao']}s! (Itens na base: {res['total_itens']})")
            else:
                print(f"     ❌ Falhou ({res['erro']}). Veja o log: {res['log']}")
    else:
        # Modo paralelo concorrente (máxima performance e tempo reduzido)
        print("  Iniciando raspagens simultâneas em segundo plano...")
        with ThreadPoolExecutor(max_workers=min(total, 6)) as executor:
            futuros = {
                executor.submit(executar_scraper, chave, info): chave
                for chave, info in selecionados.items()
            }
            for futuro in as_completed(futuros):
                res = futuro.result()
                resultados.append(res)
                if res["sucesso"]:
                    print(f"  {res['info']['icone']} {res['info']['nome']:<34} | {res['duracao']:>4}s | Itens: {res['total_itens']}")
                else:
                    print(f"  ❌ {res['info']['icone']} {res['info']['nome']:<34} | FALHOU ({res['erro']}) | Log: logs/{res['chave']}.log")

    tempo_total = round(time.time() - inicio_global, 1)

    # Relatório Final
    sucessos = sum(1 for r in resultados if r["sucesso"])
    falhas = total - sucessos

    print("\n" + "=" * 65)
    print("                  RESUMO DA OPERAÇÃO")
    print("=" * 65)
    print(f"   Tempo Total Decorrido: {tempo_total}s (tempo do mais lento, sem acumular)")
    print(f"   Sucessos:              {sucessos}/{total}")
    if falhas > 0:
        print(f"  ⚠️ Falhas:                {falhas}/{total} (consulte os arquivos em logs/)")
    print("=" * 65 + "\n")

    return 0 if falhas == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
