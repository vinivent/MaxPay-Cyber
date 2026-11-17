/* MaxPay — primitivas de grafico em SVG puro.
   Regras seguidas: um unico eixo por grafico, marcas finas, grade recessiva,
   extremidades arredondadas em 4px ancoradas na linha de base, legenda sempre
   que houver duas ou mais series, e camada de hover em todas as formas. */

const NS = 'http://www.w3.org/2000/svg';
// Paleta categorica verificada para deficiencia de visao de cores (protanopia,
// deuteranopia e tritanopia) antes de ser adotada: pior par com DeltaE 13,7 em
// OKLab x100 (alvo >= 8) e 22,2 para visao normal (piso 15), com os tres slots
// acima de 3:1 de contraste sobre o fundo branco. Os valores estao em DESIGN.md.
const SERIES = ['#2056C7', '#C2410C', '#0D9488'];

const el = (name, attrs = {}, parent) => {
  const n = document.createElementNS(NS, name);
  for (const [k, v] of Object.entries(attrs)) if (v !== undefined && v !== null) n.setAttribute(k, v);
  if (parent) parent.appendChild(n);
  return n;
};

const fmt = (v, casas = 2) =>
  Number(v).toLocaleString('pt-BR', { minimumFractionDigits: casas, maximumFractionDigits: casas });
const fmtInt = (v) => Math.round(v).toLocaleString('pt-BR');

function niceTicks(min, max, alvo = 5, inteiro = false) {
  if (!isFinite(min) || !isFinite(max) || min === max) return [min];
  const bruto = (max - min) / alvo;
  const mag = 10 ** Math.floor(Math.log10(bruto));
  let passo = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((p) => p >= bruto) ?? 10 * mag;
  // Um eixo de rodadas nao pode rotular 2,8 como "3": o passo tem de ser inteiro.
  if (inteiro) passo = Math.max(1, Math.round(passo));
  const out = [];
  for (let t = Math.ceil(min / passo) * passo; t <= max + passo * 1e-9; t += passo) out.push(+t.toFixed(10));
  return out;
}

/** Redesenha quando a largura muda: o viewBox e congelado na primeira medida. */
function observar(host, redesenhar) {
  if (host.__obs) host.__obs.disconnect();
  let largura = host.clientWidth;
  host.__obs = new ResizeObserver(() => {
    if (Math.abs(host.clientWidth - largura) < 24) return;
    largura = host.clientWidth;
    redesenhar();
  });
  host.__obs.observe(host);
}


/** Cria o SVG e a caixa de dica; devolve os helpers de escala. */
function frame(host, { height = 220, pad = {} } = {}) {
  host.innerHTML = '';
  host.classList.add('chart');
  const p = { t: 14, r: 16, b: 34, l: 52, ...pad };
  const w = Math.max(host.clientWidth || 640, 320);
  const svg = el('svg', { viewBox: `0 0 ${w} ${height}`, height, role: 'img' }, host);
  if (host.dataset.resumo) el('title', {}, svg).textContent = host.dataset.resumo;
  svg.setAttribute('aria-label', host.dataset.resumo || host.getAttribute('aria-label') || 'gráfico');
  const tip = document.createElement('div');
  tip.className = 'tip';
  host.appendChild(tip);
  const iw = w - p.l - p.r;
  const ih = height - p.t - p.b;
  return { svg, tip, w, h: height, p, iw, ih };
}

function showTip(f, host, x, y, html) {
  f.tip.innerHTML = html;
  f.tip.style.left = `${(x / f.w) * host.clientWidth}px`;
  f.tip.style.top = `${(y / f.h) * host.clientHeight}px`;
  f.tip.dataset.show = '1';
}
const hideTip = (f) => { f.tip.dataset.show = '0'; };

function axes(f, { xTicks, yTicks, xScale, yScale, xLabel, yLabel, xFormat, yFormat }) {
  const g = el('g', { class: 'axis' }, f.svg);
  for (const t of yTicks) {
    const y = yScale(t);
    el('line', { class: 'grid-line', x1: f.p.l, x2: f.p.l + f.iw, y1: y, y2: y }, g);
    el('text', { x: f.p.l - 8, y: y + 3.5, 'text-anchor': 'end' }, g).textContent = (yFormat || fmtInt)(t);
  }
  el('line', { x1: f.p.l, x2: f.p.l + f.iw, y1: f.p.t + f.ih, y2: f.p.t + f.ih }, g);
  for (const t of xTicks) {
    el('text', { x: xScale(t), y: f.p.t + f.ih + 17, 'text-anchor': 'middle' }, g).textContent =
      (xFormat || fmtInt)(t);
  }
  if (xLabel)
    el('text', { class: 'axis-title', x: f.p.l + f.iw / 2, y: f.h - 2, 'text-anchor': 'middle' }, f.svg)
      .textContent = xLabel;
  if (yLabel)
    el('text', {
      class: 'axis-title', transform: `rotate(-90)`, x: -(f.p.t + f.ih / 2), y: 11, 'text-anchor': 'middle',
    }, f.svg).textContent = yLabel;
}

