"""Gera tests/fixtures/ — dados FICTÍCIOS no formato do contrato v1, pra CI rodar o dbt antes da 1ª publicação real.

Nada aqui vem do dado real: empresas e cargos são inventados (Empresa Exemplo A…), de modo que ninguém confunda fixture
com dado. Só `python pipeline/make_fixture.py` regenera; o resultado é versionado.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

SAIDA = Path(__file__).resolve().parent.parent / "tests" / "fixtures"
CABECALHO_VAGAS = ["id_publico", "empresa", "cargo_oficial", "modo", "geografia", "regime", "cidade", "uf", "contrato",
                   "fonte", "candidatura_tipo", "mes", "url", "faixa_posting", "salario_min", "salario_max",
                   "salario_moeda", "salario_tipo"]

VAGAS = [
    # id, empresa, cargo, regime, cidade, uf, contrato, mes
    ("aaaaaaaaaaa1", "Empresa Exemplo A", "Coordenador de Dados", "hibrido", "Porto Alegre", "RS", "CLT", "2026-09"),
    ("aaaaaaaaaaa2", "Empresa Exemplo B", "Gerente de Analytics", "presencial", "São Paulo", "SP", "CLT", "2026-10"),
    ("aaaaaaaaaaa3", "Empresa Exemplo C", "Senior Manager, Data Platform", "remoto", "", "", "PJ", "2026-10"),
    ("aaaaaaaaaaa4", "Empresa Exemplo D", "Head de Dados", "hibrido", "São Paulo", "SP", "CLT", "2026-10"),
    ("aaaaaaaaaaa5", "Empresa Exemplo E", "Supervisor de BI", "presencial", "Porto Alegre", "RS", "CLT", "2026-11"),
    ("aaaaaaaaaaa6", "Empresa Exemplo F", "Gerente de Dados e IA", "hibrido", "Curitiba", "PR", "CLT", "2026-11"),
]
REQUISITOS = [
    ("aaaaaaaaaaa1", 1, "Experiência com SQL e Power BI"),
    ("aaaaaaaaaaa1", 2, "Liderança de times de analistas"),
    ("aaaaaaaaaaa2", 1, "Graduação em exatas"),
    ("aaaaaaaaaaa2", 2, "Inglês avançado"),
    ("aaaaaaaaaaa3", 1, "Conhecimento de arquitetura de dados em nuvem"),
    ("aaaaaaaaaaa4", 1, "Visão estratégica de dados e IA"),
    ("aaaaaaaaaaa5", 1, "Domínio de Power BI e modelagem dimensional"),
    ("aaaaaaaaaaa6", 1, "Experiência com governança de dados"),
    ("aaaaaaaaaaa6", 2, "Gestão de orçamento e fornecedores"),
]
BENCHMARKS = [
    ("aaaaaaaaaaa1", 1, "https://exemplo.invalid/salarios/coordenador-dados", "Faixa fictícia de exemplo"),
    ("aaaaaaaaaaa2", 1, "https://exemplo.invalid/salarios/gerente-analytics", "Faixa fictícia de exemplo"),
]
# vaga, ordem, hash, secao, natureza, itens, ferramentas, setor. Itens e ferramentas: chaves reais da taxonomia e do dicionário (conferidas pelo teste dbt).
# A vaga ...6 fica com 1 linha sem rótulo de propósito: a cobertura da fixture é parcial, como numa rodada incremental.
ROTULOS = [
    ("aaaaaaaaaaa1", 1, "f00000000001", "requisitos", "requisito", "pessoas.liderar_time", "", "nenhum"),
    ("aaaaaaaaaaa1", 2, "f00000000002", "requisitos", "requisito", "pessoas.desenvolver_pessoas|pessoas.contratar_estruturar", "SQL|Power BI", "nenhum"),
    ("aaaaaaaaaaa2", 1, "f00000000003", "responsabilidades", "contexto", "", "", "nenhum"),
    ("aaaaaaaaaaa2", 2, "f00000000004", "diferenciais", "requisito", "experiencia.setor", "Python", "financeiro"),
    ("aaaaaaaaaaa3", 1, "f00000000005", "responsabilidades", "responsabilidade", "pessoas.liderar_time", "", "nenhum"),
]
COBERTURA = {"linhas": 6, "rotuladas": len(ROTULOS)}
VERSAO_TAXONOMIA = "fixture00000"
ROTULADOR = "fixture"


def escrever(nome: str, cabecalho: list[str], linhas: list[list]) -> str:
    caminho = SAIDA / nome
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cabecalho)
        w.writerows(linhas)
    return caminho.read_bytes().decode("utf-8")


def main() -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    vagas = [
        [i, e, c, "lideranca", "br", reg, cid, uf, ctr, "linkedin", "externa", mes,
         f"https://exemplo.invalid/vaga/{i}", "", "", "", "", ""]
        for i, e, c, reg, cid, uf, ctr, mes in VAGAS
    ]
    rotulos = [[v, o, h, sec, nat, it, fe, st, VERSAO_TAXONOMIA, ROTULADOR] for v, o, h, sec, nat, it, fe, st in ROTULOS]
    arquivos = {
        "vagas.csv": escrever("vagas.csv", CABECALHO_VAGAS, vagas),
        "requisitos.csv": escrever("requisitos.csv", ["id_publico", "ordem", "texto"], [list(r) for r in REQUISITOS]),
        "benchmarks.csv": escrever("benchmarks.csv", ["id_publico", "ordem", "fonte_url", "fonte_nota"], [list(b) for b in BENCHMARKS]),
        "rotulos.csv": escrever("rotulos.csv", ["id_publico", "ordem", "hash_linha", "secao", "natureza", "itens", "ferramentas",
                                                "setor", "versao_taxonomia", "rotulador"], rotulos),
    }
    info = {n: {"sha256": hashlib.sha256(t.encode("utf-8")).hexdigest(), "linhas": len(t.splitlines()) - 1} for n, t in arquivos.items()}
    manifest = {
        "contrato": "v1",
        "gerado_em": "2026-01-01T00:00:00.000Z",
        "contagens": {"vagas": info["vagas.csv"]["linhas"], "requisitos": info["requisitos.csv"]["linhas"],
                      "benchmarks": info["benchmarks.csv"]["linhas"]},
        "arquivos": info,
        "cobertura": COBERTURA,
        "notas": ["FIXTURE: dados fictícios pra testar o pipeline, não são vagas reais."],
    }
    (SAIDA / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("fixture gerada em", SAIDA)


if __name__ == "__main__":
    main()
