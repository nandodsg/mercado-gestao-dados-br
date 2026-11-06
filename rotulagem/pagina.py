"""Monta a página de desempate de um conjunto de rotulagem: rotulagem/pagina/desempate_<conjunto>.html.

    python rotulagem/pagina.py pratica
    python rotulagem/pagina.py referencia

A página junta os rótulos dos modelos (cada um rotulou sem ver o dos outros). Item que todos marcaram vem marcado e a
pessoa pode tirar; item marcado por só alguns aparece como divergência, com o motivo de cada modelo, e espera a decisão.
`natureza` e `setor` funcionam igual. Peso, anos e ferramentas vêm de regra e aparecem só para leitura. A página não
usa nada de fora (abre do disco), guarda o progresso no navegador e "Salvar CSV" grava um arquivo com uma linha por
decisão e a origem dela: `concordou`, `mudou`, `escolheu_<rotuladores>`, `rejeitou_<rotuladores>` ou `adicionou`.
Salve o CSV em rotulagem/referencia/<conjunto>_revisado.csv.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys

import taxonomia
from common import RAIZ, AMOSTRA, ROTULADORES_GATEWAY, OPUS, SAIDA, ler_json, slug
from rotular import setores

CURTO = {OPUS: "opus", "google/gemini-4-argon": "gemini", "spacexai/grok-4.7": "grok"}
PAGINA = SAIDA.parent / "pagina"


def montar(conjunto: str) -> tuple[dict, int]:
    amostra = ler_json(AMOSTRA / f"{conjunto}.json")
    rotuladores = [m for m in (OPUS, *ROTULADORES_GATEWAY) if (SAIDA / f"{slug(m)}_{conjunto}.json").exists()]
    if len(rotuladores) < 2:
        sys.exit("Faltam rótulos: a página precisa de pelo menos dois rotuladores em rotulagem/saida/.")
    saidas = {m: ler_json(SAIDA / f"{slug(m)}_{conjunto}.json") for m in rotuladores}
    with (RAIZ / "data" / "vagas.csv").open(encoding="utf-8") as f:
        urls = {r["id_publico"]: r["url"] for r in csv.DictReader(f)}
    jd_arquivo = AMOSTRA / "jd_texto.json"
    if not jd_arquivo.exists():
        sys.exit("Falta rotulagem/amostra/jd_texto.json: gere com o exportador (JD inteiro, não versionado).")
    jd = ler_json(jd_arquivo)
    versao = taxonomia.versao()
    for m, s in saidas.items():
        faltam = [v["id_publico"] for v in amostra["vagas"] if v["id_publico"] not in s]
        if faltam:
            sys.exit(f"{m} não rotulou {len(faltam)} vagas do conjunto (ex.: {faltam[0]}).")
        velhas = {r["versao_taxonomia"] for r in s.values()} - {versao}
        if velhas:
            sys.exit(f"{m} rotulou numa versão antiga da taxonomia ({', '.join(velhas)}); a atual é {versao}.")
    dados = {
        "conjunto": conjunto,
        "versao": versao,
        "rotuladores": [{"id": m, "curto": CURTO[m]} for m in rotuladores],
        "naturezas": taxonomia.NATUREZA,
        "setores": setores(),
        "itens": [{k: i[k] for k in ("dimensao", "item", "chave", "definicao", "borda", "exemplos")}
                  for i in taxonomia.itens()],
        "vagas": [{
            "id": v["id_publico"], "nivel": v["nivel"], "empresa": v["empresa"], "cargo": v["cargo"],
            "url": urls.get(v["id_publico"], ""), "jd": jd[v["id_publico"]],
            "linhas": [{
                "ordem": l["ordem"], "texto": l["texto"], "peso": l["peso"], "anos": l["anos"],
                "ferramentas": l["ferramentas"],
                "votos": [next(x for x in saidas[m][v["id_publico"]]["linhas"] if x["ordem"] == l["ordem"])
                          for m in rotuladores],
            } for l in v["linhas"]],
        } for v in amostra["vagas"]],
    }
    divergentes = sum(
        len({i for vt in l["votos"] for i in vt["itens"]}) != len(set.intersection(*(set(vt["itens"]) for vt in l["votos"])))
        for v in dados["vagas"] for l in v["linhas"])
    return dados, divergentes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("conjunto", choices=["pratica", "referencia"])
    args = parser.parse_args()
    dados, divergentes = montar(args.conjunto)
    carga = json.dumps(dados, ensure_ascii=False).replace("</", "<\\/")
    PAGINA.mkdir(exist_ok=True)
    destino = PAGINA / f"desempate_{args.conjunto}.html"
    destino.write_text(HTML.replace("__DADOS__", carga), encoding="utf-8")
    linhas = sum(len(v["linhas"]) for v in dados["vagas"])
    print(f"{len(dados['vagas'])} vagas, {linhas} linhas, {divergentes} com divergência de itens; taxonomia {dados['versao']}")
    print(f"Abra: {destino}")


HTML = r"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Desempate dos rótulos</title>
<style>
:root { --bg:#f7f7f5; --panel:#fff; --text:#1d1d1b; --muted:#6b6b66; --line:#dddcd6; --accent:#2f5bd3; --soft:#e6ecfb;
  --ok:#2e7d4f; --okbg:#edf7f0; --warn:#c2410c; --warnbg:#fff1e8; --chip:#efeee9; }
@media (prefers-color-scheme: dark) { :root { --bg:#161615; --panel:#1f1f1d; --text:#e9e8e3; --muted:#9a9993; --line:#34332f;
  --accent:#8aa8ff; --soft:#26304d; --ok:#6cc893; --okbg:#17291e; --warn:#fb923c; --warnbg:#3a2414; --chip:#2a2a27; } }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--text); font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif; }
header { position:sticky; top:0; z-index:2; display:flex; gap:10px; align-items:center; flex-wrap:wrap; padding:10px 16px;
  background:var(--panel); border-bottom:1px solid var(--line); }
header h1 { font-size:15px; margin:0 8px 0 0; } .grow { flex:1; } .muted { color:var(--muted); }
button, select { font:inherit; color:var(--text); background:var(--panel); border:1px solid var(--line); border-radius:6px; padding:4px 10px; cursor:pointer; }
button:hover { border-color:var(--accent); } button.primary { background:var(--accent); border-color:var(--accent); color:#fff; }
main { display:grid; grid-template-columns:minmax(0,5fr) minmax(0,6fr); gap:16px; padding:12px 16px 40px; }
@media (max-width:1000px) { main { grid-template-columns:1fr; } }
section { background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:12px 16px; min-width:0; }
.linha { display:flex; gap:8px; padding:6px 8px; border-radius:6px; cursor:pointer; border:1px solid transparent; }
.linha:hover { background:var(--soft); } .linha.atual { border-color:var(--accent); background:var(--soft); }
.linha .n { width:26px; flex:none; color:var(--muted); text-align:right; }
.linha .st { width:16px; flex:none; } .st.feito { color:var(--ok); } .st.aberto { color:var(--warn); }
.chip { display:inline-block; font-size:12px; padding:0 7px; margin:2px 4px 0 0; border-radius:10px; background:var(--chip); }
.chip.regra { background:var(--soft); }
h2 { font-size:16px; margin:0 0 8px; } h3 { font-size:13px; margin:14px 0 6px; text-transform:uppercase; letter-spacing:.04em; color:var(--muted); }
.texto { font-size:17px; padding:8px 10px; background:var(--bg); border-radius:6px; margin-bottom:8px; }
.item { border:1px solid var(--line); border-radius:8px; padding:6px 10px; margin-bottom:6px; }
.item.unanime { background:var(--okbg); } .item.dividido { border-color:var(--warn); background:var(--warnbg); }
.item.dividido.decidido { background:var(--panel); border-color:var(--line); }
.item .topo { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
.item .nome { font-weight:600; } .item .dim { font-size:12px; color:var(--muted); }
.mk { font-size:11px; padding:0 5px; border-radius:3px; background:var(--chip); }
.opcoes button.on { background:var(--accent); border-color:var(--accent); color:#fff; }
.opcoes button.nao.on { background:var(--warn); border-color:var(--warn); }
.motivo { font-size:12.5px; margin-top:4px; } .motivo b { font-weight:600; }
details summary { cursor:pointer; color:var(--muted); font-size:12.5px; }
.def { font-size:12.5px; color:var(--muted); margin-top:4px; }
textarea { width:100%; min-height:50px; font:inherit; font-size:13px; color:var(--text); background:var(--bg); border:1px solid var(--line); border-radius:6px; padding:6px; }
#modal { display:none; position:fixed; inset:0; z-index:5; background:rgba(0,0,0,.5); align-items:flex-start; justify-content:center; padding:48px 16px; overflow:auto; }
#modal.aberto { display:flex; }
#modal .caixa { background:var(--panel); border:1px solid var(--line); border-radius:10px; width:min(820px,100%); padding:18px 22px; }
#modal .caixa .topo { display:flex; gap:10px; align-items:baseline; } #modal h2 { margin:0; font-size:18px; }
#modal ol { padding-left:0; list-style:none; margin:12px 0 0; }
#modal li { display:flex; gap:10px; padding:6px 8px; border-radius:6px; }
#modal li .n { width:26px; flex:none; text-align:right; color:var(--muted); }
#modal li.atual { background:var(--soft); outline:1px solid var(--accent); }
#modal li.secao { display:block; margin-top:14px; padding:2px 8px; font-weight:600; color:var(--muted); border-bottom:1px solid var(--line); border-radius:0; text-transform:uppercase; font-size:12px; letter-spacing:.04em; }
#modal li.fora { color:var(--muted); }
kbd { border:1px solid var(--line); border-bottom-width:2px; border-radius:4px; padding:0 4px; font-size:11px; }
</style>
</head>
<body>
<header>
  <h1>Desempate · <span id="conj"></span></h1>
  <span class="muted">taxonomia <span id="versao"></span></span>
  <select id="vaga"></select>
  <button id="verVaga">Ver a vaga <kbd>V</kbd></button>
  <span class="grow"></span>
  <span id="progresso" class="muted"></span>
  <button id="ant">◀</button><button id="prox">▶</button><button id="proxAberta">Próxima em aberto</button>
  <button id="confirmar" class="primary">Confirmar linha ✓ <kbd>Enter</kbd></button>
  <button id="salvar">Salvar CSV</button>
</header>
<main>
  <section><div id="lista"></div></section>
  <section id="painel"></section>
</main>
<div id="modal"><div class="caixa">
  <div class="topo"><h2 id="mTitulo"></h2><span class="grow"></span><button id="mFechar">Fechar <kbd>Esc</kbd></button></div>
  <div class="muted" id="mMeta"></div>
  <ol id="mLinhas"></ol>
</div></div>
<script id="dados" type="application/json">__DADOS__</script>
<script>
const D = JSON.parse(document.getElementById('dados').textContent);
const N = D.rotuladores.length;
const CH = Object.fromEntries(D.itens.map(i => [i.chave, i]));
const STORE = `desempate:${D.conjunto}:${D.versao}`;
let S = {}; try { S = JSON.parse(localStorage.getItem(STORE) || '{}'); } catch (e) { S = {}; }
let v = 0, l = 0;
const persist = () => { try { localStorage.setItem(STORE, JSON.stringify(S)); } catch (e) {} };
const chave = (vg, ln) => `${vg.id}:${ln.ordem}`;
const est = (vg, ln) => S[chave(vg, ln)] || (S[chave(vg, ln)] = { itens: {}, extras: [], confirmada: false });

// votos por item: lista dos rotuladores (índices) que marcaram
function votosItem(ln) {
  const m = {};
  ln.votos.forEach((vt, k) => vt.itens.forEach(c => (m[c] = m[c] || []).push(k)));
  return m;
}
function votosNat(ln) { const m = {}; ln.votos.forEach((vt, k) => (m[vt.natureza] = m[vt.natureza] || []).push(k)); return m; }
function votosSetor(ln) { const m = {}; ln.votos.forEach((vt, k) => { if (vt.setor !== 'nenhum') (m[vt.setor] = m[vt.setor] || []).push(k); }); return m; }
const curto = ks => ks.map(k => D.rotuladores[k].curto).join('+');

// padrão: o que todos marcaram já vem marcado; natureza e setor igual quando todos concordam
function aplicarPadroes() {
  D.vagas.forEach(vg => vg.linhas.forEach(ln => {
    const e = est(vg, ln), vi = votosItem(ln), vn = votosNat(ln), vs = votosSetor(ln);
    Object.entries(vi).forEach(([c, ks]) => { if (ks.length === N && !(c in e.itens)) e.itens[c] = true; });
    const nats = Object.keys(vn); if (nats.length === 1 && !e.natureza) e.natureza = nats[0];
    const sets = Object.keys(vs); if (sets.length === 1 && vs[sets[0]].length === N && !e.setor) e.setor = sets[0];
  }));
}
aplicarPadroes();

function candidatos(vg, ln) { return [...new Set([...Object.keys(votosItem(ln)), ...est(vg, ln).extras])]; }
function itensMarcados(vg, ln) { const e = est(vg, ln); return candidatos(vg, ln).filter(c => e.itens[c]); }
function abertaLinha(vg, ln) {
  const e = est(vg, ln);
  if (!e.natureza) return true;
  if (e.natureza === 'contexto') return false;
  if (candidatos(vg, ln).some(c => !(c in e.itens))) return true;
  if (itensMarcados(vg, ln).includes('experiencia.setor') && !e.setor) return true;
  return false;
}
const feita = (vg, ln) => est(vg, ln).confirmada && !abertaLinha(vg, ln);

function desenharLista() {
  const vg = D.vagas[v], cont = document.getElementById('lista'); cont.innerHTML = '';
  const t = document.createElement('div'); t.className = 'muted';
  t.textContent = `${vg.empresa} — ${vg.cargo} · nível ${vg.nivel} · ${vg.linhas.length} linhas`; cont.appendChild(t);
  vg.linhas.forEach((ln, i) => {
    const d = document.createElement('div'); d.className = 'linha' + (i === l ? ' atual' : '');
    const st = feita(vg, ln) ? ['✓', 'feito'] : abertaLinha(vg, ln) ? ['●', 'aberto'] : ['○', ''];
    d.innerHTML = `<span class="n">${ln.ordem}</span><span class="st ${st[1]}">${st[0]}</span><span></span>`;
    d.lastChild.textContent = ln.texto;
    d.onclick = () => { l = i; desenhar(); };
    cont.appendChild(d);
  });
}

function chipsRegra(ln) {
  const w = document.createElement('div');
  const add = txt => { const c = document.createElement('span'); c.className = 'chip regra'; c.textContent = txt; w.appendChild(c); };
  add(`peso: ${ln.peso}`); if (ln.anos != null) add(`anos: ${ln.anos}`); ln.ferramentas.forEach(f => add(f));
  return w;
}

function marcadores(ks) { const w = document.createDocumentFragment();
  ks.forEach(k => { const s = document.createElement('span'); s.className = 'mk'; s.textContent = D.rotuladores[k].curto; w.appendChild(s); }); return w; }

function motivos(ln, ks) {
  const w = document.createElement('div'); w.className = 'motivo';
  ln.votos.forEach((vt, k) => { const d = document.createElement('div');
    d.innerHTML = '<b></b> <span></span>'; d.firstChild.textContent = `${D.rotuladores[k].curto}${ks.includes(k) ? ' (marcou)' : ' (não marcou)'}:`;
    d.lastChild.textContent = vt.motivo; w.appendChild(d); });
  return w;
}

function desenharItem(vg, ln, c, vi) {
  const e = est(vg, ln), ks = vi[c] || [], unanime = ks.length === N, decidido = c in e.itens;
  const box = document.createElement('div');
  box.className = 'item ' + (unanime ? 'unanime' : 'dividido') + (decidido ? ' decidido' : '');
  const topo = document.createElement('div'); topo.className = 'topo';
  const nome = document.createElement('span'); nome.className = 'nome'; nome.textContent = CH[c].item;
  const dim = document.createElement('span'); dim.className = 'dim'; dim.textContent = `${CH[c].dimensao} · ${c}`;
  topo.append(nome, dim, marcadores(ks));
  if (!ks.length) { const s = document.createElement('span'); s.className = 'mk'; s.textContent = 'adicionado'; topo.appendChild(s); }
  const op = document.createElement('span'); op.className = 'opcoes grow';
  op.style.textAlign = 'right';
  [['Sim', true, ''], ['Não', false, 'nao']].forEach(([rot, val, cls]) => {
    const b = document.createElement('button'); b.textContent = rot; b.className = cls + (e.itens[c] === val ? ' on' : '');
    b.onclick = () => { e.itens[c] = val; e.confirmada = false; persist(); desenhar(); }; op.appendChild(b); });
  topo.appendChild(op); box.appendChild(topo);
  if (!unanime && ks.length) box.appendChild(motivos(ln, ks));
  else if (ks.length) { const d = document.createElement('details'); d.innerHTML = '<summary>motivos</summary>'; d.appendChild(motivos(ln, ks)); box.appendChild(d); }
  const df = document.createElement('div'); df.className = 'def'; df.textContent = `${CH[c].definicao}${CH[c].borda !== '—' ? ' · borda: ' + CH[c].borda : ''}`.replace(/\*\*/g, '');
  const dd = document.createElement('details'); dd.innerHTML = '<summary>definição</summary>'; dd.appendChild(df); box.appendChild(dd);
  return box;
}

function desenharPainel() {
  const vg = D.vagas[v], ln = vg.linhas[l], e = est(vg, ln), p = document.getElementById('painel'); p.innerHTML = '';
  const tx = document.createElement('div'); tx.className = 'texto'; tx.textContent = ln.texto; p.appendChild(tx);
  p.appendChild(chipsRegra(ln));

  const h1 = document.createElement('h3'); h1.textContent = 'Natureza'; p.appendChild(h1);
  const vn = votosNat(ln), nat = document.createElement('div'); nat.className = 'opcoes';
  D.naturezas.forEach(n => {
    const b = document.createElement('button'); b.textContent = n; b.className = e.natureza === n ? 'on' : '';
    if (vn[n]) b.appendChild(marcadores(vn[n]));
    b.onclick = () => { e.natureza = n; e.confirmada = false; persist(); desenhar(); }; nat.appendChild(b); });
  p.appendChild(nat);
  if (Object.keys(vn).length > 1 && !e.natureza) { const a = document.createElement('div'); a.className = 'motivo'; a.textContent = 'Divergência: escolha a natureza.'; p.appendChild(a); }

  if (e.natureza !== 'contexto') {
    const h2 = document.createElement('h3'); h2.textContent = 'Itens'; p.appendChild(h2);
    const vi = votosItem(ln), todos = candidatos(vg, ln);
    todos.sort((a, b) => (vi[b] || []).length - (vi[a] || []).length);
    todos.forEach(c => p.appendChild(desenharItem(vg, ln, c, vi)));
    if (!todos.length) { const a = document.createElement('div'); a.className = 'muted'; a.textContent = 'Nenhum rotulador marcou item nesta linha.'; p.appendChild(a); }
    const add = document.createElement('select'); add.innerHTML = '<option value="">+ adicionar um item…</option>';
    let dimAtual = '', og = null;
    D.itens.filter(i => !todos.includes(i.chave)).forEach(i => {
      if (i.dimensao !== dimAtual) { og = document.createElement('optgroup'); og.label = i.dimensao; add.appendChild(og); dimAtual = i.dimensao; }
      const o = document.createElement('option'); o.value = i.chave; o.textContent = i.item; og.appendChild(o); });
    add.onchange = () => { if (add.value) { e.extras.push(add.value); e.itens[add.value] = true; e.confirmada = false; persist(); desenhar(); } };
    p.appendChild(add);

    if (itensMarcados(vg, ln).includes('experiencia.setor')) {
      const h3 = document.createElement('h3'); h3.textContent = 'Setor pedido'; p.appendChild(h3);
      const vs = votosSetor(ln), sel = document.createElement('select');
      sel.innerHTML = '<option value="">escolha…</option>';
      D.setores.forEach(s => { const o = document.createElement('option'); o.value = s; o.textContent = s + (vs[s] ? '  [' + curto(vs[s]) + ']' : ''); sel.appendChild(o); });
      sel.value = e.setor || ''; sel.onchange = () => { e.setor = sel.value; e.confirmada = false; persist(); desenhar(); };
      p.appendChild(sel);
    }
  }
  const h4 = document.createElement('h3'); h4.textContent = 'Nota (opcional)'; p.appendChild(h4);
  const ta = document.createElement('textarea'); ta.value = e.nota || ''; ta.placeholder = 'Dúvida de borda, motivo da decisão…';
  ta.oninput = () => { e.nota = ta.value; persist(); }; p.appendChild(ta);
}

function desenharCabecalho() {
  const total = D.vagas.reduce((n, vg) => n + vg.linhas.length, 0);
  const prontas = D.vagas.reduce((n, vg) => n + vg.linhas.filter(ln => feita(vg, ln)).length, 0);
  document.getElementById('progresso').textContent = `${prontas} / ${total} linhas confirmadas`;
}
function desenhar() { desenharLista(); desenharPainel(); desenharCabecalho(); }

function proximaAberta() {
  for (let k = 1; k <= D.vagas.reduce((n, vg) => n + vg.linhas.length, 0); k++) {
    let vv = v, ll = l + k;
    while (ll >= D.vagas[vv].linhas.length) { ll -= D.vagas[vv].linhas.length; vv = (vv + 1) % D.vagas.length; }
    if (!feita(D.vagas[vv], D.vagas[vv].linhas[ll])) { v = vv; l = ll; document.getElementById('vaga').value = v; desenhar(); return; }
  }
}
function confirmar() {
  const vg = D.vagas[v], ln = vg.linhas[l], e = est(vg, ln);
  if (abertaLinha(vg, ln)) { desenhar(); return; }
  e.confirmada = true; e.em = new Date().toISOString(); persist(); proximaAberta();
}
function ir(passo) { const vg = D.vagas[v]; l = Math.max(0, Math.min(vg.linhas.length - 1, l + passo)); desenhar(); }

function csv() {
  const cel = x => { x = x == null ? '' : String(x); return /[",\n\r]/.test(x) ? '"' + x.replace(/"/g, '""') + '"' : x; };
  const linhas = [['id_publico', 'ordem', 'tipo', 'valor', 'incluido', 'votos', 'decisao', 'nota', 'decidido_em_utc']];
  D.vagas.forEach(vg => vg.linhas.forEach(ln => {
    const e = est(vg, ln); if (!e.confirmada) return;
    const base = [vg.id, ln.ordem], fim = [e.nota || '', e.em || ''];
    const vn = votosNat(ln), kn = vn[e.natureza] || [];
    linhas.push([...base, 'natureza', e.natureza, 1, curto(kn), kn.length === N ? 'concordou' : kn.length ? `escolheu_${curto(kn)}` : 'adicionou', ...fim]);
    if (e.natureza === 'contexto') return;
    const vi = votosItem(ln);
    candidatos(vg, ln).forEach(c => {
      const ks = vi[c] || [], inc = !!e.itens[c];
      const dec = !ks.length ? (inc ? 'adicionou' : 'adicionou_e_tirou') :
        ks.length === N ? (inc ? 'concordou' : 'mudou') : (inc ? `escolheu_${curto(ks)}` : `rejeitou_${curto(ks)}`);
      linhas.push([...base, 'item', c, inc ? 1 : 0, curto(ks), dec, ...fim]);
    });
    if (itensMarcados(vg, ln).includes('experiencia.setor')) {
      const vs = votosSetor(ln), ks = vs[e.setor] || [];
      linhas.push([...base, 'setor', e.setor, 1, curto(ks), ks.length === N ? 'concordou' : ks.length ? `escolheu_${curto(ks)}` : 'adicionou', ...fim]);
    }
  }));
  return linhas.map(r => r.map(cel).join(',')).join('\n') + '\n';
}
document.getElementById('salvar').onclick = async () => {
  const nome = `${D.conjunto}_revisado.csv`, texto = csv();
  if (window.showSaveFilePicker) {
    try { const h = await showSaveFilePicker({ suggestedName: nome, types: [{ description: 'CSV', accept: { 'text/csv': ['.csv'] } }] });
      const w = await h.createWritable(); await w.write(texto); await w.close(); return; } catch (e) { if (e.name === 'AbortError') return; }
  }
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([texto], { type: 'text/csv' })); a.download = nome; a.click();
};
// Modal com todas as linhas de requisito da vaga, na ordem do posting, com a linha atual destacada.
const modal = document.getElementById('modal');
function abrirVaga() {
  const vg = D.vagas[v];
  document.getElementById('mTitulo').textContent = `${vg.empresa} — ${vg.cargo}`;
  const meta = document.getElementById('mMeta'); meta.textContent = `nível ${vg.nivel} · texto completo do anúncio, na ordem; as ${vg.linhas.length} linhas numeradas são as que você revisa · `;
  if (vg.url) { const a = document.createElement('a'); a.href = vg.url; a.target = '_blank'; a.rel = 'noopener noreferrer'; a.textContent = 'abrir o posting original'; meta.appendChild(a); }
  const ol = document.getElementById('mLinhas'); ol.innerHTML = '';
  const atual = vg.linhas[l].ordem;
  vg.jd.forEach(sec => {
    const h = document.createElement('li'); h.className = 'secao';
    h.textContent = (sec.titulo || sec.secao.replace(/_/g, ' ')) + (sec.titulo ? ' · ' + sec.secao.replace(/_/g, ' ') : '');
    ol.appendChild(h);
    sec.linhas.forEach(ln => {
      const li = document.createElement('li'); if (ln.ordem === atual) li.className = 'atual'; if (ln.ordem == null) li.classList.add('fora');
      li.innerHTML = '<span class="n"></span><span></span>'; li.firstChild.textContent = ln.ordem == null ? '' : ln.ordem; li.lastChild.textContent = ln.texto;
      ol.appendChild(li);
    });
  });
  modal.classList.add('aberto');
  const at = ol.querySelector('.atual'); if (at) at.scrollIntoView({ block: 'center' });
}
const fecharVaga = () => modal.classList.remove('aberto');
document.getElementById('verVaga').onclick = abrirVaga;
document.getElementById('mFechar').onclick = fecharVaga;
modal.onclick = ev => { if (ev.target === modal) fecharVaga(); };
document.getElementById('confirmar').onclick = confirmar;
document.getElementById('ant').onclick = () => ir(-1);
document.getElementById('prox').onclick = () => ir(1);
document.getElementById('proxAberta').onclick = proximaAberta;
document.addEventListener('keydown', ev => {
  if (ev.key === 'Escape') { fecharVaga(); return; }
  if (ev.target.tagName === 'TEXTAREA' || ev.target.tagName === 'SELECT' || ev.ctrlKey || ev.metaKey || ev.altKey) return;
  if (ev.key === 'v' || ev.key === 'V') { modal.classList.contains('aberto') ? fecharVaga() : abrirVaga(); ev.preventDefault(); return; }
  if (ev.target.tagName === 'TEXTAREA' || ev.target.tagName === 'SELECT' || ev.ctrlKey || ev.metaKey || ev.altKey) return;
  if (ev.key === 'Enter') { confirmar(); ev.preventDefault(); }
  else if (ev.key === 'ArrowRight' || ev.key === 'ArrowDown') { ir(1); ev.preventDefault(); }
  else if (ev.key === 'ArrowLeft' || ev.key === 'ArrowUp') { ir(-1); ev.preventDefault(); }
});
const selVaga = document.getElementById('vaga');
D.vagas.forEach((vg, i) => { const o = document.createElement('option'); o.value = i; o.textContent = `${i + 1}. ${vg.empresa} (${vg.nivel})`; selVaga.appendChild(o); });
selVaga.onchange = () => { v = Number(selVaga.value); l = 0; desenhar(); };
document.getElementById('conj').textContent = D.conjunto;
document.getElementById('versao').textContent = D.versao;
persist(); desenhar();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