function legend(host, series) {
  // frame() limpa apenas o proprio host; sem remover a anterior, cada
  // redesenho empilharia mais uma linha de legenda acima do grafico.
  const anterior = host.previousElementSibling;
  if (anterior && anterior.classList.contains('legend')) anterior.remove();
  if (series.length < 2) return;
  const box = document.createElement('div');
  box.className = 'legend';
  box.innerHTML = series
    .map((s) => `<span><i style="background:${s.color}"></i>${s.name}</span>`)
    .join('');
  host.parentElement.insertBefore(box, host);
}

/* ------------------------------------------------------------------ linha */
export function line(host, opts) {
  const {
    series, xLabel, yLabel, height = 230, yDomain, xFormat, yFormat, tipFormat,
    refLine, refLabel, draw = false, xInteiro = false,
  } = opts;
  series.forEach((s, i) => { s.color = s.color || SERIES[i % SERIES.length]; });
  legend(host, series);

  const f = frame(host, { height });
  const todos = series.flatMap((s) => s.points);
  const xs = todos.map((p) => p[0]);
  const ys = todos.map((p) => p[1]);
  const x0 = Math.min(...xs), x1 = Math.max(...xs);
  const [y0, y1] = yDomain || [Math.min(0, ...ys), Math.max(...ys)];
  const xScale = (v) => f.p.l + (x1 === x0 ? 0 : ((v - x0) / (x1 - x0)) * f.iw);
  const yScale = (v) => f.p.t + f.ih - ((v - y0) / (y1 - y0 || 1)) * f.ih;

  axes(f, {
    xTicks: niceTicks(x0, x1, 6, xInteiro), yTicks: niceTicks(y0, y1, 5),
    xScale, yScale, xLabel, yLabel, xFormat, yFormat,
  });

  if (refLine !== undefined) {
    const y = yScale(refLine);
    el('line', { class: 'ref-line', x1: f.p.l, x2: f.p.l + f.iw, y1: y, y2: y }, f.svg);
    if (refLabel)
      el('text', { class: 'ref-label', x: f.p.l + f.iw, y: y - 5, 'text-anchor': 'end' }, f.svg)
        .textContent = refLabel;
  }

  for (const s of series) {
    const d = s.points.map((pt, i) => `${i ? 'L' : 'M'}${xScale(pt[0])} ${yScale(pt[1])}`).join(' ');
    const path = el('path', { class: 'series-line', d, stroke: s.color }, f.svg);
    if (draw) {
      const len = path.getTotalLength();
      path.style.setProperty('--len', len);
      path.classList.add('draw');
    }
    if (s.points.length <= 20)
      for (const pt of s.points)
        el('circle', { class: 'mark-ring', cx: xScale(pt[0]), cy: yScale(pt[1]), r: 4, fill: s.color }, f.svg);
  }

  // Mira vertical: um ponto de leitura por posicao de x.
  const mira = el('line', { class: 'ref-line', y1: f.p.t, y2: f.p.t + f.ih, opacity: 0 }, f.svg);
  const captura = el('rect', {
    x: f.p.l, y: f.p.t, width: f.iw, height: f.ih, fill: 'transparent', style: 'cursor:crosshair',
  }, f.svg);
  captura.addEventListener('pointermove', (ev) => {
    const r = host.getBoundingClientRect();
    const vx = ((ev.clientX - r.left) / r.width) * f.w;
    const alvo = x0 + ((vx - f.p.l) / f.iw) * (x1 - x0);
    const linhas = series.map((s) => {
      const pt = s.points.reduce((a, b) => (Math.abs(b[0] - alvo) < Math.abs(a[0] - alvo) ? b : a));
      return { s, pt };
    });
    const px = xScale(linhas[0].pt[0]);
    mira.setAttribute('x1', px); mira.setAttribute('x2', px); mira.setAttribute('opacity', 1);
    showTip(f, host, px, f.p.t + 4,
      `<div class="tip-key">${(xFormat || fmtInt)(linhas[0].pt[0])}</div>` +
      linhas.map(({ s, pt }) =>
        `<div><i style="display:inline-block;width:7px;height:7px;border-radius:var(--r-xs);background:${s.color};margin-right:5px"></i>${s.name} <b>${(tipFormat || yFormat || fmt)(pt[1])}</b></div>`,
      ).join(''));
  });
  captura.addEventListener('pointerleave', () => { hideTip(f); mira.setAttribute('opacity', 0); });
  observar(host, () => line(host, opts));
  return f;
}

