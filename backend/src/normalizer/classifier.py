# backend/src/normalizer/classifier.py

import re
from typing import Dict, List, Set, Any

# Mapeamento de Cursos com palavras-chave e sinônimos
MAPEAMENTO_CURSOS = {
    "Educação Física": [
        r"\beducaç[aã]o f[íi]sica\b", r"\bed\.?\s*f[íi]sica\b", r"\besporte\b",
        r"\bdesporto\b", r"\batividade f[íi]sica\b", r"\bacupuntura desportiva\b"
    ],
    "Letras": [
        r"\bletras\b", r"\bl[íi]ngua portuguesa\b", r"\bl[íi]ngua inglesa\b",
        r"\bl[íi]ngua espanhola\b", r"\bliteratura\b", r"\blingu[íi]stica\b",
        r"\blibras\b", r"\btraduç[aã]o\b"
    ],
    "História": [
        r"\bhist[óo]ria\b", r"\bhistoriador\b", r"\bpatrim[ôo]nio hist[óo]rico\b",
        r"\barquivologia\b", r"\bmem[óo]ria cultural\b"
    ],
    "Pedagogia": [
        r"\bpedagogia\b", r"\bpedag[óo]gic[ao]\b", r"\bdoc[êe]ncia\b",
        r"\beducaç[aã]o infantil\b", r"\bensino fundamental\b", r"\bgest[aã]o escolar\b",
        r"\bpibid\b", r"\bresid[êe]ncia pedag[óo]gica\b", r"\blicenciatura\b"
    ],
    "Ciências Biológicas": [
        r"\bci[êe]ncias biol[óo]gicas\b", r"\bbiologia\b", r"\bbi[óo]log[ao]\b",
        r"\bbiodiversidade\b", r"\becologia\b", r"\bzoologia\b", r"\bbot[âa]nica\b",
        r"\bgen[ée]tica\b", r"\bbiotecnologia\b"
    ],
    "Serviço Social": [
        r"\bserviço social\b", r"\bassisten(te|cia) social\b", r"\bpol[íi]ticas p[úu]blicas\b",
        r"\bvulnerabilidade social\b", r"\bcras\b", r"\bcreas\b"
    ],
    "Geografia": [
        r"\bgeografia\b", r"\bge[óo]graf[ao]\b", r"\bgeoprocessamento\b",
        r"\bcartografia\b", r"\bclimatologia\b", r"\brelevo\b", r"\bmeio ambiente\b"
    ],
    "Filosofia": [
        r"\bfilosofia\b", r"\bfil[óo]sof[ao]\b", r"\b[ée]tica\b", r"\bepistemologia\b"
    ],
    "Ciência da Computação": [
        r"\bci[êe]ncia da computaç[aã]o\b", r"\bcomputaç[aã]o\b", r"\binform[áa]tica\b",
        r"\bsistemas de informaç[aã]o\b", r"\bengenharia de software\b",
        r"\ban[áa]lise e desenvolvimento\b", r"\bdesenvolvimento web\b",
        r"\bprogramaç[aã]o\b", r"\bdesenvolvedor\b", r"\bti\b", r"\btecnologia da informaç[aã]o\b"
    ],
    "Direito": [
        r"\bdireito\b", r"\bci[êe]ncias jur[íi]dicas\b", r"\bjur[íi]dic[ao]\b",
        r"\badvocacia\b", r"\btribunal\b", r"\bvara c[íi]vel\b", r"\bvara criminal\b",
        r"\bjuizado\b", r"\bpromotoria\b", r"\bdefensoria\b"
    ],
    "Administração": [
        r"\badministraç[aã]o\b", r"\badministrador\b", r"\bgest[aã]o\b",
        r"\brecursos humanos\b", r"\brh\b", r"\bfinanceir[ao]\b", r"\bmarketing\b",
        r"\blog[íi]stica\b", r"\bprocessos administrativos\b"
    ],
    "Ciências Contábeis": [
        r"\bci[êe]ncias cont[áa]beis\b", r"\bcontabilidade\b", r"\bcontador\b",
        r"\bauditoria\b", r"\bfiscal\b", r"\btribut[áa]ri[ao]\b"
    ]
}

