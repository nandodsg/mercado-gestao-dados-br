"""Concordância entre rotuladores num conjunto: rotulagem/saida/concordancia_<conjunto>.md. Grátis: só lê arquivos locais.

    python rotulagem/concordancia.py pratica

Para cada par de rotuladores (e, se existir, a decisão final em rotulagem/referencia/<conjunto>_revisado.csv):
`natureza` (concordância e kappa de Cohen), presença por dimensão (a linha cita algum item da dimensão? sim/não, kappa),
presença por item (F1 só dos itens com 10 ou mais linhas positivas na referência; abaixo disso, só a contagem) e
conjunto exato de itens (a linha tem exatamente os mesmos itens nos dois). Kappa = concordância corrigida pelo que os
dois acertariam por acaso com as mesmas frequências (0 = acaso, 1 = perfeito).
"""

from __future__ import annotations

import argparse
import csv
import itertools
from collections import Counter, defaultdict

import taxonomia
from common import AMOSTRA, OPUS, REFERENCIA, ROTULADORES_GATEWAY, SAIDA, ler_json, slug


def kappa(a: list, b: list) -> float | None:
    n = len(a)
    if not n:
        return None
    observado = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    esperado = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return None if esperado == 1 else (observado - esperado) / (1 - esperado)


def f1(a: list[bool], b: list[bool]) -> float | None:
    tp = sum(x and y for x, y in zip(a, b))
    fp = sum((not x) and y for x, y in zip(a, b))
    fn = sum(x and (not y) for x, y in zip(a, b))
    return None if tp + fp + fn == 0 else 2 * tp / (2 * tp + fp + fn)


def carregar_modelo(modelo: str, conjunto: str) -> dict[tuple[str, int], dict]:
    bruto = ler_json(SAIDA / f"{slug(modelo)}_{conjunto}.json")
    return {(i, l["ordem"]): {"natureza": l["natureza"], "itens": set(l["itens"])}
            for i, r in bruto.items() for l in r["linhas"]}


def carregar_revisado(conjunto: str) -> dict[tuple[str, int], dict] | None:
    caminho = REFERENCIA / f"{conjunto}_revisado.csv"
    if not caminho.exists():
        return None
    saida: dict[tuple[str, int], dict] = defaultdict(lambda: {"natureza": None, "itens": set()})
    with caminho.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            e = saida[(r["id_publico"], int(r["ordem"]))]
            if r["tipo"] == "natureza":
                e["natureza"] = r["valor"]
            elif r["tipo"] == "item" and r["incluido"] == "1":
                e["itens"].add(r["valor"])
    return dict(saida)


def fmt(x: float | None) -> str:
    return "n/d" if x is None else f"{x:.2f}"


def comparar(nome_a: str, a: dict, nome_b: str, b: dict, dim_de: dict[str, str], minimo: int = 10) -> list[str]:
    chaves = sorted(set(a) & set(b))
    linhas = [f"## {nome_a} × {nome_b}", "", f"{len(chaves)} linhas rotuladas pelos dois.", ""]
    nat_a, nat_b = [a[k]["natureza"] for k in chaves], [b[k]["natureza"] for k in chaves]
    concord = sum(x == y for x, y in zip(nat_a, nat_b))
    linhas += [f"- `natureza`: {concord}/{len(chaves)} iguais, kappa {fmt(kappa(nat_a, nat_b))}"]
    exato = sum(a[k]["itens"] == b[k]["itens"] for k in chaves)
    linhas += [f"- conjunto exato de itens: {exato}/{len(chaves)} linhas", "", "| dimensão | kappa da presença | linhas com a dimensão (A / B) |",
               "|---|---|---|"]
    for dim in dict.fromkeys(dim_de.values()):
        pa = [any(dim_de[i] == dim for i in a[k]["itens"]) for k in chaves]
        pb = [any(dim_de[i] == dim for i in b[k]["itens"]) for k in chaves]
        linhas.append(f"| {dim} | {fmt(kappa(pa, pb))} | {sum(pa)} / {sum(pb)} |")
    linhas += ["", f"| item | positivas (A / B) | F1 (só com {minimo}+ positivas em A) |", "|---|---|---|"]
    for item in taxonomia.chaves():
        pa = [item in a[k]["itens"] for k in chaves]
        pb = [item in b[k]["itens"] for k in chaves]
        if sum(pa) + sum(pb) == 0:
            continue
        linhas.append(f"| `{item}` | {sum(pa)} / {sum(pb)} | {fmt(f1(pa, pb)) if sum(pa) >= minimo else 'não avaliável'} |")
    return linhas + [""]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("conjunto", choices=["pratica", "referencia"])
    args = parser.parse_args()
    dim_de = {i["chave"]: i["dimensao"] for i in taxonomia.itens()}
    rotulos = {m: carregar_modelo(m, args.conjunto) for m in (OPUS, *ROTULADORES_GATEWAY)
               if (SAIDA / f"{slug(m)}_{args.conjunto}.json").exists()}
    revisado = carregar_revisado(args.conjunto)
    if revisado:
        rotulos["revisado"] = revisado
    if len(rotulos) < 2:
        raise SystemExit("Precisa de pelo menos dois rotuladores.")
    linhas = [f"# Concordância — conjunto {args.conjunto}", "", f"Taxonomia {taxonomia.versao()}.", ""]
    for (na, a), (nb, b) in itertools.combinations(rotulos.items(), 2):
        linhas += comparar(na, a, nb, b, dim_de)
    destino = SAIDA / f"concordancia_{args.conjunto}.md"
    destino.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print("\n".join(linhas[:40]))
    print(f"-> {destino}")


if __name__ == "__main__":
    main()
