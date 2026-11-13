// Página pública do mercado de gestão de dados. Os números de cada gráfico vêm de dados/pagina.json, calculado na publicação
// por pipeline/gerar_site.py (o mesmo cálculo do analise/achados.md); a consulta de cada gráfico roda em DuckDB-WASM sobre os
// marts em Parquet de dados/. A página nunca espera o DuckDB pra mostrar número: ele só serve à consulta.
const DATA = await (await fetch('dados/pagina.json')).json();

const NS = 'http://www.w3.org/2000/svg';
const RM = matchMedia('(prefers-reduced-motion: reduce)').matches;
const C = { coordenador: '#5b8cff', gerente: '#ff4c33', outros: '#9a9a96' };
const NOME = { coordenador: 'Coordenação', gerente: 'Gerência' };
const NC = DATA.nc, NG = DATA.ng;
const fmt = n => Math.round(n).toLocaleString('pt-BR');
const brl = n => 'R$ ' + (n / 1000).toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + ' mil';
const pct = (k, n) => Math.round(100 * k / n);
const lerp = (a, b, t) => a + (b - a) * t;
const IT = Object.fromEntries(DATA.items.map(i => [i.chave, i]));
const ROWS = DATA.graficos;

// ---------- Fisher bicaudal (mesma conta do achados.py) ----------
function comb(n, k) { k = Math.min(k, n - k); let r = 1; for (let i = 1; i <= k; i++) r = r * (n - k + i) / i; return r; }
const hiper = (a, b, c, d) => comb(a + b, a) * comb(c + d, c) / comb(a + b + c + d, a + c);
function fisher(xc, nc, xg, ng) {
  const a = xc, b = nc - xc, c = xg, d = ng - xg, p0 = hiper(a, b, c, d), r1 = a + b, c1 = a + c, n = a + b + c + d;
  let tot = 0;
  for (let x = Math.max(0, c1 - (n - r1)); x <= Math.min(r1, c1); x++) { const p = hiper(x, r1 - x, c1 - x, n - r1 - c1 + x); if (p <= p0 * (1 + 1e-9)) tot += p; }
  return Math.min(1, tot);
}
const pTxt = p => p < 0.001 ? 'p < 0,001' : 'p = ' + p.toFixed(3).replace('.', ',');
const selo = p => p < 0.01 ? ['DIFERENÇA FIRME', '#d4f542'] : p < 0.05 ? ['DIREÇÃO', '#ffffff'] : ['SEM DIFERENÇA CLARA', '#9a9a96'];

// ---------- motor de movimento ----------
const EASE = { out: t => 1 - Math.pow(1 - t, 3), outQuint: t => 1 - Math.pow(1 - t, 5),
  back: t => { const c = 1.4, c3 = c + 1; return 1 + c3 * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2); } };
function tween(dur, delay, fn, ease = EASE.out) {
  if (RM) { fn(1); return; }
  const t0 = performance.now() + delay;
  const tick = now => { const t = Math.min(1, Math.max(0, (now - t0) / dur)); fn(ease(t)); if (t < 1) requestAnimationFrame(tick); };
  requestAnimationFrame(tick);
}
function stage(box) {
  const anims = [];
  return { add(dur, delay, fn, ease) { anims.push({ dur, delay, fn, ease }); },
    done() { if (box.dataset.seen === '1') anims.forEach(a => a.fn(1));
      else { anims.forEach(a => a.fn(0)); box._play = () => anims.forEach(a => tween(a.dur, a.delay, a.fn, a.ease)); } } };
}
const io = new IntersectionObserver(es => es.forEach(e => {
  if (!e.isIntersecting) return;
  const t = e.target; io.unobserve(t);
  if (t.classList.contains('chart') || t.id === 'art') { t.dataset.seen = '1'; t._play && t._play(); }
  else t.classList.add('in');
}), { threshold: 0.12, rootMargin: '0px 0px -6% 0px' });

function el(tag, attrs = {}, parent) { const e = document.createElementNS(NS, tag); for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v); if (parent) parent.appendChild(e); return e; }
function txt(parent, x, y, s, attrs = {}) { const t = el('text', { x, y, ...attrs }, parent); t.textContent = s; return t; }
const set = (e, o) => { for (const [k, v] of Object.entries(o)) e.setAttribute(k, v); };
const tip = document.getElementById('tip');
function showTip(ev, html) { tip.innerHTML = html; tip.classList.add('on'); const pad = 14, w = tip.offsetWidth, h = tip.offsetHeight;
  let x = ev.clientX + pad, y = ev.clientY + pad; if (x + w > innerWidth - 8) x = ev.clientX - w - pad; if (y + h > innerHeight - 8) y = ev.clientY - h - pad;
  tip.style.left = Math.max(8, x) + 'px'; tip.style.top = Math.max(8, y) + 'px'; }
function hideTip() { tip.classList.remove('on'); }
const sw = c => `<span class="sw" style="background:${c}"></span>`;
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');

// ---------- texto ----------
let ci = 0;
document.querySelectorAll('#word .ln').forEach(ln => { ln.innerHTML = [...ln.dataset.t].map(ch => ch === ' ' ? ' ' : `<span class="ch" style="--i:${ci++}">${ch}</span>`).join(''); });
document.querySelectorAll('h2[data-split]').forEach(h => { h.innerHTML = h.innerHTML.split('|').map((s, k) => `<span class="l"><span style="--i:${k}">${s}</span></span>`).join(''); io.observe(h); });
document.querySelectorAll('.rv').forEach(e => io.observe(e));

const word = document.getElementById('word'), prog = document.getElementById('prog');
let ticking = false;
let railUpdate = () => {};
addEventListener('scroll', () => { if (ticking) return; ticking = true; requestAnimationFrame(() => {
  const y = scrollY; railUpdate();
  if (!RM && y < innerHeight * 1.2) { word.style.transform = `translateY(${y * 0.35}px)`; word.style.opacity = Math.max(0, 1 - y / (innerHeight * 0.9)); }
  ticking = false; }); }, { passive: true });

// ---------- 1 · arte ----------
function art() {
  const s = document.getElementById('art'); s.innerHTML = ''; const st = stage(s);
  const L = DATA.manifest.cobertura.rotuladas, V = DATA.manifest.contagens.vagas, F = DATA.faixa_posting;
  const rr = 200, rv = rr * Math.sqrt(V / L) * 1.6;
  const big = el('circle', { cx: 250, cy: 220, r: rr, fill: '#d9d9d9' }, s);
  const mid = el('circle', { cx: 250 + rr * 0.86, cy: 220 + rr * 0.42, r: rv, fill: '#ff4c33', stroke: '#000', 'stroke-width': 2 }, s);
  const gz = el('g', {}, s); el('circle', { cx: 520, cy: 70, r: 34, fill: '#d4f542', class: 'breathe' }, gz);
  const tR = txt(s, 230, 210, '0', { 'text-anchor': 'middle', 'font-size': 44, fill: '#000' });
  const tL = txt(s, 230, 238, 'LINHAS DE ANÚNCIO', { 'text-anchor': 'middle', 'font-size': 12, fill: '#000', 'letter-spacing': '0.1em', 'font-weight': 200 });
  const tV = txt(s, 250 + rr * 0.86, 220 + rr * 0.42 + 6, '0', { 'text-anchor': 'middle', 'font-size': 18, fill: '#000' });
  const tZ = txt(s, 520, 78, String(F), { 'text-anchor': 'middle', 'font-size': 22, fill: '#000' });
  st.add(1300, 0, t => { set(big, { r: rr * t }); tR.textContent = fmt(L * t); tR.style.opacity = tL.style.opacity = Math.min(1, t * 2); }, EASE.back);
  st.add(1000, 350, t => { set(mid, { r: rv * t }); tV.textContent = fmt(V * t); tV.style.opacity = t; }, EASE.back);
  st.add(800, 750, t => { gz.style.opacity = t; gz.style.transform = `translateY(${(1 - t) * -40}px)`; tZ.style.opacity = t; }, EASE.back);
  st.done(); io.observe(s);
  const f = document.getElementById('facts');
  const fio = new IntersectionObserver(es => es.forEach(e => { if (!e.isIntersecting) return; fio.unobserve(e.target); e.target.classList.add('in');
    const b = e.target.querySelector('b'), n = +b.dataset.n, suf = b.dataset.suf || '';
    tween(1400, parseInt(e.target.style.getPropertyValue('--d')) || 0, t => b.textContent = fmt(n * t) + suf, EASE.outQuint); }), { threshold: 0.3 });
  f.querySelectorAll('.rv').forEach(d => fio.observe(d));
}

// ---------- 2 · base: um ponto por vaga ----------
function base(box) {
  box.innerHTML = ''; const st = stage(box);
  const tot = DATA.base.reduce((a, b) => a + b.n, 0);
  const W = box.clientWidth, cols = W < 600 ? 15 : 30, gap = W / cols, r = Math.min(9, gap * 0.36);
  const rows = Math.ceil(tot / cols), H = rows * gap + 4;
  const s = el('svg', { viewBox: `0 0 ${W} ${H}`, height: H, role: 'img', 'aria-label': DATA.base.map(b => `${b.n} ${b.nome}`).join('; ') }, box);
  let i = 0;
  DATA.base.forEach(({ k, n, nome, onde }) => {
    for (let j = 0; j < n; j++, i++) {
      const cx = (i % cols) * gap + gap / 2, cy = Math.floor(i / cols) * gap + gap / 2;
      const a = k === 'sem' ? { fill: 'transparent', stroke: '#5c5a57', 'stroke-width': 1.5 } : k === 'rep' ? { fill: 'transparent', stroke: '#d9d9d9', 'stroke-width': 1.5, 'stroke-dasharray': '2 2' } : { fill: C[k] };
      const c = el('circle', { cx, cy, r: 0, ...a }, s);
      st.add(500, 80 + i * 14, t => set(c, { r: Math.max(0, r * t) }), EASE.back);
      c.addEventListener('mousemove', ev => showTip(ev, `<b>${n} ${n === 1 ? 'vaga' : 'vagas'}</b>: ${nome}<br>${onde}`));
      c.addEventListener('mouseleave', hideTip);
    }
  });
  st.done(); io.observe(box);
  document.getElementById('leg-base').innerHTML = DATA.base.map(({ k, n, nome }) =>
    `<span><i class="${k === 'sem' ? 'out' : k === 'rep' ? 'dash' : ''}" style="background:${C[k] || ''}"></i>${n} ${nome}</span>`).join('');
}

// ---------- halteres ----------
// rows: {label, c, g, ref?, apagado?}  (c = vagas de coordenação, g = de gerência)
function dumb(box, rows, o = {}) {
  box.innerHTML = ''; const st = stage(box);
  const W = box.clientWidth, narrow = W < 600;
  const L = narrow ? 0 : (o.L || 330), Rm = narrow ? 34 : 215, rowH = narrow ? 70 : 44, top = 24;
  const H = top + rows.length * rowH + 4;
  const s = el('svg', { viewBox: `0 0 ${W} ${H}`, height: H }, box);
  const X = v => L + 22 + (W - L - Rm - 44) * v / 100;
  [0, 25, 50, 75, 100].forEach((v, k) => {
    const gl = el('line', { x1: X(v), x2: X(v), y1: top - 6, y2: top - 6, stroke: '#2a2727', 'stroke-width': 1 }, s);
    st.add(900, k * 60, t => set(gl, { y2: lerp(top - 6, H - 4, t) }), EASE.out);
    txt(s, X(v), 12, v + '%', { 'text-anchor': 'middle', class: 'tick' });
  });
  rows.forEach((r, i) => {
    const pc = 100 * r.c / NC, pg = 100 * r.g / NG, p = fisher(r.c, NC, r.g, NG), [st_, sc] = r.ref ? ['RÉGUA', '#5c5a57'] : selo(p);
    const yRow = top + i * rowH, y = narrow ? yRow + 40 : yRow + rowH / 2, dly = 200 + i * 70;
    const g = el('g', { class: 'row' }, s);
    if (r.ref) g.style.opacity = 0.75;
    const lab = txt(g, 0, narrow ? yRow + 16 : y + 5, r.label, { class: 'term', style: r.ref ? 'fill:#9a9a96' : '' });
    const colC = r.apagado ? '#3f5a99' : C.coordenador, colG = r.apagado ? '#99402f' : C.gerente;
    const ln = el('line', { x1: X(0), x2: X(0), y1: y, y2: y, stroke: '#5c5a57', 'stroke-width': 2, 'stroke-dasharray': r.ref ? '3 4' : '' }, g);
    const cc = el('circle', { cx: X(0), cy: y, r: 7, fill: colC, stroke: '#1d1a1a', 'stroke-width': 2 }, g);
    const cg = el('circle', { cx: X(0), cy: y, r: 7, fill: colG, stroke: '#1d1a1a', 'stroke-width': 2 }, g);
    const lo = Math.min(pc, pg), hi = Math.max(pc, pg), loC = pc <= pg;
    const vLo = txt(g, X(lo) - 14, y + 4, Math.round(lo) + '%', { 'text-anchor': 'end', class: 'val', style: `fill:${loC ? colC : colG}` });
    const vHi = txt(g, X(hi) + 14, y + 4, Math.round(hi) + '%', { class: 'val', style: `fill:${loC ? colG : colC}` });
    if (hi - lo < 6) { vHi.textContent = ''; vLo.textContent = `${Math.round(pc)}% · ${Math.round(pg)}%`; vLo.style.fill = '#d9d9d9'; }
    else if (X(lo) - 14 < 30) {  // o menor valor encostaria na borda esquerda (3%): os dois rótulos vão juntos pra direita dos pontos
      vHi.textContent = ''; vLo.setAttribute('text-anchor', 'start'); vLo.setAttribute('x', X(hi) + 14);
      vLo.textContent = `${Math.round(pc)}% · ${Math.round(pg)}%`; vLo.style.fill = '#d9d9d9'; }
    const sl = txt(g, narrow ? 0 : W, narrow ? yRow + 64 : y + 4, st_, { 'text-anchor': narrow ? 'start' : 'end', class: 'tick', style: `fill:${sc};letter-spacing:.1em` });
    st.add(1100, dly, k => { lab.style.opacity = Math.min(1, k * 2);
      set(cc, { cx: X(pc * k) }); set(cg, { cx: X(pg * k) }); set(ln, { x1: X(lo * k), x2: X(hi * k) });
      vLo.style.opacity = vHi.style.opacity = Math.max(0, k * 2 - 1); }, EASE.outQuint);
    st.add(500, dly + 900, k => { sl.style.opacity = k; });
    const hit = el('rect', { x: 0, y: yRow, width: W, height: rowH, fill: 'transparent' }, g);
    hit.addEventListener('mouseenter', () => { s.classList.add('hovering'); g.classList.add('on'); });
    hit.addEventListener('mousemove', ev => showTip(ev, `<b>${esc(r.label)}</b><br>${sw(C.coordenador)}Coordenação ${Math.round(pc)}% · ${r.c} de ${NC}<br>${sw(C.gerente)}Gerência ${Math.round(pg)}% · ${r.g} de ${NG}<br>${r.ref ? 'régua de comparação' : pTxt(p) + ' · ' + selo(p)[0].toLowerCase()}`));
    hit.addEventListener('mouseleave', () => { s.classList.remove('hovering'); g.classList.remove('on'); hideTip(); });
  });
  st.done(); io.observe(box);
}