/* -------------------------------------------------------------------- barras */
export function bars(host, opts) {
  const {
    data, height = 230, xLabel, yLabel, color = SERIES[0], dense = false,
    yFormat, tipFormat, refLine, refLabel, yDomain, xTickEvery, larguraMax = 44,
  } = opts;
  const f = frame(host, { height, pad: dense ? { l: 52, b: 32 } : {} });
  const vals = data.map((d) => d.value);
  const [y0, y1] = yDomain || [0, Math.max(...vals) * 1.08 || 1];
  const yScale = (v) => f.p.t + f.ih - ((v - y0) / (y1 - y0 || 1)) * f.ih;
  const passo = f.iw / data.length;
  // Marcas finas: a barra nunca engorda alem do limite, por mais espaco que sobre.
  const gap = dense ? 0 : Math.max(Math.min(10, passo * 0.28), passo - larguraMax);
  const bw = Math.max(1, passo - gap);
  const raio = dense ? 0 : Math.min(4, bw / 2);

  const g = el('g', { class: 'axis' }, f.svg);
  for (const t of niceTicks(y0, y1, 5)) {
    const y = yScale(t);
    el('line', { class: 'grid-line', x1: f.p.l, x2: f.p.l + f.iw, y1: y, y2: y }, g);
    el('text', { x: f.p.l - 8, y: y + 3.5, 'text-anchor': 'end' }, g).textContent = (yFormat || fmtInt)(t);
  }
  el('line', { x1: f.p.l, x2: f.p.l + f.iw, y1: f.p.t + f.ih, y2: f.p.t + f.ih }, g);

  if (refLine !== undefined) {
    const y = yScale(refLine);
    el('line', { class: 'ref-line', x1: f.p.l, x2: f.p.l + f.iw, y1: y, y2: y }, f.svg);
    if (refLabel)
      el('text', { class: 'ref-label', x: f.p.l + f.iw, y: y - 5, 'text-anchor': 'end' }, f.svg)
        .textContent = refLabel;
  }

  data.forEach((d, i) => {
    const x = f.p.l + i * passo + gap / 2;
    const y = yScale(Math.max(d.value, y0));
    const alt = Math.max(0, f.p.t + f.ih - y);
    // Extremidade arredondada so no topo, ancorada na linha de base.
    const r = Math.min(raio, alt);
    const caminho = r > 0
      ? `M${x} ${y + alt} L${x} ${y + r} Q${x} ${y} ${x + r} ${y} L${x + bw - r} ${y} Q${x + bw} ${y} ${x + bw} ${y + r} L${x + bw} ${y + alt} Z`
      : `M${x} ${y} h${bw} v${alt} h${-bw} Z`;
    const barra = el('path', { d: caminho, fill: d.color || color }, f.svg);
    barra.style.cursor = 'pointer';
    barra.addEventListener('pointerenter', () => {
      barra.setAttribute('opacity', 0.78);
      showTip(f, host, x + bw / 2, y,
        `<div class="tip-key">${d.label}</div><b>${(tipFormat || yFormat || fmt)(d.value)}</b>${d.nota ? `<div class="tip-key">${d.nota}</div>` : ''}`);
    });
    barra.addEventListener('pointerleave', () => { barra.removeAttribute('opacity'); hideTip(f); });

    const cada = xTickEvery || (dense ? Math.ceil(data.length / 8) : 1);
    if (i % cada === 0 && (!dense || i % cada === 0))
      el('text', {
        x: x + bw / 2, y: f.p.t + f.ih + 17, 'text-anchor': 'middle',
        class: dense ? '' : 'cat',
      }, g).textContent = d.label;
  });

  if (xLabel)
    el('text', { class: 'axis-title', x: f.p.l + f.iw / 2, y: f.h - 2, 'text-anchor': 'middle' }, f.svg)
      .textContent = xLabel;
  if (yLabel)
    el('text', {
      class: 'axis-title', transform: 'rotate(-90)', x: -(f.p.t + f.ih / 2), y: 11, 'text-anchor': 'middle',
    }, f.svg).textContent = yLabel;
  observar(host, () => bars(host, opts));
  return f;
}

