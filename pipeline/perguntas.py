"""Os seis cards de pergunta executiva da página (Análises P1–P6): cada um tem uma resposta, quatro destaques e uma lista de
seguimentos, e cada seguimento é um arquivo `.sql` de `consultas/`.

O que este módulo faz, na publicação:
  1. lê cada `consultas/pN_M.sql` e roda no DuckDB dos marts (`dbt/target/mercado.duckdb`): a página e a CI usam o mesmo arquivo;
  2. monta, com o resultado, o texto de cada resposta e a estrutura que o `app.js` desenha (nada é digitado à mão: número
     e condição saem do dado, e a conclusão que o dado deixar de sustentar vira aviso, como nos achados);
  3. devolve o HTML do cartão (a lista de seguimentos funciona sem JavaScript) e o bloco `perguntas` do `pagina.json`.

A régua do p é a D36: abaixo de 0,01 é diferença firme; entre 0,01 e 0,05, direção; acima, sem diferença clara. O p é o do
teste exato de Fisher entre coordenação e gerência, o mesmo que o `app.js` refaz no navegador.
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "analise"))
import achados as A  # noqa: E402

CONSULTAS = RAIZ / "consultas"
# Mínimos pra um seguimento virar gráfico: abaixo disso ele fica no card, sem gráfico, e entra em "o que os dados ainda não sustentam".
MIN_EMPRESAS = 10   # empresas com vaga nos dois níveis (P1·4)
MIN_SETOR_VAGAS, MIN_SETORES = 10, 5   # setores com ao menos 10 vagas, pelo menos 5 deles (P3·4, P5·1)
MIN_PJ = 10         # vagas que declaram PJ (P4·2)
MIN_N_REF = 5       # vagas com referência salarial por grupo (P5·2, P6·2)
DEZ = ["zero", "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito", "nove", "dez"]
TIPO_SEM_FORMACAO = ("Formação, idioma e experiência", "Comportamental e condições")
NOME_NIVEL = {"coordenador": "coordenação", "gerente": "gerência"}


# ---------- utilitários ----------

def ler(c, nome: str) -> dict:
    """Roda `consultas/<nome>.sql` e devolve texto, colunas e linhas (números inteiros como int, o resto como veio)."""
    sql = (CONSULTAS / f"{nome}.sql").read_text(encoding="utf-8")
    r = c.sql(sql)

    def v(x):
        if isinstance(x, float) and x == int(x):
            return int(x)
        return x

    return {"f": nome, "sql": sql.strip(), "cols": list(r.columns), "rows": [[v(x) for x in row] for row in r.fetchall()]}


def col(res: dict, nome: str) -> int:
    return res["cols"].index(nome)


def pt(x: float, casas: int = 1) -> str:
    return f"{x:.{casas}f}".replace(".", ",")


def reais(v: float) -> str:
    return A.reais(v)


def selo_p(p: float) -> tuple[str, str]:
    return ("DIFERENÇA FIRME", "firme") if p < 0.01 else ("DIREÇÃO", "dir") if p < 0.05 else ("SEM DIFERENÇA CLARA", "sem")


def melhor_selo(ps: list[float]) -> list[str]:
    s = selo_p(min(ps)) if ps else ("SEM DIFERENÇA CLARA", "sem")
    return list(s)


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def marca(s: str) -> str:
    """Troca `{dim:texto}` por um link pra seção que descreve as dimensões (metodologia, 3.1). Roda sobre texto já escapado."""
    return re.sub(r"\{dim:([^}]+)\}", lambda m: f'<a class="lk" href="#dimensoes">{m.group(1)}</a>', s)


def plural(n: int, um: str, varios: str) -> str:
    return f"{n} {um if n == 1 else varios}"


def inicial_minuscula(s: str) -> str:
    return s[0].lower() + s[1:] if len(s) > 1 and s[1].islower() else s


def juntar(xs: list[str]) -> str:
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " e " + xs[-1]


# ---------- os cards ----------

def montar(c, raw: dict, cond: dict, v: dict, pagina: dict, cob_nota: str) -> list[dict]:
    """Devolve os seis cards, prontos pra `html()` e pro `pagina.json`. `raw`/`cond`/`v` vêm de `achados.calcular`."""
    nc, ng = raw["nc"], raw["ng"]
    n_tot = nc + ng
    fisher = lambda xc, xg: A.fisher(xc, nc, xg, ng)  # noqa: E731
    base_nota = f"Base: {nc} vagas de coordenação e {ng} de gerência com o anúncio classificado.{cob_nota}"
    R = {n: ler(c, n) for n in sorted(p.stem for p in CONSULTAS.glob("p*_*.sql"))}

    def linhas_cg(res: dict) -> list[dict]:
        i, ic, ig = col(res, "item"), col(res, "coord"), col(res, "ger")
        return [{"label": r[i], "c": r[ic], "g": r[ig]} for r in res["rows"]]

    def view(k, q, a, f, tipo, d, tag="", leg=0, nota="", selo=None, ns=None) -> dict:
        return {"k": k, "q": q, "a": a, "selo": selo, "f": f, "tipo": tipo, "d": d, "tag": tag, "leg": leg, "nota": nota,
                "sql": R[f]["sql"], "res": {"cols": R[f]["cols"], "rows": R[f]["rows"]}, "ns": ns}

    cards: list[dict] = []

    # ================= P1 · da coordenação à gerência =================
    r0 = linhas_cg(R["p1_0"])
    por_item_mapa = {r["label"]: r for r in r0}
    # P1·1 núcleo (Wilson na consulta; o p é o da página)
    r1 = R["p1_1"]
    ii, ik, ibase, iv, il, ih, inv = (col(r1, x) for x in ("item", "nivel", "base", "vagas", "ic_baixo", "ic_alto", "pct"))
    nucleo: dict[str, dict] = {}
    for row in r1["rows"]:
        nucleo.setdefault(row[ii], {"label": row[ii]})["c" if row[ik] == "coordenador" else "g"] = [row[iv], row[il], row[ih]]
    nucleo_l = list(nucleo.values())
    p_nucleo = [fisher(x["c"][0], x["g"][0]) for x in nucleo_l]
    pmin_n = min(p_nucleo) if p_nucleo else 1
    # P1·2 diferenças de 15 pontos ou mais, com a régua
    r2 = R["p1_2"]
    dif_l = [{"label": r[0], "c": r[1], "g": r[2], "d": r[3]} for r in r2["rows"]]
    for x in dif_l:
        x["p"] = fisher(x["c"], x["g"])
    n_firme = sum(1 for x in dif_l if x["p"] < 0.01)
    dir_l = [x for x in dif_l if 0.01 <= x["p"] < 0.05]
    # P1·3 tarefa × requisito
    r3 = R["p1_3"]
    nat = [dict(zip(r3["cols"], r)) for r in r3["rows"]]
    nat_op = next((x for x in nat if x["item"] == "Operação do time"), None)
    nat_es = next((x for x in nat if x["item"] == "Estratégia e visão"), None)
    # P1·4 mesma empresa
    r4 = R["p1_4"]
    emp = [{"label": r[0], "c": r[1], "g": r[2]} for r in r4["rows"]]

    nf_txt = ("Só " if n_firme <= 2 else "") + (f"{n_firme} passa firme" if n_firme == 1 else f"{n_firme} passam firmes") + " na régua"
    a_dif = f"{len(dif_l)} itens têm 15 pontos ou mais de diferença. {nf_txt} e {len(dir_l)} {'aponta' if len(dir_l) == 1 else 'apontam'} direção."
    if pmin_n >= 0.1:
        a_nuc = f"Sim. Nos {len(nucleo_l)} itens que mais de 60% pedem nos dois níveis, as faixas se cruzam e nenhum passa na régua (p > {pt(int(pmin_n * 10) / 10)} em todos)."
    elif pmin_n >= 0.05:
        a_nuc = f"Sim. Nos {len(nucleo_l)} itens que mais de 60% pedem nos dois níveis, nenhum passa na régua (p > 0,05 em todos)."
    else:
        a_nuc = f"Em parte. Dos {len(nucleo_l)} itens que mais de 60% pedem nos dois níveis, {sum(1 for p in p_nucleo if p < 0.05)} passam na régua."
    if nat_op and nat_es:
        t_op = nat_op["so_tarefa"] + nat_op["tarefa_e_requisito"]
        t_es = nat_es["so_tarefa"] + nat_es["tarefa_e_requisito"]
        a_nat = (f"No que se faz. A operação do time é tarefa em {t_op} das {nat_op['vagas']} vagas de coordenação; a estratégia da gerência aparece "
                 f"como tarefa em {t_es} de {nat_es['vagas']} vagas e só como requisito em {nat_es['so_requisito']}.")
    else:
        a_nat = "Sem o dado pra comparar nesta publicação."
    n_emp = len(emp)
    emp_ok = n_emp >= MIN_EMPRESAS
    liderar = por_item_mapa.get("Liderar time")
    estr = next((x for x in dif_l if x["label"] == "Estratégia e visão"), None)
    oper = next((x for x in dif_l if x["label"] == "Operação do time"), None)
    p1_nome_dir = " · ".join(x["label"] for x in dir_l[:3]) + (f" · e mais {len(dir_l) - 3}" if len(dir_l) > 3 else "")
    cond_p1 = cond["c1"] and cond["c2"] and n_firme == 2
    pp = lambda p: A.p_txt(p)  # noqa: E731
    cards.append({
        "id": "p1", "rail": "P1 · Coordenação → gerência", "sumario": "O que muda quando a cadeira sobe de coordenação pra gerência?",
        "label": "Da coordenação à gerência",
        "h2": ["Mesmo núcleo. Coordenação opera o time;", "gerência decide", "para onde ele vai."], "virou": not cond_p1,
        "pergunta": "O que muda quando a cadeira sobe de coordenação pra gerência?",
        "lede": "Menos do que o título do cargo sugere. O núcleo do anúncio é o mesmo nos dois níveis: liderar o time, lidar com stakeholders, "
                "desenvolver pessoas. Só duas diferenças passam folgadas na régua: a gerência pede estratégia, a coordenação pede a operação do time.",
        "tk": [
            {"r": "Igual nos dois", "t": "Liderar time", "n": f'<i class="c">{pt(100 * liderar["c"] / nc, 0)}%</i> · <i class="g">{pt(100 * liderar["g"] / ng, 0)}%</i>'} if liderar else None,
            {"r": "Sobe na gerência", "t": "Estratégia e visão", "n": f'<i class="c">{pt(100 * estr["c"] / nc, 0)}%</i> → <i class="g">{pt(100 * estr["g"] / ng, 0)}%</i> · {pp(estr["p"])}'} if estr else None,
            {"r": "Fica na coordenação", "t": "Operação do time", "n": f'<i class="c">{pt(100 * oper["c"] / nc, 0)}%</i> → <i class="g">{pt(100 * oper["g"] / ng, 0)}%</i> · {pp(oper["p"])}'} if oper else None,
            {"r": "Na mesma direção, sem folga", "t": p1_nome_dir or "—", "n": "p entre 0,01 e 0,05"},
        ],
        "views": [
            view("P1", "O mapa", "O que fica igual e o que muda, num gráfico só.", "p1_0", "mapa", r0, "% das vagas que pedem", 1, base_nota),
            view("1", "O núcleo é mesmo igual?", a_nuc, "p1_1", "nucleo", nucleo_l, "% das vagas que pedem · faixa = intervalo de 95%", 1,
                 "Faixa = intervalo de 95% de Wilson, calculado na própria consulta. Faixas que se cruzam não provam igualdade, mas mostram que a amostra não separa os níveis nesses itens.",
                 melhor_selo(p_nucleo)),
            view("2", "O que mais muda?", a_dif, "p1_2", "dif", dif_l, "diferença em pontos · gerência − coordenação", 2,
                 "Barra cheia = passa na régua (firme abaixo de p = 0,01; direção até 0,05). Tracejada = sem diferença clara: a distância em pontos existe, mas cabe no acaso com esta amostra.",
                 melhor_selo([x["p"] for x in dif_l])),
            view("3", "Muda no que se faz ou no que se exige?", a_nat, "p1_3", "nat",
                 [{"label": f'{x["item"]} · {NOME_NIVEL[x["nivel"]]}', "total": x["vagas"], "cor": "c" if x["nivel"] == "coordenador" else "g",
                   "segs": [["só como tarefa", x["so_tarefa"], 1], ["tarefa e requisito", x["tarefa_e_requisito"], .5], ["só como requisito", x["so_requisito"], 0]]} for x in nat],
                 "onde o item aparece no anúncio", 0,
                 "Tarefa = a linha é uma responsabilidade do cargo; requisito = a linha pede algo de quem se candidata. Uma vaga pode ter o item nos dois.", ["DESCRITIVO", "desc"]),
            (view("4", "Vale dentro da mesma empresa?", f"Ainda não dá pra dizer: só {plural(n_emp, 'empresa tem', 'empresas têm')} vaga nos dois níveis.", "p1_4", "nao",
                  {"n": n_emp, "min": MIN_EMPRESAS, "unidade": "empresas", "grande": "empresas com vaga classificada nos dois níveis", "itens": emp,
                   "texto": f"Comparar a mesma empresa tira o efeito do setor e do porte, e por isso é a pergunta mais forte do card. <b>Com {n_emp} {'empresa' if n_emp == 1 else 'empresas'}, qualquer resposta seria anedota.</b> O seguimento fica aqui e na lista \"O que os dados ainda não sustentam\" até a amostra chegar ao mínimo."},
                  f"empresas com vaga nos dois níveis", 0, f"Mínimo pro gráfico: {MIN_EMPRESAS} empresas com vaga classificada nos dois níveis.", ["NÃO SUSTENTA", "nao"],
                  [f"{n_emp} empresas com vaga nos dois níveis", f"{MIN_EMPRESAS} empresas"])
             if not emp_ok else
             view("4", "Vale dentro da mesma empresa?", f"{n_emp} empresas têm vaga nos dois níveis.", "p1_4", "grupos", emp, "vagas por empresa, nos dois níveis", 1,
                  "Cada empresa conta as vagas classificadas de cada nível.", ["DESCRITIVO", "desc"])),
        ],
    })

    # ================= P2 · quanto de técnico =================
    r20 = R["p2_0"]
    mm = {r[0]: (r[1], r[2]) for r in r20["rows"]}
    mm_c, mm_g = mm.get("coordenador", (0, nc)), mm.get("gerente", (0, ng))
    p_mm = fisher(mm_c[0], mm_g[0])
    f1 = linhas_cg(R["p2_1"])
    for x in f1:
        x["p"] = fisher(x["c"], x["g"])
    f1_firme = [x["label"] for x in f1 if x["p"] < 0.01]
    f1_top = max(f1, key=lambda x: x["c"] + x["g"]) if f1 else None
    r22 = R["p2_2"]
    mm_ferr = {(r[0], bool(r[1])): (r[2], r[3]) for r in r22["rows"]}
    p2_2_rows, p2_2_ok = [], True
    for niv in ("coordenador", "gerente"):
        for flag, nome in ((True, "pede mão na massa"), (False, "não pede")):
            n_, m_ = mm_ferr.get((niv, flag), (0, 0))
            p2_2_rows.append({"label": f"{NOME_NIVEL[niv].capitalize()} · {nome}", "v": m_, "n": n_, "cor": "c" if niv == "coordenador" else "g", "txt": f"{pt(m_)} ferramentas por vaga · {n_} vagas", "op": 1 if flag else .5})
        p2_2_ok = p2_2_ok and mm_ferr.get((niv, True), (0, 0))[1] > mm_ferr.get((niv, False), (0, 0))[1]
    a_22 = ("Sim, nos dois níveis: " if p2_2_ok else "Não nos dois níveis: ") + (
        f"{pt(mm_ferr.get(('coordenador', True), (0, 0))[1])} contra {pt(mm_ferr.get(('coordenador', False), (0, 0))[1])} ferramentas por vaga na coordenação, "
        f"{pt(mm_ferr.get(('gerente', True), (0, 0))[1])} contra {pt(mm_ferr.get(('gerente', False), (0, 0))[1])} na gerência.")
    r23 = R["p2_3"]
    dif_ferr = [dict(zip(r23["cols"], r)) for r in r23["rows"]]
    tot_v = sum(x["vagas"] for x in dif_ferr)
    tot_d = sum(x["so_diferencial"] for x in dif_ferr)
    pct_d = 100 * tot_d / tot_v if tot_v else 0
    a_23 = (f"Quase sempre é exigência, não diferencial: só {tot_d} de {tot_v} citações das {len(dif_ferr)} ferramentas mais citadas aparecem apenas na seção de diferenciais."
            if pct_d < 20 else
            f"Uma parte relevante é diferencial: {tot_d} de {tot_v} citações das {len(dif_ferr)} ferramentas mais citadas aparecem apenas na seção de diferenciais ({pt(pct_d, 0)}%).")
    maior_dif = max(dif_ferr, key=lambda x: (x["so_diferencial"] / x["vagas"], x["vagas"])) if dif_ferr else None
    r24 = R["p2_4"]
    pares = [dict(zip(r24["cols"], r)) for r in r24["rows"]]
    base_pares = pares[0]["base"] if pares else n_tot
    topo_pares = [x for x in pares if x["vagas"] == pares[0]["vagas"]] if pares else []
    a_24 = (f"{juntar([x['ferramenta_a'] + ' + ' + x['ferramenta_b'] for x in topo_pares])} " + ("é o par mais comum" if len(topo_pares) == 1 else "são os pares mais comuns")
            + f", em {pares[0]['vagas']} de {base_pares} vagas" + ("." if len(topo_pares) == 1 else " cada.")) if pares else "Sem pares de ferramentas nesta publicação."
    py_ = next((x for x in f1 if x["label"] == "Python"), None)
    cond_p2 = cond["c3"] and cond["c4"]
    cards.append({
        "id": "p2", "rail": "P2 · Quanto de técnico?", "sumario": "Quanto de técnico um gestor de dados ainda precisa ter?", "label": "O lado técnico",
        "h2": ["Metade pede mão na massa.", "Python é pedido", "de coordenação."], "virou": not cond_p2,
        "pergunta": "Quanto de técnico um gestor de dados ainda precisa ter?",
        "lede": "Cerca de metade dos anúncios pede mão na massa, nos dois níveis, e subir de nível não muda a conta. Entre as ferramentas, Python é a única em que os níveis "
                "se separam com folga; SQL e nuvem citada pelo nome não se separam do acaso. Citar o nome é diferente de exigir (pode estar num diferencial ou numa lista de exemplos), "
                "e quem não nomeia pode pedir por outro termo: trate como piso.",
        "tk": [
            {"r": "Pedem mão na massa", "t": "Referência técnica / hands-on", "n": f'<i class="c">{pt(100 * mm_c[0] / mm_c[1], 0)}%</i> · <i class="g">{pt(100 * mm_g[0] / mm_g[1], 0)}%</i> · {pp(p_mm)}'},
            {"r": "A mais citada pelo nome", "t": f1_top["label"] if f1_top else "—", "n": f'<i class="c">{pt(100 * f1_top["c"] / nc, 0)}%</i> · <i class="g">{pt(100 * f1_top["g"] / ng, 0)}%</i>'} if f1_top else None,
            {"r": "Separa os níveis", "t": juntar(f1_firme) if f1_firme else "Nenhuma", "n": (f'<i class="c">{pt(100 * py_["c"] / nc, 0)}%</i> → <i class="g">{pt(100 * py_["g"] / ng, 0)}%</i> · {pp(py_["p"])}' if py_ and "Python" in f1_firme else "p ≥ 0,01 em todas")},
            {"r": "Mais perto de diferencial", "t": maior_dif["ferramenta"] if maior_dif else "—", "n": f'{maior_dif["so_diferencial"]} de {maior_dif["vagas"]} vagas só como diferencial' if maior_dif else ""},
        ],
        "views": [
            view("P2", "O mapa", "Quantas vagas pedem mão na massa, em cada nível.", "p2_0", "waffle", {"c": list(mm_c), "g": list(mm_g)},
                 "cada ponto é uma vaga · aceso = pede mão na massa", 0, base_nota, melhor_selo([p_mm])),
            view("1", "Quais ferramentas, por nível?", (f"{f1_top['label']} é a mais citada pelo nome. " if f1_top else "") + (f"{juntar(f1_firme)} separa{'m' if len(f1_firme) > 1 else ''} os níveis com folga." if f1_firme else "Nenhuma separa os níveis com folga."),
                 "p2_1", "mapa", [{"label": x["label"], "c": x["c"], "g": x["g"]} for x in f1], "% das vagas que citam pelo nome", 1,
                 "Regra fixa sobre o anúncio inteiro (dbt/seeds/ferramentas.csv), publicada na coluna ferramentas de rotulos.csv. Quem pede por outro nome não é contado.", melhor_selo([x["p"] for x in f1])),
            view("2", "Quem pede mão na massa pede mais ferramenta?", a_22, "p2_2", "hb", {"rows": p2_2_rows, "max": max([r["v"] for r in p2_2_rows] + [1])},
                 "ferramentas citadas pelo nome por vaga, média", 0, "Média entre as vagas de cada grupo (coordenação e gerência, com e sem o item de mão na massa). Descrição, não comparação: os grupos têm poucas vagas.", ["DESCRITIVO", "desc"]),
            view("3", "O técnico é obrigatório ou diferencial?", a_23, "p2_3", "nat",
                 [{"label": x["ferramenta"], "total": x["vagas"], "cor": "m", "segs": [["pedida como requisito ou tarefa", x["vagas"] - x["so_diferencial"], 1], ["só como diferencial", x["so_diferencial"], 0]]} for x in dif_ferr],
                 "onde a ferramenta aparece no anúncio · as 6 mais citadas", 0, "Só como diferencial = todas as linhas que citam a ferramenta estão na seção de diferenciais do anúncio. Os dois níveis juntos.", ["DESCRITIVO", "desc"]),
            view("4", "Que stack aparece junta?", a_24, "p2_4", "hb",
                 {"rows": [{"label": f"{x['ferramenta_a']} + {x['ferramenta_b']}", "v": x["vagas"], "n": base_pares, "cor": "m", "txt": f"{x['vagas']} de {base_pares} vagas"} for x in pares], "max": pares[0]["vagas"] if pares else 1},
                 "pares de ferramentas citadas na mesma vaga", 0, "Par = as duas ferramentas citadas pelo nome na mesma vaga, nos dois níveis juntos. Cada par conta uma vez por vaga.", ["DESCRITIVO", "desc"]),
        ],
    })

    # ================= P3 · IA =================
    r30 = linhas_cg(R["p3_0"])
    algum = next((x for x in r30 if x["label"] == "Algum item de IA"), {"c": 0, "g": 0})
    ia_tot = algum["c"] + algum["g"]
    ia_pct = 100 * ia_tot / n_tot if n_tot else 0
    r31 = linhas_cg(R["p3_1"])
    papel = {x["label"]: x["c"] + x["g"] for x in r31}
    r32 = linhas_cg(R["p3_2"])
    for x in r32:
        x["p"] = fisher(x["c"], x["g"])
    f32 = [x["label"] for x in r32 if x["p"] < 0.01]
    d32 = [x["label"] for x in r32 if 0.01 <= x["p"] < 0.05]
    r33 = R["p3_3"]
    j33 = [dict(zip(r33["cols"], r)) for r in r33["rows"]]
    for x in j33:
        x["p"] = A.fisher(x["com_ia"], x["base_com_ia"], x["sem_ia"], x["base_sem_ia"])
    top33 = j33[0] if j33 else None
    r34 = R["p3_4"]
    set34 = [dict(zip(r34["cols"], r)) for r in r34["rows"]]
    m_set34 = sum(1 for x in set34 if x["vagas"] >= MIN_SETOR_VAGAS)
    ia_ok = m_set34 >= MIN_SETORES
    a_32 = (f"{r32[0]['label']} é o item de IA mais pedido, em {r32[0]['c'] + r32[0]['g']} de {n_tot} vagas. " if r32 else "") + (
        f"{juntar(f32)} separa{'m' if len(f32) > 1 else ''} os níveis com folga" + (f"; {juntar(d32)} aponta{'m' if len(d32) > 1 else ''} direção." if d32 else ".") if f32 else
        (f"Nenhum item separa os níveis com folga; {juntar(d32)} aponta{'m' if len(d32) > 1 else ''} direção." if d32 else "Nenhum item separa os níveis."))
    mais_ia = "Gerência" if algum["g"] / ng >= algum["c"] / nc else "Coordenação"
    cond_p3 = cond["c5"] and ia_pct > 50
    cards.append({
        "id": "p3", "rail": "P3 · IA é exigência?", "sumario": "IA já é exigência pra liderar dados?", "label": "Onde a IA entra",
        "h2": ["IA já está na maioria das vagas,", "mais como tarefa do que", "como pré-requisito."], "virou": not cond_p3,
        "pergunta": "IA já é exigência pra liderar dados?",
        "lede": f"Algum item de IA (ciência de dados e ML, IA aplicada ao negócio, IA generativa, agentes, MLOps) aparece em {DEZ[round(10 * ia_tot / n_tot)] if n_tot else 'zero'} de cada dez vagas. "
                "Ele aparece mais no que a pessoa vai fazer do que no que ela já precisa saber, e a gerência cita mais que a coordenação.",
        "tk": [
            {"r": "Vagas com algum item de IA", "t": f"{pt(ia_pct, 0)}% das vagas", "n": f"{ia_tot} de {n_tot} · <i class=\"c\">{pt(100 * algum['c'] / nc, 0)}%</i> · <i class=\"g\">{pt(100 * algum['g'] / ng, 0)}%</i>"},
            {"r": "Como tarefa", "t": f"{papel.get('Como tarefa', 0)} de {ia_tot} vagas com IA", "n": "a linha é uma responsabilidade do cargo"},
            {"r": "Como requisito", "t": f"{papel.get('Como requisito', 0)} de {ia_tot} vagas com IA", "n": "a linha pede algo de quem se candidata"},
            {"r": "O item mais pedido", "t": r32[0]["label"] if r32 else "—", "n": f"{r32[0]['c'] + r32[0]['g']} de {n_tot} vagas" if r32 else ""},
        ],
        "views": [
            view("P3", "O mapa", f"{mais_ia} cita mais IA, e a IA aplicada ao negócio vai na mesma direção.", "p3_0", "mapa", r30, "% das vagas que pedem", 1, base_nota + " Os seis itens de IA somados na primeira linha."),
            view("1", "Tarefa, requisito ou diferencial?", f"Mais como tarefa ({papel.get('Como tarefa', 0)} das {ia_tot} vagas com IA) do que como requisito ({papel.get('Como requisito', 0)}); como diferencial, {papel.get('Como diferencial', 0)}.",
                 "p3_1", "mapa", r31, "% das vagas que pedem · em cada papel", 1, "Uma vaga pode ter IA em mais de um papel. Tarefa = linha de responsabilidade · diferencial = linha da seção de diferenciais · requisito = o resto das linhas de requisito.", ["DESCRITIVO", "desc"]),
            view("2", "Que IA?", a_32, "p3_2", "mapa", [{"label": x["label"], "c": x["c"], "g": x["g"]} for x in r32], "% das vagas que pedem", 1, "Os seis itens de IA da lista fechada.", melhor_selo([x["p"] for x in r32])),
            view("3", "A IA aparece junto de quê?",
                 (f"{top33['item']} é o que mais acompanha a IA: {top33['pct_com_ia']}% das vagas com IA contra {top33['pct_sem_ia']}% das sem IA." if top33 else "Sem dado pra comparar."),
                 "p3_3", "dumb2", {"rows": [{"label": x["item"], "a": x["com_ia"], "na": x["base_com_ia"], "b": x["sem_ia"], "nb": x["base_sem_ia"]} for x in j33], "legA": "vagas com IA", "legB": "vagas sem IA"},
                 "% das vagas que pedem o item · com IA × sem IA", 3, "Os dois níveis juntos. Seis itens escolhidos pelo que a IA costuma acompanhar (produto, governança, plataforma, KPIs, estratégia e engenharia de dados).", melhor_selo([x["p"] for x in j33])),
            (view("4", "A IA muda por setor?", f"Ainda não dá pra dizer: só {plural(m_set34, 'setor tem', 'setores têm')} {MIN_SETOR_VAGAS} vagas ou mais com o anúncio classificado.", "p3_4", "nao",
                  {"n": m_set34, "min": MIN_SETORES, "unidade": f"setores com {MIN_SETOR_VAGAS} vagas ou mais", "grande": f"setores com {MIN_SETOR_VAGAS} vagas ou mais", "itens": [{"label": x["setor"], "c": x["vagas"], "g": x["com_ia"], "fmt": f'{x["com_ia"]} de {x["vagas"]} com IA'} for x in set34[:6]],
                   "texto": f"O setor é proposto pela classificação e muda a conversa (financeiro não pede o que varejo pede), mas com {len(set34)} setores e poucas vagas em cada, qualquer diferença seria acaso. <b>Aparece aqui e em \"O que os dados ainda não sustentam\".</b>"},
                  "vagas com IA por setor", 0, f"Mínimo pro gráfico: {MIN_SETORES} setores com {MIN_SETOR_VAGAS} vagas ou mais.", ["NÃO SUSTENTA", "nao"],
                  [f"{m_set34} setores com {MIN_SETOR_VAGAS} vagas ou mais", f"{MIN_SETORES} setores"])
             if not ia_ok else
             view("4", "A IA muda por setor?", f"{juntar([x['setor'] for x in set34 if x['vagas'] >= MIN_SETOR_VAGAS][:3])} lideram em número de vagas; a IA aparece em " +
                  f"{min(100 * x['com_ia'] // x['vagas'] for x in set34 if x['vagas'] >= MIN_SETOR_VAGAS)}% a {max(100 * x['com_ia'] // x['vagas'] for x in set34 if x['vagas'] >= MIN_SETOR_VAGAS)}% das vagas deles.",
                  "p3_4", "hb", {"rows": [{"label": x["setor"], "v": round(100 * x["com_ia"] / x["vagas"]), "n": x["vagas"], "cor": "m", "txt": f'{x["com_ia"]} de {x["vagas"]} vagas · {round(100 * x["com_ia"] / x["vagas"])}%'} for x in set34 if x["vagas"] >= MIN_SETOR_VAGAS], "max": 100},
                  "% das vagas com algum item de IA, por setor", 0, f"Só setores com {MIN_SETOR_VAGAS} vagas ou mais. O setor é proposto pela classificação.", ["DESCRITIVO", "desc"])),
        ],
    })

    # ================= P4 · quanto paga =================
    r41 = R["p4_1"]
    fontes = sum(r[col(r41, "fontes_citadas")] for r in r41["rows"])
    r42 = R["p4_2"]
    n_pj = sum(r[col(r42, "vagas")] for r in r42["rows"] if r[col(r42, "contrato")] == "PJ")
    r43 = R["p4_3"]
    n_benef = sum(r[col(r43, "com_secao_beneficios")] for r in r43["rows"])
    n_43 = sum(r[col(r43, "vagas")] for r in r43["rows"])
    r40 = R["p4_0"]
    sal_n = {r[0]: (r[1], r[2]) for r in r40["rows"]}
    sc, sg = sal_n.get("coordenador", (0, 0)), sal_n.get("gerente", (0, 0))
    cond_p4 = cond["c6"]
    perc4 = lambda a, b: pt(100 * a / b, 0) if b else "0"  # noqa: E731
    f41 = {r[col(r41, "nivel")]: dict(zip(r41["cols"], r)) for r in r41["rows"]}
    f43 = {r[col(r43, "nivel")]: dict(zip(r43["cols"], r)) for r in r43["rows"]}
    pj42 = {r[col(r42, "nivel")]: r[col(r42, "vagas")] for r in r42["rows"] if r[col(r42, "contrato")] == "PJ"}
    por_vaga = lambda d: pt(d["fontes_citadas"] / d["vagas_com_referencia"], 1) if d.get("vagas_com_referencia") else "0"  # noqa: E731
    cor_n = {"coordenador": "c", "gerente": "g"}
    b41 = [{"v": str(f41[n]["fontes_citadas"]), "cor": cor_n[n], "rot": f"{NOME_NIVEL[n]} · fontes citadas em {f41[n]['vagas_com_referencia']} vagas"} for n in ("coordenador", "gerente") if n in f41]
    b41b = [{"v": por_vaga(f41[n]), "cor": cor_n[n], "rot": f"{NOME_NIVEL[n]} · fontes por vaga com referência, em média"} for n in ("coordenador", "gerente") if n in f41]
    b42 = [{"v": str(pj42.get(n, 0)), "cor": cor_n[n], "rot": f"{NOME_NIVEL[n]} · vagas que declaram PJ"} for n in ("coordenador", "gerente")]
    b43 = [{"v": f"{perc4(f43[n]['com_secao_beneficios'], f43[n]['vagas'])}%", "cor": cor_n[n], "rot": f"{NOME_NIVEL[n]} · {f43[n]['com_secao_beneficios']} de {f43[n]['vagas']} vagas têm seção de benefícios"} for n in ("coordenador", "gerente") if n in f43]
    cards.append({
        "id": "p4", "rail": "P4 · Quanto paga?", "sumario": "Quanto paga uma cadeira de gestão de dados, e por que o anúncio não diz?", "label": "Quanto paga",
        "h2": ["Nenhum anúncio", "diz quanto paga."], "virou": not cond_p4,
        "pergunta": "Quanto paga uma cadeira de gestão de dados, e por que o anúncio não diz?",
        "lede": f"<b>{v['n_faixa']} de {v['n_vagas']}</b> anúncios declaram faixa salarial. O que se sabe de salário vem de fora do anúncio: a referência de mercado pesquisada vaga a vaga "
                f"põe o meio da faixa em <b>{v['sal_med_c']}</b> na coordenação e <b>{v['sal_med_g']}</b> na gerência, por mês.",
        "tk": [
            {"r": "Anúncios com faixa", "t": f"{v['n_faixa']} de {v['n_vagas']}", "n": "o que o anúncio declara"},
            {"r": "Referência, coordenação", "t": v["sal_med_c"], "n": f"mediana por mês · {sc[0]} vagas"},
            {"r": "Referência, gerência", "t": v["sal_med_g"], "n": f"mediana por mês · {sg[0]} vagas"},
            {"r": "Fontes pesquisadas", "t": f"{v['bench_fontes']} referências", "n": f"em {v['bench_dominios']} sites"},
        ],
        "views": [
            view("P4", "A referência por nível", f"Mediana de {v['sal_med_c']} na coordenação e {v['sal_med_g']} na gerência, por mês.", "p4_0", "salario", {"fontes": v["bench_fontes"], "dominios": v["bench_dominios"]},
                 "referência salarial pesquisada por vaga · R$ por mês", 4,
                 "Cada linha é uma vaga: a faixa de referência pesquisada pro cargo e a cidade dela. A mesma faixa de um guia salarial se repete em muitas vagas (tracejada): a mediana da gerência, em especial, fica presa a ela. A fonte de cada número está em benchmarks.csv.",
                 ["DESCRITIVO", "desc"]),
            view("1", "As fontes concordam entre si?", f"Ainda não dá pra dizer: o dado publicado diz quantas fontes cada vaga tem ({fontes} nas vagas da comparação), não o valor de cada uma.", "p4_1", "falta",
                 {"texto": "A referência de cada vaga junta várias fontes, mas o arquivo publicado guarda a fonte e uma nota, não o mínimo e o máximo de cada uma. Sem o valor por fonte, não dá pra medir se elas concordam. <b>Falta no dado</b>, não na amostra.", "n": fontes, "rotulo": "fontes citadas, sem o valor de cada uma", "blocos": b41, "blocos2": b41b},
                 "fontes citadas por nível", 0, "", ["FALTA NO DADO", "nao"], ["o valor por fonte não está no dado publicado", "o dado ganhar o valor por fonte"]),
            (view("2", "CLT × PJ", f"Ainda não dá pra dizer: só {plural(n_pj, 'vaga declara', 'vagas declaram')} PJ.", "p4_2", "nao",
                  {"n": n_pj, "min": MIN_PJ, "unidade": "vagas PJ", "grande": "vagas declaram PJ", "blocos": b42,
                   "texto": f"A referência salarial muda com o contrato, mas <b>com {n_pj} vagas PJ qualquer comparação seria anedota</b>. O seguimento fica aqui e na lista \"O que os dados ainda não sustentam\"."},
                  "vagas por contrato declarado", 0, f"Mínimo pro gráfico: {MIN_PJ} vagas que declaram PJ.", ["NÃO SUSTENTA", "nao"], [f"{n_pj} vagas PJ", f"{MIN_PJ} vagas PJ"])
             if n_pj < MIN_PJ else
             view("2", "CLT × PJ", f"{n_pj} vagas declaram PJ.", "p4_2", "tabela", {}, "vagas por contrato declarado", 0, "", ["DESCRITIVO", "desc"])),
            view("3", "Quem não diz o salário diz o quê?", f"Ainda não dá pra dizer: o dado publicado só diz se o anúncio tem seção de benefícios ({n_benef} de {n_43} vagas), não o que ela contém.", "p4_3", "falta",
                 {"texto": "Saber o que o anúncio oferece no lugar do salário pede o texto da seção de benefícios, que não atravessa a fronteira de sigilo. <b>Falta no dado</b>: o contrato de dados só leva se a seção existe.", "n": n_benef, "rotulo": f"de {n_43} vagas têm seção de benefícios", "blocos": b43},
                 "anúncios com seção de benefícios", 0, "", ["FALTA NO DADO", "nao"], ["o dado só diz se a seção existe, não o que ela contém", "o dado levar o conteúdo da seção"]),
        ],
    })

    # ================= P5 · tipos de cadeira =================
    r50 = R["p5_0"]
    tipos = [{"label": r[0], "c": r[1], "g": r[2]} for r in r50["rows"]]
    for x in tipos:
        x["p"] = fisher(x["c"], x["g"])
    est_t = next((x for x in tipos if x["label"].startswith("Estratégia")), None)
    topo_g = max(tipos, key=lambda x: x["g"]) if tipos else None
    max_c = max((x["c"] for x in tipos), default=0)
    topo_c = [x["label"] for x in tipos if x["c"] == max_c]
    raro = min(tipos, key=lambda x: x["c"] + x["g"]) if tipos else None
    r51 = R["p5_1"]
    setor_tot: dict[str, int] = {}
    for r in r51["rows"]:
        setor_tot[r[0]] = setor_tot.get(r[0], 0) + r[2]
    m_set51 = sum(1 for n_ in setor_tot.values() if n_ >= MIN_SETOR_VAGAS)
    r52 = R["p5_2"]
    ref_t = [{"label": r[0], "v": r[2], "n": r[1], "cor": "m", "txt": f"{reais(r[2])} · {r[1]} vagas"} for r in r52["rows"] if r[1] >= MIN_N_REF]
    ref_t.sort(key=lambda x: -x["v"])
    a_52 = (f"{ref_t[0]['label']} tem a referência mais alta ({reais(ref_t[0]['v'])}, {ref_t[0]['n']} vagas) e {ref_t[-1]['label']} a mais baixa ({reais(ref_t[-1]['v'])}, {ref_t[-1]['n']} vagas). "
            f"Com poucas vagas por tipo, é descrição, não comparação." if len(ref_t) >= 2 else "Poucas vagas por tipo pra comparar a referência salarial.")
    est_g_txt = f" ({est_t['g']} de {ng} vagas)" if est_t else ""
    cond_p5 = bool(est_t and topo_g and topo_g["label"] == est_t["label"] and est_t["g"] / ng > est_t["c"] / nc and est_t["p"] < 0.05 and max_c / nc < 0.35)
    cards.append({
        "id": "p5", "rail": "P5 · Que tipos de cadeira?", "sumario": "Que tipos de cadeira de liderança de dados existem?", "label": "Tipos de cadeira",
        "h2": ["Na gerência, a cadeira é de estratégia;", "na coordenação,", "se divide."], "virou": not cond_p5,
        "pergunta": "Que tipos de cadeira de liderança de dados existem?",
        "lede": "O tipo da cadeira é a dimensão que mais pesa no anúncio, entre {dim:as seis de conteúdo}: gente, estratégia, engenharia, analytics, IA e governança. "
                f"Estratégia lidera a gerência{est_g_txt}; na coordenação nenhuma domina e o tipo se divide entre engenharia, analytics e estratégia.",
        "tk": [
            {"r": "Gerência: o tipo mais comum", "t": topo_g["label"] if topo_g else "—", "n": f"{topo_g['g']} de {ng} vagas · {pt(100 * topo_g['g'] / ng, 0)}%" if topo_g else ""},
            {"r": "Coordenação: o mais comum", "t": juntar(topo_c) if topo_c else "—", "n": f"{max_c} de {nc} vagas cada · {pt(100 * max_c / nc, 0)}%"},
            {"r": "O que separa os níveis", "t": est_t["label"] if est_t else "—", "n": (f'<i class="c">{pt(100 * est_t["c"] / nc, 0)}%</i> → <i class="g">{pt(100 * est_t["g"] / ng, 0)}%</i> · {pp(est_t["p"])}' if est_t else "")},
            {"r": "O tipo mais raro", "t": raro["label"] if raro else "—", "n": f"{raro['c'] + raro['g']} de {n_tot} vagas" if raro else ""},
        ],
        "views": [
            view("P5", "Quantas de cada tipo, por nível?", (f"{est_t['label']} é o tipo dominante em {est_t['g']} de {ng} vagas de gerência, contra {est_t['c']} de {nc} na coordenação." if est_t else "Sem dado."),
                 "p5_0", "grupos", tipos, "vagas por tipo da cadeira", 1,
                 "Tipo = a dimensão com mais linhas no anúncio, entre {dim:as seis de conteúdo}; empate vai pra ordem alfabética. " + base_nota, melhor_selo([x["p"] for x in tipos])),
            (view("1", "Qual setor pede qual tipo?", f"Ainda não dá pra dizer: só {plural(m_set51, 'setor tem', 'setores têm')} {MIN_SETOR_VAGAS} vagas ou mais com o anúncio classificado.", "p5_1", "nao",
                  {"n": m_set51, "min": MIN_SETORES, "unidade": f"setores com {MIN_SETOR_VAGAS} vagas ou mais", "grande": f"setores com {MIN_SETOR_VAGAS} vagas ou mais",
                   "itens": [{"label": k, "c": n_, "g": 0, "fmt": f"{n_} vagas"} for k, n_ in sorted(setor_tot.items(), key=lambda kv: -kv[1])[:6]],
                   "texto": "Cruzar setor e tipo divide as vagas em dezenas de células pequenas: <b>qualquer padrão seria acaso</b>. O seguimento fica aqui e em \"O que os dados ainda não sustentam\"."},
                  "vagas por setor", 0, f"Mínimo pro gráfico: {MIN_SETORES} setores com {MIN_SETOR_VAGAS} vagas ou mais.", ["NÃO SUSTENTA", "nao"], [f"{m_set51} setores com {MIN_SETOR_VAGAS} vagas ou mais", f"{MIN_SETORES} setores"])
             if m_set51 < MIN_SETORES else
             view("1", "Qual setor pede qual tipo?", f"{m_set51} setores têm {MIN_SETOR_VAGAS} vagas ou mais.", "p5_1", "tabela", {}, "vagas por setor e tipo", 0, "", ["DESCRITIVO", "desc"])),
            view("2", "O tipo muda a referência salarial?", a_52, "p5_2", "hb", {"rows": ref_t, "max": max([x["v"] for x in ref_t] + [1]), "moeda": 1}, "referência salarial pesquisada · mediana por tipo", 0,
                 f"Só tipos com {MIN_N_REF} vagas ou mais com referência. O tipo é a dimensão dominante entre {{dim:as seis de conteúdo}}. A referência é a pesquisada pro cargo e a cidade, nunca o que a vaga paga.", ["DESCRITIVO", "desc"]),
        ],
    })

    # ================= P6 · o gestor-unicórnio =================
    r60 = R["p6_0"]
    am = {r[0]: dict(zip(r60["cols"], r)) for r in r60["rows"]}
    ac, ag = am.get("coordenador"), am.get("gerente")
    seis_c, seis_g = (ac["seis_dimensoes"] if ac else 0), (ag["seis_dimensoes"] if ag else 0)
    seis_t = seis_c + seis_g
    p_seis = fisher(seis_c, seis_g)
    r61 = R["p6_1"]
    dist = [{"label": f"{r[0]} dimensões", "c": r[1], "g": r[2]} for r in r61["rows"]]
    p_dist = [fisher(x["c"], x["g"]) for x in dist]
    r62 = R["p6_2"]
    amp = {(r[0], bool(r[1])): (r[2], r[3]) for r in r62["rows"]}
    amp_rows = [{"label": f"{NOME_NIVEL[niv].capitalize()} · {'as seis dimensões' if flag else 'menos de seis'}", "v": amp[(niv, flag)][1], "n": amp[(niv, flag)][0], "cor": "c" if niv == "coordenador" else "g",
                 "op": 1 if flag else .5, "txt": f"{reais(amp[(niv, flag)][1])} · {amp[(niv, flag)][0]} vagas"}
                for niv in ("coordenador", "gerente") for flag in (True, False) if (niv, flag) in amp and amp[(niv, flag)][0] >= MIN_N_REF]
    metade = abs(seis_t / n_tot - 0.5) <= 0.05 if n_tot else False
    titulo6 = "Metade das vagas pede" if metade else f"{pt(100 * seis_t / n_tot, 0) if n_tot else 0}% das vagas pedem"
    perc = lambda a, b: pt(100 * a / b, 0) if b else "0"  # noqa: E731
    cond_p6 = bool(ac and ag and seis_g / ng > seis_c / nc)
    c5_6 = sum(x["c"] for x in dist if int(x["label"].split()[0]) >= 5)
    g5_6 = sum(x["g"] for x in dist if int(x["label"].split()[0]) >= 5)
    if len(amp_rows) == 4:
        a_62 = (f"Na gerência, a referência é {reais(amp[('gerente', True)][1])} nas vagas que pedem as seis dimensões e {reais(amp[('gerente', False)][1])} nas outras; "
                f"na coordenação, {reais(amp[('coordenador', True)][1])} e {reais(amp[('coordenador', False)][1])}.")
    else:
        a_62 = "Poucas vagas com referência por grupo pra comparar."
    cards.append({
        "id": "p6", "rail": "P6 · O gestor-unicórnio", "sumario": "O gestor-unicórnio existe? Quão ampla é a vaga?", "label": "O gestor-unicórnio",
        "h2": [f"{titulo6}", "as seis dimensões", "de uma vez."], "virou": not cond_p6,
        "pergunta": "O gestor-unicórnio existe? Quão ampla é a vaga?",
        "lede": f"{{dim:Seis dimensões de conteúdo}}: gente, estratégia, engenharia, analytics, IA e governança. {seis_t} das {n_tot} vagas pedem as seis. "
                f"Na gerência o anúncio é mais amplo ({perc(seis_g, ng)}% contra {perc(seis_c, nc)}%), mas o tamanho é parecido: {pt(ag['itens_mediana'], 0) if ag else 0} itens por vaga na mediana contra {pt(ac['itens_mediana'], 0) if ac else 0}.",
        "tk": [
            {"r": "Pedem {dim:as seis dimensões}", "t": f"{seis_t} de {n_tot} vagas", "n": f"{perc(seis_t, n_tot)}% das vagas da comparação"},
            {"r": "Coordenação", "t": f"{perc(seis_c, nc)}% · {seis_c} de {nc}", "n": f"{pp(p_seis)} · {selo_p(p_seis)[0].lower()}"},
            {"r": "Gerência", "t": f"{perc(seis_g, ng)}% · {seis_g} de {ng}", "n": "pedem as seis dimensões"},
            {"r": "Itens por vaga (mediana)", "t": f"{pt(ac['itens_mediana'], 0) if ac else 0} · {pt(ag['itens_mediana'], 0) if ag else 0}", "n": f"de {min(ac['itens_min'], ag['itens_min']) if ac and ag else 0} a {max(ac['itens_max'], ag['itens_max']) if ac and ag else 0} itens"},
        ],
        "views": [
            view("P6", "O mapa", f"{seis_t} de {n_tot} vagas cobrem as seis dimensões de conteúdo; a diferença entre os níveis é {selo_p(p_seis)[0].lower()} ({pp(p_seis)}).", "p6_0", "big",
                 {"blocos": [{"v": f"{perc(seis_c, nc)}%", "cor": "c", "rot": f"coordenação · {seis_c} de {nc} pedem as seis"}, {"v": f"{perc(seis_g, ng)}%", "cor": "g", "rot": f"gerência · {seis_g} de {ng} pedem as seis"}],
                  "blocos2": [{"v": pt(ac["itens_mediana"], 0) if ac else "0", "rot": "itens por vaga, mediana, coordenação"}, {"v": pt(ag["itens_mediana"], 0) if ag else "0", "rot": "itens por vaga, mediana, gerência"}]},
                 "vagas que pedem as seis dimensões", 0,
                 "{dim:Dimensões de conteúdo}: gestão de pessoas; estratégia, negócio e gestão; engenharia e plataforma; analytics e BI; IA e ciência de dados; governança, qualidade e segurança. Fora: formação e comportamento.", melhor_selo([p_seis])),
            view("1", "Quantas dimensões uma vaga pede, por nível?", f"A maior parte pede cinco ou seis: {perc(c5_6, nc)}% das vagas de coordenação e {perc(g5_6, ng)}% das de gerência.", "p6_1", "grupos", dist, "vagas por número de dimensões de conteúdo", 1, base_nota + " Conta as {dim:dimensões de conteúdo} (seis), sem formação e comportamento.", ["DESCRITIVO", "desc"]),
            view("2", "Vaga mais ampla paga mais?", a_62, "p6_2", "hb", {"rows": amp_rows, "max": max([x["v"] for x in amp_rows] + [1]), "moeda": 1}, "referência salarial pesquisada · mediana por grupo", 0,
                 f"Só grupos com {MIN_N_REF} vagas ou mais com referência. Grupos: vagas que pedem {{dim:as seis dimensões}} × as outras. A referência é a pesquisada pro cargo e a cidade, nunca o que a vaga paga.", ["DESCRITIVO", "desc"]),
        ],
    })

    for card in cards:
        card["tk"] = [t for t in card["tk"] if t]
    return cards


# ---------- HTML ----------

def html_sumario(cards: list[dict]) -> str:
    li = [f'<li><a href="#{c["id"]}"><span>{c["id"].upper()}</span><span>{esc(c["sumario"])}</span></a></li>' for c in cards]
    li.append('<li><a href="#ns"><span>—</span><span>O que os dados ainda não sustentam</span></a></li>')
    return "\n        ".join(li)


def html_cards(cards: list[dict]) -> str:
    out = []
    for c in cards:
        v0 = c["views"][0]
        h2 = "|".join(esc(s) for s in c["h2"][:-1]) + "|<em>" + esc(c["h2"][-1]) + "</em>"
        aviso = ('<div class="banner"><span class="dot"></span><span><b>Não se sustenta nesta publicação.</b> A direção que o título afirma mudou com o dado novo; '
                 'o texto espera revisão. O gráfico abaixo mostra o dado de hoje.</span></div>') if c["virou"] else ""
        tk = "".join(f'<div><span class="mono">{marca(esc(t["r"]))}</span><b>{esc(t["t"])}</b><span class="n">{t["n"]}</span></div>' for t in c["tk"])
        lis = []
        for i, vw in enumerate(c["views"]):
            selo = f'<span class="ss"><span class="selo2 {esc(vw["selo"][1])}">{esc(vw["selo"][0])}</span></span>' if vw["selo"] else ""
            lis.append(f'<li><button type="button" class="nqb{" on" if i == 0 else ""}" aria-pressed="{"true" if i == 0 else "false"}" data-i="{i}">'
                       f'<span class="k">{"·" if i == 0 else vw["k"]}</span><span class="qq">{esc(vw["q"])}</span><span class="aa">{esc(vw["a"])}</span>{selo}</button></li>')
        pid = c["id"]
        out.append(f'''<section class="achado{" virou" if c["virou"] else ""}" id="{pid}" data-cap="ana" data-rail="{esc(c["rail"])}" data-p="{pid}">
  <div class="label mono rv"><span class="dot"></span><span class="num">01 · Análises · {pid.upper()}</span> · {esc(c["label"])}</div>
  <h2 data-split>{h2}</h2>
  {aviso}
  <p class="lede rv"><b>"{esc(c["pergunta"])}"</b> {marca(c["lede"])}</p>
  <div class="tk rv">{tk}</div>
  <div class="card rv pq">
    <div class="pg">
      <div class="nq"><h3>Próximas perguntas</h3><ol>{"".join(lis)}</ol></div>
      <div class="view">
        <div class="vh"><span class="tag mono vtag">{esc(v0["tag"])}</span><span class="mono vfile">consultas/{v0["f"]}.sql</span></div>
        <div class="leg"></div>
        <div class="chart" id="c-{pid}"></div>
        <p class="note vnote">{marca(esc(v0["nota"]))}</p>
        <details class="q-sql"><summary class="pill mono">Consulta</summary></details>
      </div>
    </div>
  </div>
</section>
''')
    return "\n".join(out)


def html_ns_tabela(cards: list[dict]) -> str:
    linhas = []
    for c in cards:
        for vw in c["views"]:
            if vw.get("ns"):
                linhas.append(f'<tr><td style="color:var(--bone)">{c["id"].upper()}·{vw["k"]} · {esc(vw["q"])}</td><td>{esc(vw["ns"][0])}</td><td>{esc(vw["ns"][1])}</td></tr>')
    if not linhas:
        return ""
    return ('<div class="card rv"><span class="tag mono">Seguimentos que a amostra ainda não responde</span>'
            '<table class="res nsres"><tr><th>pergunta</th><th>por quê</th><th>volta quando</th></tr>' + "".join(linhas) + '</table>'
            '<p class="note">Cada um tem a consulta pronta em <code>consultas/</code>: quando o dado chegar ao mínimo, o gráfico aparece sozinho, pela condição da própria consulta.</p></div>')
