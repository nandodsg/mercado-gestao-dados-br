"""Gera dbt/seeds/taxonomia.csv a partir de rotulagem/taxonomia.md (a fonte única). Rodar da raiz do repo.

    python rotulagem/gerar_seeds.py

`setores.csv` e `ferramentas.csv` são escritos à mão (são tabelas de decisão, não derivam da taxonomia); este script só
confere que o que eles prometem é coerente com ela.
"""

from __future__ import annotations

import csv

from taxonomia import RAIZ, itens, versao

SEEDS = RAIZ / "dbt" / "seeds"


def main() -> None:
    todos = itens()
    with (SEEDS / "taxonomia.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["ordem", "dimensao", "chave", "item", "definicao", "borda"])
        for n, i in enumerate(todos, 1):
            w.writerow([n, i["dimensao"], i["chave"], i["item"], i["definicao"], i["borda"]])
    print(f"taxonomia.csv: {len(todos)} itens (taxonomia {versao()})")

    with (SEEDS / "setores.csv").open(encoding="utf-8") as f:
        setores = list(csv.DictReader(f))
    print(f"setores.csv: {len(setores)} empresas, {len({s['setor'] for s in setores})} setores")
    with (SEEDS / "ferramentas.csv").open(encoding="utf-8") as f:
        ferramentas = list(csv.DictReader(f))
    print(f"ferramentas.csv: {len(ferramentas)} regras")


if __name__ == "__main__":
    main()
