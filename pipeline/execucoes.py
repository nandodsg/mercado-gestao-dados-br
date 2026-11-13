"""Seção 4.3 "As execuções": o retrato do último `dbt build` e das execuções do GitHub Actions deste repositório.

Nada é digitado à mão. Tudo sai do build que está gerando a página (decisão D53: retrato gerado na publicação, com link pro histórico
ao vivo no GitHub):

  (a) testes     dbt/target/run_results.json + dbt/target/manifest.json (a tabela de cada teste) do mesmo `dbt build`;
                 a frase de cada teste vem de `frases_testes.py` (genéricos pelo tipo; escritos à mão por dicionário, e a falta de frase
                 quebra o build); o que um aviso achou vem da consulta compilada do próprio teste, rodada no DuckDB do build.
  (b) execuções  API do GitHub Actions deste repositório (`GITHUB_TOKEN` com `actions: read`, sem segredo novo) e `git log` de
                 data/manifest.json (uma publicação do dado por commit; o checkout precisa do histórico: `fetch-depth: 0`).
  fechado        bloco `execucoes_privadas` do data/manifest.json (só contagens acumuladas, escritas pelo exportador).

Saída: HTML pronto pros marcadores do modelo e o mesmo retrato em dados/execucoes.json.
"""
from __future__ import annotations

import html
import json
import os
import re
import statistics
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

import frases_testes as FT

RAIZ = Path(__file__).resolve().parents[1]
BRASILIA = timezone(timedelta(hours=-3))  # Brasil sem horário de verão
FLUXOS = {"pipeline.yml": "testes", "pages.yml": "página"}
ESTA = "esta execução"
LOG_ULTIMAS = 8  # esta execução + as 7 concluídas mais recentes (E7)
LOG_TETO = 30  # nos filtros "Falhas" e "Dado novo", o resto fica no link do GitHub

esc = html.escape


