"""Mede cada candidato contra o gabarito da referência e escreve evals/relatorio.md e evals/metricas.json. Grátis: só lê.

    python rotulagem/avaliar.py

Gabarito = rotulagem/referencia/referencia_revisado.csv (rótulos de modelos revisados por pessoa, D25). Métricas do
método do Item 5 (§7): kappa de `natureza`; kappa da presença por dimensão; F1 por item só com 10+ positivas na
referência; F1 micro (todos os pares linha × item); conjunto exato de itens por linha; setor onde o gabarito tem setor;
custo por 1.000 linhas; latência; vagas que o candidato não conseguiu devolver válidas. Pro Jev, o limiar de sim/não é
escolhido na **prática** (nunca na referência) e há a leitura da abstenção: o erro cai quando a probabilidade é firme?
Os três rotuladores da referência entram só como régua (a referência partiu deles: leem melhor do que leriam num conjunto novo).
"""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from pathlib import Path

import taxonomia
from common import AMOSTRA, CANDIDATOS_GATEWAY, JEV_MODELOS, OPUS, RAIZ, REFERENCIA, ROTULADORES_GATEWAY, SAIDA, ler_json, slug
from concordancia import carregar_revisado, f1, fmt, kappa

MINIMO_POSITIVAS = 10
GRADE_LIMIAR = [round(x * 0.05, 2) for x in range(1, 20)]
CANDIDATOS = [*(f"typesafe/{m}" for m in JEV_MODELOS), *CANDIDATOS_GATEWAY]
REGUA = [OPUS, *ROTULADORES_GATEWAY]
EVALS = RAIZ / "evals"


def arquivo(modelo: str, conjunto: str) -> Path:
    return SAIDA / f"{slug(modelo)}_{conjunto}.json"


def setor_revisado(conjunto: str) -> dict[tuple[str, int], str]:
    import csv
    with (REFERENCIA / f"{conjunto}_revisado.csv").open(encoding="utf-8") as f:
        return {(r["id_publico"], int(r["ordem"])): r["valor"] for r in csv.DictReader(f)
                if r["tipo"] == "setor" and r["incluido"] == "1"}


def carregar(modelo: str, conjunto: str, limiar: float | None = None) -> dict | None:
    """Rótulos por (vaga, linha) + resumo de custo, latência e vagas devolvidas. `limiar` reaplica o sim/não do Jev."""
    f = arquivo(modelo, conjunto)
    if not f.exists():
        return None
    bruto = ler_json(f)
    linhas, usd, lat, reparos = {}, 0.0, [], 0
    for vid, r in bruto.items():
        usd += r.get("usd", 0.0)
        reparos += r.get("reparos", 0) or 0
        n = len(r["linhas"])
        if r.get("latencia_s") is not None:  # uma chamada por vaga
            lat += [r["latencia_s"] / n] * n
        for l in r["linhas"]:
            itens = set(l["itens"]) - {taxonomia.OUTRO}  # `outro` fica fora das métricas de item
            natureza = l["natureza"]
            if limiar is not None and "probs" in l:
                itens = set() if natureza == "contexto" else {k for k, p in l["probs"].items() if p >= limiar}
            if "latencia_s" in l:  # uma requisição por linha
                lat.append(l["latencia_s"])
            linhas[(vid, l["ordem"])] = {"natureza": natureza, "itens": itens, "setor": l["setor"] if "experiencia.setor" in itens else "nenhum",
                                         "probs": l.get("probs"), "natureza_prob": l.get("natureza_prob")}
    return {"linhas": linhas, "usd": usd, "latencias": lat, "vagas": len(bruto), "reparos": reparos}


