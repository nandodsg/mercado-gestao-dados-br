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
addEventListener('scroll', () => { if (ticking) return; ticking = true; requestAnimationFrame(() => {
  const y = scrollY, h = document.documentElement.scrollHeight - innerHeight; prog.style.transform = `scaleX(${h > 0 ? y / h : 0})`;
  if (!RM && y < innerHeight * 1.2) { word.style.transform = `translateY(${y * 0.35}px)`; word.style.opacity = Math.max(0, 1 - y / (innerHeight * 0.9)); }
  ticking = false; }); }, { passive: true });

// ---------- 1 · arte ----------
function art() {
  const s = document.getElementById('art'); s.innerHTML = ''; const st = stage(s);
  const L = DATA.manifest.cobertura.linhas, V = DATA.manifest.contagens.vagas, F = DATA.faixa_posting;
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
  const W = box.clientWidth, narrow = W < 600, it = IT[chave];
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
    el('line', { x1: X(v), x2: X(v), y1: top - 6, y2: H, stroke: '#e4e4df', 'stroke-width': 1 }, s);
    txt(s, X(v), 12, narrow ? (v === 0 ? '0' : v === max ? (v / 1000) + ' MIL' : String(v / 1000)) : v === 0 ? 'R$ 0' : (v / 1000) + ' MIL',
      { 'text-anchor': v === 0 ? 'start' : v === max ? 'end' : 'middle', class: 'tick', style: 'fill:#6b6865' });
  }
  let y0 = top + 26, gi = 0;
  grupos.forEach(g => {
    const yTop = y0, b0 = gi * 700, nrep = g.xs.filter(g.rep).length;
    const rot = { style: `letter-spacing:${narrow ? '.03em;font-size:10px' : '.1em'};fill:#1d1a1a;font-weight:400` };
    if (narrow) { txt(s, 0, yTop - 25, `${NOME[g.k].toUpperCase()} · ${g.xs.length} VAGAS`, rot); txt(s, 0, yTop - 13, `${nrep} NA FAIXA REPETIDA`, rot); }
    else txt(s, 0, yTop - 12, `${NOME[g.k].toUpperCase()} · ${g.xs.length} VAGAS · ${nrep} NA FAIXA REPETIDA`, rot);
    const lines = g.xs.map((v, i) => {
      const y = yTop + i * rowH + rowH / 2, rep = g.rep(v);
      const ln = el('line', { x1: X(v.mid), x2: X(v.mid), y1: y, y2: y, stroke: C[g.k], 'stroke-width': 4, 'stroke-linecap': rep ? 'butt' : 'round', 'stroke-dasharray': rep ? '3 3' : '', class: 'sl' }, s);
      st.add(800, b0 + 150 + i * 22, t => { set(ln, { x1: X(lerp(v.mid, v.min, t)), x2: X(lerp(v.mid, v.max, t)) }); ln.style.opacity = t > 0 ? 1 : 0; }, EASE.outQuint);
      return ln;
    });
    const yb = yTop + g.xs.length * rowH;
    const ml = el('line', { x1: X(g.med), x2: X(g.med), y1: yTop - 4, y2: yTop - 4, stroke: '#000', 'stroke-width': 1.5 }, s);
    const mt = txt(s, X(g.med), yb + 22, 'MEDIANA ' + (DATA.sal_txt[g.k] || brl(g.med)).toUpperCase(), { 'text-anchor': 'middle', style: 'fill:#000;letter-spacing:.06em;font-weight:400' });
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
  document.getElementById('leg-sal').innerHTML = `<span><i style="background:${C.coordenador}"></i>Coordenação</span><span><i style="background:${C.gerente}"></i>Gerência</span><span style="color:#1d1a1a"><span class="dashl"></span>faixa repetida de um guia salarial</span>`;
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
  a1: { sql: itemSQL(chavesDe(ROWS.a1)), p: 'pedem' },
  a2: { sql: itemSQL(chavesDe(ROWS.a2)), p: 'pedem' },
  a3: { sql: `-- Python citado pelo nome no anúncio, por nível
with base as (
  select distinct id_publico, nivel
  from mart_vaga_item
  where nivel in ('coordenador', 'gerente')
)
select b.nivel,
       count(*) as vagas,
       count(f.id_publico) as citam_python,
       round(100.0 * citam_python / vagas) as pct
from base b
left join mart_vaga_ferramenta f
  on f.id_publico = b.id_publico
 and f.ferramenta = 'Python'
group by b.nivel
order by b.nivel;`, p: 'citam_python' },
  a4: { sql: itemSQL([ROWS.a4]), p: 'pedem' },
  a5: { sql: `-- vagas com algum item de IA, por nível
select nivel, count(distinct id_publico) as vagas_com_ia
from mart_vaga_item
where item_chave like 'ia.%'
group by nivel
order by vagas_com_ia desc;` },
  a6: { sql: `-- referência salarial pesquisada: mediana do ponto médio da faixa
select nivel,
       count(*) as vagas,
       median((salario_min + salario_max) / 2) as mediana
from mart_vagas
where nivel in ('coordenador', 'gerente')
  and salario_min is not null
  and id_publico not in (select id_publico from mart_repost)
group by nivel;` },
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
  const cols = res.schema.fields.map(f => f.name);
  const rows = res.toArray().map(r => cols.map(c => { const v = r[c]; return typeof v === 'bigint' ? Number(v) : v; }));
  return { cols, rows };
}

const KW = /\b(select|from|where|join|left|on|and|in|group by|order by|with|as|count|distinct|round|median|any_value|using|not|like|desc)\b/g;
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
const num = c => /^(vagas|pedem|pct|citam|mediana)/.test(c);
function celula(col, v) {
  if (v === null || v === undefined) return '';
  if (typeof v === 'number') return col === 'pct' ? Math.round(v) + '%' : col === 'mediana' ? brl(v) : Number.isInteger(v) ? fmt(v) : v.toLocaleString('pt-BR');
  return esc(v);
}
function tabela(res) {
  return `<table><tr>${res.cols.map(c => `<th class="${num(c) ? 'n' : ''}">${esc(c)}</th>`).join('')}</tr>${res.rows.map(r =>
    `<tr>${r.map((v, i) => `<td class="${num(res.cols[i]) ? 'n' : ''}">${celula(res.cols[i], v)}</td>`).join('')}</tr>`).join('')}</table>`;
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

// ---------- render ----------
let lastW = -1;
function render() {
  lastW = document.querySelector('.wrap').clientWidth;
  base(document.getElementById('c-base'));
  dumb(document.getElementById('c-a1'), ROWS.a1);
  dumb(document.getElementById('c-a2'), ROWS.a2);
  dumb(document.getElementById('c-a3'), ROWS.a3);
  waffle(document.getElementById('c-a4'), ROWS.a4);
  hbar(document.getElementById('c-a5a'), [{ label: 'em responsabilidades', x: DATA.ia.resp, n: DATA.ia.tot, hl: true }, { label: 'em requisitos', x: DATA.ia.req, n: DATA.ia.tot }], { L: 190 });
  dumb(document.getElementById('c-a5b'), ROWS.a5b, { L: 200 });
  hbar(document.getElementById('c-a5c'), DATA.difs.map(([l, x], i) => ({ label: l, x, n: DATA.ia.ndif, hl: i === 0 })));
  salario(document.getElementById('c-sal'));
  dumb(document.getElementById('c-ns'), ROWS.ns);
  explorar();
}
function iaBig() {
  const b = document.getElementById('ia-big'), alvo = Math.round(100 * DATA.ia.tot / DATA.ia.base);
  const fio = new IntersectionObserver(es => es.forEach(e => { if (!e.isIntersecting) return; fio.unobserve(b);
    tween(1400, 0, t => b.textContent = Math.round(alvo * t), EASE.outQuint); }), { threshold: 0.5 });
  fio.observe(b);
}
art(); iaBig(); render();
document.fonts && document.fonts.ready.then(render);
if (window.ResizeObserver) new ResizeObserver(() => { const w = document.querySelector('.wrap').clientWidth; if (Math.abs(w - lastW) > 1) render(); }).observe(document.body);