// ---------- pontos acesos ----------
function waffle(box, chave) {
  box.innerHTML = ''; const st = stage(box);
  const W = box.clientWidth, narrow = W < 600, it = typeof chave === 'string' ? IT[chave] : { c: chave.c[0], g: chave.g[0] };
  const grupos = [['coordenador', it.c, NC], ['gerente', it.g, NG]];
  const cols = narrow ? 9 : 12, gap = narrow ? Math.min(30, (W - 10) / cols) : Math.min(34, (W / 2 - 60) / cols), r = Math.max(0, gap * 0.36);  // caixa ainda sem largura (1º desenho, antes do layout): raio 0, o desenho seguinte refaz
  const blocos = grupos.map(([, , n]) => Math.ceil(n / cols) * gap);
  const H = narrow ? blocos[0] + blocos[1] + 190 : Math.max(...blocos) + 110;
  const s = el('svg', { viewBox: `0 0 ${W} ${H}`, height: H }, box);
  grupos.forEach(([k, x, n], gi) => {
    const ox = narrow ? 0 : gi * (W / 2), oy = narrow ? (gi ? blocos[0] + 95 : 0) : 0;
    const bigT = txt(s, ox, oy + 50, '0%', { class: 'term', style: 'font-size:52px;letter-spacing:-0.04em' });
    txt(s, ox, oy + 76, `${NOME[k].toUpperCase()} · ${x} DE ${n}`, { style: `letter-spacing:.1em;fill:${C[k]}` });
    for (let j = 0; j < n; j++) {
      const cx = ox + (j % cols) * gap + gap / 2, cy = oy + 100 + Math.floor(j / cols) * gap + gap / 2, on = j < x;
      const c = el('circle', { cx, cy, r, fill: on ? C[k] : 'transparent', stroke: on ? C[k] : '#3d3d3d', 'stroke-width': 1.5 }, s);
      if (on) st.add(400, 200 + gi * 300 + j * 45, t => { c.setAttribute('fill-opacity', t); }, EASE.out); else c.setAttribute('fill-opacity', 1);
    }
    st.add(1300, 200 + gi * 300, t => bigT.textContent = Math.round(100 * x / n * t) + '%', EASE.outQuint);
  });
  const p = fisher(it.c, NC, it.g, NG), [sl, sc] = selo(p);
  txt(s, narrow ? 0 : W, H - 6, `${sl} · ${pTxt(p)}`, { 'text-anchor': narrow ? 'start' : 'end', class: 'tick', style: `fill:${sc};letter-spacing:.1em` });
  st.done(); io.observe(box);
}

// ---------- barras de proporção ----------
function hbar(box, rows, o = {}) {
  box.innerHTML = ''; const st = stage(box);
  const W = box.clientWidth, narrow = W < 600, L = narrow ? 0 : (o.L || 260), rowH = narrow ? 52 : 36, H = rows.length * rowH;
  const s = el('svg', { viewBox: `0 0 ${W} ${H}`, height: H }, box);
  const X = v => (W - L - 150) * v / 100;
  rows.forEach((r, i) => {
    const y = i * rowH, by = narrow ? y + 24 : y + 11, v = 100 * r.x / r.n;
    txt(s, 0, narrow ? y + 16 : y + 23, r.label, { class: 'term', style: 'font-size:14px' + (r.hl ? '' : ';fill:#d9d9d9') });
    const b = el('rect', { x: L, y: by, width: 0, height: 14, rx: 4, fill: r.hl ? '#ffffff' : '#5c5a57' }, s);
    const lab = txt(s, L, by + 11, '', { class: 'tick' });
    st.add(1000, 100 + i * 90, t => { const w = Math.max(X(v) * t, 0.01); set(b, { width: w }); set(lab, { x: L + w + 10 }); lab.textContent = `${Math.round(v * t)}% · ${r.x} de ${r.n}`; }, EASE.outQuint);
  });
  st.done(); io.observe(box);
}

// ---------- 8 · salário ----------
function salario(box) {
  box.innerHTML = ''; const st = stage(box);
  const grupos = ['coordenador', 'gerente'].map(k => {
    const xs = DATA.sal[k].map(v => ({ ...v, mid: (v.min + v.max) / 2 })).sort((a, b) => a.mid - b.mid);
    const m = xs.map(v => v.mid), med = m.length ? (m.length % 2 ? m[(m.length - 1) / 2] : (m[m.length / 2 - 1] + m[m.length / 2]) / 2) : 0;
    const [mmin, mmax] = DATA.moda[k];
    return { k, xs, med, rep: v => v.min === mmin && v.max === mmax };
  }).filter(g => g.xs.length);
  if (!grupos.length) return;
  const max = Math.ceil(Math.max(...grupos.flatMap(g => g.xs.map(v => v.max))) / 10000) * 10000;
  const W = box.clientWidth, narrow = W < 520, rowH = 7, gapG = 74, top = 24;  // celular: rótulos menores, eixo sem o "MIL" repetido
  const H = top + grupos.reduce((a, g) => a + g.xs.length * rowH + gapG, 0) + 4;
  const s = el('svg', { viewBox: `0 0 ${W} ${H}`, height: H, role: 'img', 'aria-label': 'Faixa de referência salarial pesquisada por vaga, coordenação e gerência' }, box);
  const X = v => (W - 8) * v / max;
  for (let v = 0; v <= max; v += 10000) {
    el('line', { x1: X(v), x2: X(v), y1: top - 6, y2: H, stroke: '#2a2727', 'stroke-width': 1 }, s);
    txt(s, X(v), 12, narrow ? (v === 0 ? '0' : v === max ? (v / 1000) + ' MIL' : String(v / 1000)) : v === 0 ? 'R$ 0' : (v / 1000) + ' MIL',
      { 'text-anchor': v === 0 ? 'start' : v === max ? 'end' : 'middle', class: 'tick' });
  }
  let y0 = top + 26, gi = 0;
  grupos.forEach(g => {
    const yTop = y0, b0 = gi * 700, nrep = g.xs.filter(g.rep).length;
    const rot = { style: `letter-spacing:${narrow ? '.03em;font-size:10px' : '.1em'};fill:#d9d9d9;font-weight:400` };
    if (narrow) { txt(s, 0, yTop - 25, `${NOME[g.k].toUpperCase()} · ${g.xs.length} VAGAS`, rot); txt(s, 0, yTop - 13, `${nrep} NA FAIXA REPETIDA`, rot); }
    else txt(s, 0, yTop - 12, `${NOME[g.k].toUpperCase()} · ${g.xs.length} VAGAS · ${nrep} NA FAIXA REPETIDA`, rot);
    const lines = g.xs.map((v, i) => {
      const y = yTop + i * rowH + rowH / 2, rep = g.rep(v);
      const ln = el('line', { x1: X(v.mid), x2: X(v.mid), y1: y, y2: y, stroke: C[g.k], 'stroke-width': 4, 'stroke-linecap': rep ? 'butt' : 'round', 'stroke-dasharray': rep ? '3 3' : '', class: 'sl' }, s);
      st.add(800, b0 + 150 + i * 22, t => { set(ln, { x1: X(lerp(v.mid, v.min, t)), x2: X(lerp(v.mid, v.max, t)) }); ln.style.opacity = t > 0 ? 1 : 0; }, EASE.outQuint);
      return ln;
    });
    const yb = yTop + g.xs.length * rowH;
    const ml = el('line', { x1: X(g.med), x2: X(g.med), y1: yTop - 4, y2: yTop - 4, stroke: '#ffffff', 'stroke-width': 1.5 }, s);
    const mt = txt(s, X(g.med), yb + 22, 'MEDIANA ' + (DATA.sal_txt[g.k] || brl(g.med)).toUpperCase(), { 'text-anchor': 'middle', style: 'fill:#ffffff;letter-spacing:.06em;font-weight:400' });
    st.add(700, b0 + 150 + g.xs.length * 22 + 300, t => { set(ml, { y2: lerp(yTop - 4, yb + 8, t) }); mt.style.opacity = t; }, EASE.out);
    const hit = el('rect', { x: 0, y: yTop, width: W, height: g.xs.length * rowH, fill: 'transparent' }, s);
    let on = null;
    hit.addEventListener('mousemove', ev => { const r = s.getBoundingClientRect(), yy = (ev.clientY - r.top) * (H / r.height);
      const i = Math.max(0, Math.min(g.xs.length - 1, Math.floor((yy - yTop) / rowH))), v = g.xs[i];
      if (on !== lines[i]) { on && on.classList.remove('on'); on = lines[i]; on.classList.add('on'); s.classList.add('hovering'); }
      showTip(ev, `${sw(C[g.k])}<b>${esc(v.e)}</b><br>${esc(v.cargo)}<br>${esc(v.cid) || 'cidade não informada'}<br>${brl(v.min)} a ${brl(v.max)}${g.rep(v) ? '<br>faixa repetida de um guia salarial' : ''}`); });
    hit.addEventListener('mouseleave', () => { on && on.classList.remove('on'); on = null; s.classList.remove('hovering'); hideTip(); });
    y0 = yb + gapG; gi++;
  });
  st.done(); io.observe(box);
}

// ---------- 10 · explorar ----------
const DIMS = ['Todas', ...new Set(DATA.items.map(i => i.dim))];
let exDim = 'Todas', exSort = 'dif', exAll = false;
function explorar() {
  let rows = DATA.items.filter(i => exDim === 'Todas' || i.dim === exDim).map(i => ({ label: i.item, c: i.c, g: i.g }));
  rows.sort(exSort === 'dif' ? (a, b) => Math.abs(b.g / NG - b.c / NC) - Math.abs(a.g / NG - a.c / NC) : (a, b) => (b.c + b.g) - (a.c + a.g));
  const total = rows.length; if (!exAll) rows = rows.slice(0, 12);
  const box = document.getElementById('c-ex'); box.dataset.seen = '1';
  dumb(box, rows);
  const b = document.getElementById('mais'); b.style.display = total > 12 ? '' : 'none'; b.textContent = exAll ? 'Mostrar menos' : `Mostrar os ${total}`;
  document.getElementById('chips').innerHTML = DIMS.map(d => `<button class="pill mono ${d === exDim ? 'on' : ''}" data-d="${esc(d)}" type="button">${esc(d)}</button>`).join('');
  document.getElementById('sort').innerHTML = [['dif', 'Maior diferença'], ['freq', 'Mais citados']].map(([k, n]) => `<button class="pill mono ${k === exSort ? 'on' : ''}" data-s="${k}" type="button">${n}</button>`).join('');
}
document.getElementById('chips').addEventListener('click', e => { const d = e.target.dataset.d; if (d) { exDim = d; exAll = false; explorar(); } });
document.getElementById('sort').addEventListener('click', e => { const k = e.target.dataset.s; if (k) { exSort = k; explorar(); } });
document.getElementById('mais').addEventListener('click', () => { exAll = !exAll; explorar(); });