# Mapeamento de Áreas de Conhecimento
MAPEAMENTO_AREAS = {
    "Tecnologia": [
        r"\btecnologia\b", r"\bcomputaç[aã]o\b", r"\binform[áa]tica\b", r"\bsoftware\b",
        r"\bsistemas\b", r"\bti\b", r"\bdados\b", r"\bweb\b", r"\bprogramador\b",
        r"\bintelig[êe]ncia artificial\b", r"\bredes\b", r"\bautomaç[aã]o\b"
    ],
    "Saúde": [
        r"\bsa[úu]de\b", r"\bm[ée]dic[ao]\b", r"\benfermagem\b", r"\bfarm[áa]cia\b",
        r"\bambulat[óo]ri\b", r"\bhospital\b", r"\bcl[íi]nica\b", r"\bcl[íi]nic[ao]\b",
        r"\bnutriç[aã]o\b", r"\bfisioterapia\b", r"\bodontologia\b", r"\bbiol[óo]gic[ao]\b"
    ],
    "Humanas": [
        r"\bhumanas\b", r"\bletras\b", r"\bhist[óo]ria\b", r"\bpedagogia\b",
        r"\bserviço social\b", r"\bgeografia\b", r"\bfilosofia\b", r"\bdireito\b",
        r"\bci[êe]ncias sociais\b", r"\beducaç[aã]o\b", r"\bpsicologia\b",
        r"\bcomunicaç[aã]o\b", r"\bjornalismo\b", r"\bci[êe]ncias humanas\b"
    ],
    "Exatas": [
        r"\bexatas\b", r"\bmatem[áa]tica\b", r"\bf[íi]sica\b", r"\bqu[íi]mica\b",
        r"\bengenharia\b", r"\bcontabilidade\b", r"\bestat[íi]stica\b",
        r"\bc[áa]lculo\b", r"\bci[êe]ncias exatas\b"
    ],
    "Extensão": [
        r"\bextens[aã]o\b", r"\bproex\b", r"\bproec\b", r"\bcomunidade\b",
        r"\bcultural\b", r"\bprojeto social\b", r"\baç[aã]o comunit[áa]ria\b"
    ],
    "Pesquisa": [
        r"\bpesquisa\b", r"\bpibic\b", r"\bpibiti\b", r"\bfapern\b", r"\bcnpq\b",
        r"\bcapes\b", r"\biniciaç[aã]o cient[íi]fica\b", r"\bcient[íi]fic[ao]\b",
        r"\blaborat[óo]rio\b", r"\bp[óo]s-graduaç[aã]o\b", r"\bmestrado\b"
    ],
    "Inovação": [
        r"\binovaç[aã]o\b", r"\bstartup\b", r"\bincubadora\b", r"\bsebrae\b",
        r"\bali\b", r"\bempreendedorismo\b", r"\bpatente\b", r"\btecnol[óo]gic[ao]\b"
    ]
}


def classificar_oportunidade(titulo: str, texto: str = "") -> Dict[str, Any]:
 
    conteudo_completo = f"{titulo or ''} {texto or ''}".lower()

    cursos_encontrados: Set[str] = set()
    areas_encontradas: Set[str] = set()

    # 1. Busca por cursos
    for curso, padroes in MAPEAMENTO_CURSOS.items():
        for padrao in padroes:
            if re.search(padrao, conteudo_completo, re.IGNORECASE):
                cursos_encontrados.add(curso)
                break

    # 2. Busca por áreas
    for area, padroes in MAPEAMENTO_AREAS.items():
        for padrao in padroes:
            if re.search(padrao, conteudo_completo, re.IGNORECASE):
                areas_encontradas.add(area)
                break

    # 3. Detecta oportunidades gerais/universais (atendem a todos os cursos)
    termos_gerais = [
        r"\bassist[êe]ncia estudantil\b", r"\baux[íi]lio creche\b", r"\baux[íi]lio moradia\b",
        r"\baux[íi]lio alimentaç[aã]o\b", r"\brestaurante universit[áa]rio\b", r"\binclus[aã]o digital\b",
        r"\btodos os cursos\b", r"\bqualquer curso\b", r"\bqualquer graduaç[aã]o\b"
    ]
    eh_geral = any(re.search(tg, conteudo_completo, re.IGNORECASE) for tg in termos_gerais)

    # Se identificou cursos, garante que as áreas correspondentes também sejam incluídas
    if any(c in cursos_encontrados for c in ["Pedagogia", "Letras", "História", "Filosofia", "Serviço Social", "Geografia", "Direito"]):
        areas_encontradas.add("Humanas")

    if any(c in cursos_encontrados for c in ["Ciência da Computação"]):
        areas_encontradas.add("Tecnologia")
        areas_encontradas.add("Exatas")

    if any(c in cursos_encontrados for c in ["Educação Física", "Ciências Biológicas"]):
        areas_encontradas.add("Saúde")

    # Se não achou nenhuma área mas é geral
    if not areas_encontradas and eh_geral:
        areas_encontradas.add("Extensão")

    return {
        "cursos": sorted(list(cursos_encontrados)),
        "areas": sorted(list(areas_encontradas)),
        "geral": eh_geral
    }
