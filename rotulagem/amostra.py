"""Sorteia as vagas dos conjuntos de rotulagem, com semente, e grava rotulagem/amostra/<conjunto>.json.

    python rotulagem/amostra.py pratica       # 3 vagas: 1 coordenador, 1 gerente e 1 de qualquer um dos dois
    python rotulagem/amostra.py referencia    # 16 vagas: 8 coordenador + 8 gerente, fora as da prática

A unidade é a linha do JD (responsabilidades, requisitos e diferenciais), com a seção de origem. Nível vem do mart
`mart_vagas` (rode `dbt build` antes). Vaga repetida (mesmo texto de JD, mesmo que o título ou a empresa mudem) conta
uma vez: fica a de menor id público. Cada vaga sai com as linhas já limpas e com o que as regras dão (peso, anos,
ferramentas); o nome da empresa e o cargo vão só pra página de revisão, nunca pro prompt.
"""

from __future__ import annotations

import argparse
import hashlib
import random

import duckdb

from common import AMOSTRA, RAIZ, ROTULAGEM, gravar_json, ler_json
from regras import anos, ferramentas, limpar, peso

BANCO = RAIZ / "dbt" / "target" / "mercado.duckdb"
SEMENTE = 20261106
CONJUNTOS = {"pratica": {"coordenador": 1, "gerente": 1, "qualquer": 1}, "referencia": {"coordenador": 8, "gerente": 8}}


JD_LINHAS = AMOSTRA / "jd_linhas.json"


def ler_jd_linhas() -> dict[str, list[dict]]:
    """Linhas do JD por vaga (`ordem`, `secao`, `texto`), geradas pelo exportador a partir do texto do anúncio."""
    if not JD_LINHAS.exists():
        raise SystemExit("Falta rotulagem/amostra/jd_linhas.json: gere com o exportador (linhas do JD, não versionadas).")
    return ler_json(JD_LINHAS)


def carregar() -> dict[str, dict]:
    if not BANCO.exists():
        raise SystemExit("Falta dbt/target/mercado.duckdb: rode `dbt build --project-dir dbt --profiles-dir dbt`.")
    con = duckdb.connect(str(BANCO), read_only=True)
    vagas = {r[0]: {"id_publico": r[0], "empresa": r[1], "cargo": r[2], "nivel": r[3], "linhas": []}
             for r in con.execute("select id_publico, empresa, cargo_oficial, nivel from mart_vagas "
                                  "order by id_publico").fetchall()}
    for id_publico, linhas in ler_jd_linhas().items():
        if id_publico not in vagas:
            continue
        for l in linhas:
            limpo = limpar(l["texto"])
            vagas[id_publico]["linhas"].append({
                "ordem": l["ordem"], "secao": l["secao"], "texto": limpo,
                "peso": "diferencial" if l["secao"] == "diferenciais" else peso(limpo), "anos": anos(limpo),
                "ferramentas": ferramentas(limpo)})
    vagas = {i: v for i, v in vagas.items() if v["linhas"]}  # vaga sem seção de responsabilidade/requisito não entra
    for v in vagas.values():
        v["impressao"] = hashlib.sha256("\n".join(l["texto"] for l in v["linhas"]).encode()).hexdigest()[:12]
    return vagas


def sem_repeticao(vagas: dict[str, dict]) -> dict[str, dict]:
    vistas, saida = set(), {}
    for id_publico in sorted(vagas):
        if vagas[id_publico]["impressao"] not in vistas:
            vistas.add(vagas[id_publico]["impressao"])
            saida[id_publico] = vagas[id_publico]
    return saida


def sortear(conjunto: str, semente: int) -> list[dict]:
    todas = sem_repeticao(carregar())
    excluir: set[str] = set()
    anterior = ROTULAGEM / "historico" / "unidade-linha-do-fit" / "amostra" / "pratica.json"
    if anterior.exists():  # quem revisa já viu estas vagas (e as da mesma empresa): ficam fora de qualquer sorteio
        empresas = {v["empresa"] for v in ler_json(anterior)["vagas"]}
        excluir = {i for i, v in todas.items() if v["empresa"] in empresas}
    if conjunto == "referencia":
        prat = ler_json(AMOSTRA / "pratica.json")
        excluir |= {v["id_publico"] for v in prat["vagas"]}
        empresas_pratica = {v["empresa"] for v in prat["vagas"]}  # quem revisa já viu estas empresas
        excluir |= {i for i, v in todas.items() if v["empresa"] in empresas_pratica}
        impressoes = {v["impressao"] for v in carregar().values() if v["id_publico"] in excluir}
        excluir |= {i for i, v in todas.items() if v["impressao"] in impressoes}
    rng = random.Random(semente)
    escolhidas: list[dict] = []
    for nivel, n in CONJUNTOS[conjunto].items():
        if nivel == "qualquer":
            pool = [v for i, v in sorted(todas.items()) if v["nivel"] in ("coordenador", "gerente")
                    and i not in excluir and i not in {e["id_publico"] for e in escolhidas}]
        else:
            pool = [v for i, v in sorted(todas.items()) if v["nivel"] == nivel and i not in excluir]
        escolhidas += rng.sample(pool, n)
    return escolhidas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("conjunto", choices=sorted(CONJUNTOS))
    parser.add_argument("--semente", type=int, default=SEMENTE)
    args = parser.parse_args()
    destino = AMOSTRA / f"{args.conjunto}.json"
    if destino.exists():
        raise SystemExit(f"{destino.name} já existe: o sorteio é único (apague o arquivo de propósito pra refazer).")
    vagas = sortear(args.conjunto, args.semente)
    gravar_json(destino, {"conjunto": args.conjunto, "semente": args.semente, "criterio": CONJUNTOS[args.conjunto],
                          "unidade": "linha do JD", "vagas": [{k: v[k] for k in ("id_publico", "nivel", "empresa", "cargo", "impressao", "linhas")}
                                    for v in vagas]})
    for v in vagas:
        print(f"{v['id_publico']}  {v['nivel']:11s} {len(v['linhas']):2d} linhas  {v['empresa']} — {v['cargo']}")
    print(f"{sum(len(v['linhas']) for v in vagas)} linhas -> {destino}")


if __name__ == "__main__":
    main()