// ---------- consultas: SQL + resultado, DuckDB-WASM sobre os marts em Parquet ----------
const MARTS = ['mart_vaga_item', 'mart_vaga_ferramenta', 'mart_vagas', 'mart_repost'];
const itemSQL = chaves => `-- % de vagas que pedem cada item, por nível
with base as (
  select nivel, count(distinct id_publico) as vagas
  from mart_vaga_item
  where nivel in ('coordenador', 'gerente')
  group by nivel
)
select i.item, i.nivel,
       count(distinct i.id_publico) as pedem,
       b.vagas,
       round(100.0 * pedem / b.vagas) as pct
from mart_vaga_item i
join base b using (nivel)
where i.item_chave in (${chaves.map(c => `'${c}'`).join(',\n                       ')})
group by i.item, i.nivel, b.vagas
order by i.item, i.nivel;`;
const chavesDe = linhas => linhas.filter(r => r.chave).map(r => r.chave);
const SQLS = {
  base: { sql: `-- quem entra na comparação
select nivel, count(distinct id_publico) as vagas
from mart_vaga_item
group by nivel
order by vagas desc;` },
  ats: { sql: `-- onde o anúncio está publicado (o ATS é lido do endereço do anúncio, pelo seed ats_hosts)
select coalesce(ats, 'sem link do anúncio') as ats,
       count(*) as vagas
from mart_vagas
group by 1
order by vagas desc;` },
  ns: { sql: itemSQL(chavesDe(ROWS.ns)), p: 'pedem' },
};

let dbPromise = null;
function getDB() {
  if (!dbPromise) dbPromise = (async () => {
    const duckdb = await import('https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.29.0/+esm');
    const bundle = await duckdb.selectBundle(duckdb.getJsDelivrBundles());
    const workerUrl = URL.createObjectURL(new Blob([`importScripts("${bundle.mainWorker}");`], { type: 'text/javascript' }));
    const db = new duckdb.AsyncDuckDB(new duckdb.ConsoleLogger(duckdb.LogLevel.WARNING), new Worker(workerUrl));
    await db.instantiate(bundle.mainModule, bundle.pthreadWorker);
    URL.revokeObjectURL(workerUrl);
    const conn = await db.connect();
    for (const t of MARTS) {
      const r = await fetch(`dados/${t}.parquet`);
      if (!r.ok) throw new Error(`${t}.parquet: ${r.status}`);
      await db.registerFileBuffer(`${t}.parquet`, new Uint8Array(await r.arrayBuffer()));
      await conn.query(`create or replace view ${t} as select * from read_parquet('${t}.parquet')`);
    }
    return conn;
  })().catch(e => { dbPromise = null; throw e; });
  return dbPromise;
}
async function rodar(sql) {
  const conn = await getDB();
  const res = await conn.query(sql);
  const cols = res.schema.fields.map(f => f.name), tipos = res.schema.fields.map(f => String(f.type));
  const rows = res.toArray().map(r => cols.map((c, i) => { const v = r[c];
    if (typeof v === 'bigint') return Number(v);
    if (v instanceof Date) return v.toISOString().slice(0, 10);
    if (typeof v === 'number' && /^Date/.test(tipos[i])) return new Date(v).toISOString().slice(0, 10);
    return v; }));
  return { cols, rows };
}