/* ------------------------------------------------------- matriz / mapa de calor */
export function heatmap(host, opts) {
  const { matrix, height = 260, mid = 0.5, span = 0.5, xLabel, yLabel, rotulo } = opts;
  const f = frame(host, { height, pad: { t: 10, r: 14, b: 32, l: 44 } });
  const n = matrix.length;
  const lado = Math.min(f.iw, f.ih);
  const cel = lado / n;
  const ox = f.p.l;
  const oy = f.p.t;

  // Divergente: dois polos e cinza neutro no meio (o SAC gira em torno de 0,5).
  const cor = (v) => {
    const t = Math.max(-1, Math.min(1, (v - mid) / span));
    const neutro = [0xED, 0xED, 0xEF];
    const polo = t < 0 ? [0x20, 0x56, 0xC7] : [0xC2, 0x41, 0x0C];
    const k = Math.abs(t);
    return `rgb(${neutro.map((c, i) => Math.round(c + (polo[i] - c) * k)).join(',')})`;
  };

  const cv = document.createElement('canvas');
  cv.width = n; cv.height = n;
  const ctx = cv.getContext('2d');
  for (let y = 0; y < n; y++)
    for (let x = 0; x < n; x++) { ctx.fillStyle = cor(matrix[y][x]); ctx.fillRect(x, y, 1, 1); }
  el('image', {
    href: cv.toDataURL(), x: ox, y: oy, width: lado, height: lado,
    'image-rendering': 'pixelated', preserveAspectRatio: 'none',
  }, f.svg);
  el('rect', { x: ox, y: oy, width: lado, height: lado, fill: 'none', stroke: 'var(--line)' }, f.svg);

  const captura = el('rect', { x: ox, y: oy, width: lado, height: lado, fill: 'transparent' }, f.svg);
  captura.style.cursor = 'crosshair';
  captura.addEventListener('pointermove', (ev) => {
    const r = host.getBoundingClientRect();
    const vx = ((ev.clientX - r.left) / r.width) * f.w;
    const vy = ((ev.clientY - r.top) / r.height) * f.h;
    const cx = Math.floor((vx - ox) / cel);
    const cy = Math.floor((vy - oy) / cel);
    if (cx < 0 || cy < 0 || cx >= n || cy >= n) return;
    showTip(f, host, vx, vy - 6,
      `<div class="tip-key">bit de entrada ${cy} → bit de saída ${cx}</div><b>${fmt(matrix[cy][cx], 3)}</b> <span class="tip-key">(ideal 0,500)</span>`);
  });
  captura.addEventListener('pointerleave', () => hideTip(f));

  // Escala divergente, legendada.
  const lx = ox + lado + 22;
  if (lx < f.w - 60) {
    const lh = Math.min(lado, 150);
    const grad = el('linearGradient', { id: `g-${Math.random().toString(36).slice(2)}`, x1: 0, y1: 1, x2: 0, y2: 0 }, f.svg);
    el('stop', { offset: '0%', 'stop-color': cor(mid - span) }, grad);
    el('stop', { offset: '50%', 'stop-color': cor(mid) }, grad);
    el('stop', { offset: '100%', 'stop-color': cor(mid + span) }, grad);
    el('rect', { x: lx, y: oy, width: 10, height: lh, fill: `url(#${grad.id})`, stroke: 'var(--line)' }, f.svg);
    const t = el('g', { class: 'axis' }, f.svg);
    el('text', { x: lx + 15, y: oy + 8 }, t).textContent = fmt(mid + span, 2).replace('.', ',');
    el('text', { x: lx + 15, y: oy + lh / 2 + 4 }, t).textContent = fmt(mid, 2).replace('.', ',');
    el('text', { x: lx + 15, y: oy + lh }, t).textContent = fmt(mid - span, 2).replace('.', ',');
    if (rotulo) el('text', { class: 'axis-title', x: lx, y: oy + lh + 22 }, f.svg).textContent = rotulo;
  }
  if (xLabel)
    el('text', { class: 'axis-title', x: ox + lado / 2, y: f.h - 2, 'text-anchor': 'middle' }, f.svg).textContent = xLabel;
  if (yLabel)
    el('text', {
      class: 'axis-title', transform: 'rotate(-90)', x: -(oy + lado / 2), y: 11, 'text-anchor': 'middle',
    }, f.svg).textContent = yLabel;
  observar(host, () => heatmap(host, opts));
  return f;
}

export { SERIES, fmt, fmtInt };