def metricas(r: dict, gab: dict, setores_gab: dict, dim_de: dict[str, str], chaves_linhas: list) -> dict:
    ks = [k for k in chaves_linhas if k in r["linhas"]]
    itens = [i for i in taxonomia.chaves() if i != taxonomia.OUTRO]
    nat_g, nat_r = [gab[k]["natureza"] for k in ks], [r["linhas"][k]["natureza"] for k in ks]
    por_dim = {}
    for dim in dict.fromkeys(dim_de.values()):
        pg = [any(dim_de[i] == dim for i in gab[k]["itens"]) for k in ks]
        pr = [any(dim_de[i] == dim for i in r["linhas"][k]["itens"]) for k in ks]
        por_dim[dim] = {"kappa": kappa(pg, pr), "positivas_gabarito": sum(pg), "positivas_candidato": sum(pr)}
    por_item = {}
    tp = fp = fn = 0
    for i in itens:
        pg = [i in gab[k]["itens"] for k in ks]
        pr = [i in r["linhas"][k]["itens"] for k in ks]
        tp += sum(a and b for a, b in zip(pg, pr))
        fp += sum((not a) and b for a, b in zip(pg, pr))
        fn += sum(a and (not b) for a, b in zip(pg, pr))
        por_item[i] = {"positivas_gabarito": sum(pg), "positivas_candidato": sum(pr),
                       "f1": f1(pg, pr) if sum(pg) >= MINIMO_POSITIVAS else None}
    avaliaveis = [v["f1"] for v in por_item.values() if v["f1"] is not None]
    exato = sum(gab[k]["itens"] == r["linhas"][k]["itens"] for k in ks)
    sg = [k for k in ks if k in setores_gab]
    setor_ok = sum(r["linhas"][k]["setor"] == setores_gab[k] for k in sg)
    n_linhas = len(r["linhas"])
    return {
        "linhas": len(ks), "vagas_devolvidas": r["vagas"],
        "natureza_concordancia": sum(a == b for a, b in zip(nat_g, nat_r)) / len(ks), "natureza_kappa": kappa(nat_g, nat_r),
        "dimensoes": por_dim, "kappa_dimensao_medio": statistics.mean(v["kappa"] for v in por_dim.values() if v["kappa"] is not None),
        "itens": por_item, "itens_avaliaveis": len(avaliaveis), "f1_item_medio": statistics.mean(avaliaveis) if avaliaveis else None,
        "f1_micro": 2 * tp / (2 * tp + fp + fn) if tp + fp + fn else None, "precisao_micro": tp / (tp + fp) if tp + fp else None,
        "revocacao_micro": tp / (tp + fn) if tp + fn else None,
        "conjunto_exato": exato / len(ks), "setor_acertos": setor_ok, "setor_linhas": len(sg),
        "usd": r["usd"], "usd_por_mil_linhas": r["usd"] / n_linhas * 1000 if n_linhas else None,
        "latencia_mediana_s": statistics.median(r["latencias"]) if r["latencias"] else None,
        "latencia_s_por_mil_linhas_em_serie": sum(r["latencias"]) / len(r["latencias"]) * 1000 if r["latencias"] else None,
        "reparos": r["reparos"],
    }


def f1_micro_conjunto(r: dict, gab: dict, itens: list[str]) -> float:
    tp = fp = fn = 0
    for k, l in r["linhas"].items():
        if k not in gab:
            continue
        for i in itens:
            g, p = i in gab[k]["itens"], i in l["itens"]
            tp, fp, fn = tp + (g and p), fp + ((not g) and p), fn + (g and (not p))
    return 2 * tp / (2 * tp + fp + fn) if tp + fp + fn else 0.0


def escolher_limiar(modelo: str, itens: list[str]) -> tuple[float, list[tuple[float, float]]]:
    """Limiar que maximiza o F1 micro na prática (gabarito da prática, 88 linhas), nunca na referência."""
    gab = {k: {**v, "itens": v["itens"] - {taxonomia.OUTRO}} for k, v in carregar_revisado("pratica").items()}
    pontos = []
    for lim in GRADE_LIMIAR:
        r = carregar(modelo, "pratica", lim)
        pontos.append((lim, f1_micro_conjunto(r, gab, itens)))
    melhor = max(pontos, key=lambda p: (p[1], -abs(p[0] - 0.5)))
    return melhor[0], pontos


def abstencao(r: dict, gab: dict, itens: list[str], limiar: float) -> list[dict]:
    """Taxa de erro das decisões sim/não por faixa de firmeza da probabilidade (a decisão é p >= limiar)."""
    faixas = [("firme (p ≤ 0,10 ou ≥ 0,90)", lambda p: p <= 0.10 or p >= 0.90),
              ("média (0,10–0,25 ou 0,75–0,90)", lambda p: 0.10 < p <= 0.25 or 0.75 <= p < 0.90),
              ("incerta (0,25–0,75)", lambda p: 0.25 < p < 0.75)]
    saida = []
    for nome, pred in faixas:
        n = erros = 0
        for k, l in r["linhas"].items():
            if k not in gab or l["probs"] is None or l["natureza"] == "contexto":
                continue
            for i in itens:
                p = l["probs"][i]
                if pred(p):
                    n += 1
                    erros += (p >= limiar) != (i in gab[k]["itens"])
        saida.append({"faixa": nome, "decisoes": n, "erros": erros, "taxa_erro": erros / n if n else None})
    return saida


