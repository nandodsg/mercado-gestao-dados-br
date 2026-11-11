"""Confere data/ contra o contrato v1, sem rede e sem credencial.

Uso:
  python pipeline/check_data.py [pasta]      # padrão: data

Quatro checagens, nesta ordem, e qualquer falha sai com código 1:
  1. manifest.json existe e o sha256 e o número de linhas de cada CSV batem com o que ele declara;
  2. cada CSV tem exatamente as colunas do contrato v1, na ordem;
  3. `cobertura` do manifest (linhas do anúncio × linhas rotuladas) é um par de inteiros coerente (rotuladas ≤ linhas);
     a fração rotulada é aviso no dbt, não falha aqui: rodada parcial é estado normal;
  4. sigilo (2ª camada, depois da aplicada na publicação): nenhum texto carrega código de achievement/território/inventário
     nem o nome do autor. Repete de propósito a regra da publicação: o repo público não confia em quem escreve nele.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path

COLUNAS = {
    "vagas.csv": ["id_publico", "empresa", "cargo_oficial", "modo", "geografia", "regime", "cidade", "uf", "contrato",
                  "fonte", "candidatura_tipo", "mes", "url", "faixa_posting", "salario_min", "salario_max",
                  "salario_moeda", "salario_tipo"],
    "requisitos.csv": ["id_publico", "ordem", "texto"],
    "benchmarks.csv": ["id_publico", "ordem", "fonte_url", "fonte_nota"],
    "rotulos.csv": ["id_publico", "ordem", "hash_linha", "secao", "natureza", "itens", "ferramentas", "setor", "versao_taxonomia",
                    "rotulador"],
}
TEXTOS = {
    "vagas.csv": ["empresa", "cargo_oficial", "cidade", "contrato", "fonte", "url", "salario_tipo"],
    "requisitos.csv": ["texto"],
    "benchmarks.csv": ["fonte_url", "fonte_nota"],
    "rotulos.csv": [],  # sem prosa: chaves da taxonomia, nomes de ferramenta, hash e listas fechadas
}
REGRAS = [
    ("código de achievement/território/inventário", re.compile(r"\b(?:A\d{2}|E\d{2}|C\d{2}|T\d{1,2})\b")),
    ("nome do autor", re.compile(r"\bNando\b|Fernando\s+Guimar", re.I)),
]


def main() -> int:
    pasta = Path(sys.argv[1] if len(sys.argv) > 1 else "data")
    erros: list[str] = []
    manifest_path = pasta / "manifest.json"
    if not manifest_path.exists():
        print(f"FALHA: {manifest_path} não existe")
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("contrato") != "v1":
        erros.append(f"contrato {manifest.get('contrato')!r}, esperado 'v1'")

    cob = manifest.get("cobertura")
    if not (isinstance(cob, dict) and isinstance(cob.get("linhas"), int) and isinstance(cob.get("rotuladas"), int)
            and 0 <= cob["rotuladas"] <= cob["linhas"]):
        erros.append(f"cobertura {cob!r}: esperado {{linhas, rotuladas}} inteiros com 0 ≤ rotuladas ≤ linhas")

    for nome, colunas in COLUNAS.items():
        caminho = pasta / nome
        if not caminho.exists():
            erros.append(f"{nome}: arquivo ausente")
            continue
        bruto = caminho.read_bytes()
        declarado = manifest.get("arquivos", {}).get(nome, {})
        if hashlib.sha256(bruto).hexdigest() != declarado.get("sha256"):
            erros.append(f"{nome}: sha256 não bate com o manifest")
        with open(caminho, encoding="utf-8", newline="") as f:
            leitor = csv.DictReader(f)
            if leitor.fieldnames != colunas:
                erros.append(f"{nome}: colunas {leitor.fieldnames} ≠ contrato {colunas}")
                continue
            linhas = list(leitor)
        if len(linhas) != declarado.get("linhas"):
            erros.append(f"{nome}: {len(linhas)} linhas, manifest declara {declarado.get('linhas')}")
        for i, linha in enumerate(linhas, start=2):
            for campo in TEXTOS[nome]:
                for regra, re_ in REGRAS:
                    if linha[campo] and (m := re_.search(linha[campo])):
                        erros.append(f"{nome}:{i} {campo}: {regra} ({m.group(0)!r})")

    for e in erros:
        print("FALHA:", e)
    if not erros:
        print(f"ok: {pasta} confere com o manifest ({manifest['contagens']}), contrato v1, cobertura {cob['rotuladas']}/{cob['linhas']}, sem ocorrência de sigilo")
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