def fr(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def seg(x: float, casas: int = 2) -> str:
    return f"{x:.{casas}f}".replace(".", ",") + " s"


def brasilia(dt: datetime) -> datetime:
    return dt.astimezone(BRASILIA)


# ------------------------------------------------------------------------------------------------------------ (a) testes

def _fr_tempo(x: float) -> str:
    return seg(x, 2 if x < 10 else 1)


def testes(c, rr: dict, nos: dict, manifest: dict) -> dict:
    """Lê o run_results.json do build e devolve o painel (a). `c` é a conexão DuckDB do build (só leitura)."""
    resultados = rr["results"]
    por_status: dict[str, int] = {}
    n_seeds = n_modelos = n_testes = 0
    for r in resultados:
        tipo = r["unique_id"].split(".")[0]
        n_seeds += tipo == "seed"
        n_modelos += tipo == "model"
        n_testes += tipo == "test"
        por_status[r["status"]] = por_status.get(r["status"], 0) + 1
    avisos = por_status.get("warn", 0)
    erros = por_status.get("fail", 0) + por_status.get("error", 0)
    ok = len(resultados) - avisos - erros - por_status.get("skipped", 0)

    grupos: dict[str, list[dict]] = {t: [] for t in FT.TABELAS}
    faltam: list[str] = []
    for r in resultados:
        uid = r["unique_id"]
        if not uid.startswith("test."):
            continue
        no = nos[uid]
        meta = no.get("test_metadata")
        nome = no["name"]
        if meta is None:  # escrito à mão (dbt/tests/*.sql)
            ent = FT.ESCRITOS_A_MAO.get(nome)
            if ent is None:
                faltam.append(f"teste escrito à mão sem frase: {nome} (pipeline/frases_testes.py, ESCRITOS_A_MAO)")
                continue
            tabela, frase, aviso = ent["tabela"], ent["frase"], ent.get("aviso")
            achou_fn = ent.get("achou")
        else:
            attached = no.get("attached_node") or ""
            tabela = attached.split(".")[-1]
            kw = {k: v for k, v in meta["kwargs"].items() if k != "model"}
            f = FT.frase_generica(meta["name"], no.get("column_name"), kw)
            if f is None:
                faltam.append(f"teste genérico sem frase: {nome} (tipo {meta['name']}; pipeline/frases_testes.py, frase_generica)")
                continue
            frase, aviso, achou_fn = f, None, None
        if tabela not in grupos:
            faltam.append(f"tabela sem nome de leitor: {tabela} (teste {nome}; pipeline/frases_testes.py, TABELAS)")
            continue
        item = {"nome": nome, "tabela": tabela, "frase": frase, "status": r["status"], "tempo": r["execution_time"], "falhas": r.get("failures") or 0}
        if r["status"] != "pass":
            item["aviso"] = aviso or FT.AVISO_PADRAO
            item["achou"] = ""
            if achou_fn is not None and r.get("compiled_code"):
                cur = c.execute(r["compiled_code"])
                cols = [d[0] for d in cur.description]
                item["achou"] = achou_fn([dict(zip(cols, linha)) for linha in cur.fetchall()])
            if not item["achou"]:
                item["achou"] = f"<b>{fr(int(item['falhas']))}</b> {'linha' if item['falhas'] == 1 else 'linhas'} fora do esperado."
        grupos[tabela].append(item)
    if faltam:
        raise SystemExit("FALHA (execuções): " + "; ".join(faltam))
    return {
        "ok": ok, "avisos": avisos, "erros": erros, "seeds": n_seeds, "modelos": n_modelos, "testes": n_testes,
        "duracao": rr["elapsed_time"],
        "grupos": [{"tabela": t, "nome": FT.TABELAS[t], "etapa": _etapa_da(t), "testes": sorted(ts, key=lambda x: (x["status"] == "pass", x["nome"]))}
                   for t, ts in grupos.items() if ts],
        "avisos_lista": [dict(i, nome_tabela=FT.TABELAS[g]) for g, ts in grupos.items() for i in ts if i["status"] != "pass"],
    }


def _etapa_da(tabela: str) -> str:
    if tabela.startswith("stg_"):
        return FT.ETAPAS["staging"]
    if tabela.startswith("mart_"):
        return FT.ETAPAS["marts"]
    return FT.ETAPAS["seed"]


# ------------------------------------------------------------------------------------------------------ (b) execuções

def _repo() -> str:
    r = os.environ.get("GITHUB_REPOSITORY")
    if r:
        return r
    try:
        url = subprocess.run(["git", "remote", "get-url", "origin"], cwd=RAIZ, capture_output=True, text=True, check=True).stdout.strip()
        m = re.search(r"github\.com[:/]([^/]+/[^/.]+)", url)
        if m:
            return m.group(1)
    except Exception:  # noqa: BLE001
        pass
    return "nandodsg/mercado-gestao-dados-br"


def _token() -> str | None:
    t = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if t or os.environ.get("GITHUB_ACTIONS"):
        return t
    try:  # rodando na máquina de quem publica: usa o login do `gh`, se houver
        return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=10).stdout.strip() or None
    except Exception:  # noqa: BLE001
        return None


def _api(caminho: str, token: str | None) -> dict:
    req = urllib.request.Request(f"https://api.github.com{caminho}", headers={
        "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "mercado-gestao-dados-br-gerador",
        **({"Authorization": f"Bearer {token}"} if token else {}),
    })
    ultimo: Exception | None = None
    for tentativa in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 404):  # não adianta repetir: token sem `actions: read`, limite ou repositório errado
                raise SystemExit(f"FALHA (execuções): a API do GitHub recusou {caminho} ({e.code}); o fluxo precisa de `actions: read`") from e
            ultimo = e
        except (urllib.error.URLError, TimeoutError) as e:
            ultimo = e
        time.sleep(2 * (tentativa + 1))
    raise SystemExit(f"FALHA (execuções): a API do GitHub não respondeu em {caminho}: {ultimo}")