def tabela_item(m_por_modelo: dict[str, dict], itens_aval: list[str], nomes: dict[str, str]) -> list[str]:
    cab = "| item | positivas | " + " | ".join(nomes[m] for m in m_por_modelo) + " |"
    linhas = [cab, "|---|---|" + "---|" * len(m_por_modelo)]
    for i in itens_aval:
        pos = next(iter(m_por_modelo.values()))["itens"][i]["positivas_gabarito"]
        linhas.append(f"| `{i}` | {pos} | " + " | ".join(fmt(m["itens"][i]["f1"]) for m in m_por_modelo.values()) + " |")
    return linhas


def main() -> None:
    gab = {k: {**v, "itens": v["itens"] - {taxonomia.OUTRO}} for k, v in carregar_revisado("referencia").items()}
    setores_gab = setor_revisado("referencia")
    dim_de = {i["chave"]: i["dimensao"] for i in taxonomia.itens() if i["chave"] != taxonomia.OUTRO}
    chaves_linhas = [(v["id_publico"], l["ordem"]) for v in ler_json(AMOSTRA / "referencia.json")["vagas"] for l in v["linhas"]]
    itens = list(dim_de)
    outro_pos = sum(taxonomia.OUTRO in v["itens"] for v in carregar_revisado("referencia").values())

    resultados: dict[str, dict] = {}
    notas_limiar: dict[str, dict] = {}
    for modelo in [*CANDIDATOS, *REGUA]:
        if modelo.startswith("typesafe/") and arquivo(modelo, "referencia").exists() and arquivo(modelo, "pratica").exists():
            limiar, pontos = escolher_limiar(modelo, itens)
            r = carregar(modelo, "referencia", limiar)
            m = metricas(r, gab, setores_gab, dim_de, chaves_linhas)
            m["limiar"] = limiar
            m5 = metricas(carregar(modelo, "referencia", 0.5), gab, setores_gab, dim_de, chaves_linhas)
            notas_limiar[modelo] = {"escolhido_na_pratica": limiar, "curva_pratica": pontos,
                                    "f1_micro_com_limiar_0_5": m5["f1_micro"], "abstencao": abstencao(r, gab, itens, limiar)}
            resultados[modelo] = m
        else:
            r = carregar(modelo, "referencia")
            if r is not None:
                resultados[modelo] = metricas(r, gab, setores_gab, dim_de, chaves_linhas)
    candidatos = {m: resultados[m] for m in CANDIDATOS if m in resultados}
    nomes = {m: m.split("/")[-1] for m in resultados}

    EVALS.mkdir(exist_ok=True)
    (EVALS / "metricas.json").write_text(json.dumps({"taxonomia": taxonomia.versao(), "gabarito": "referencia_revisado.csv",
                                                      "resultados": resultados, "jev": notas_limiar}, indent=2, ensure_ascii=False) + "\n",
                                         encoding="utf-8")

    L = ["# Harness de modelos — candidatos × referência", "",
         f"Taxonomia `{taxonomia.versao()}`, esforço `medium` nos modelos de texto, uma chamada por vaga (Jev: uma requisição por linha). "
         f"Gabarito: {len(chaves_linhas)} linhas de 16 vagas, rótulos de modelos revisados por pessoa (D25). "
         f"Itens com {MINIMO_POSITIVAS}+ positivas no gabarito ({next(iter(resultados.values()))['itens_avaliaveis']}) têm F1 próprio; "
         f"o item `outro` ({outro_pos} positivas) fica fora das métricas de item (o Jev não o pergunta).", ""]
    cab = ["métrica", *(nomes[m] for m in resultados)]
    linhas = [
        ("vagas devolvidas válidas (de 16)", lambda m: str(m["vagas_devolvidas"])),
        ("`natureza`: kappa", lambda m: fmt(m["natureza_kappa"])),
        ("kappa da presença por dimensão (média das 8)", lambda m: fmt(m["kappa_dimensao_medio"])),
        ("F1 por item (média dos itens avaliáveis)", lambda m: fmt(m["f1_item_medio"])),
        ("F1 micro (linha × item)", lambda m: fmt(m["f1_micro"])),
        ("precisão / revocação micro", lambda m: f"{fmt(m['precisao_micro'])} / {fmt(m['revocacao_micro'])}"),
        ("conjunto exato de itens", lambda m: f"{m['conjunto_exato']:.0%}"),
        ("setor (linhas com setor no gabarito)", lambda m: f"{m['setor_acertos']}/{m['setor_linhas']}"),
        ("US$ por 1.000 linhas", lambda m: f"{m['usd_por_mil_linhas']:.2f}" if m["usd_por_mil_linhas"] else "—"),
        ("latência por linha, mediana (s)", lambda m: fmt(m["latencia_mediana_s"])),
        ("reparos de forma", lambda m: str(m["reparos"])),
    ]
    L += ["## Resultado", "", "| " + " | ".join(cab) + " |", "|---|" + "---|" * len(resultados)]
    for nome, fn in linhas:
        L.append(f"| {nome} | " + " | ".join(fn(m) for m in resultados.values()) + " |")
    L += ["", f"Os três últimos ({', '.join(nomes[m] for m in REGUA if m in resultados)}) são a **régua**: rotularam a referência antes da "
          "revisão, então leem melhor do que leriam num conjunto novo. Latência dos modelos de texto = tempo da chamada da vaga ÷ linhas, "
          "uma de cada vez; a do Jev é por requisição (4 em paralelo).", ""]
    L += ["## F1 por item (só os avaliáveis)", ""]
    aval = [i for i in itens if next(iter(resultados.values()))["itens"][i]["f1"] is not None]
    L += tabela_item(resultados, aval, nomes) + [""]
    L += ["## Kappa da presença por dimensão", "", "| dimensão | " + " | ".join(nomes[m] for m in resultados) + " |",
          "|---|" + "---|" * len(resultados)]
    for dim in dict.fromkeys(dim_de.values()):
        L.append(f"| {dim} | " + " | ".join(fmt(m["dimensoes"][dim]["kappa"]) for m in resultados.values()) + " |")
    if notas_limiar:
        L += ["", "## Jev: limiar e abstenção", "",
              "O sim/não do Jev vira item quando a probabilidade passa do limiar. O limiar foi escolhido na **prática** (88 linhas, "
              "maximiza o F1 micro; gabarito dela foi revisado numa versão anterior da taxonomia), não na referência.", ""]
        for modelo, n in notas_limiar.items():
            L += [f"**{modelo}**: limiar escolhido {n['escolhido_na_pratica']:.2f}; F1 micro na referência "
                  f"{fmt(resultados[modelo]['f1_micro'])} (com 0,50: {fmt(n['f1_micro_com_limiar_0_5'])}).", "",
                  "| faixa de probabilidade | decisões sim/não | erros | taxa de erro |", "|---|---|---|---|"]
            for a in n["abstencao"]:
                L.append(f"| {a['faixa']} | {a['decisoes']:,} | {a['erros']:,} | {'—' if a['taxa_erro'] is None else format(a['taxa_erro'], '.1%')} |")
            L.append("")
    L += ["", "## Conferência de viés de família", "",
          "O Opus escreveu a taxonomia e rotulou a referência. Pra ver se o Haiku (mesma empresa) se beneficia, o F1 micro de cada "
          "candidato de texto contra os rótulos **de cada rotulador original**, antes da revisão:", "",
          "| candidato | × opus | × gemini | × grok |", "|---|---|---|---|"]
    brutos = {m: carregar(m, "referencia") for m in REGUA if arquivo(m, "referencia").exists()}
    for m in CANDIDATOS_GATEWAY:
        r = carregar(m, "referencia")
        if r:
            L.append(f"| {nomes[m]} | " + " | ".join(fmt(f1_micro_conjunto(r, brutos[x]["linhas"], itens)) for x in REGUA if x in brutos) + " |")
    L += ["", "## Ressalvas", "",
          "- A referência é \"rótulos de modelos revisados por pessoa\" (D25), não rotulagem cega dele: 34 das 877 decisões de item "
          "foram mudadas na revisão, o resto ele aceitou. Os três rotuladores de origem têm vantagem na régua.",
          "- O Opus também escreveu a taxonomia; Haiku é da mesma empresa (ver a conferência acima).",
          "- Os modelos de texto rodaram uma vez, esforço `medium`; o prompt é o do Item 5, sem ajuste por modelo. Jev: um único desenho "
          "de perguntas (definição, borda e exemplos do `taxonomia.md` por item), sem iteração; outro desenho pode render mais ou menos.",
          "- Jev não devolve justificativa nem escreve o `outro`; benchmarks dele são do fornecedor e há quem conteste a categoria "
          "([InfoWorld](https://www.infoworld.com/article/4236103/typesafes-jev-even-more-susceptible-to-attack-than-llms-says-security-vendor.html)).",
          "- `peso`, `anos` e ferramentas saem por regra (`regras.py`), fora da disputa; o gabarito da referência não tem esses campos, "
          "então não foram medidos aqui.",
          "- Latência e custo: uma rodada, uma máquina, rede doméstica; ordem de grandeza, não benchmark."]
    leitura = EVALS / "leitura.md"
    if leitura.exists():
        L += ["", leitura.read_text(encoding="utf-8").rstrip()]
    (EVALS / "relatorio.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    print(f"-> {EVALS / 'relatorio.md'}")


if __name__ == "__main__":
    main()