const KW = /\b(select|from|where|join|left|on|and|or|in|is|null|group by|order by|having|limit|with|as|case|when|then|else|end|count|distinct|round|median|any_value|coalesce|using|not|like|desc|asc|between)\b/g;
function hl(s) { return s.split('\n').map(l => { const i = l.indexOf('--'); const code = i >= 0 ? l.slice(0, i) : l, cm = i >= 0 ? l.slice(i) : '';
  return esc(code).replace(/'[^']*'/g, m => `\u0001${m}\u0002`).replace(KW, '<span class="k">$1</span>').replace(/\u0001/g, '<span class="s">').replace(/\u0002/g, '</span>') + (cm ? `<span class="c">${esc(cm)}</span>` : ''); }).join('\n'); }

// acrescenta o p do teste exato de Fisher nas consultas que comparam os dois níveis (E3: o p aparece na tabela da consulta)
function comP(res, colunaN) {
  const iN = res.cols.indexOf('nivel'), iX = res.cols.indexOf(colunaN), iV = res.cols.indexOf('vagas'), iI = res.cols.indexOf('item');
  const grupos = new Map();
  res.rows.forEach((r, k) => { const chave = iI >= 0 ? r[iI] : ''; (grupos.get(chave) || grupos.set(chave, {}).get(chave))[r[iN]] = { x: r[iX], n: r[iV], k }; });
  const rows = res.rows.map(r => [...r, '']);
  grupos.forEach(gr => { if (gr.coordenador && gr.gerente) rows[Math.min(gr.coordenador.k, gr.gerente.k)][res.cols.length] =
    pTxt(fisher(gr.coordenador.x, gr.coordenador.n, gr.gerente.x, gr.gerente.n)); });
  return { cols: [...res.cols, 'p'], rows };
}
function celula(col, v) {
  if (v === null || v === undefined) return '';
  if (typeof v === 'number') return col === 'pct' ? Math.round(v) + '%' : col === 'mediana' ? brl(v) : Number.isInteger(v) ? fmt(v) : v.toLocaleString('pt-BR');
  return esc(String(v));
}
function tabela(res) {
  const num = res.cols.map((c, i) => res.rows.length > 0 && res.rows.every(r => r[i] === null || typeof r[i] === 'number' || /^(pct|p)$/.test(c)));
  return `<table><tr>${res.cols.map((c, i) => `<th class="${num[i] ? 'n' : ''}">${esc(c)}</th>`).join('')}</tr>${res.rows.map(r =>
    `<tr>${r.map((v, i) => `<td class="${num[i] ? 'n' : ''}">${celula(res.cols[i], v)}</td>`).join('')}</tr>`).join('')}</table>`;
}
const FORA = `<div class="banner sql-aviso"><span class="dot"></span><span><b>A consulta não rodou neste navegador.</b> Os números da página não dependem dela: foram calculados na publicação. Copie a SQL ou baixe o CSV pra rodar no seu DuckDB.</span></div>`;

document.querySelectorAll('details.q-sql[data-sql]').forEach(d => {
  const q = SQLS[d.dataset.sql]; if (!q) return;
  let box = null, digitando = 0;
  const executar = async () => {
    const out = box.querySelector('.res'); out.innerHTML = '<span class="mono" style="color:var(--muted)">rodando…</span>';
    try { let r = await rodar(q.sql); if (q.p) r = comP(r, q.p); out.innerHTML = tabela(r); }
    catch (e) { console.error(e); out.innerHTML = FORA; }
  };
  d.addEventListener('toggle', () => {
    if (!d.open) return;
    if (!box) {
      box = document.createElement('div'); box.className = 'sqlbox';
      box.innerHTML = `<div class="hdr mono"><span>DuckDB · roda no seu navegador</span><span><button type="button" class="btn-mini copiar">copiar SQL</button> &nbsp; <button type="button" class="btn-mini run">▶ rodar de novo</button></span></div><pre></pre><div class="res"></div>`;
      d.appendChild(box);
      box.querySelector('.run').addEventListener('click', executar);
      box.querySelector('.copiar').addEventListener('click', ev => { navigator.clipboard && navigator.clipboard.writeText(q.sql).then(() => { ev.target.textContent = 'copiado'; setTimeout(() => ev.target.textContent = 'copiar SQL', 1500); }); });
    }
    const pre = box.querySelector('pre');
    if (RM) pre.innerHTML = hl(q.sql);
    else { const id = ++digitando; pre.innerHTML = '<span class="cur"></span>';
      tween(Math.min(1400, q.sql.length * 9), 150, t => { if (id !== digitando) return; const n = Math.round(q.sql.length * t); pre.innerHTML = hl(q.sql.slice(0, n)) + (t < 1 ? '<span class="cur"></span>' : ''); }, t => t); }
    executar();
  });
});

// ---------- cards de pergunta executiva (P1–P6): cada seguimento é uma consulta de consultas/ e o gráfico responde a pergunta dele ----------
// Os números e o texto de cada vista vêm de DATA.perguntas (montado na publicação por pipeline/perguntas.py, a partir dos mesmos
// arquivos .sql que a página mostra e que a CI confere). O p é o do teste de Fisher, refeito aqui sobre as contagens.
const PQ = DATA.perguntas || {};
const COR = { c: C.coordenador, g: C.gerente, m: '#d9d9d9' };
const pctN = (k, n) => n ? Math.round(100 * k / n) : 0;
const CARDS = [];

// halteres: linhas {label, xa, na, xb, nb}. Com `grupos`, separa "igual nos dois níveis" de "muda de um nível pro outro" pela régua.
function halteres(box, rows, o = {}) {
  box.innerHTML = ''; const st = stage(box);
  const W = Math.max(320, box.clientWidth), nar = W < 560, L = nar ? 0 : (o.L || 270), Rm = nar ? 6 : 168, rowH = nar ? 58 : 36, top = 22, gapG = 34;
  const cA = o.colA || C.coordenador, cB = o.colB || C.gerente, nA = o.nameA || 'Coordenação', nB = o.nameB || 'Gerência';
  rows = rows.map(r => ({ ...r, pa: 100 * r.xa / r.na, pb: 100 * r.xb / r.nb, p: fisher(r.xa, r.na, r.xb, r.nb) }));
  let ordem;
  if (o.grupos) {
    const igual = rows.filter(r => r.p >= 0.05).sort((a, b) => (b.xa + b.xb) - (a.xa + a.xb));
    const muda = rows.filter(r => r.p < 0.05).sort((a, b) => Math.abs(b.pb - b.pa) - Math.abs(a.pb - a.pa));
    ordem = [...igual.map(r => [r, 'igual']), ...muda.map(r => [r, 'muda'])];
  } else ordem = rows.map(r => [r, '']);
  const ngr = new Set(ordem.map(x => x[1]).filter(Boolean)).size;
  const H = top + ordem.length * rowH + gapG * ngr + 10;
  const s = el('svg', { viewBox: `0 0 ${W} ${H}`, height: H, role: 'img', 'aria-label': ordem.map(([r]) => `${r.label}: ${nA} ${Math.round(r.pa)}%, ${nB} ${Math.round(r.pb)}%`).join('; ') }, box);
  const X = v => L + 18 + (W - L - Rm - 36) * v / 100;
  [0, 25, 50, 75, 100].forEach(v => { el('line', { x1: X(v), x2: X(v), y1: top - 6, y2: H - 4, stroke: '#2a2727' }, s); txt(s, X(v), 12, v + '%', { 'text-anchor': 'middle', class: 'tick' }); });
  let y0 = top, last = '';
  ordem.forEach(([r, grp], i) => {
    if (grp && grp !== last) { y0 += gapG * (last ? 1 : 0.85); txt(s, 0, y0 - 10, grp === 'igual' ? 'IGUAL NOS DOIS NÍVEIS' : 'MUDA DE UM NÍVEL PRO OUTRO', { class: 'grp' }); last = grp; }
    const [stx, sc] = selo(r.p), yR = y0, y = nar ? yR + 34 : yR + rowH / 2; y0 += rowH;
    const g = el('g', { class: 'row' }, s);
    txt(g, 0, nar ? yR + 14 : y + 5, r.label, { class: 'term' });
    const lo = Math.min(r.pa, r.pb), hi = Math.max(r.pa, r.pb);
    const ln = el('line', { y1: y, y2: y, stroke: '#5c5a57', 'stroke-width': 2 }, g);
    const ca = el('circle', { cy: y, r: 6.5, fill: cA, stroke: '#1d1a1a', 'stroke-width': 2 }, g);
    const cb = el('circle', { cy: y, r: 6.5, fill: cB, stroke: '#1d1a1a', 'stroke-width': 2 }, g);
    const esq = lo >= 22;
    const v = txt(g, 0, y + 4, `${Math.round(r.pa)}% · ${Math.round(r.pb)}%`, { class: 'val', style: 'fill:#d9d9d9', 'text-anchor': esq ? 'end' : 'start' });
    const sl = txt(g, W, nar ? yR + 14 : y + 4, nar && sc === '#9a9a96' ? '' : stx, { 'text-anchor': 'end', class: 'tick', style: `fill:${sc};letter-spacing:.1em` });
    st.add(1000, 120 + i * 60, k => { set(ca, { cx: X(r.pa * k) }); set(cb, { cx: X(r.pb * k) }); set(ln, { x1: X(lo * k), x2: X(hi * k) });
      set(v, { x: esq ? X(lo * k) - 13 : X(hi * k) + 13 }); v.style.opacity = Math.max(0, k * 2 - 1); sl.style.opacity = k; }, EASE.outQuint);
    const hit = el('rect', { x: 0, y: yR, width: W, height: rowH, fill: 'transparent' }, g);
    hit.addEventListener('mouseenter', () => { s.classList.add('hovering'); g.classList.add('on'); });
    hit.addEventListener('mousemove', ev => showTip(ev, `<b>${esc(r.label)}</b><br>${sw(cA)}${nA} ${Math.round(r.pa)}% · ${r.xa} de ${r.na}<br>${sw(cB)}${nB} ${Math.round(r.pb)}% · ${r.xb} de ${r.nb}<br>${pTxt(r.p)} · ${stx.toLowerCase()}`));
    hit.addEventListener('mouseleave', () => { s.classList.remove('hovering'); g.classList.remove('on'); hideTip(); });
  });
  st.done(); io.observe(box);
}
const mapaCG = (box, v) => halteres(box, v.d.map(r => ({ label: r.label, xa: r.c, na: NC, xb: r.g, nb: NG })), { grupos: true });
const dumb2 = (box, v) => halteres(box, v.d.rows.map(r => ({ label: r.label, xa: r.a, na: r.na, xb: r.b, nb: r.nb })),
  { colA: '#ffffff', colB: '#9a9a96', nameA: v.d.legA, nameB: v.d.legB, grupos: false });

// núcleo: o % de cada nível com a faixa de 95% (Wilson, calculada na consulta)
function nucleo(box, v) {
  box.innerHTML = ''; const st = stage(box); const rows = v.d;
  const W = Math.max(320, box.clientWidth), nar = W < 560, L = nar ? 0 : 270, Rm = nar ? 6 : 60, rowH = nar ? 66 : 44, top = 22;
  const H = top + rows.length * rowH + 4;
  const s = el('svg', { viewBox: `0 0 ${W} ${H}`, height: H, role: 'img', 'aria-label': 'Itens que mais de 60% das vagas pedem nos dois níveis, com a faixa de 95%' }, box);
  const X = x => L + 18 + (W - L - Rm - 36) * x / 100;
  [0, 25, 50, 75, 100].forEach(x => { el('line', { x1: X(x), x2: X(x), y1: top - 6, y2: H - 4, stroke: '#2a2727' }, s); txt(s, X(x), 12, x + '%', { 'text-anchor': 'middle', class: 'tick' }); });
  rows.forEach((r, i) => {
    const yR = top + i * rowH, base = nar ? yR + 30 : yR + rowH / 2 - 6, g = el('g', { class: 'row' }, s);
    txt(g, 0, nar ? yR + 14 : base + 10, r.label, { class: 'term' });
    [[r.c, NC, C.coordenador, base], [r.g, NG, C.gerente, base + 12]].forEach(([d, n, col, y], j) => {
      const [k, lo, hi] = d, p0 = 100 * k / n;
      const band = el('line', { y1: y, y2: y, stroke: col, 'stroke-width': 4, 'stroke-linecap': 'round', opacity: .45 }, g);
      const dot = el('circle', { cy: y, r: 5, fill: col, stroke: '#1d1a1a', 'stroke-width': 1.5 }, g);
      st.add(900, 150 + i * 70 + j * 60, t => { set(band, { x1: X(lerp(p0, lo, t)), x2: X(lerp(p0, hi, t)) }); set(dot, { cx: X(p0) }); dot.style.opacity = t; }, EASE.outQuint);
    });
    const p = fisher(r.c[0], NC, r.g[0], NG), hit = el('rect', { x: 0, y: yR, width: W, height: rowH, fill: 'transparent' }, g);
    hit.addEventListener('mouseenter', () => { s.classList.add('hovering'); g.classList.add('on'); });
    hit.addEventListener('mousemove', ev => showTip(ev, `<b>${esc(r.label)}</b><br>${sw(C.coordenador)}Coordenação ${pctN(r.c[0], NC)}% (${r.c[1]}–${r.c[2]}%)<br>${sw(C.gerente)}Gerência ${pctN(r.g[0], NG)}% (${r.g[1]}–${r.g[2]}%)<br>${pTxt(p)} · ${p < 0.05 ? 'as faixas não se cruzam por inteiro' : 'as faixas se cruzam'}`));
    hit.addEventListener('mouseleave', () => { s.classList.remove('hovering'); g.classList.remove('on'); hideTip(); });
  });
  st.done(); io.observe(box);
}

// diferença em pontos (gerência − coordenação); a barra cheia passa na régua, a tracejada não
function difBars(box, v) {
  box.innerHTML = ''; const st = stage(box); const rows = v.d;
  const W = Math.max(320, box.clientWidth), nar = W < 560, L = nar ? 0 : 270, Rm = nar ? 6 : 150, rowH = nar ? 50 : 27, top = 24;
  const H = top + rows.length * rowH + 8;
  const s = el('svg', { viewBox: `0 0 ${W} ${H}`, height: H, role: 'img', 'aria-label': 'Diferença em pontos percentuais entre gerência e coordenação, por item' }, box);
  const M = Math.max(45, Math.ceil(Math.max(...rows.map(r => Math.abs(r.d)), 1) / 5) * 5 + 2), X = x => L + 10 + (W - L - Rm - 20) * (x + M) / (2 * M);
  [-40, -20, 0, 20, 40].filter(x => Math.abs(x) <= M).forEach(x => { el('line', { x1: X(x), x2: X(x), y1: top - 6, y2: H - 4, stroke: x === 0 ? '#5c5a57' : '#2a2727' }, s); txt(s, X(x), 12, (x > 0 ? '+' : '') + x, { 'text-anchor': 'middle', class: 'tick' }); });
  rows.forEach((r, i) => {
    const p = fisher(r.c, NC, r.g, NG), [stx, sc] = selo(p), strong = p < 0.05, yR = top + i * rowH, y = nar ? yR + 32 : yR + rowH / 2, col = r.d > 0 ? C.gerente : C.coordenador;
    const g = el('g', { class: 'row' }, s);
    txt(g, 0, nar ? yR + 14 : y + 5, r.label, { class: 'term', style: strong ? '' : 'fill:#9a9a96' });
    const bar = el('rect', { y: y - 7, height: 14, rx: 3, fill: strong ? col : 'transparent', stroke: col, 'stroke-width': strong ? 0 : 1, 'stroke-dasharray': strong ? '' : '3 3', opacity: strong ? 1 : .55 }, g);
    const val = txt(g, 0, y + 4, (r.d > 0 ? '+' : '') + r.d, { class: 'val', style: `fill:${strong ? '#ffffff' : '#9a9a96'}`, 'text-anchor': r.d > 0 ? 'start' : 'end' });
    const sl = txt(g, W, nar ? yR + 14 : y + 4, nar && !strong ? '' : stx, { 'text-anchor': 'end', class: 'tick', style: `fill:${sc};letter-spacing:.1em` });
    st.add(900, 120 + i * 40, k => { const a = X(0), b = X(r.d * k); set(bar, { x: Math.min(a, b), width: Math.max(0.01, Math.abs(b - a)) });
      set(val, { x: r.d > 0 ? b + 8 : b - 8 }); val.style.opacity = Math.max(0, k * 2 - 1); sl.style.opacity = k; }, EASE.outQuint);
    const hit = el('rect', { x: 0, y: yR, width: W, height: rowH, fill: 'transparent' }, g);
    hit.addEventListener('mouseenter', () => { s.classList.add('hovering'); g.classList.add('on'); });
    hit.addEventListener('mousemove', ev => showTip(ev, `<b>${esc(r.label)}</b><br>${sw(C.coordenador)}Coordenação ${pctN(r.c, NC)}% · ${r.c} de ${NC}<br>${sw(C.gerente)}Gerência ${pctN(r.g, NG)}% · ${r.g} de ${NG}<br>${r.d > 0 ? '+' : ''}${r.d} pontos · ${pTxt(p)} · ${stx.toLowerCase()}`));
    hit.addEventListener('mouseleave', () => { s.classList.remove('hovering'); g.classList.remove('on'); hideTip(); });
  });
  st.done(); io.observe(box);
}

// barras empilhadas por linha (onde o item aparece no anúncio)
function stack(box, v) {
  box.innerHTML = ''; const wrap = document.createElement('div'); wrap.className = 'stks'; box.appendChild(wrap);
  v.d.forEach((r, i) => {
    const col = COR[r.cor] || COR.m, d = document.createElement('div');
    d.innerHTML = `<div class="stk-h"><span><i style="background:${col}"></i>${esc(r.label)}</span><span class="mono">${r.total} ${r.total === 1 ? 'vaga' : 'vagas'}</span></div><div class="stk"></div><div class="stk-l"></div>`;
    wrap.appendChild(d);
    const stk = d.querySelector('.stk'), lg = d.querySelector('.stk-l');
    r.segs.forEach(([nome, k, op], j) => {
      const c = op === 0 ? '#5c5a57' : col, o = op === 0 ? 1 : op, seg = document.createElement('div');
      seg.style.cssText = `background:${c};opacity:${o};width:0;transition:width ${RM ? 0 : .9}s var(--ease) ${RM ? 0 : 0.15 * j + 0.1 * i}s`;
      seg.textContent = k >= 3 ? k : ''; seg.title = `${nome}: ${k} de ${r.total}`;
      stk.appendChild(seg);
      requestAnimationFrame(() => requestAnimationFrame(() => { seg.style.width = (r.total ? 100 * k / r.total : 0) + '%'; }));
      lg.insertAdjacentHTML('beforeend', `<span><i style="background:${c};opacity:${o}"></i>${esc(nome)} · ${k}</span>`);
    });
  });
}

// barras horizontais simples: {label, v, txt, cor, op}
function hbars(box, v) {
  box.innerHTML = '';
  const rows = v.d.rows, max = v.d.max || 1;
  box.innerHTML = '<div class="hbs">' + rows.map(r => `<div class="hb"><span class="hl">${esc(r.label)}</span><span class="ht"><i data-w="${(100 * r.v / max).toFixed(1)}" style="background:${COR[r.cor] || COR.m};opacity:${r.op ?? 1}"></i></span><span class="hv">${esc(r.txt)}</span></div>`).join('') + '</div>';
  box.querySelectorAll('.ht i').forEach((b, i) => { b.style.transition = `width ${RM ? 0 : .9}s var(--ease) ${RM ? 0 : i * 0.07}s`; requestAnimationFrame(() => requestAnimationFrame(() => { b.style.width = b.dataset.w + '%'; })); });
}

// contagens por categoria, coordenação × gerência (barras pareadas)
function grupos(box, v) {
  const rows = v.d, max = Math.max(1, ...rows.map(r => Math.max(r.c / NC, r.g / NG)));
  box.innerHTML = '<div class="cbars">' + rows.map(r => {
    const p = fisher(r.c, NC, r.g, NG);
    return `<div class="cbar" title="${esc(r.label)}: coordenação ${r.c} de ${NC} · gerência ${r.g} de ${NG} · ${pTxt(p)}"><span>${esc(r.label)}</span><div class="tr">
      <span style="background:${C.coordenador}" data-w="${(80 * r.c / NC / max).toFixed(1)}"><em>${r.c} · ${pctN(r.c, NC)}%</em></span>
      <span style="background:${C.gerente}" data-w="${(80 * r.g / NG / max).toFixed(1)}"><em>${r.g} · ${pctN(r.g, NG)}%</em></span></div></div>`;
  }).join('') + '</div>';
  box.querySelectorAll('.tr > span').forEach((b, i) => { b.style.transition = `width ${RM ? 0 : .9}s var(--ease) ${RM ? 0 : i * 0.05}s`; requestAnimationFrame(() => requestAnimationFrame(() => { b.style.width = b.dataset.w + '%'; })); });
}

// números grandes por nível (P6, e o topo dos seguimentos "não sustenta" e "falta no dado")
const blocosHTML = xs => `<div class="big2">${xs.map(b => `<div><b style="${b.cor ? 'color:' + COR[b.cor] : ''}">${esc(b.v)}</b><span class="mono">${esc(b.rot)}</span></div>`).join('')}</div>`;
function big(box, v) {
  box.innerHTML = blocosHTML(v.d.blocos) + blocosHTML(v.d.blocos2);
}

// seguimento que a amostra não sustenta (ou que falta no dado): fica no card, com os números do que existe, a tabela da consulta e o que falta
function semGrafico(box, v, medidor) {
  const d = v.d;
  const blocos = d.blocos || [{ v: fmt(d.n), rot: d.grande }, { v: fmt(d.min), rot: `mínimo pro gráfico aparecer, em ${d.unidade}` }];
  const lista = d.itens
    ? `<div class="res-t"><table>${d.itens.map(x => `<tr><td>${esc(x.label)}</td><td class="n">${x.fmt ? esc(x.fmt) : `<span style="color:${C.coordenador}">${x.c} coord.</span> · <span style="color:${C.gerente}">${x.g} ger.</span>`}</td></tr>`).join('')}</table></div>`
    : `<div class="res-t">${tabela({ cols: v.res.cols, rows: v.res.rows })}</div>`;
  const meter = medidor ? `<div class="meter"><i style="width:${Math.min(100, 100 * d.n / d.min)}%"></i><b style="left:100%"></b></div><span class="mono mt">${fmt(d.n)} de ${fmt(d.min)} ${esc(d.unidade)} pro gráfico aparecer</span>` : '';
  box.innerHTML = `<div class="ns2 fadein">${blocosHTML(blocos)}${d.blocos2 ? blocosHTML(d.blocos2) : ''}${meter}${lista}<p class="ns-p">${d.texto}</p></div>`;
}
const naoSustenta = (box, v) => semGrafico(box, v, true);
const falta = (box, v) => semGrafico(box, v, false);

const DESENHA = {
  mapa: mapaCG, nucleo, dif: difBars, nat: stack, hb: hbars, grupos, big, nao: naoSustenta, falta, dumb2,
  waffle: (box, v) => waffle(box, v.d),
  salario: box => salario(box),
  tabela: (box, v) => { box.innerHTML = '<div class="res-t">' + tabela({ cols: v.res.cols, rows: v.res.rows }) + '</div>'; },
};
function legenda(v) {
  if (v.leg === 1) return `<span><i style="background:${C.coordenador}"></i>Coordenação, ${NC} vagas</span><span><i style="background:${C.gerente}"></i>Gerência, ${NG} vagas</span>`;
  if (v.leg === 2) return `<span><i class="sq" style="background:${C.coordenador}"></i>mais pedido na coordenação</span><span><i class="sq" style="background:${C.gerente}"></i>mais pedido na gerência</span><span><i class="sq" style="border:1px dashed #9a9a96;background:transparent"></i>sem diferença clara</span>`;
  if (v.leg === 4) return `<span><i style="background:${C.coordenador}"></i>Coordenação</span><span><i style="background:${C.gerente}"></i>Gerência</span><span><span class="dashl"></span>faixa repetida de um guia salarial</span>`;
  if (v.leg === 3) return `<span><i style="background:#ffffff"></i>${esc(v.d.legA)}</span><span><i style="background:#9a9a96"></i>${esc(v.d.legB)}</span>`;
  return '';
}
function aviso(v) {
  if (v.tipo !== 'salario') return '';
  const b = v.d;
  return `<div class="warn"><b>Isto não é o que as vagas pagam.</b> É a referência de mercado pro cargo e a cidade de cada vaga, de ${fmt(b.fontes)} referências em ${fmt(b.dominios)} sites (guias salariais, Glassdoor, Indeed e outros). Parte das fontes bloqueia leitura automática e veio de resumo de busca.</div>`;
}

function iniciaCards() {
  document.querySelectorAll('.pq').forEach(root => {
    const sec = root.closest('section'), spec = PQ[sec.dataset.p]; if (!spec) return;
    const chart = root.querySelector('.chart'), ol = root.querySelector('.nq ol'), det = root.querySelector('details.q-sql'), view = root.querySelector('.view');
    const avisoBox = document.createElement('div'); avisoBox.className = 'vaviso'; chart.before(avisoBox);
    let cur = 0, box = null, digitando = 0;
    const V = () => spec.views[cur];
    const desenha = () => { const v = V(); chart.innerHTML = ''; chart.classList.remove('fadein'); void chart.offsetWidth; chart.classList.add('fadein'); (DESENHA[v.tipo] || (() => {}))(chart, v); };
    async function preencheSQL(animar) {
      if (!box) return; const v = V(), pre = box.querySelector('pre'), out = box.querySelector('.res');
      box.querySelector('.fn').textContent = 'consultas/' + v.f + '.sql';
      if (RM || !animar) pre.innerHTML = hl(v.sql);
      else { const id = ++digitando; pre.innerHTML = '<span class="cur"></span>';
        tween(Math.min(1400, v.sql.length * 6), 100, t => { if (id !== digitando) return; const n = Math.round(v.sql.length * t); pre.innerHTML = hl(v.sql.slice(0, n)) + (t < 1 ? '<span class="cur"></span>' : ''); }, t => t); }
      out.innerHTML = '<span class="mono" style="color:var(--muted)">rodando…</span>';
      const i0 = cur;
      try { const r = await rodar(v.sql); if (i0 === cur) out.innerHTML = tabela(r); }
      catch (e) { console.error(e); if (i0 === cur) out.innerHTML = FORA + tabela(v.res); }
    }
    function mostra(i) {
      cur = i; const v = V();
      ol.querySelectorAll('.nqb').forEach((b, j) => { b.classList.toggle('on', j === i); b.setAttribute('aria-pressed', j === i); });
      root.querySelector('.vtag').textContent = v.tag; root.querySelector('.vfile').textContent = 'consultas/' + v.f + '.sql';
      root.querySelector('.leg').innerHTML = legenda(v); avisoBox.innerHTML = aviso(v); root.querySelector('.vnote').textContent = v.nota;
      chart.dataset.seen = ''; desenha(); if (det.open) preencheSQL(true);
    }
    ol.addEventListener('click', e => { const b = e.target.closest('.nqb'); if (b) mostra(+b.dataset.i); });
    det.addEventListener('toggle', () => {
      if (!det.open) return;
      if (!box) {
        box = document.createElement('div'); box.className = 'sqlbox';
        box.innerHTML = `<div class="hdr mono"><span class="fn"></span><span>DuckDB · roda no seu navegador &nbsp; <button type="button" class="btn-mini copiar">copiar SQL</button> &nbsp; <button type="button" class="btn-mini run">▶ rodar de novo</button></span></div><pre></pre><div class="res"></div>`;
        det.appendChild(box);
        box.querySelector('.run').addEventListener('click', () => preencheSQL(false));
        box.querySelector('.copiar').addEventListener('click', ev => { navigator.clipboard && navigator.clipboard.writeText(V().sql).then(() => { ev.target.textContent = 'copiado'; setTimeout(() => ev.target.textContent = 'copiar SQL', 1500); }); });
      }
      preencheSQL(true);
    });
    CARDS.push({ desenha });
    mostra(0);
  });
}

// ---------- navegação: rail de bolas, sumário no celular, barra de progresso na cor do capítulo (Item 18) ----------
const secs = [...document.querySelectorAll('section[data-rail]')];
const CAPCOR = { cap: '--c-cap', met: '--c-met', ana: '--c-ana', arq: '--c-arq', exp: '--c-exp' };
let curSec = 0;
(function () {
  const rail = document.getElementById('rail'); let prev = null;
  secs.forEach(s => {
    const li = document.createElement('li'); li.dataset.cap = s.dataset.cap;
    if (prev && prev !== s.dataset.cap) li.className = 'gap';
    prev = s.dataset.cap;
    const a = document.createElement('a'); a.href = '#' + s.id; a.setAttribute('aria-label', s.dataset.rail);
    const t = document.createElement('span'); t.className = 'rail-tip'; t.textContent = s.dataset.rail;
    li.append(a, t); rail.appendChild(li);
  });
  const dots = [...rail.querySelectorAll('a')];
  railUpdate = () => {
    const y = scrollY + innerHeight * 0.35;
    let cur = 0; secs.forEach((s, i) => { if (s.getBoundingClientRect().top + scrollY <= y) cur = i; });
    curSec = cur;
    dots.forEach((d, i) => d.setAttribute('aria-current', i === cur ? 'true' : 'false'));
    document.documentElement.style.setProperty('--sec-now', `var(${CAPCOR[secs[cur].dataset.cap]})`);
    const h = document.documentElement.scrollHeight - innerHeight; prog.style.transform = `scaleX(${h > 0 ? scrollY / h : 0})`;
  };
  railUpdate();

  // folha de baixo pra cima (celular): o mesmo sumário da página
  const fab = document.getElementById('fab'), folha = document.getElementById('folha'), dim = document.getElementById('dim');
  const fecha = () => { folha.hidden = true; dim.hidden = true; fab.setAttribute('aria-expanded', 'false'); };
  fab.addEventListener('click', () => {
    const aqui = secs[curSec];
    folha.innerHTML = '<div class="grab"></div><div class="mono" style="color:var(--muted)">Sumário · você está em ' + esc(aqui.dataset.rail) + '</div>' +
      `<div class="scap" data-cap="cap"><span class="mono">00 · O projeto</span><a href="#s-projeto" class="${aqui.id === 's-projeto' ? 'cur' : ''}"><i></i>O que é, o que tem aqui e quem fez</a></div>` +
      [...document.querySelectorAll('.sumario .cap')].map(c => `<div class="scap" data-cap="${c.dataset.cap}"><span class="mono">${esc(c.querySelector('.mono').textContent)} · ${esc(c.querySelector('h3').textContent)}</span>` +
        [...c.querySelectorAll('li a')].map(a => { const [n, t] = [a.children[0].textContent, a.children[1].textContent], h = a.getAttribute('href');
          return `<a href="${h}" class="${h === '#' + aqui.id ? 'cur' : ''}"><i></i>${esc(n === '—' ? t : n + ' ' + t)}</a>`; }).join('') + '</div>').join('');
    folha.hidden = false; dim.hidden = false; fab.setAttribute('aria-expanded', 'true');
  });
  folha.addEventListener('click', e => { if (e.target.closest('a')) fecha(); });
  dim.addEventListener('click', fecha);
  addEventListener('keydown', e => { if (e.key === 'Escape') fecha(); });
  // o botão fica no canto da parte visível da tela: com a barra do navegador que encolhe, ou com zoom por pinça, o `fixed` do layout pode sair da tela
  if (window.visualViewport) {
    const vv = window.visualViewport;
    const ajusta = () => { const dx = vv.offsetLeft + vv.width - innerWidth, dy = vv.offsetTop + vv.height - innerHeight;
      fab.style.transform = (Math.abs(dx) > 0.5 || Math.abs(dy) > 0.5) ? `translate3d(${dx}px, ${dy}px, 0)` : ''; };
    vv.addEventListener('resize', ajusta); vv.addEventListener('scroll', ajusta); ajusta();
  }
})();

// ---------- 3.2 · do anúncio às linhas (exemplo inventado, site/exemplo.json) ----------
async function exemplo() {
  const paper = document.getElementById('paper'); if (!paper) return;
  const EX = await (await fetch('exemplo.json')).json();
  let n = 0, marcas = 0, outro = 0; const ferrSet = new Set(), cont = {}, csv = ['id_publico,ordem,secao,natureza,itens,ferramentas'];
  let html = `<div class="ph">${esc(EX.titulo)}</div><div class="pm">${esc(EX.meta)}</div>`;
  html += `<div class="blk solta"><h4><span>Sobre a empresa</span><span class="fora">fica de fora</span></h4><p>${esc(EX.sobre)}</p></div>`;
  EX.secoes.forEach(([sec, linhas]) => {
    html += `<div class="blk"><h4><span>${esc(sec)}</span><span class="fora"></span></h4>`;
    linhas.forEach(([t, nat, its, fer]) => {
      n++; marcas += its.length; if (!its.length) outro++; fer.forEach(f => ferrSet.add(f)); its.forEach(k => cont[k] = (cont[k] || 0) + 1);
      const chips = `<span class="chip nat">${nat}</span>` + (its.length ? its.map(k => `<span class="chip">${esc(IT[k].item)}</span>`).join('') : '<span class="chip out">outro</span>') + fer.map(f => `<span class="chip fer">${esc(f)}</span>`).join('');
      html += `<div class="lin"><span class="n">${String(n).padStart(2, '0')}</span><div class="t"><span>${esc(t)}</span><div class="chips2">${chips}</div></div></div>`;
      if (csv.length < 6) csv.push(`exemplo,${n},${sec.toLowerCase()},${nat},${its.join('|') || 'outro'},${fer.join('|')}`);
    });
    html += '</div>';
  });
  html += `<div class="blk solta"><h4><span>Benefícios</span><span class="fora">fica de fora</span></h4><p>${esc(EX.beneficios)}</p></div>`;
  paper.innerHTML = html;
  const vals = { linhas: n, secoes: EX.secoes.length, marcas, outro, distintos: Object.keys(cont).length, ferr: ferrSet.size };
  document.querySelectorAll('#ex [data-k]').forEach(b => b.textContent = vals[b.dataset.k]);
  const porDim = {}; Object.entries(cont).forEach(([k, c]) => { (porDim[IT[k].dim] = porDim[IT[k].dim] || []).push([IT[k].item, c]); });
  document.getElementById('itens').innerHTML = Object.entries(porDim).map(([d, its]) => `<div><div class="dm">${esc(d)}</div><div class="its">${its.map(([t, c]) => `<span>${esc(t)}${c > 1 ? `<i>(${c})</i>` : ''}</span>`).join('')}</div></div>`).join('');
  document.getElementById('csv').textContent = '# rotulos.csv, colunas resumidas: o que sai pra fora (sem o texto)\n' + csv.join('\n') + '\n…';
  const ex = document.getElementById('ex'), btns = [...document.querySelectorAll('#passos .pill')];
  let timer = null;
  const go = s => { ex.dataset.s = s; btns.forEach(b => b.classList.toggle('on', b.dataset.s == s)); };
  btns.forEach(b => b.addEventListener('click', () => { clearInterval(timer); go(b.dataset.s); }));
  if (RM) { go(4); return; }
  const o = new IntersectionObserver(es => { if (es[0].isIntersecting) { o.disconnect(); let s = 1; timer = setInterval(() => { s++; go(s); if (s >= 4) clearInterval(timer); }, 2800); } }, { threshold: 0.35 });
  o.observe(ex);
}

// ---------- 3.4 · retrato da amostra (descreve a busca, não o mercado) ----------
const RT = DATA.retrato;
const barIO = new IntersectionObserver(es => es.forEach(e => { if (!e.isIntersecting) return; barIO.unobserve(e.target); e.target.querySelectorAll('.fl').forEach(f => f.style.width = f.dataset.w); }), { threshold: 0.12 });
function barras(id, rows, tot) {
  const box = document.getElementById(id); if (!box) return; box.innerHTML = '';
  const max = Math.max(1, ...rows.map(r => r[1]));
  rows.forEach(([k, v, na]) => {
    const r = document.createElement('div'); r.className = 'bar';
    r.innerHTML = `<span>${esc(k)}</span><span class="tr"><span class="fl${na ? ' na' : ''}" data-w="${(100 * v / max).toFixed(1)}%"></span></span><span class="v">${fmt(v)}</span>`;
    r.addEventListener('mousemove', e => showTip(e, `<b>${esc(k)}</b><br>${fmt(v)} de ${fmt(tot)}${tot ? ' · ' + Math.round(100 * v / tot) + '%' : ''}`));
    r.addEventListener('mouseleave', hideTip);
    box.appendChild(r);
  });
  if (RM) box.querySelectorAll('.fl').forEach(f => f.style.width = f.dataset.w); else barIO.observe(box);
}
const dias = n => `${n} ${n === 1 ? 'dia' : 'dias'}`;
function retrato() {
  const V = DATA.manifest.contagens.vagas;
  barras('b-uf', RT.uf, V); barras('b-cid', RT.cid, V); barras('b-ats', RT.ats, V); barras('b-niv', RT.niv, V); barras('b-reg', RT.reg, V);
  barras('b-con', RT.con, V); barras('b-set', RT.set, V); barras('b-idi', RT.idi, V); barras('b-sec', RT.sec, V); barras('b-ref', RT.ref, RT.ref_total);
  const A = RT.atraso;
  document.getElementById('s-tempo').innerHTML =
    `<div><b>${dias(A.pub_cap)}</b><span>mediana entre a publicação e a captura (dos ${fmt(A.n_pub)} anúncios com data de publicação)</span></div>` +
    `<div><b>${dias(A.cap_ana)}</b><span>mediana entre a captura e a leitura linha a linha</span></div>` +
    `<div><b>${fmt(A.mesmo_dia)} de ${fmt(V)}</b><span>lidas no mesmo dia da captura</span></div>`;
  document.getElementById('s-tam').innerHTML =
    `<div><b>${RT.med_secoes.join(' · ')}</b><span>mediana de linhas em responsabilidades, requisitos e diferenciais</span></div>` +
    `<div><b>${fmt(RT.n_com_dif)} de ${fmt(RT.n_classificadas)}</b><span>anúncios classificados têm seção de diferenciais</span></div>` +
    `<div><b>${String(RT.itens_linha).replace('.', ',')}</b><span>itens por linha, em média (nas linhas com ao menos um item)</span></div>`;
  tempo(document.getElementById('c-tempo')); tamanho(document.getElementById('c-tam'));
}
function tempo(box) {
  box.innerHTML = ''; const st = stage(box);
  const W = Math.max(320, box.clientWidth), narrow = W < 600, L = narrow ? 0 : 150, band = 54, H = band * 3 + 34 + (narrow ? 14 * 3 : 0);
  const s = el('svg', { viewBox: `0 0 ${W} ${H}`, height: H, role: 'img', 'aria-label': 'Vagas por semana: publicadas, capturadas e lidas linha a linha' }, box);
  const n = RT.semanas.length; if (!n) return;
  const bw = (W - L) / n, max = Math.max(1, ...['pub', 'cap', 'ana'].flatMap(k => Object.values(RT[k])));
  const faixa = narrow ? band + 14 : band;
  [['publicada', RT.pub, 'pelo anúncio'], ['capturada', RT.cap, 'quando o autor viu'], ['lida linha a linha', RT.ana, 'estruturada']].forEach(([nome, m, sub], r) => {
    const y0 = r * faixa + band - 6 + (narrow ? 14 : 0);
    txt(s, 0, y0 - (narrow ? 32 : 18), nome.toUpperCase(), { class: 'tick', style: 'fill:#d9d9d9' });
    if (!narrow) txt(s, 0, y0 - 4, sub, { class: 'tick' });
    el('line', { x1: L, x2: W, y1: y0, y2: y0, stroke: '#3d3d3d' }, s);
    RT.semanas.forEach((w, i) => { const v = m[w] || 0; if (!v) return;
      const h = Math.max(2, (band - 12) * v / max);
      const rc = el('rect', { x: L + i * bw + 1, y: y0, width: Math.max(1, bw - 2), height: 0, rx: 2, fill: '#d9d9d9' }, s);
      st.add(500, 80 + i * 14, t => set(rc, { y: y0 - h * t, height: h * t }));
      rc.addEventListener('mousemove', e => showTip(e, `<b>${nome}</b><br>semana de ${w.slice(8)}/${w.slice(5, 7)}: ${v} vaga${v > 1 ? 's' : ''}`)); rc.addEventListener('mouseleave', hideTip);
    });
  });
  const MES = ['', 'jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']; let last = '';
  RT.semanas.forEach((w, i) => { const m = w.slice(5, 7); if (m !== last) { last = m; txt(s, L + i * bw, H - 4, MES[+m], { class: 'tick' }); el('line', { x1: L + i * bw, x2: L + i * bw, y1: 6, y2: H - 18, stroke: '#2a2727' }, s); } });
  st.done(); io.observe(box);
}
function tamanho(box) {
  box.innerHTML = ''; const st = stage(box);
  const W = Math.max(320, box.clientWidth), narrow = W < 600, L = narrow ? 0 : 130, H = narrow ? 190 : 150;
  const todos = [...RT.tam.coordenador, ...RT.tam.gerente]; if (!todos.length) return;
  const xmax = Math.max(50, Math.ceil(Math.max(...todos) / 10) * 10);
  const s = el('svg', { viewBox: `0 0 ${W} ${H}`, height: H, role: 'img', 'aria-label': 'Linhas classificadas por vaga, por nível' }, box);
  const x = v => L + (W - L - 10) * v / xmax;
  for (let t = 0; t <= xmax; t += 10) { el('line', { x1: x(t), x2: x(t), y1: 8, y2: H - 22, stroke: '#2a2727' }, s); txt(s, x(t) - 6, H - 4, String(t), { class: 'tick' }); }
  [['coordenador', 'Coordenação', C.coordenador, narrow ? 62 : 40], ['gerente', 'Gerência', C.gerente, narrow ? 132 : 92]].forEach(([k, nome, cor, cy]) => {
    txt(s, 0, narrow ? cy - 34 : cy + 4, nome.toUpperCase(), { class: 'tick', style: 'fill:#d9d9d9' });
    const seen = {};
    RT.tam[k].forEach((v, i) => { const o = (seen[v] = (seen[v] || 0) + 1) - 1;
      const c = el('circle', { cx: x(v), cy: cy + (o % 2 ? 1 : -1) * Math.ceil(o / 2) * 7, r: 0, fill: cor, stroke: '#1d1a1a', 'stroke-width': 1.5 }, s);
      st.add(400, 100 + i * 25, t => set(c, { r: Math.max(0, 4.5 * t) }), EASE.back);
      c.addEventListener('mousemove', e => showTip(e, `<b>${nome}</b><br>uma vaga com ${v} linhas`)); c.addEventListener('mouseleave', hideTip); });
    const m = [...RT.tam[k]].sort((a, b) => a - b), med = m.length % 2 ? m[(m.length - 1) / 2] : (m[m.length / 2 - 1] + m[m.length / 2]) / 2;
    el('line', { x1: x(med), x2: x(med), y1: cy - 22, y2: cy + 22, stroke: '#ffffff', 'stroke-width': 2 }, s);
    txt(s, x(med) + 6, cy - 16, 'mediana ' + String(med).replace('.', ','), { class: 'tick' });
  });
  txt(s, W - 110, 10, 'linhas por vaga →', { class: 'tick' });
  st.done(); io.observe(box);
}

// ---------- 2.2 · tabelas e colunas, e a consulta livre ----------
const AMBAR = new Set(['uf', 'cidade', 'regime', 'contrato', 'fonte', 'ats', 'setor', 'mes', 'data_publicacao', 'data_captura', 'data_analise', 'idioma', 'tem_sobre_empresa', 'tem_beneficios']);
function colunas() {
  document.getElementById('colunas').innerHTML = '<div class="tabcols">' + Object.entries(DATA.colunas).map(([t, cols]) =>
    `<span class="mono">${esc(t)}</span><div class="campos">${cols.map(c => `<span class="${AMBAR.has(c) ? 'am' : ''}">${esc(c)}</span>`).join('')}</div>`).join('') + '</div>';
  const u = document.getElementById('url-parquet');
  if (u && /^https?:/.test(location.href)) u.textContent = `select * from '${new URL('dados/mart_vagas.parquet', location.href).href}'`;
  const ta = document.getElementById('sql-livre'), out = document.getElementById('sql-res');
  const roda = async () => {
    out.innerHTML = '<span class="mono" style="color:var(--muted)">rodando…</span>';
    try { const r = await rodar(ta.value); const MAXL = 200;
      out.innerHTML = tabela({ cols: r.cols, rows: r.rows.slice(0, MAXL) }) + (r.rows.length > MAXL ? `<p class="note">Mostrando as primeiras ${MAXL} de ${fmt(r.rows.length)} linhas.</p>` : r.rows.length === 0 ? '<p class="note">Nenhuma linha.</p>' : ''); }
    catch (e) { console.error(e); out.innerHTML = /Failed to fetch|\.parquet|instantiate|wasm|worker/i.test(String(e)) ? FORA : `<div class="erro">${esc(e.message || e)}</div>`; }
  };
  document.getElementById('sql-rodar').addEventListener('click', roda);
  ta.addEventListener('keydown', e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); roda(); } });
}

