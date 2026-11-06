"""Lê rotulagem/taxonomia.md (fonte única) e entrega a lista de itens, os níveis dos rótulos e a versão (hash).

    python rotulagem/taxonomia.py        # imprime a versão e a contagem de itens por dimensão
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO = Path(__file__).resolve().parent / "taxonomia.md"
NATUREZA = ["responsabilidade", "requisito", "contexto"]
OUTRO = "outro"


def versao() -> str:
    """12 primeiros hex do sha256 do texto (fim de linha normalizado): muda quando qualquer palavra da taxonomia muda."""
    return hashlib.sha256(ARQUIVO.read_bytes().replace(b"\r\n", b"\n")).hexdigest()[:12]


def texto() -> str:
    return ARQUIVO.read_text(encoding="utf-8")


def itens() -> list[dict]:
    """Itens em ordem de arquivo: dimensao, item, chave, definicao, borda, exemplos. O item `outro` vem por último."""
    dimensao = ""
    saida = []
    for linha in texto().splitlines():
        if linha.startswith("### "):
            dimensao = linha[4:].strip()
            continue
        if not linha.startswith("|"):
            continue
        celulas = [c.strip() for c in linha.strip().strip("|").split("|")]
        if len(celulas) != 5:
            continue
        m = re.fullmatch(r"`([a-z_]+(?:\.[a-z_]+)?)`", celulas[1])
        if not m or not dimensao:
            continue
        saida.append({"dimensao": dimensao, "item": celulas[0], "chave": m.group(1), "definicao": celulas[2],
                      "borda": celulas[3], "exemplos": celulas[4]})
    chaves = [i["chave"] for i in saida]
    if len(chaves) != len(set(chaves)):
        raise SystemExit("taxonomia.md: chave repetida")
    if OUTRO not in chaves:
        raise SystemExit("taxonomia.md: falta o item `outro`")
    return saida


def chaves() -> list[str]:
    return [i["chave"] for i in itens()]


if __name__ == "__main__":
    todos = itens()
    print(f"versão {versao()}: {len(todos)} itens")
    contagem: dict[str, int] = {}
    for i in todos:
        contagem[i["dimensao"]] = contagem.get(i["dimensao"], 0) + 1
    for d, n in contagem.items():
        print(f"  {n:2d}  {d}")
