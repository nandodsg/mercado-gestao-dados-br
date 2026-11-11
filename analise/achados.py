"""Gera `analise/achados.md` a partir dos marts do dbt (DuckDB em dbt/target/mercado.duckdb) e de `data/`.

Nenhum número do texto é digitado à mão: cada um sai de uma consulta abaixo, e o arquivo se refaz a cada publicação
(`dbt build` e depois `python analise/achados.py`). Cada achado tem uma condição: se a publicação nova inverter a direção
que o texto afirma, o achado sai marcado como "não se sustenta nesta publicação", em vez de continuar dizendo o contrário
do dado.

`calcular()` devolve também os números brutos (`raw`), e `pipeline/gerar_site.py` usa o mesmo cálculo pra montar a página:
o texto dela e o do `achados.md` saem das mesmas contas, sem número digitado à mão.

Base das contagens: vagas de coordenação e de gerência com o anúncio classificado (`mart_vaga_item`, que já tira o anúncio
repetido). Alta gestão e "outros" entram só nos totais: são poucas vagas pra quebrar.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parents[1]
DB = RAIZ / "dbt" / "target" / "mercado.duckdb"
MODELO = Path(__file__).with_name("achados.modelo.md")
SAIDA = Path(__file__).with_name("achados.md")
NIVEIS = ("coordenador", "gerente")

# Itens de cada achado (chave da taxonomia, prefixo no texto). A página desenha exatamente estes.
NUCLEO = (("pessoas.liderar_time", "liderar"), ("negocio.stakeholders", "stake"), ("pessoas.desenvolver_pessoas", "desenv"))
ESTRATEGIA = ("negocio.estrategia", "estrat")
OPERACAO = ("pessoas.operacao_time", "oper")
CONTRATAR = ("pessoas.contratar_estruturar", "contratar")
LIDERAR_LIDERES = ("pessoas.liderar_lideres", "lidlid")
MAO_NA_MASSA = ("pessoas.hands_on", "hands")
IA_APLICADA = ("ia.ia_aplicada", "iaap")
NAO_SUSTENTA = (("idioma.ingles", "ingles"), ("ia.genai_llm", "genai"), ("eng.plataforma_cloud", "cloud"),
                ("analytics.kpis_metricas", "kpis"), LIDERAR_LIDERES)


# ---------- estatística (sem numpy/scipy: o repo não depende deles) ----------

def _hiper(a: int, b: int, c: int, d: int) -> float:
    return math.comb(a + b, a) * math.comb(c + d, c) / math.comb(a + b + c + d, a + c)


def fisher(xc: int, nc: int, xg: int, ng: int) -> float:
    """Teste exato de Fisher, bicaudal, pra 'x de n' em coordenação × gerência."""
    a, b, c, d = xc, nc - xc, xg, ng - xg
    p0, r1, c1, n = _hiper(a, b, c, d), a + b, a + c, a + b + c + d
    tot = 0.0
    for x in range(max(0, c1 - (n - r1)), min(r1, c1) + 1):
        p = _hiper(x, r1 - x, c1 - x, n - r1 - c1 + x)
        if p <= p0 * (1 + 1e-9):
            tot += p
    return min(1.0, tot)


# ---------- formatação pt-BR ----------

def pct(x: int, n: int) -> str:
    return f"{round(100 * x / n)}%" if n else "—"


def frac(x: int, n: int) -> str:
    return f"{pct(x, n)} ({x} de {n})"


def p_txt(p: float) -> str:
    return "p < 0,001" if p < 0.001 else f"p = {p:.3f}".replace(".", ",")


def reais(v: float) -> str:
    return f"R$ {v / 1000:.1f} mil".replace(".", ",")


# ---------- consultas ----------

def calcular(c: "duckdb.DuckDBPyConnection", dados: Path = RAIZ / "data") -> tuple[dict, dict, dict]:
    """Devolve (v, cond, raw): `v` = textos formatados do modelo, `cond` = condição de cada achado, `raw` = números brutos.
    `dados` é a pasta do manifest (data/ no dado real, tests/fixtures na CI sem publicação)."""
    um = lambda s: c.sql(s).fetchall()[0][0]  # noqa: E731
    v: dict[str, object] = {}
    raw: dict[str, object] = {}

    manifest = json.loads((dados / "manifest.json").read_text(encoding="utf-8"))
    cob = manifest.get("cobertura") or {}
    v["versao_dado"] = manifest.get("gerado_em", "")[:10]
    v["cobertura"] = frac(cob.get("rotuladas", 0), cob.get("linhas", 0))

    v["n_vagas"] = um("select count(*) from mart_vagas")
    n_rep = um("select count(*) from mart_repost")
    raw["n_repost"] = n_rep
    v["repost_txt"] = "nenhum anúncio repetido" if n_rep == 0 else (
        "1 anúncio repetido" if n_rep == 1 else f"{n_rep} anúncios repetidos")
    v["n_rotuladas"] = um("select count(distinct id_publico) from mart_vaga_item")
    v["n_sem_rotulo"] = um("select count(*) from mart_vagas where id_publico not in (select id_publico from stg_rotulos)")
    n = dict(c.sql("""select nivel, count(distinct id_publico) from mart_vaga_item group by 1""").fetchall())
    nc, ng = n.get("coordenador", 0), n.get("gerente", 0)
    v["nc"], v["ng"] = nc, ng
    v["n_outros_niveis"] = sum(k for nivel, k in n.items() if nivel not in NIVEIS)
    raw.update(nc=nc, ng=ng, n_vagas=v["n_vagas"], n_rotuladas=v["n_rotuladas"], n_outros_niveis=v["n_outros_niveis"],
               n_sem_rotulo=v["n_sem_rotulo"])

    por_item = {
        (chave, nivel): k
        for chave, nivel, k in c.sql("select item_chave, nivel, count(distinct id_publico) from mart_vaga_item group by 1, 2").fetchall()
    }

    def item(chave: str, prefixo: str) -> tuple[int, int]:
        xc, xg = por_item.get((chave, "coordenador"), 0), por_item.get((chave, "gerente"), 0)
        v[f"{prefixo}_c"], v[f"{prefixo}_g"] = frac(xc, nc), frac(xg, ng)
        v[f"{prefixo}_p"] = p_txt(fisher(xc, nc, xg, ng))
        return xc, xg

    # 1. núcleo comum
    nucleo = [item(*par) for par in NUCLEO]
    # 2. estratégia × operação
    est = item(*ESTRATEGIA)
    ope = item(*OPERACAO)
    item(*CONTRATAR)
    item(*LIDERAR_LIDERES)
    # 4. mão na massa
    hands = item(*MAO_NA_MASSA)
    # sem força estatística (seção "o que não dá pra afirmar") e IA aplicada ao negócio (achado 5)
    for chave, pref in (*NAO_SUSTENTA, IA_APLICADA):
        item(chave, pref)
    raw["por_item"] = por_item

    # 5. IA: qualquer item da dimensão
    ia = dict(c.sql("""select nivel, count(distinct id_publico) from mart_vaga_item where item_chave like 'ia.%' group by 1""").fetchall())
    ia_tot = um("select count(distinct id_publico) from mart_vaga_item where item_chave like 'ia.%'")
    raw["ia_nivel"] = (ia.get("coordenador", 0), ia.get("gerente", 0))
    raw["ia_tot"] = ia_tot
    v["ia_tot"] = frac(ia_tot, v["n_rotuladas"])
    v["ia_c"], v["ia_g"] = frac(ia.get("coordenador", 0), nc), frac(ia.get("gerente", 0), ng)
    base_rot = "select id_publico from mart_vaga_item"
    ia_resp = um(f"""select count(distinct id_publico) from stg_rotulo_itens
                     where item like 'ia.%' and secao = 'responsabilidades' and id_publico in ({base_rot})""")
    ia_req = um(f"""select count(distinct id_publico) from stg_rotulo_itens
                    where item like 'ia.%' and secao = 'requisitos' and id_publico in ({base_rot})""")
    v["ia_resp"], v["ia_req"] = frac(ia_resp, ia_tot), frac(ia_req, ia_tot)
    n_dif = um(f"select count(distinct id_publico) from stg_rotulos where secao = 'diferenciais' and id_publico in ({base_rot})")
    difs = c.sql(f"""select case when item like 'ia.%' then 'ia' else item end g, count(distinct id_publico) k
                     from stg_rotulo_itens where secao = 'diferenciais' and item <> 'outro' and id_publico in ({base_rot})
                     group by 1 order by k desc""").fetchall()
    dif = dict(difs)
    v["n_dif"] = n_dif
    raw.update(ia_resp=ia_resp, ia_req=ia_req, n_dif=n_dif, difs=difs)
    v["ia_dif"] = frac(dif.get("ia", 0), n_dif)
    v["setor_dif"] = frac(dif.get("experiencia.setor", 0), n_dif)
    ia_primeiro = bool(difs) and difs[0][0] == "ia"

    # 3. ferramenta pelo nome no anúncio inteiro (regra determinística aplicada antes da publicação; mart_vaga_ferramenta,
    #    mesma base 36 × 42 das outras seções)
    por_ferr = {
        (nome, nivel): k
        for nome, nivel, k in c.sql("select ferramenta, nivel, count(distinct id_publico) from mart_vaga_ferramenta group by 1, 2").fetchall()
    }
    # a ferramenta mais citada em cada nível (pra condição do achado 1: nenhuma chega à frequência do núcleo)
    v["ferr_top"], ferr_top_pct = "", 0.0
    for nome in sorted({n_ for n_, _ in por_ferr}):
        frac_max = max(por_ferr.get((nome, "coordenador"), 0) / nc if nc else 0, por_ferr.get((nome, "gerente"), 0) / ng if ng else 0)
        if frac_max > ferr_top_pct:
            v["ferr_top"], ferr_top_pct = nome, frac_max

    raw["ferr_top"] = v["ferr_top"]
    raw["ferr_top_cg"] = (por_ferr.get((v["ferr_top"], "coordenador"), 0), por_ferr.get((v["ferr_top"], "gerente"), 0))

    def ferramenta(nome: str, pref: str) -> tuple[int, int]:
        xc, xg = por_ferr.get((nome, "coordenador"), 0), por_ferr.get((nome, "gerente"), 0)
        v[f"{pref}_c"], v[f"{pref}_g"], v[f"{pref}_p"] = frac(xc, nc), frac(xg, ng), p_txt(fisher(xc, nc, xg, ng))
        return xc, xg

    py = ferramenta("Python", "py")
    ferramenta("SQL", "sql")
    nuvem = dict(c.sql("""select nivel, count(distinct id_publico) from mart_vaga_ferramenta
                          where ferramenta in ('AWS', 'Azure', 'GCP') group by 1""").fetchall())
    nuvem_c, nuvem_g = nuvem.get("coordenador", 0), nuvem.get("gerente", 0)
    raw["ferr"] = {"SQL": (por_ferr.get(("SQL", "coordenador"), 0), por_ferr.get(("SQL", "gerente"), 0)),
                   "Python": py, "nuvem": (nuvem_c, nuvem_g)}
    v["nuvem_c"], v["nuvem_g"] = frac(nuvem_c, nc), frac(nuvem_g, ng)
    v["nuvem_p"] = p_txt(fisher(nuvem_c, nc, nuvem_g, ng))

    # 6. salário: transparência do anúncio × referência pesquisada
    v["n_faixa"] = um("select count(*) from mart_vagas where faixa_posting is not null")
    raw["n_faixa"] = v["n_faixa"]
    sal = {nivel: (k, med, rep) for nivel, k, med, rep in c.sql(f"""
        with b as (select * from mart_vagas where nivel in {NIVEIS} and salario_min is not null
                     and id_publico not in (select id_publico from mart_repost)),
             moda as (select nivel, salario_min, salario_max, count(*) k from b group by nivel, salario_min, salario_max
                      qualify row_number() over (partition by nivel order by count(*) desc) = 1)
        select b.nivel, count(*), median((b.salario_min + b.salario_max) / 2), any_value(m.k)
        from b join moda m using (nivel) group by 1""").fetchall()}
    raw["sal"] = sal
    for nivel, pref in (("coordenador", "c"), ("gerente", "g")):
        k, med, rep = sal.get(nivel, (0, 0, 0))
        v[f"sal_n_{pref}"], v[f"sal_med_{pref}"], v[f"sal_rep_{pref}"] = k, reais(med or 0), frac(rep or 0, k)
    v["bench_fontes"] = um("select count(*) from stg_benchmarks")
    v["bench_dominios"] = um("select count(distinct regexp_extract(fonte_url, 'https?://(?:www\\.)?([^/]+)', 1)) from stg_benchmarks")

    # condições: a direção que cada texto afirma
    gap = lambda xc, xg: 100 * xg / ng - 100 * xc / nc  # noqa: E731
    cond = {
        "c1": all(min(xc / nc, xg / ng) >= 0.75 for xc, xg in nucleo)
              and ferr_top_pct < min(min(xc / nc, xg / ng) for xc, xg in nucleo),
        "c2": gap(*est) > 0 and gap(*ope) < 0,
        "c3": py[0] / nc > py[1] / ng,
        "c4": abs(gap(*hands)) < 10 and 0.3 <= (hands[0] + hands[1]) / (nc + ng) <= 0.7,
        "c5": ia.get("gerente", 0) / ng >= ia.get("coordenador", 0) / nc and ia_primeiro and ia_resp > ia_req,
        "c6": v["n_faixa"] <= 0.1 * v["n_vagas"],
    }
    raw["cond"] = cond
    aviso = "> ⚠ **Não se sustenta nesta publicação**: a direção abaixo mudou com o dado novo; o texto espera revisão.\n\n"
    for k, ok in cond.items():
        v[f"aviso_{k}"] = "" if ok else aviso

    return v, cond, raw


def main() -> None:
    c = duckdb.connect(str(DB), read_only=True)
    v, cond, _ = calcular(c)
    SAIDA.write_text(MODELO.read_text(encoding="utf-8").format(**v), encoding="utf-8", newline="\n")
    falhas =[k for k, ok in cond.items() if not ok]
    print(f"achados.md gerado ({len(cond) - len(falhas)}/{len(cond)} achados se sustentam{'; revisar: ' + ', '.join(falhas) if falhas else ''})")


if __name__ == "__main__":
    main()