// ---------- 4.1 · arquitetura: o fluxo do dado, animado (Item 14) ----------
// Todos os números vêm de DATA.arq (calculado na publicação por pipeline/gerar_site.py); nada é digitado aqui.
const AQ = DATA.arq;
const NUM = ['zero', 'um', 'dois', 'três', 'quatro', 'cinco', 'seis', 'sete', 'oito', 'nove', 'dez'];
const ST = [
  { n: '00', t: ['Origem', 'privada'], c: fmt(AQ.vagas), num: AQ.vagas, cl: ['vagas, com o', 'anúncio inteiro'], origem: 1 },
  { n: '01', t: ['Classificação', 'por IA'], c: fmt(AQ.rot), num: AQ.rot, cl: ['de ' + fmt(AQ.linhas) + ' linhas', 'classificadas'], ai: 1 },
  { n: '02', t: ['Exportador', 'e sigilo'], c: AQ.arquivos + ' + 1', cl: ['arquivos e', 'o manifesto'] },
  { n: '03', t: ['Repositório', 'público'], c: '1 commit', cl: ['por publicação:', 'um retrato do dado'] },
  { n: '04', t: ['CI · GitHub Actions'], c: fmt(AQ.testes), num: AQ.testes, cl: ['testes a cada', 'publicação'], ci: 1 },
  { n: '05', t: ['GitHub', 'Pages'], c: String(AQ.parquet), num: AQ.parquet, cl: ['tabelas em Parquet', '+ pagina.json'] },
  { n: '06', t: ['Seu', 'navegador'], c: '0', num: 0, cl: ['servidor na', 'sua consulta'] },
];
const MODES = { fluxo: [0, 1, 2, 3, 4, 5, 6], testes: [2, 4, 5], sigilo: [2, 4], ia: [1], custo: [1, 4, 5, 6] };
const CHIPS = [['fluxo', 'Fluxo'], ['testes', 'Testes'], ['sigilo', 'Sigilo'], ['ia', 'Onde há IA'], ['custo', 'Custo']];
const DET = [
  { h: 'A vaga é guardada aqui, com o anúncio inteiro, e daqui não sai sozinha.',
    p: ['Os dados nascem de um app de acompanhamento de vagas que o autor desenvolveu. Ele fica fechado: nenhuma parte deste repositório se conecta a ele, e a página não mostra o que tem dentro.',
        'Toda semana, de forma automática, sai daqui só o que o contrato de dados permite.'],
    g: 'Nenhuma: a guarda está no estágio 02.', w: 'README, "Como a amostra foi formada"' },
  { h: 'Um modelo de linguagem marca os itens da lista fechada em cada linha.',
    p: [`Cada anúncio é quebrado em linhas (responsabilidades, requisitos, diferenciais) e o <b>${AQ.modelo}</b> marca, em cada uma, a natureza e os itens da lista de ${AQ.itens}. Ferramenta não passa pelo modelo: é regra fixa sobre o nome.`,
        'Roda do lado privado, pela assinatura do autor, sem API paga. Só linha nova é classificada. <b>O texto da linha fica; só o rótulo segue.</b>'],
    g: 'A régua: uma referência revisada por pessoa e o modelo escolhido contra ela (a bancada, abaixo).', w: '<code>rotulagem/prompt.md</code> · <code>evals/relatorio.md</code>' },
  { h: 'Monta os arquivos públicos e barra o que não pode sair.',
    p: ['Sai uma vaga por linha (empresa, cargo, local, link, datas), o rótulo de cada linha sem o texto, o resumo dos requisitos, a referência salarial com a fonte e o setor da empresa: <code>vagas.csv</code>, <code>rotulos.csv</code>, <code>requisitos.csv</code>, <code>benchmarks.csv</code>, <code>empresas.csv</code> e o <code>manifest.json</code>.',
        'O texto do anúncio não atravessa.'],
    g: 'Checagem de sigilo antes do commit.', w: 'README, "Contrato de dados"' },
  { h: 'Cada publicação é um commit em data/.',
    p: ['Ninguém edita os CSV à mão: só a publicação automática escreve em <code>data/</code>, um commit por vez. O histórico do git guarda cada retrato do dado, e é dele que sai uma série no tempo, quando houver janela pra isso.'],
    g: 'O histórico: qualquer número pode ser refeito sobre a versão daquela semana.', w: '<code>data/</code> · histórico do repositório' },
  { h: 'O commit dispara a conferência, sem nenhuma credencial.',
    p: [`O GitHub Actions confere o contrato, o hash de cada arquivo e o sigilo de novo (<code>check_data.py</code>), roda o <code>dbt build</code> sobre DuckDB, com <b>${AQ.testes} testes</b> (chave única, valor na lista, linha de contexto sem item, datas coerentes, cobertura da classificação), e refaz os achados em texto.`,
        '<b>Se um teste falha, nada é publicado e a versão anterior da página continua no ar.</b>'],
    g: 'Testes do contrato e do dbt.', w: '<code>.github/workflows/</code> · <code>dbt/</code>' },
  { h: 'A página é estática: HTML, números e tabelas.',
    p: ['O gerador escreve o HTML, o <code>pagina.json</code> com os números de cada gráfico e as tabelas em Parquet. Os números saem das mesmas tabelas que o texto dos achados, sem nada digitado à mão. Sem o contrato completo, nada é implantado.'],
    g: 'Só implanta sobre dado real e completo.', w: '<code>pipeline/gerar_site.py</code>' },
  { h: 'A consulta roda no seu navegador.',
    p: [`O DuckDB-WASM lê os Parquet e responde as ${AQ.consultas} consultas da página e a consulta livre, aqui, sem servidor. Se ele não carregar, os gráficos continuam, porque os números já vêm prontos.`],
    g: 'Nenhuma pergunta sua sai do navegador.', w: 'Exploração livre, 2.2' },
];
const USOS = [
  { t: `A lista de ${AQ.itens} itens`, m: 'propôs a lista lendo as linhas dos anúncios', p: 'revisou item a item, escreveu a regra de borda de cada um e congelou a versão', w: 'rotulagem/taxonomia.md', s: 1 },
  { t: 'A referência', m: `${NUM[AQ.rotuladores] || AQ.rotuladores} modelos de empresas diferentes rotularam as mesmas ${fmt(AQ.ref_linhas)} linhas de ${AQ.ref_vagas} vagas`, p: 'desempatou cada divergência, linha a linha', w: 'rotulagem/referencia/', s: 1 },
  { t: 'A escolha do modelo', m: `${AQ.candidatos} candidatos rotularam a referência e foram medidos contra ela`, p: `escolheu pelo resultado: ${AQ.modelo}, F1 de ${AQ.f1}`, w: 'evals/relatorio.md', s: 1 },
  { t: 'A classificação, toda semana', m: `o ${AQ.modelo} marca os itens de cada linha nova`, p: 'ninguém revisa linha a linha: a régua veio antes. Por isso a contagem é piso', w: 'README, "Classificação"', s: 0 },
  { t: 'O setor da empresa', m: 'propõe o setor quando aparece uma empresa nova', p: 'confirma ou corrige depois; a publicação não espera', w: 'empresas.csv', s: 1 },
  { t: 'O código de tudo isto', m: 'um assistente de código (Claude Code) escreveu o pipeline, os testes e esta página', p: 'decidiu o desenho, revisou e aprovou cada mudança', w: 'histórico do repositório', s: 1 },
];
function panelMode(m) {
  if (m === 'fluxo') return `<div class="ph"><span class="mono">Fluxo · toda semana</span></div>
    <h3>Da vaga ao seu navegador, em sete estágios.</h3>
    <p>Clique num estágio pra ver o que entra, o que sai e a guarda que se prende ali. Os chips acima mostram cada guarda no diagrama.</p>`;
  if (m === 'ia') return `<div class="ph"><span class="mono">Onde há IA · seis usos</span><span class="selo mono">Pessoa no circuito</span></div>
    <h3>O modelo faz o volume. A pessoa define a régua e confere.</h3>
    <div class="g3">${USOS.map(u => `<div class="uso${u.s ? ' pc' : ''}"><b>${u.t}</b>
      <div class="r"><span>Modelo</span><span>${u.m}</span></div>
      <div class="r pes"><span>Pessoa</span><span>${u.p}</span></div>
      <div class="r"><span>Onde ver</span><code>${u.w}</code></div>
      <span class="selo mono${u.s ? '' : ' nao'}">${u.s ? 'Pessoa no circuito' : 'Sem revisão por linha'}</span></div>`).join('')}</div>`;
  if (m === 'testes') return `<div class="ph"><span class="mono">Testes · três barreiras</span></div>
    <h3>Três lugares onde o dado pode ser barrado.</h3>
    <div class="g3"><div class="box2"><span class="mono">02 · antes do commit</span><b>Sigilo</b>Nenhum texto de anúncio, nenhuma coluna fora do contrato.</div>
    <div class="box2"><span class="mono">04 · na CI</span><b>Contrato e ${AQ.testes} testes</b>Arquivos, hash, sigilo de novo e os testes do dbt.</div>
    <div class="box2"><span class="mono">05 · antes de implantar</span><b>Dado completo</b>Sem os cinco arquivos, a página não troca.</div></div>
    <p style="margin-top:14px"><b>Se qualquer barreira falha, nada novo vai ao ar e a versão anterior fica.</b></p>`;
  if (m === 'sigilo') return `<div class="ph"><span class="mono">Sigilo · a fronteira</span></div>
    <h3>O que atravessa e o que fica.</h3>
    <div class="g2"><div class="box2 ok"><span class="mono">Atravessa</span><ul><li>a vaga: empresa, cargo, local, regime, link e datas</li><li>o rótulo de cada linha, sem o texto</li><li>o resumo dos requisitos</li><li>a referência salarial, com a fonte</li><li>o setor da empresa</li></ul></div>
    <div class="box2 fica"><span class="mono">Fica do lado privado</span><ul><li>o texto inteiro do anúncio</li><li>tudo o que não está no contrato de dados</li><li>qualquer credencial</li></ul></div></div>
    <p style="margin-top:14px">Defesa em profundidade: o <code>check_data.py</code> repete a checagem do lado público, porque este repositório não confia em quem escreve em <code>data/</code>.</p>`;
  return `<div class="ph"><span class="mono">Custo</span></div>
    <h3>Do lado público, nada se paga.</h3>
    <div class="g4"><div class="k"><b>R$ 0</b><span>GitHub Actions e Pages, gratuitos pra repositório público</span></div>
    <div class="k"><b>0</b><span>servidor: a consulta roda no seu navegador</span></div>
    <div class="k"><b>Assinatura</b><span>a classificação usa a assinatura do autor, sem API paga</span></div>
    <div class="k"><b>US$ ${AQ.usd_mil}</b><span>por mil linhas, o custo do modelo escolhido medido por API (<code>evals/</code>)</span></div></div>`;
}
function panelStage(i) {
  const s = ST[i], d = DET[i];
  return `<div class="ph"><span class="mono">${s.n} · ${s.t.join(' ')}</span><button class="x mono" type="button" data-x>× fechar</button></div>
    <h3>${d.h}</h3>${d.p.map(x => `<p>${x}</p>`).join('')}
    <div class="g2" style="margin-top:16px"><div class="box2"><span class="mono">Guarda</span>${d.g}</div><div class="box2"><span class="mono">Onde ver</span>${d.w}</div></div>`;
}