def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _publicacoes() -> list[str]:
    """Commits que mudaram data/manifest.json (um por publicação do dado), do mais novo ao mais antigo."""
    out = subprocess.run(["git", "log", "--format=%H", "--", "data/manifest.json"], cwd=RAIZ, capture_output=True, text=True, check=True).stdout
    return out.split()


def _vagas_no_commit(sha: str) -> int | None:
    r = subprocess.run(["git", "show", f"{sha}:data/manifest.json"], cwd=RAIZ, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        return int(json.loads(r.stdout)["contagens"]["vagas"])
    except (KeyError, ValueError, TypeError):
        return None


PASSO = (("Contrato v1", "contrato do dado"), ("dbt build", "dbt build"), ("Gerar a página", "geração da página"),
         ("Gerador da página", "geração da página"), ("Consultas de", "conferência das consultas"), ("Python compila", "compilação do Python"),
         ("Instalar", "instalação das dependências"), ("Regerar", "análise dos achados"), ("Commitar", "commit dos achados"))


def _passo(nome: str) -> str:
    for inicio, curto in PASSO:
        if nome.startswith(inicio):
            return curto
    return nome


def _execucoes(token: str | None) -> tuple[list[dict], dict | None]:
    repo = _repo()
    brutas: list[dict] = []
    pagina = 1
    while True:
        r = _api(f"/repos/{repo}/actions/runs?per_page=100&page={pagina}", token)
        brutas += r["workflow_runs"]
        if len(brutas) >= r["total_count"] or not r["workflow_runs"]:
            break
        pagina += 1
    publicacoes = _publicacoes()
    dado = set(publicacoes)
    run_id = os.environ.get("GITHUB_RUN_ID")
    brutas = [b for b in brutas if Path(b["path"]).name in FLUXOS]
    brutas.sort(key=lambda b: (b["run_started_at"] or b["created_at"], b["id"]))
    esta_bruta = next((b for b in brutas if str(b["id"]) == run_id), None) if run_id else None
    if not run_id:  # fora do GitHub Actions: a página mais recente faz o papel de "esta execução"
        esta_bruta = next((b for b in reversed(brutas) if FLUXOS[Path(b["path"]).name] == "página"), None)

    linhas: list[dict] = []
    for b in brutas:
        eh_esta = esta_bruta is not None and b["id"] == esta_bruta["id"]
        if not eh_esta and b["status"] != "completed":
            continue  # ainda rodando (a outra metade do mesmo push): não conta
        fluxo = FLUXOS[Path(b["path"]).name]
        evento = b["event"]
        gatilho = "agendado" if evento == "schedule" else "manual" if evento == "workflow_dispatch" else \
            "dado novo" if b["head_sha"] in dado else "código"
        ini = _dt(b["run_started_at"] or b["created_at"])
        item = {
            "id": b["id"], "quando": brasilia(ini), "fluxo": fluxo, "gatilho": gatilho, "url": b["html_url"], "sha": b["head_sha"][:7],
            "esta": eh_esta, "segundos": 0, "resultado": "", "ok": False, "publicou": None, "vagas": _vagas_no_commit(b["head_sha"]) if gatilho == "dado novo" else None,
        }
        if eh_esta:
            linhas.append(item)
            continue
        item["segundos"] = max(0, round((_dt(b["updated_at"]) - ini).total_seconds()))
        conclusao = b["conclusion"]
        item["ok"] = conclusao == "success"
        item["conclusao"] = conclusao
        if conclusao == "success" and fluxo == "testes":
            item["resultado"] = "passou" + (f" · {fr(item['vagas'])} vagas" if item["vagas"] else "")
        elif conclusao == "success":  # página: o passo de deploy rodou?
            jobs = _api(f"/repos/{repo}/actions/runs/{b['id']}/jobs?per_page=100", token)["jobs"]
            passos = [p for j in jobs for p in j.get("steps", [])]
            item["publicou"] = any("deploy-pages" in p["name"] and p["conclusion"] == "success" for p in passos)
            item["resultado"] = "publicou a página" if item["publicou"] else "rodou sem publicar"
        elif conclusao == "failure":
            jobs = _api(f"/repos/{repo}/actions/runs/{b['id']}/jobs?per_page=100", token)["jobs"]
            falho = next((p["name"] for j in jobs for p in j.get("steps", []) if p["conclusion"] == "failure"), None)
            item["resultado"] = f"falhou em: {_passo(falho)}" if falho else "não abriu: erro no arquivo do fluxo"
        else:
            item["resultado"] = "cancelada" if conclusao == "cancelled" else (conclusao or "sem resultado")
        linhas.append(item)
    esta = next((i for i in linhas if i["esta"]), None)
    if esta is None and run_id:  # a API ainda não listou a execução em curso: monta do ambiente
        evento = os.environ.get("GITHUB_EVENT_NAME", "push")
        sha = os.environ.get("GITHUB_SHA", "")
        gatilho = "agendado" if evento == "schedule" else "manual" if evento == "workflow_dispatch" else "dado novo" if sha in dado else "código"
        esta = {"id": int(run_id), "quando": datetime.now(BRASILIA), "fluxo": "página", "gatilho": gatilho, "esta": True,
                "url": f"https://github.com/{repo}/actions/runs/{run_id}", "sha": sha[:7], "segundos": 0, "resultado": "", "ok": False, "publicou": None, "vagas": None}
        linhas.append(esta)
    return linhas, {"repo": repo, "publicacoes": len(publicacoes)}


def execucoes(token: str | None = None) -> dict:
    token = token if token is not None else _token()
    linhas, info = _execucoes(token)
    concluidas = [l for l in linhas if not l["esta"]]
    esta = next((l for l in linhas if l["esta"]), None)
    # a mediana é das execuções que passaram: uma falha que nem abriu (0 s) puxaria o número pra baixo sem dizer nada do tempo real
    med = lambda fluxo: round(statistics.median([l["segundos"] for l in concluidas if l["fluxo"] == fluxo and l["ok"]] or [0]))  # noqa: E731
    return {
        "repo": info["repo"], "publicacoes": info["publicacoes"], "concluidas": concluidas, "esta": esta,
        "n": len(concluidas), "n_ok": sum(1 for l in concluidas if l["ok"]), "mediana_testes": med("testes"), "mediana_pagina": med("página"),
        "desde": concluidas[0]["quando"] if concluidas else None,
    }


# ------------------------------------------------------------------------------------------------------------- HTML

def _hora(dt: datetime) -> str:
    return dt.strftime("%d/%m %H:%M")


def _linha_log(l: dict, repo: str) -> str:
    if l["esta"]:
        return (f'<div class="row esta"><span>{_hora(l["quando"])}</span><span>página</span><span>{l["gatilho"]}</span><span>—</span>'
                f'<span class="res">esta execução: gerando esta página</span><a href="{esc(l["url"])}" aria-label="Abrir esta execução no GitHub">↗</a>'
                f'<span class="meta">página · {l["gatilho"]}</span></div>')
    falha = not l["ok"]
    sem = l["fluxo"] == "página" and l["publicou"] is False
    cls_res = "res" + ("" if falha else " exe-dim" if sem else " exe-ok")
    return (f'<div class="row{" fail" if falha else ""}"><span>{_hora(l["quando"])}</span><span>{l["fluxo"]}</span><span>{l["gatilho"]}</span>'
            f'<span>{l["segundos"]} s</span><span class="{cls_res}">{esc(l["resultado"])}</span>'
            f'<a href="{esc(l["url"])}" title="Abrir no GitHub" aria-label="Abrir a execução de {_hora(l["quando"])} no GitHub">↗</a>'
            f'<span class="meta">{l["fluxo"]} · {l["gatilho"]} · {l["segundos"]} s</span></div>')


_CAB = '<div class="row hd"><span>quando</span><span>fluxo</span><span>gatilho</span><span>tempo</span><span>resultado</span><span></span></div>'


def _faixa(ex: dict) -> str:
    quadros = []
    for l in ex["concluidas"] + ([ex["esta"]] if ex["esta"] else []):
        cls = []
        if l["esta"]:
            cls.append("esta")
            titulo = f"{_hora(l['quando'])} · página · esta execução"
        else:
            if not l["ok"]:
                cls.append("f")
            elif l["fluxo"] == "página" and l["publicou"] is False:
                cls.append("s")
            if l["gatilho"] == "dado novo" and l["fluxo"] == "testes":
                cls.append("pub")
            titulo = f"{_hora(l['quando'])} · {l['fluxo']} · {l['gatilho']} · {l['resultado']}"
        quadros.append(f'<i{" class=" + chr(34) + " ".join(cls) + chr(34) if cls else ""} title="{esc(titulo)}"></i>')
    return "".join(quadros)


def html_painel_a(a: dict, carimbo: dict) -> str:
    def t_html(i: dict, aviso: bool = False) -> str:
        ic = "!" if i["status"] != "pass" else "✓"
        cl = "exe-warn" if i["status"] == "warn" else "exe-err" if i["status"] != "pass" else "exe-ok"
        return (f'<div class="t"><span class="{cl}">{ic}</span><span class="fr">{i["frase"]}</span>'
                f'<span class="tm">{_fr_tempo(i["tempo"])}</span><span class="nm">{esc(i["nome"])}</span></div>')

    avisos = "".join(
        f'<div class="aviso-t"><span class="ic">!</span><span class="fr">{i["frase"][:1].upper() + i["frase"][1:]}.</span>'
        f'<span class="tm">{_fr_tempo(i["tempo"])}</span>'
        f'<span class="ac">{i["achou"]} {esc(i["aviso"])}</span>'
        f'<span class="nm">{esc(i["nome"])} · {esc(i["nome_tabela"])} ({esc(i["tabela"])})</span></div>'
        for i in a["avisos_lista"])
    if not avisos:
        avisos = '<div class="vazio">Nenhum aviso neste build: todos os testes passaram.</div>'
    corpo, etapa = [], None
    for g in a["grupos"]:
        if g["etapa"] != etapa:
            corpo.append(f'<div class="etapa">{esc(g["etapa"])}</div>')
            etapa = g["etapa"]
        n_av = sum(1 for t in g["testes"] if t["status"] != "pass")
        cont = f'{len(g["testes"])} {"teste" if len(g["testes"]) == 1 else "testes"}'
        corpo.append(
            f'<details class="grupo"><summary><span class="car">›</span><span class="gn">{esc(g["nome"])}<code>{esc(g["tabela"])}</code></span>'
            f'<span class="gc">{cont}{f"<span class=exe-warn>· {n_av} aviso</span>" if n_av else ""}</span></summary>'
            f'<div class="tests">{"".join(t_html(t) for t in g["testes"])}</div></details>')
    n_av = a["avisos"] + a["erros"]
    return (
        '<div class="ctl" id="exe-a">'
        f'<div class="head"><b>(a) Último dbt build</b><span>{carimbo["hora"]} · commit {esc(carimbo["sha"])} · {seg(a["duracao"], 1)}</span></div>'
        f'<div class="resumo"><span class="big exe-ok">{fr(a["ok"])}<small>ok</small></span>'
        f'<span class="big {"exe-warn" if a["avisos"] else "exe-dim"}">{a["avisos"]}<small>{"aviso" if a["avisos"] == 1 else "avisos"}</small></span>'
        f'<span class="big {"exe-err" if a["erros"] else "exe-dim"}">{a["erros"]}<small>{"erro" if a["erros"] == 1 else "erros"}</small></span>'
        f'<span class="exe-dim">{a["seeds"]} listas de referência · {a["modelos"]} modelos · {a["testes"]} testes</span></div>'
        '<div class="filtros exe-filtros" hidden>'
        f'<button class="pill mono sm on" type="button" data-fa="avisos">Avisos · {n_av}</button>'
        f'<button class="pill mono sm" type="button" data-fa="todos">Todos os testes · {a["testes"]}</button></div>'
        f'<div class="exe-pane on" data-pane-a="avisos">{avisos}</div>'
        f'<div class="exe-pane" data-pane-a="todos">{"".join(corpo)}</div>'
        '<div class="rodape"><span class="dot"></span><span><b>Erro não aparece aqui, por construção:</b> se um teste falha, a página não é refeita '
        'e a versão anterior continua no ar. As falhas ficam no histórico, logo abaixo.</span></div></div>')


def html_painel_b(ex: dict) -> str:
    repo = ex["repo"]
    todas = f"https://github.com/{repo}/actions"
    ult = ([ex["esta"]] if ex["esta"] else []) + list(reversed(ex["concluidas"]))[: LOG_ULTIMAS - (1 if ex["esta"] else 0)]
    falhas = [l for l in reversed(ex["concluidas"]) if not l["ok"]]
    dado = [l for l in reversed(ex["concluidas"]) if l["gatilho"] == "dado novo" and l["fluxo"] == "testes"]

    def pane(nome: str, linhas: list[dict], rodape: str, vazio: str, ligado: bool) -> str:
        mostra = linhas[:LOG_TETO]
        corpo = _CAB + "".join(_linha_log(l, repo) for l in mostra) if mostra else f'<div class="mais"><span>{esc(vazio)}</span></div>'
        mais = len(linhas) - len(mostra)
        extra = f" · mais {fr(mais)} no GitHub" if mais > 0 else ""
        return (f'<div class="exe-pane{" on" if ligado else ""}" data-pane-b="{nome}"><div class="log">{corpo}'
                f'<div class="mais"><span>{esc(rodape)}{extra}</span><a class="pill mono sm" href="{esc(todas)}">Todas no GitHub ↗</a></div></div></div>')

    resto = ex["n"] - (len(ult) - (1 if ex["esta"] else 0))
    desde = ex["desde"].strftime("%d/%m/%Y") if ex["desde"] else "—"
    return (
        '<div class="ctl" id="exe-b">'
        f'<div class="head"><b>(b) Execuções</b><span>desde {desde} · GitHub Actions deste repositório</span></div>'
        '<div class="kpis">'
        f'<div><b>{fr(ex["n"])}</b><span>execuções</span></div><div><b>{fr(ex["n_ok"])}</b><span>com sucesso</span></div>'
        f'<div><b>{ex["mediana_testes"]} s<small class="exe-pg"> · {ex["mediana_pagina"]} s</small></b>'
        '<span><span class="exe-pg">mediana · testes · página</span><span class="exe-so-t">mediana · testes</span></span></div>'
        f'<div><b>{fr(ex["publicacoes"])}</b><span>publicações do dado</span></div></div>'
        f'<div class="strip" role="img" aria-label="Uma execução por quadrado, da primeira à mais recente">{_faixa(ex)}</div>'
        '<div class="legenda"><span><i style="background:var(--neon)"></i>passou</span><span><i style="background:var(--ember)"></i>falhou</span>'
        '<span><i style="background:var(--muted)"></i>rodou sem publicar</span><span><i style="border:1.5px dashed var(--c-arq)"></i>esta execução</span>'
        '<span>• publicação do dado</span></div>'
        '<div class="filtros exe-filtros" hidden>'
        f'<button class="pill mono sm on" type="button" data-fb="ult">Últimas · {len(ult)}</button>'
        f'<button class="pill mono sm" type="button" data-fb="falhas">Falhas · {len(falhas)}</button>'
        f'<button class="pill mono sm" type="button" data-fb="dado">Dado novo · {len(dado)}</button></div>'
        + pane("ult", ult, f"mais {fr(resto)} execuções" if resto > 0 else "todas as execuções estão aqui", "", True)
        + pane("falhas", falhas, f"{len(falhas)} {'falha' if len(falhas) == 1 else 'falhas'} nas {fr(ex['n'])} execuções desde {desde[:5]}",
               f"Nenhuma falha nas {fr(ex['n'])} execuções desde {desde[:5]}.", False)
        + pane("dado", dado, f"{len(dado)} publicações do dado: uma por commit em data/", "Nenhuma publicação do dado ainda.", False)
        + '</div>')


def html_fechado(bloco: dict) -> str:
    cl = bloco["classificacao"]
    return (
        '<div class="fechado">'
        '<div class="t1"><b>Do lado fechado</b>só contagens · até a última publicação do dado · o que acontece antes do commit</div>'
        f'<div class="n"><b>{fr(cl["rodadas"])}</b><span class="lab">{"rodada" if cl["rodadas"] == 1 else "rodadas"} da classificação</span>'
        f'<div class="quebra"><span class="exe-ok">{fr(cl["concluidas"])} {"concluída" if cl["concluidas"] == 1 else "concluídas"}</span> · '
        f'<span class="exe-err">{fr(cl["interrompidas"])} {"interrompida" if cl["interrompidas"] == 1 else "interrompidas"}</span></div>'
        '<p>Cada rodada pega as linhas que ainda não têm rótulo. A interrompida não grava nada, e a seguinte pega as mesmas linhas.</p></div>'
        f'<div class="n"><b>{fr(bloco["verificacoes_sem_mudanca"])}</b><span class="lab">'
        f'{"verificação semanal sem mudança" if bloco["verificacoes_sem_mudanca"] == 1 else "verificações semanais sem mudança"}</span>'
        '<p>Toda semana o exportador compara a impressão digital de cada arquivo com a que está no repositório. Se nada mudou, não há commit, '
        'nem execução aqui em cima.</p></div></div>')


def montar(c, manifest: dict, token: str | None = None) -> dict:
    """Tudo da 4.3: marcadores do modelo + o retrato em JSON."""
    rr = json.loads((RAIZ / "dbt" / "target" / "run_results.json").read_text(encoding="utf-8"))
    nos = json.loads((RAIZ / "dbt" / "target" / "manifest.json").read_text(encoding="utf-8"))["nodes"]
    a = testes(c, rr, nos, manifest)
    ex = execucoes(token)
    sha = os.environ.get("GITHUB_SHA") or subprocess.run(["git", "rev-parse", "HEAD"], cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    agora = datetime.now(BRASILIA)
    carimbo = {"hora": agora.strftime("%d/%m/%Y, %H:%M"), "sha": sha[:7], "repo": ex["repo"]}
    bloco = manifest.get("execucoes_privadas")
    assert bloco, "o manifest não traz execucoes_privadas (check_data.py deveria ter barrado)"
    retrato = {
        "carimbo": carimbo,
        "testes": {k: v for k, v in a.items() if k not in ("avisos_lista",)},
        "execucoes": {"n": ex["n"], "n_ok": ex["n_ok"], "mediana_testes_s": ex["mediana_testes"], "mediana_pagina_s": ex["mediana_pagina"],
                      "publicacoes": ex["publicacoes"],
                      "lista": [{"quando": l["quando"].isoformat(), "fluxo": l["fluxo"], "gatilho": l["gatilho"], "segundos": l["segundos"],
                                 "resultado": l["resultado"], "sucesso": l["ok"], "url": l["url"], "esta": l["esta"]}
                                for l in ex["concluidas"] + ([ex["esta"]] if ex["esta"] else [])]},
        "lado_fechado": bloco,
    }
    return {
        "exe_hora": carimbo["hora"], "exe_sha": carimbo["sha"], "exe_repo": ex["repo"],
        "exe_painel_a": html_painel_a(a, carimbo), "exe_painel_b": html_painel_b(ex), "exe_fechado": html_fechado(bloco),
        "retrato": retrato,
    }
