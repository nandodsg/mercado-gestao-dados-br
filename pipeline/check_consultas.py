"""Confere que cada consulta de `consultas/` dá, sobre os Parquet que a página publica, o mesmo resultado que a página mostra.

A página lê os marts em Parquet (`<pasta>/dados/*.parquet`) com DuckDB no navegador; a publicação (`gerar_site.py`) roda os
mesmos arquivos `.sql` no DuckDB do dbt e grava o resultado de cada um em `dados/pagina.json`. Este script é a terceira ponta:
abre só os Parquet publicados (nada do dbt), roda cada `consultas/pN_M.sql` e compara com o `pagina.json`. Se alguém mexer
numa consulta e a página não refletir, ou o Parquet divergir do mart, a CI cai.

Uso (depois de `python pipeline/gerar_site.py _site --dados data`):
    python pipeline/check_consultas.py _site
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parents[1]
CONSULTAS = RAIZ / "consultas"
TABELAS = ("mart_vaga_item", "mart_vaga_ferramenta", "mart_vagas", "mart_repost")


def norm(x):
    """Mesma regra de `perguntas.ler`: número inteiro vira int; float fica com 9 casas (a ordem de soma pode mudar o último dígito)."""
    if isinstance(x, float):
        return int(x) if x == int(x) else round(x, 9)
    return x


def rodar(con, sql: str) -> dict:
    r = con.sql(sql)
    return {"cols": list(r.columns), "rows": [[norm(x) for x in row] for row in r.fetchall()]}


def main(site: Path) -> int:
    dados = site / "dados"
    pagina = json.loads((dados / "pagina.json").read_text(encoding="utf-8"))
    con = duckdb.connect()
    for t in TABELAS:
        f = dados / f"{t}.parquet"
        if not f.exists():
            print(f"FALTA {f}")
            return 1
        con.sql(f"create view {t} as select * from read_parquet('{f.as_posix()}')")

    erros: list[str] = []
    arquivos = sorted(p for p in CONSULTAS.glob("p*_*.sql"))
    na_pagina = {v["f"]: v for card in pagina["perguntas"].values() for v in card["views"]}
    for p in arquivos:
        nome = p.stem
        sql = p.read_text(encoding="utf-8")
        v = na_pagina.get(nome)
        if v is None:
            erros.append(f"{nome}: o arquivo existe em consultas/, mas nenhuma vista da página o usa")
            continue
        if (site / "consultas" / p.name).read_text(encoding="utf-8") != sql:
            erros.append(f"{nome}: a cópia publicada em {site.name}/consultas/ difere do arquivo")
        if v["sql"].strip() != sql.strip():
            erros.append(f"{nome}: o SQL mostrado na página difere do arquivo")
        try:
            r = rodar(con, sql)
        except Exception as e:  # noqa: BLE001 — qualquer erro de SQL é falha da conferência
            erros.append(f"{nome}: não rodou sobre os Parquet ({str(e).splitlines()[0]})")
            continue
        esperado = {"cols": v["res"]["cols"], "rows": [[norm(x) for x in row] for row in v["res"]["rows"]]}
        if r["cols"] != esperado["cols"]:
            erros.append(f"{nome}: colunas {r['cols']} ≠ {esperado['cols']} da página")
        elif r["rows"] != esperado["rows"]:
            erros.append(f"{nome}: {len(r['rows'])} linhas sobre o Parquet, {len(esperado['rows'])} na página (ou valores diferentes)")
    for nome in sorted(set(na_pagina) - {p.stem for p in arquivos}):
        erros.append(f"{nome}: a página usa uma vista sem arquivo em consultas/")

    views = (CONSULTAS / "_views.sql").read_text(encoding="utf-8")
    for t in TABELAS:
        if not re.search(rf"\b{t}\b.*{t}\.parquet", views):
            erros.append(f"_views.sql não cria a vista {t} a partir de {t}.parquet")

    if erros:
        print(f"{len(erros)} problema(s) nas consultas:")
        for e in erros:
            print("  -", e)
        return 1
    print(f"{len(arquivos)} consultas rodaram sobre os Parquet publicados e batem com a página")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1] if len(sys.argv) > 1 else "_site")))
