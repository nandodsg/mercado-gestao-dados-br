"""Monta a pasta do site: `index.html` (do modelo `site/index.modelo.html`), `dados/pagina.json` e os marts em Parquet.

Uso (depois do `dbt build`):
  python pipeline/gerar_site.py <saida> [--dados data]

  <saida>/index.html          modelo com todos os {{marcadores}} preenchidos (texto dos achados, números, avisos)
  <saida>/estilo.css, app.js  copiados de site/
  <saida>/dados/pagina.json   os números de cada gráfico, calculados na publicação (a página não espera o DuckDB pra mostrar número)
  <saida>/dados/mart_*.parquet  os marts que a consulta de cada gráfico lê, em DuckDB no navegador

Nada do que vai pra página é digitado à mão: os números e a condição de cada achado vêm de `analise/achados.py` (`calcular`),
o mesmo cálculo que gera `analise/achados.md`. Achado cuja condição falhou na publicação ganha o aviso e espera revisão,
em vez de dizer o contrário do dado.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "analise"))
import achados as A  # noqa: E402

DB = RAIZ / "dbt" / "target" / "mercado.duckdb"
SITE = RAIZ / "site"
MARTS = ("mart_vaga_item", "mart_vaga_ferramenta", "mart_vagas", "mart_repost")
NIVEIS = A.NIVEIS

# Rótulo curto de cada item nos gráficos (a taxonomia tem o nome completo; aqui entra a fala de quem lê a página).
ROTULO = {
    "pessoas.liderar_time": "Liderar o time",
    "negocio.stakeholders": "Relacionamento com áreas de negócio",
    "pessoas.desenvolver_pessoas": "Desenvolver pessoas",
    "negocio.estrategia": "Estratégia e visão",
    "pessoas.operacao_time": "Operação do time",
    "pessoas.contratar_estruturar": "Contratar e estruturar o time",
    "idioma.ingles": "Inglês",
    "ia.genai_llm": "IA generativa e LLMs",
    "analytics.kpis_metricas": "KPIs e métricas",
    "pessoas.liderar_lideres": "Liderar líderes",
    "eng.plataforma_cloud": "Plataforma de dados e nuvem",
    "ia.ia_aplicada": "IA aplicada ao negócio",
    "experiencia.setor": "Experiência no setor da empresa",
}
DEZ = ["zero", "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito", "nove", "dez"]


def fmt(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def reais(v: float) -> str:
    return A.reais(v)


def minuscula(s: str) -> str:
    return s[0].lower() + s[1:] if len(s) > 1 and s[1].islower() else s


def aviso_html(texto: str) -> str:
    return f'<div class="banner"><span class="dot"></span><span>{texto}</span></div>'


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("saida")
    ap.add_argument("--dados", default="data")
    a = ap.parse_args()
    saida, dados = Path(a.saida), Path(a.dados)
    if not DB.exists():
        print(f"FALHA: {DB} não existe; rode o dbt build antes")
        return 1
    c = duckdb.connect(str(DB), read_only=True)
    v, cond, raw = A.calcular(c, dados)
    manifest = json.loads((dados / "manifest.json").read_text(encoding="utf-8"))
    cob = manifest.get("cobertura") or {"linhas": 0, "rotuladas": 0}
    nc, ng = raw["nc"], raw["ng"]
    por_item = raw["por_item"]

    # ---------- os itens da taxonomia, lado a lado ----------
    itens = [
        {"dim": dim, "chave": chave, "item": item, "c": por_item.get((chave, "coordenador"), 0), "g": por_item.get((chave, "gerente"), 0)}
        for dim, chave, item in c.sql("select dimensao, chave, item from taxonomia where chave <> 'outro' order by ordem").fetchall()
    ]
    por_chave = {i["chave"]: i for i in itens}

    def linha(chave: str, apagado: bool | None = None) -> dict:
        i = por_chave[chave]
        r = {"chave": chave, "label": ROTULO.get(chave, i["item"]), "c": i["c"], "g": i["g"]}
        if apagado is not None:
            r["apagado"] = apagado
        return r

    py, sql, nuvem = raw["ferr"]["Python"], raw["ferr"]["SQL"], raw["ferr"]["nuvem"]
    apaga = lambda cg: A.fisher(cg[0], nc, cg[1], ng) >= 0.05  # noqa: E731  (régua: acima de 0,05 não é achado)
    top = raw["ferr_top"]
    graficos = {
        "a1": [linha(ch) for ch, _ in A.NUCLEO]
              + [{"label": f"{top} (a ferramenta mais citada)", "c": raw["ferr_top_cg"][0], "g": raw["ferr_top_cg"][1], "ref": True}],
        "a2": [linha(A.ESTRATEGIA[0]), linha(A.OPERACAO[0]), linha(A.CONTRATAR[0])],
        "a3": [{"label": "Python", "c": py[0], "g": py[1], "apagado": apaga(py)},
               {"label": "SQL", "c": sql[0], "g": sql[1], "apagado": apaga(sql)},
               {"label": "AWS, Azure ou GCP", "c": nuvem[0], "g": nuvem[1], "apagado": apaga(nuvem)}],
        "a4": A.MAO_NA_MASSA[0],
        "a5b": [{"label": "Algum item de IA", "c": raw["ia_nivel"][0], "g": raw["ia_nivel"][1]}, linha(A.IA_APLICADA[0])],
        "ns": [linha(ch, True) for ch, _ in A.NAO_SUSTENTA],
    }

    # ---------- diferenciais: IA somada numa linha só ----------
    difs = []
    for chave, k in raw["difs"][:6]:
        difs.append(["IA (qualquer item)" if chave == "ia" else ROTULO.get(chave) or por_chave[chave]["item"], k])

    # ---------- referência salarial por vaga (camada 2: nunca o que a vaga paga) ----------
    sal, moda = {}, {}
    for nivel in NIVEIS:
        rows = c.sql("""select empresa, cargo_oficial, coalesce(cidade, ''), salario_min, salario_max from mart_vagas
                        where nivel = ? and salario_min is not null and id_publico not in (select id_publico from mart_repost)
                        order by (salario_min + salario_max) / 2, empresa""", params=[nivel]).fetchall()
        sal[nivel] = [{"e": e, "cargo": cg, "cid": cd, "min": mn, "max": mx} for e, cg, cd, mn, mx in rows]
        cont: dict[tuple, int] = {}
        for _, _, _, mn, mx in rows:
            cont[(mn, mx)] = cont.get((mn, mx), 0) + 1
        (mmin, mmax), k = max(cont.items(), key=lambda kv: kv[1]) if cont else ((0, 0), 0)
        moda[nivel] = [mmin, mmax, k]
        esperado = raw["sal"].get(nivel, (0, 0, 0))
        assert (len(rows), k) == (esperado[0], esperado[2]), f"salário {nivel}: página {len(rows)}/{k} × achados {esperado[0]}/{esperado[2]}"
    sal_txt = {n: reais(raw["sal"][n][1]) for n in NIVEIS if n in raw["sal"]}

    # ---------- a base: quem entra, quem fica só no total, quem sai ----------
    base = [
        {"k": "coordenador", "n": nc, "nome": "coordenação", "onde": "na comparação"},
        {"k": "gerente", "n": ng, "nome": "gerência", "onde": "na comparação"},
        {"k": "outros", "n": raw["n_outros_niveis"], "nome": "alta gestão ou fora da gestão de dados", "onde": "só nos totais"},
        {"k": "sem", "n": raw["n_sem_rotulo"], "nome": "anúncio sem classificação", "onde": "fora"},
        {"k": "rep", "n": raw["n_repost"], "nome": "anúncio repetido", "onde": "fora"},
    ]
    soma = sum(b["n"] for b in base)
    assert soma == raw["n_vagas"], f"a base não fecha: {soma} pontos × {raw['n_vagas']} vagas (alguma vaga tem anúncio classificado mas nenhum item?)"

    n_vagas, n_linhas = raw["n_vagas"], int(cob.get("linhas", 0))
    ia_tot, ia_base = raw["ia_tot"], raw["n_rotuladas"]
    ia_c, ia_g = raw["ia_nivel"]
    pagina = {
        "manifest": {"gerado_em": manifest.get("gerado_em", ""), "contagens": manifest.get("contagens", {}), "cobertura": cob},
        "nc": nc, "ng": ng, "cond": cond, "base": base, "items": itens, "graficos": graficos,
        "ferr": raw["ferr"], "faixa_posting": raw["n_faixa"],
        "ia": {"nivel": [ia_c, ia_g], "tot": ia_tot, "base": ia_base, "resp": raw["ia_resp"], "req": raw["ia_req"], "ndif": raw["n_dif"]},
        "difs": difs, "sal": sal, "moda": moda, "sal_txt": sal_txt,
    }

    # ---------- texto: marcadores do modelo ----------
    gerado = datetime.fromisoformat(manifest["gerado_em"].replace("Z", "+00:00"))
    local = gerado.astimezone(timezone(timedelta(hours=-3)))  # Brasil sem horário de verão
    parcial = int(cob.get("rotuladas", 0)) < n_linhas
    pct_cob = round(100 * cob["rotuladas"] / n_linhas) if n_linhas else 0
    cob_txt = f"{fmt(int(cob['rotuladas']))} de {fmt(n_linhas)} linhas ({pct_cob}%)"
    mais_ia = "Gerência" if ia_g / ng >= ia_c / nc else "Coordenação"
    pia, piaap = A.fisher(ia_c, nc, ia_g, ng), A.fisher(por_chave["ia.ia_aplicada"]["c"], nc, por_chave["ia.ia_aplicada"]["g"], ng)
    iaap_c, iaap_g = por_chave["ia.ia_aplicada"]["c"] / nc, por_chave["ia.ia_aplicada"]["g"] / ng
    mesma_direcao = (iaap_g >= iaap_c) == (ia_g / ng >= ia_c / nc)
    ia_h3 = f"{mais_ia} cita mais IA; IA aplicada ao negócio " + (
        "vai na mesma direção" + (", com menos força." if piaap > pia else ".") if mesma_direcao else "não segue a mesma direção.")
    dif_h3 = f"{difs[0][0] if difs[0][0] != 'IA (qualquer item)' else 'IA'} é o diferencial mais citado."
    if len(difs) > 1:
        dif_h3 += f" O segundo é {minuscula(difs[1][0])}."
    n_dims = len({i["dim"] for i in itens})
    marc = {
        "atualizado_em": local.strftime("%d.%m.%Y"),
        "n_vagas": n_vagas, "n_vagas_raw": n_vagas, "n_linhas": fmt(n_linhas), "n_linhas_raw": n_linhas,
        "n_faixa": raw["n_faixa"], "n_faixa_raw": raw["n_faixa"], "n_itens": len(itens), "n_dims": n_dims,
        "n_comparacao": nc + ng, "nc": nc, "ng": ng, "ferr_top": top,
        "aviso_cobertura": aviso_html(f"<b>Classificação em andamento: {cob_txt}.</b> Os números abaixo podem mudar quando ela terminar.").replace(
            'class="banner"', 'class="banner n"') if parcial else "",
        "cob_nota": f" Classificação em andamento: {pct_cob}% das linhas." if parcial else "",
        "ia_dez": DEZ[round(10 * ia_tot / ia_base)], "ia_pct": round(100 * ia_tot / ia_base), "ia_tot_n": ia_tot, "ia_base": ia_base,
        "ia_h3": ia_h3, "dif_h3": dif_h3, "n_dif": raw["n_dif"],
        "sal_med_c": v["sal_med_c"], "sal_med_g": v["sal_med_g"],
        "bench_fontes": v["bench_fontes"], "bench_dominios": v["bench_dominios"],
    }
    for k, ok in cond.items():
        marc[f"virou_{k}"] = "" if ok else " virou"
        marc[f"aviso_{k}"] = "" if ok else aviso_html(
            "<b>Não se sustenta nesta publicação.</b> A direção que o título afirma mudou com o dado novo; o texto espera revisão. "
            "O gráfico abaixo mostra o dado de hoje.")

    modelo = (SITE / "index.modelo.html").read_text(encoding="utf-8")

    def sub(m: re.Match) -> str:
        return str(marc[m.group(1)])

    html = re.sub(r"\{\{(\w+)\}\}", sub, modelo)
    assert "{{" not in html

    # ---------- escrever ----------
    if saida.exists():
        shutil.rmtree(saida)
    (saida / "dados").mkdir(parents=True)
    (saida / "index.html").write_text(html, encoding="utf-8", newline="\n")
    for f in SITE.iterdir():
        if f.is_file() and f.name not in ("index.modelo.html", "index.html"):
            shutil.copy2(f, saida / f.name)
    (saida / "dados" / "pagina.json").write_text(json.dumps(pagina, ensure_ascii=False, separators=(",", ":"), default=str), encoding="utf-8", newline="\n")
    for t in MARTS:
        c.sql(f"copy (select * from {t}) to '{(saida / 'dados' / (t + '.parquet')).as_posix()}' (format parquet)")
    falhas = [k for k, ok in cond.items() if not ok]
    print(f"site gerado em {saida} ({len(cond) - len(falhas)}/{len(cond)} achados se sustentam"
          f"{'; revisar: ' + ', '.join(falhas) if falhas else ''}; cobertura {cob_txt})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