// Desenha o fluxo (horizontal no desktop, vertical abaixo de 900 px) e devolve a função que desfaz tudo. `est` guarda o chip e o estágio
// escolhidos, pra a troca de layout não perder o que o leitor tinha aberto.
function fluxo(host, V, est) {
  const G = V
    ? { W: 340, H: 960, M: [70, 190, 310, 520, 640, 760, 880], B: 418, cx: 92, bw: 140, bh: 64 }
    : { W: 1080, H: 500, M: [80, 215, 350, 560, 710, 860, 1010], B: 455, cy: 190, bw: 112, bh: 74 };
  const half = V ? G.bh / 2 : G.bw / 2;
  const P = (m, o) => V ? [G.cx + o, m] : [m, G.cy + o];
  let dead = false; const timers = [];

  const chips = document.createElement('div'); chips.className = 'chips';
  chips.innerHTML = CHIPS.map(([k, t]) => `<button class="pill mono${k === est.mode ? ' on' : ''}" data-m="${k}" type="button" aria-pressed="${k === est.mode}">${t}</button>`).join('');
  host.appendChild(chips);

  let s = `<svg viewBox="0 0 ${G.W} ${G.H}" role="group" aria-label="Fluxo do dado: origem privada, classificação por IA, exportador e sigilo, repositório público, CI, GitHub Pages e o seu navegador"><g class="root">`;
  if (V) {
    s += `<rect class="zone" x="4" y="14" width="${G.W - 8}" height="${G.B - 30}" rx="22"/>`;
    s += `<text class="zl" x="${G.W - 18}" y="36" text-anchor="end">LADO PRIVADO · FECHADO</text>`;
    s += `<line class="front" x1="0" x2="${G.W}" y1="${G.B}" y2="${G.B}"/><text class="fl" x="${G.W - 12}" y="${G.B - 8}" text-anchor="end">FRONTEIRA DE SIGILO</text>`;
    s += `<text class="zl" x="${G.W - 18}" y="${G.B + 30}" text-anchor="end">LADO PÚBLICO · NESTE REPOSITÓRIO</text>`;
    s += `<line class="wire" x1="${G.cx}" x2="${G.cx}" y1="${G.M[0]}" y2="${G.M[6]}"/>`;
  } else {
    s += `<rect class="zone" x="8" y="62" width="${G.B - 26}" height="270" rx="24"/>`;
    s += `<text class="zl" x="26" y="86">LADO PRIVADO · FECHADO</text>`;
    s += `<text class="zl" x="${G.B + 30}" y="86">LADO PÚBLICO · TUDO NESTE REPOSITÓRIO</text>`;
    s += `<line class="front" x1="${G.B}" x2="${G.B}" y1="40" y2="340"/><text class="fl" x="${G.B}" y="30" text-anchor="middle">FRONTEIRA DE SIGILO</text>`;
    s += `<line class="wire" x1="${G.M[0]}" x2="${G.M[6]}" y1="${G.cy}" y2="${G.cy}"/>`;
    // bancada: como a régua foi feita, uma vez
    const BY = 432, BX = [100, 266, 432];
    s += `<g class="bk"><text class="zl" x="26" y="482">BANCADA · FEITA UMA VEZ, REFEITA QUANDO A LISTA MUDA</text>`;
    const bt = [[`Lista de ${AQ.itens} itens`, 'taxonomia.md'], ['Referência revisada', `${fmt(AQ.ref_linhas)} linhas · ${AQ.rotuladores} modelos`], ['Escolha do modelo', `${AQ.candidatos} candidatos medidos`]];
    BX.forEach((x, i) => {
      s += `<rect x="${x - 75}" y="${BY - 24}" width="150" height="48" rx="12"/><text x="${x}" y="${BY - 3}" text-anchor="middle" style="font-family:var(--f-text);font-size:12.5px;fill:var(--bone)">${bt[i][0]}</text><text x="${x}" y="${BY + 13}" text-anchor="middle" style="font-size:8.5px;letter-spacing:.04em">${bt[i][1]}</text>`;
      if (i < 2) s += `<line class="bkarrow" x1="${x + 77}" x2="${BX[i + 1] - 77}" y1="${BY}" y2="${BY}"/>`;
    });
    s += `<path class="bkarrow" d="M${BX[2]},${BY - 26} C${BX[2]},330 ${G.M[1]},320 ${G.M[1]},${G.cy + 72}"/>`;
    s += `<text x="${BX[2] + 14}" y="358" style="font-size:9.5px;letter-spacing:.1em;fill:var(--muted)">A RÉGUA</text></g>`;
    // moldura e etiqueta (só no chip IA)
    s += `<g class="iaonly"><rect class="frame" x="2" y="8" width="${G.W - 4}" height="${G.H - 6}" rx="26"/>
      <text x="${G.W - 18}" y="${G.H - 12}" text-anchor="end" style="font-size:9.5px;letter-spacing:.08em;fill:var(--c-arq)">O CÓDIGO DE TUDO ISTO: CLAUDE CODE ESCREVEU, O AUTOR DECIDIU E REVISOU</text>
      <g class="tagia"><rect x="${G.M[0] - 62}" y="${G.cy + 108}" width="124" height="22" rx="11"/><text x="${G.M[0]}" y="${G.cy + 123}" text-anchor="middle">SETOR: IA PROPÕE</text></g></g>`;
  }
  s += `<g class="parts"></g>`;
  ST.forEach((st, i) => {
    const [x, y] = P(G.M[i], 0);
    const cls = 'nd' + (st.ai ? ' ai' : '') + (st.origem ? ' origem' : '');
    s += `<g class="${cls}" data-i="${i}" tabindex="0" role="button" aria-label="${st.n} ${st.t.join(' ')}">`;
    s += `<circle class="glow" cx="${x}" cy="${y}" r="${half + 6}"/>`;
    s += `<rect class="ping" x="${x - G.bw / 2}" y="${y - G.bh / 2}" width="${G.bw}" height="${G.bh}" rx="16"/>`;
    s += `<rect class="box" x="${x - G.bw / 2}" y="${y - G.bh / 2}" width="${G.bw}" height="${G.bh}" rx="16"/>`;
    if (st.origem) { // cadeado
      const lx = x + G.bw / 2 - 18, ly = y - G.bh / 2 + 14;
      s += `<path d="M${lx - 4},${ly} v-3 a4,4 0 0 1 8,0 v3" fill="none" stroke="var(--muted)" stroke-width="1.3"/><rect x="${lx - 6}" y="${ly}" width="12" height="9" rx="2" fill="var(--muted)"/>`;
    }
    if (st.ai) s += `<g class="badge"><rect x="${x + G.bw / 2 - 26}" y="${y - G.bh / 2 - 8}" width="30" height="16" rx="8"/><text x="${x + G.bw / 2 - 11}" y="${y - G.bh / 2 + 3}" text-anchor="middle">IA</text></g>`;
    if (st.ci) {
      s += `<text class="nm" x="${x}" y="${y - G.bh / 2 + 22}" text-anchor="middle" style="font-size:11.5px">${st.t[0]}</text>`;
      const cols = 15, gap = V ? 7.4 : 6.2, x0 = x - (cols - 1) * gap / 2, y0 = y - G.bh / 2 + (V ? 34 : 36);
      for (let k = 0; k < AQ.testes; k++) s += `<circle class="led" cx="${x0 + (k % cols) * gap}" cy="${y0 + Math.floor(k / cols) * (V ? 5.4 : 6.6)}" r="${V ? 1.8 : 2.1}"/>`;
    } else {
      s += `<text class="nm" x="${x}" y="${y - (st.t.length > 1 ? 2 : -4)}" text-anchor="middle">${st.t[0]}</text>`;
      if (st.t[1]) s += `<text class="nm" x="${x}" y="${y + 15}" text-anchor="middle">${st.t[1]}</text>`;
    }
    if (V) {
      s += `<text class="st" x="${x - G.bw / 2 + 12}" y="${y - G.bh / 2 + 14}">${st.n}</text>`;
      s += `<text class="cnt" x="${x + G.bw / 2 + 14}" y="${y - 2}" data-n="${st.num ?? ''}">${st.c}</text>`;
      s += `<text class="cl" x="${x + G.bw / 2 + 14}" y="${y + 14}">${st.cl[0]}</text><text class="cl" x="${x + G.bw / 2 + 14}" y="${y + 26}">${st.cl[1]}</text>`;
    } else {
      s += `<text class="st" x="${x}" y="${y - G.bh / 2 - 14}" text-anchor="middle">${st.n}</text>`;
      s += `<text class="cnt" x="${x}" y="${y + G.bh / 2 + 34}" text-anchor="middle" data-n="${st.num ?? ''}">${st.c}</text>`;
      s += `<text class="cl" x="${x}" y="${y + G.bh / 2 + 52}" text-anchor="middle">${st.cl[0]}</text><text class="cl" x="${x}" y="${y + G.bh / 2 + 65}" text-anchor="middle">${st.cl[1]}</text>`;
    }
    s += `</g>`;
  });
  if (V) s += `<g class="iaonly"><g class="tagia"><rect x="${G.cx + G.bw / 2 + 10}" y="${G.M[0] + 32}" width="118" height="20" rx="10"/><text x="${G.cx + G.bw / 2 + 69}" y="${G.M[0] + 46}" text-anchor="middle" style="font-size:8.5px">SETOR: IA PROPÕE</text></g></g>`;
  s += `</g></svg>`;
  const box = document.createElement('div'); box.className = 'quadro'; box.innerHTML = s; host.appendChild(box);
  const hint = document.createElement('div'); hint.className = 'mono hint'; hint.textContent = RM ? 'Movimento reduzido: diagrama parado' : (V ? 'Toque num estágio' : 'Clique num estágio');
  host.appendChild(hint);
  const panel = document.createElement('div'); panel.setAttribute('aria-live', 'polite'); host.appendChild(panel);

  const svg = box.querySelector('svg'), root = svg.querySelector('.root'), parts = svg.querySelector('.parts');
  const nodes = [...svg.querySelectorAll('.nd')], leds = [...svg.querySelectorAll('.led')], front = svg.querySelector('.front');

  function paint() {
    root.setAttribute('class', 'root mode-' + est.mode);
    svg.classList.toggle('dimparts', est.mode !== 'fluxo');
    const on = MODES[est.mode];
    nodes.forEach((n, i) => { n.classList.toggle('off', !on.includes(i)); n.classList.toggle('lit', est.mode !== 'fluxo' && on.includes(i)); n.classList.toggle('sel', est.sel === i); });
    chips.querySelectorAll('.pill').forEach(b => { const a = b.dataset.m === est.mode; b.classList.toggle('on', a); b.setAttribute('aria-pressed', a); });
    panel.className = 'apanel'; void panel.offsetWidth;
    panel.innerHTML = est.sel != null ? panelStage(est.sel) : panelMode(est.mode);
    const x = panel.querySelector('[data-x]'); if (x) x.onclick = () => { est.sel = null; paint(); };
  }
  chips.addEventListener('click', e => { const b = e.target.closest('[data-m]'); if (!b) return; est.mode = b.dataset.m; est.sel = null; paint(); });
  nodes.forEach((n, i) => {
    const go = () => { est.sel = est.sel === i ? null : i; paint(); };
    n.addEventListener('click', go);
    n.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(); } });
  });
  paint();

  if (RM) { leds.forEach(l => l.classList.add('on')); return () => { dead = true; }; }

  // animação (JS puro, D19): vaga → linhas rotuladas + traço de texto que some na fronteira; os testes acendem na CI
  const pulse = (i, ai) => { const g = nodes[i].querySelector(ai ? '.glow' : '.ping'); g.classList.remove('pulse'); void g.getBBox(); g.classList.add('pulse'); };
  let ledK = 0;
  const lightLed = () => { if (ledK >= leds.length) { leds.forEach(l => l.classList.remove('on')); ledK = 0; } leds[ledK++].classList.add('on'); };
  const L = []; const speed = V ? 110 : 150;
  const mk = (type, m, o, to, extra = {}) => {
    const e = document.createElementNS(NS, type === 't' ? 'rect' : 'circle');
    e.setAttribute('class', 'pt-' + type);
    if (type === 't') { e.setAttribute('width', V ? 3 : 8); e.setAttribute('height', V ? 8 : 3); e.setAttribute('rx', 1.5); }
    else e.setAttribute('r', type === 'v' ? 4 : 2.6);
    parts.appendChild(e);
    L.push(Object.assign({ type, m, o, to, e, next: 2, a: 1 }, extra));
  };
  const OFF = V ? [-16, 0, 16] : [-11, 0, 11];
  const spawnVaga = () => mk('v', G.M[0] + half, 0, G.M[1] - half);
  function onArrive(p) {
    if (p.type === 'v') {
      timers.push(setTimeout(() => {
        if (dead) return;
        pulse(1, true);
        OFF.forEach((o, k) => mk('l', G.M[1] + half, o, G.M[6], { lead: k === 1 }));
        mk('t', G.M[1] + half, V ? 30 : 24, G.B - 4, { dying: true });
      }, 260));
      return true;
    }
    if (p.type === 't') { p.fade = true; front.classList.add('flash'); timers.push(setTimeout(() => front.classList.remove('flash'), 220)); return false; }
    if (p.type === 'l' && p.lead) pulse(6);
    return true;
  }
  let last = 0, acc = 0, run = false, raf;
  function tick(t) {
    const dt = Math.min(0.05, (t - (last || t)) / 1000); last = t;
    acc += dt; if (acc > 1.0) { acc = 0; spawnVaga(); }
    for (let i = L.length - 1; i >= 0; i--) {
      const p = L[i];
      if (p.fade) { p.a -= dt * 3; if (p.a <= 0) { p.e.remove(); L.splice(i, 1); continue; } p.e.setAttribute('opacity', p.a); continue; }
      p.m += speed * dt;
      if (p.type === 'l') while (p.next < 6 && p.m >= G.M[p.next]) {
        if (p.next === 4) lightLed();
        if (p.lead) pulse(p.next);
        p.next++;
      }
      if (p.m >= p.to) { p.m = p.to; if (onArrive(p)) { p.e.remove(); L.splice(i, 1); continue; } }
      const [x, y] = P(p.m, p.o);
      if (p.type === 't') { p.e.setAttribute('x', x - (V ? 1.5 : 4)); p.e.setAttribute('y', y - (V ? 4 : 1.5)); }
      else { p.e.setAttribute('cx', x); p.e.setAttribute('cy', y); }
    }
    if (run) raf = requestAnimationFrame(tick);
  }
  // os contadores sobem ao entrar na tela, e a animação só roda enquanto o diagrama está visível
  let counted = false;
  const vis = new IntersectionObserver(es => es.forEach(en => {
    if (en.isIntersecting) {
      if (!counted) { counted = true; svg.querySelectorAll('.cnt[data-n]').forEach(c => {
        const n = +c.dataset.n; if (!c.dataset.n || !n) return; const t0 = performance.now();
        const step = t => { if (dead) return; const k = Math.min(1, (t - t0) / 1400), e = 1 - Math.pow(1 - k, 3); c.textContent = fmt(Math.round(n * e)); if (k < 1) requestAnimationFrame(step); };
        requestAnimationFrame(step); }); }
      if (!run) { run = true; last = 0; spawnVaga(); raf = requestAnimationFrame(tick); }
    } else { run = false; cancelAnimationFrame(raf); }
  }), { threshold: 0.15 });
  vis.observe(svg);
  return () => { dead = true; run = false; cancelAnimationFrame(raf); vis.disconnect(); timers.forEach(clearTimeout); };
}
function arquitetura() {
  const host = document.getElementById('fluxo'); if (!host || !AQ) return;
  const est = { mode: 'fluxo', sel: null }, mq = matchMedia('(max-width: 900px)');
  let desfaz = () => {};
  const monta = () => { desfaz(); host.innerHTML = ''; desfaz = fluxo(host, mq.matches, est); };
  mq.addEventListener('change', monta);
  monta();
}

// ---------- render ----------
let lastW = -1, renderizado = false;
function render() {
  lastW = document.querySelector('.wrap').clientWidth;
  base(document.getElementById('c-base'));
  if (renderizado) CARDS.forEach(c => c.desenha());
  dumb(document.getElementById('c-ns'), ROWS.ns);
  explorar();
  retrato();
  renderizado = true;
}
art(); iniciaCards(); render(); colunas(); exemplo(); arquitetura();
document.fonts && document.fonts.ready.then(render);
if (window.ResizeObserver) new ResizeObserver(() => { const w = document.querySelector('.wrap').clientWidth; if (Math.abs(w - lastW) > 1) render(); }).observe(document.body);
