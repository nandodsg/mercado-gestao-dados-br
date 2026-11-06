"""Rótulos que saem por regra, sem modelo: texto limpo, peso (obrigatório | diferencial), anos e ferramentas.

As regras valem pra qualquer linha de requisito e são medidas na referência como mais um rotulador. As ferramentas
vêm do dicionário dbt/seeds/ferramentas.csv (regex sobre o texto sem acento e em minúsculas; `remover` é apagado antes).
"""

from __future__ import annotations

import csv
import re
import unicodedata
from functools import lru_cache

from taxonomia import RAIZ

MARCADORES_DIFERENCIAL = re.compile(
    r"\bdif\.|\bdiferencial|\bdiferenciais|\bdesejavel|\bdesejaveis|nice[ -]to[ -]have|nice \(to have\)|great[ -]to[ -]have"
    r"|\bplus\b|\bpreferred\b|\bdest\.|\(destaque\)|\bdestaque\b|\bwould be a plus|\bis a plus")
NUMEROS = {"um": 1, "uma": 1, "dois": 2, "duas": 2, "tres": 3, "quatro": 4, "cinco": 5, "seis": 6, "sete": 7,
           "oito": 8, "nove": 9, "dez": 10, "doze": 12, "quinze": 15}
ANOS = re.compile(r"(\d{1,2}|" + "|".join(NUMEROS) + r")(?:\s*(?:\+|a|e|ou|-|–|to)\s*(\d{1,2}))?\s*\+?\s*"
                  r"(?:anos?|years?)\b")


def sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def limpar(texto: str) -> str:
    """Tira negrito, aspas soltas e o ` · ` que junta trechos da origem; o sentido do texto não muda."""
    s = texto.replace("**", "")
    s = re.sub(r'"\s*·\s*"', "; ", s)
    s = s.replace(" · ", "; ")
    return s.strip().strip('"').strip()


def peso(texto: str) -> str:
    """`diferencial` se a linha traz um marcador; senão `obrigatorio`. "Preferencialmente" não conta."""
    return "diferencial" if MARCADORES_DIFERENCIAL.search(sem_acento(texto)) else "obrigatorio"


def anos(texto: str) -> int | None:
    """Menor número de anos citado ("5 e 10 anos" -> 5); vazio quando não cita."""
    achados = []
    for m in ANOS.finditer(sem_acento(texto)):
        for g in m.groups():
            if g:
                achados.append(int(g) if g.isdigit() else NUMEROS[g])
    return min(achados) if achados else None


@lru_cache(maxsize=1)
def dicionario() -> list[tuple[str, re.Pattern, re.Pattern | None]]:
    with (RAIZ / "dbt" / "seeds" / "ferramentas.csv").open(encoding="utf-8") as f:
        linhas = sorted(csv.DictReader(f), key=lambda r: int(r["ordem"]))
    return [(r["ferramenta"], re.compile(r["padrao"]), re.compile(r["remover"]) if r["remover"] else None)
            for r in linhas]


def ferramentas(texto: str) -> list[str]:
    t = sem_acento(texto)
    achadas = []
    for nome, padrao, remover in dicionario():
        alvo = remover.sub(" ", t) if remover else t
        if padrao.search(alvo):
            achadas.append(nome)
    return achadas


if __name__ == "__main__":
    for exemplo in ["Dif.: SQL avançado, Power BI e Python", "5 a 8 anos de experiência com liderança",
                    "Experiência com SQL Server e Azure DevOps", "Preferencialmente Big Four",
                    "mínimo de três anos liderando equipes", "**Domínio** em Spark (PySpark)"]:
        print(f"{exemplo!r}: peso={peso(exemplo)} anos={anos(exemplo)} ferramentas={ferramentas(exemplo)}")
