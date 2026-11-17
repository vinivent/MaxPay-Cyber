/* FinalPay, dashboard.
   Busca os resultados medidos pela bateria e os desenha. Nenhum numero e
   escrito aqui: tudo vem de results/experimentos.json via API. */

import { bars, heatmap, line, SERIES } from './charts.js';

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];

const nf = (v, c = 2) =>
  v === null || v === undefined || Number.isNaN(v)
    ? 'n/d'
    : Number(v).toLocaleString('pt-BR', { minimumFractionDigits: c, maximumFractionDigits: c });
const ni = (v) => (v === null || v === undefined ? 'n/d' : Math.round(v).toLocaleString('pt-BR'));
const pct = (v, c = 2) => `${nf(v, c)}%`;
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (m) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[m]));
const rotulo = (s) => estado.nomes?.[s] ?? String(s ?? '').replace(/_/g, ' ');
const rotuloCurto = (s) => estado.nomesCurtos?.[s] ?? rotulo(s);
const sup = (n) => String(n).replace(/-/g, '⁻').replace(/[0-9]/g, (d) => '⁰¹²³⁴⁵⁶⁷⁸⁹'[+d]);

const estado = { resultados: null, carregado: new Set(), nomes: null, nomesCurtos: null };

async function api(rota, opcoes) {
  const r = await fetch(rota, opcoes);
  if (!r.ok) {
    let msg = `${r.status}`;
    try { msg = (await r.json()).detail || msg; } catch { /* resposta sem corpo JSON */ }
    throw new Error(msg);
  }
  return r.json();
}

const carregando = (alvo, texto = 'Carregando') =>
  (alvo.innerHTML = `<div class="note"><span class="spinner"></span>${texto}…</div>`);
const falha = (alvo, erro) =>
  (alvo.innerHTML = `<div class="note note-warn"><svg><use href="#ic-alert"/></svg><div>
    <b>Não foi possível carregar.</b> ${esc(erro.message)}<br>
    Rode <code>python -m finalpay.experiments</code> e recarregue a página.</div></div>`);

function tag(texto, tipo = '') { return `<span class="tag ${tipo}">${esc(texto)}</span>`; }

function medidas(alvo, itens) {
  alvo.innerHTML = itens
    .map((m) => `<div><span class="label">${esc(m.label)}</span>
      <span class="num-lg">${m.valor}</span>
      <div class="meta">${m.nota ?? ''}</div></div>`)
    .join('');
}

function tabela(alvo, colunas, linhas) {
  if (!linhas.length) {
    alvo.innerHTML =
      `<thead><tr>${colunas.map((c) => `<th class="${c.n ? 'n' : ''}">${esc(c.titulo)}</th>`).join('')}</tr></thead>` +
      `<tbody><tr><td colspan="${colunas.length}" class="muted">Nenhum registro para este recorte.</td></tr></tbody>`;
    return;
  }
  alvo.innerHTML =
    `<thead><tr>${colunas.map((c) => `<th class="${c.n ? 'n' : ''}">${esc(c.titulo)}</th>`).join('')}</tr></thead>` +
    `<tbody>${linhas.map((l) => `<tr>${colunas.map((c) => `<td class="${c.n ? 'n' : ''}">${c.celula(l)}</td>`).join('')}</tr>`).join('')}</tbody>`;
}

/* ------------------------------------------------------------- navegacao */
const PAGINAS = new Set($$('.page').map((p) => p.id.replace('page-', '')));

function irPara(pagina) {
  // Sem esta guarda, um hash que nao seja de pagina (o link de pular para o
  // conteudo, por exemplo) esconderia todas as secoes de uma vez.
  if (!PAGINAS.has(pagina)) pagina = 'cofre';
  $$('.page').forEach((p) => (p.hidden = p.id !== `page-${pagina}`));
  $$('.nav-item').forEach((b) =>
    b.dataset.page === pagina ? b.setAttribute('aria-current', 'page') : b.removeAttribute('aria-current'));
  history.replaceState(null, '', `#${pagina}`);
  window.scrollTo({ top: 0 });
  desenhar(pagina);
}

$$('.nav-item').forEach((b) => b.addEventListener('click', () => irPara(b.dataset.page)));

/* --------------------------------------------------------------- paginas */
const paginas = { antifraude: desenharAntifraude, resistencia: desenharResistencia };
const PRIMEIRO_SLOT = { antifraude: '#mon-medidas', resistencia: '#ecb-imagens' };

function desenhar(pagina) {
  if (!paginas[pagina] || estado.carregado.has(pagina)) return;
  const slot = $(PRIMEIRO_SLOT[pagina]);
  if (!estado.resultados && pagina !== 'resistencia') {
    // A interface precisa dizer que a bateria nao rodou, nao ficar em branco.
    if (slot) falha(slot, new Error('a bateria de experimentos ainda não foi executada'));
    return;
  }
  estado.carregado.add(pagina);
  paginas[pagina]().catch((e) => {
    console.error(pagina, e);
    estado.carregado.delete(pagina);   // permite tentar de novo
    if (slot) falha(slot, e);
  });
}

/* ----------------------------------------------------------- antifraude */
async function desenharAntifraude() {
  const bd = estado.resultados.bigdata;
  const res = bd.resumo;
  const ia = bd.ia.metricas;

  medidas($('#mon-medidas'), [
    { label: 'Eventos monitorados', valor: ni(res.eventos), nota: `${res.dias} dias, ${ni(res.usuarios)} contas` },
    { label: 'Alertas abertos', valor: ni(ia.alertas), nota: `de ${ni(ia.janelas)} janelas de comportamento` },
    { label: 'Taxa de falha', valor: pct(res.taxa_falha_pct, 3), nota: `${ni(res.falhas)} operações falharam` },
    { label: 'Latência p99', valor: `${nf(res.latencia_p99)} ms`, nota: `mediana de ${nf(res.latencia_mediana)} ms` },
  ]);

  const serie = bd.serie_temporal;
  line($('#chart-serie'), {
    height: 240, xLabel: 'dia', yLabel: 'eventos por hora',
    xFormat: (v) => new Date(v).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }),
    yFormat: (v) => ni(v), tipFormat: (v) => ni(v),
    series: [
      { name: 'Todos os eventos', color: SERIES[0], points: serie.map((p) => [new Date(p.instante).getTime(), p.eventos]) },
      { name: 'Eventos anômalos', color: SERIES[1], points: serie.map((p) => [new Date(p.instante).getTime(), p.anomalos]) },
    ],
  });

  tabela($('#tab-alertas'), [
    { titulo: 'Conta', celula: (l) => `<span class="num">${esc(l.usuario)}</span>` },
    { titulo: 'Quando', celula: (l) => `<span class="num">${esc(l.janela.slice(5, 16))}</span>` },
    { titulo: 'Risco', n: true, celula: (l) => nf(l.score, 3) },
    { titulo: 'Suspeita', celula: (l) => esc(rotulo(l.tipo_previsto)) },
    { titulo: 'Por quê', celula: (l) => `<span class="meta">${esc(l.explicacao)}</span>` },
    { titulo: 'Confere', celula: (l) => (l.tipo_previsto === l.rotulo_real ? tag('correto', 'tag-ok') : tag(rotulo(l.rotulo_real), 'tag-warn')) },
  ], bd.ia.alertas);

  tabela($('#tab-suspeitos'), [
    { titulo: 'Conta', celula: (l) => `<span class="num">${esc(l.usuario)}</span>` },
    { titulo: 'Eventos', n: true, celula: (l) => ni(l.eventos) },
    { titulo: 'Falhas', n: true, celula: (l) => ni(l.falhas) },
    { titulo: 'IPs', n: true, celula: (l) => ni(l.ips) },
    { titulo: 'Taxa', n: true, celula: (l) => pct(l.taxa_falha_pct, 1) },
  ], bd.top_suspeitos);

  tabela($('#tab-tipo'), [
    { titulo: 'Tipo', celula: (l) => esc(rotulo(l.chave)) },
    { titulo: 'Eventos', n: true, celula: (l) => ni(l.eventos) },
    { titulo: 'Falhas', n: true, celula: (l) => ni(l.falhas) },
    { titulo: 'Taxa', n: true, celula: (l) => pct(l.taxa_falha_pct) },
  ], bd.por_tipo);

  bars($('#chart-ia-tipos'), {
    height: 220, yDomain: [0, 100], yLabel: '% detectado', yFormat: (v) => `${nf(v, 0)}%`,
    tipFormat: (v) => pct(v, 1),
    data: ia.por_tipo.map((t) => ({
      label: rotuloCurto(t.tipo), value: t.revocacao_pct, color: SERIES[0],
      nota: `${t.detectadas} de ${t.janelas} janelas, tipo correto em ${nf(t.acerto_tipo_pct, 1)}%`,
    })),
  });

  const d = bd.desempenho_consultas;
  $('#ia-spec').innerHTML = [
    ['Modelo', 'Isolation Forest'],
    ['Treinado com rótulos', 'não'],
    ['ROC AUC', nf(ia.roc_auc, 4)],
    ['Precisão média', nf(ia.average_precision, 4)],
    ['Ganho sobre o acaso', `${nf(ia.ganho_sobre_acaso, 1)}×`],
    ['Revocação', pct(ia.revocacao * 100, 1)],
    ['Eventos resumidos em janelas', d.reducao_dimensional],
    ['Tempo de treino e pontuação', `${nf(d.ia_segundos, 3)} s`],
  ].map(([k, val]) => `<dt>${esc(k)}</dt><dd>${esc(val)}</dd>`).join('');
}

/* ---------------------------------------------------------- resistencia */
async function desenharResistencia() {
  const alvo = $('#ecb-imagens');
  carregando(alvo, 'Carregando imagens');
  try {
    const e = await api('/api/resultados/ecb');
    const nomeEcb = {
      original: 'Imagem original', ecb_1_rodada_sem_difusao: 'ECB, 1 rodada, sem difusão',
      ecb_14_rodadas: 'ECB, 14 rodadas', ctr_14_rodadas: 'CTR, 14 rodadas',
    };
    alvo.innerHTML = e.variantes.map((x) => `<figure style="margin:0">
        <img alt="${esc(nomeEcb[x.nome] ?? rotulo(x.nome))}" src="data:image/png;base64,${x.png_base64}"
             style="width:100%;display:block;border:1px solid var(--line);border-radius:var(--r)">
        <figcaption class="meta" style="margin-top:8px">${esc(nomeEcb[x.nome] ?? rotulo(x.nome))}<br>
          <span class="num">${nf(x.repeticao_blocos.pct_repetidos)}%</span> de blocos repetidos</figcaption></figure>`).join('');
    const ecb14 = e.variantes.find((x) => x.nome === 'ecb_14_rodadas');
    $('#ecb-nota').textContent =
      `Mesmo com 14 rodadas e difusão completa, o modo ECB preserva ${nf(ecb14.repeticao_blocos.pct_repetidos)}% ` +
      `dos blocos repetidos, e o contorno da imagem sobrevive à cifragem: blocos claros iguais produzem blocos ` +
      `cifrados iguais. No modo CTR, zero repetições. O modo de operação pesa mais que o número de rodadas.`;
  } catch (err) { falha(alvo, err); }
}

/* ------------------------------------------------------- laboratorio ao vivo */
function ligaSlider(id, saida, sufixo = '') {
  const s = $(id);
  const o = $(saida);
  const atualiza = () => (o.textContent = s.value + sufixo);
  s.addEventListener('input', atualiza);
  atualiza();
}
ligaSlider('#bf-bits', '#bf-bits-v');
ligaSlider('#df-rodadas', '#df-rodadas-v');
ligaSlider('#fq-rodadas', '#fq-rodadas-v');

async function executar(botao, alvo, rota, render) {
  const el = $(alvo);
  botao.disabled = true;
  carregando(el, 'Executando');
  try { render(el, await api(rota)); }
  catch (e) { falha(el, e); }
  finally { botao.disabled = false; }
}

$('#btn-bf').addEventListener('click', (ev) =>
  executar(ev.currentTarget, '#bf-saida', `/api/laboratorio/forca-bruta?bits=${$('#bf-bits').value}`, (el, d) => {
    el.innerHTML = `
      <div class="measures" style="margin-bottom:16px">
        <div><span class="label">Chaves por segundo</span><span class="num-lg">${ni(d.chaves_por_segundo)}</span><div class="meta">1 núcleo, medido agora</div></div>
        <div><span class="label">Chaves testadas</span><span class="num-lg">${ni(d.chaves_testadas)}</span><div class="meta">esperado: ${ni(d.chaves_esperadas_ate_achar)}</div></div>
        <div><span class="label">Tempo</span><span class="num-lg">${nf(d.segundos, 2)} s</span><div class="meta">espaço de 2^${d.bits_entropia}</div></div>
        <div><span class="label">Resultado</span><span class="num-lg">${d.chave_encontrada ? 'Quebrada' : 'Resistiu'}</span>
          <div class="meta">${d.chave_encontrada ? 'entropia reduzida é insuficiente' : 'limite de tempo atingido'}</div></div>
      </div>
      <table><thead><tr><th>Espaço de chaves</th><th>Cenário</th><th class="n">Tempo esperado</th><th>Viável</th></tr></thead>
      <tbody>${d.projecao.map((p) => `<tr><td class="num">2^${p.bits}</td><td>${esc(p.cenario)}</td>
        <td class="n">${esc(p.anos_fmt)}</td><td>${p.viavel ? tag('sim', 'tag-crit') : tag('não', 'tag-ok')}</td></tr>`).join('')}</tbody></table>`;
  }));

$('#btn-df').addEventListener('click', (ev) =>
  executar(ev.currentTarget, '#df-saida',
    `/api/laboratorio/avalanche?rodadas=${$('#df-rodadas').value}&difusao=${$('#df-difusao').checked}&amostras=4096`,
    (el, d) => {
      const ok = Math.abs(d.media_pct - 50) < 1.5;
      el.innerHTML = `<div class="measures" style="margin-bottom:16px">
          <div><span class="label">Bits alterados</span><span class="num-lg">${pct(d.media_pct)}</span><div class="meta">ideal 50,00%</div></div>
          <div><span class="label">Desvio padrão</span><span class="num-lg">${nf(d.desvio_padrao, 3)}</span><div class="meta">binomial(128; 0,5) = 5,657</div></div>
          <div><span class="label">Faixa</span><span class="num-lg">${d.minimo}–${d.maximo}</span><div class="meta">de 128 bits</div></div>
          <div><span class="label">Veredito</span><span class="num-lg">${ok ? 'Resistiu' : 'Falhou'}</span>
            <div class="meta">${ok ? 'avalanche adequada' : 'difusão insuficiente'}</div></div>
        </div><div id="df-chart"></div>`;
      line($('#df-chart'), {
        height: 230, yDomain: [0, 60], refLine: 50, refLabel: 'ideal 50%',
        xLabel: 'rodada', yLabel: '% de bits alterados',
        yFormat: (v) => `${nf(v, 0)}%`, tipFormat: (v) => `${nf(v)}%`,
        series: [{ name: 'avalanche acumulada', color: ok ? SERIES[0] : SERIES[1], points: d.por_rodada.map((p) => [p.rodada, p.pct]) }],
      });
    }));

$('#btn-fq').addEventListener('click', (ev) =>
  executar(ev.currentTarget, '#fq-saida',
    `/api/laboratorio/frequencia?rodadas=${$('#fq-rodadas').value}&difusao=${$('#fq-difusao').checked}&linhas=1500`,
    (el, d) => {
      el.innerHTML = `<div class="measures" style="margin-bottom:16px">
          <div><span class="label">Texto recuperado</span><span class="num-lg">${pct(d.acuracia_pct)}</span><div class="meta">sem nenhuma chave</div></div>
          <div><span class="label">Linha de base</span><span class="num-lg">${pct(d.linha_base_unigrama_pct)}</span><div class="meta">quem só chuta o byte mais comum</div></div>
          <div><span class="label">Posições expostas</span><span class="num-lg">${d.posicoes_expostas}</span><div class="meta">de ${d.posicoes_registro} do registro</div></div>
          <div><span class="label">Veredito</span><span class="num-lg">${d.quebrado ? 'Quebrada' : 'Resistiu'}</span>
            <div class="meta">${d.supera_linha_base ? 'vazou informação real' : 'abaixo da linha de base'}</div></div>
        </div>
        <p class="label" style="margin-bottom:8px">Original × recuperado</p>
        <pre class="code">${esc(d.trecho_original.slice(0, 80))}
${esc(d.trecho_recuperado.slice(0, 80))}</pre>`;
    }));

/* ------------------------------------------------------------------ cofre */
$$('#cofre-tipo button').forEach((b) => b.addEventListener('click', () => {
  $$('#cofre-tipo button').forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
  $('#campo-texto').hidden = b.dataset.tipo !== 'texto';
  $('#campo-arquivo').hidden = b.dataset.tipo !== 'arquivo';
}));

const lerB64 = (input) => new Promise((ok, erro) => {
  const f = input.files?.[0];
  if (!f) return ok(null);
  const fr = new FileReader();
  fr.onload = () => ok({ b64: String(fr.result).split(',')[1], nome: f.name });
  fr.onerror = () => erro(new Error('não foi possível ler o arquivo'));
  fr.readAsDataURL(f);
});

$('#btn-cifrar').addEventListener('click', async (ev) => {
  const btn = ev.currentTarget;
  const erro = $('#cofre-erro');
  erro.textContent = '';
  btn.disabled = true;
  try {
    const texto = $$('#cofre-tipo button').find((b) => b.getAttribute('aria-pressed') === 'true').dataset.tipo === 'texto';
    const arq = texto ? null : await lerB64($('#cofre-arquivo'));
    if (!texto && !arq) throw new Error('escolha um arquivo');
    const d = await api('/api/cofre/cifrar', {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        senha: $('#cofre-senha').value,
        algoritmo: $('#cofre-algo').value,
        modo: $('#cofre-modo').value,
        ...(texto ? { texto: $('#cofre-texto').value } : { conteudo_b64: arq.b64, nome_arquivo: arq.nome }),
      }),
    });
    $('#dec-envelope').value = d.envelope_b64;
    mostrarCifragem(d);
    atualizarLog();
  } catch (e) { erro.textContent = e.message; }
  finally { btn.disabled = false; }
});

function mostrarCifragem(d) {
  const m = d.metadados;
  $('#cofre-resultado').innerHTML = `
    <div class="panel"><div class="panel-head"><h2 class="h3">Envelope protegido</h2>
      ${tag(`${m.modo}, ${m.rodadas} rodadas`, 'tag-info')}
      ${tag('integridade por HMAC-SHA256', 'tag-ok')}</div>
      <div class="panel-body stack">
        <div class="measures">
          <div><span class="label">Entropia na entrada</span><span class="num-lg">${nf(d.entropia_clara, 3)}</span><div class="meta">bits por byte</div></div>
          <div><span class="label">Entropia na saída</span><span class="num-lg">${nf(d.entropia_cifrada, 3)}</span>
            <div class="meta">${d.entropia_confiavel ? 'máximo 8,000' : 'amostra curta demais para ser conclusiva'}</div></div>
          <div><span class="label">Latência</span><span class="num-lg">${nf(d.latencia_ms)} ms</span><div class="meta">${nf(d.vazao_mb_s)} MB/s</div></div>
          <div><span class="label">Tamanho</span><span class="num-lg">${ni(m.bytes_cifrados)}</span><div class="meta">de ${ni(m.bytes_claros)} bytes de entrada</div></div>
        </div>
        <div class="grid grid-2">
          <div><p class="label" style="margin-bottom:10px">Distribuição de bytes na entrada</p><div id="hist-claro"></div></div>
          <div><p class="label" style="margin-bottom:10px">Distribuição de bytes na saída</p><div id="hist-cifrado"></div></div>
        </div>
        <dl class="spec">
          <dt>Salt (novo a cada operação)</dt><dd>${esc(m.salt)}</dd>
          <dt>Nonce (novo a cada operação)</dt><dd>${esc(m.nonce)}</dd>
        </dl>
      </div></div>`;
  const hist = (sel, dados, cor) => bars($(sel), {
    data: dados.map((v, idx) => ({ label: String(idx), value: v })),
    dense: true, height: 150, color: cor, xTickEvery: 64, tipFormat: (v) => ni(v), yLabel: 'ocorrências',
  });
  hist('#hist-claro', d.histograma_claro, SERIES[1]);
  hist('#hist-cifrado', d.histograma_cifrado, SERIES[0]);
}

$('#btn-decifrar').addEventListener('click', async () => {
  const saida = $('#dec-saida');
  const envelope = $('#dec-envelope').value.trim();
  if (!envelope) { saida.innerHTML = `<div class="note"><svg><use href="#ic-info"/></svg>Cole um envelope ou proteja algo ao lado.</div>`; return; }
  carregando(saida, 'Abrindo');
  try {
    const d = await api('/api/cofre/decifrar', {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ envelope_b64: envelope, senha: $('#dec-senha').value }),
    });
    saida.innerHTML = `<div class="note" style="background:var(--ok-bg);border-color:var(--ok-line);color:var(--ok)">
        <svg><use href="#ic-info"/></svg><div><b>Integridade verificada.</b>
        ${ni(d.bytes)} bytes recuperados em ${nf(d.latencia_ms)} ms.</div></div>
      ${d.texto !== null ? `<pre class="code wrap" style="margin-top:12px">${esc(d.texto.slice(0, 1200))}</pre>`
        : `<p class="small" style="margin-top:12px">Conteúdo binário. <a download="finalpay.bin" href="data:application/octet-stream;base64,${d.conteudo_b64}">Baixar arquivo</a>.</p>`}`;
  } catch (e) {
    saida.innerHTML = `<div class="note note-warn"><svg><use href="#ic-alert"/></svg>
      <div><b>Recusado.</b> ${esc(e.message)}</div></div>`;
  }
  atualizarLog();
});

async function atualizarLog() {
  try {
    const { operacoes } = await api('/api/cofre/operacoes');
    const corpo = $('#cofre-log tbody');
    if (!operacoes.length) { corpo.innerHTML = `<tr><td colspan="7" class="muted">Nenhuma operação ainda.</td></tr>`; return; }
    corpo.innerHTML = operacoes.map((o) => `<tr>
      <td class="num">${esc(o.ts.slice(11))}</td><td>${esc(rotulo(o.tipo))}</td><td class="num">${esc(o.algoritmo)}</td>
      <td>${o.resultado === 'sucesso' ? tag('sucesso', 'tag-ok') : tag('falha', 'tag-crit')}</td>
      <td class="n">${ni(o.bytes)}</td><td class="n">${nf(o.latencia_ms)} ms</td>
      <td class="meta">${esc(o.detalhe)}</td></tr>`).join('');
  } catch { /* o log e acessorio: uma falha aqui nao deve quebrar a pagina */ }
}

/* ------------------------------------------------- lupa: antes e depois */
const lupa = { antes: null, depois: null, nota: '' };

function abrirLupa(lado = 'antes') {
  if (!lupa.antes || !lupa.depois) return;
  $('#lupa-img').src = `data:image/png;base64,${lupa[lado]}`;
  $('#lupa-img').alt = lado === 'antes' ? 'Imagem portadora original' : 'Imagem com o conteúdo oculto';
  $('#lupa-nota').textContent = lupa.nota;
  $$('#lupa-abas button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.lado === lado)));
  $('#lupa').setAttribute('open', '');
  $('#lupa-fechar').focus();
}
const fecharLupa = () => $('#lupa').removeAttribute('open');

$('#lupa-fechar').addEventListener('click', fecharLupa);
$('#lupa').addEventListener('click', (e) => { if (e.target.id === 'lupa') fecharLupa(); });
$$('#lupa-abas button').forEach((b) => b.addEventListener('click', () => abrirLupa(b.dataset.lado)));
addEventListener('keydown', (e) => {
  if (!$('#lupa').hasAttribute('open')) return;
  if (e.key === 'Escape') fecharLupa();
  // Alternar com as setas e o que prova o ponto: a diferenca nao aparece.
  if (e.key === 'ArrowLeft') abrirLupa('antes');
  if (e.key === 'ArrowRight') abrirLupa('depois');
});

/* ---------------------------------------------------------------- ocultar */
let portadora = null;        // { b64, capacidade } escolhida para ocultar
let exemploRevelar = null;   // imagem de exemplo ja com conteudo escondido

function mostrarPortadora(nome) {
  $('#oc-erro').textContent = '';
  $('#oc-resultado').innerHTML = `<div class="panel"><div class="panel-body">
    <div class="row" style="gap:14px">
      <img alt="Imagem portadora escolhida" src="data:image/png;base64,${portadora.b64}"
           style="width:120px;border:1px solid var(--line);border-radius:var(--r)">
      <div><p class="h3">Portadora pronta</p>
        <p class="small">${esc(nome)}${portadora.capacidade ? ` · cabem até ${ni(portadora.capacidade)} bytes` : ''}</p></div>
    </div></div></div>`;
}

$('#btn-exemplo').addEventListener('click', async (ev) => {
  const btn = ev.currentTarget;
  btn.disabled = true;
  try {
    const d = await api('/api/estego/portadora');
    portadora = { b64: d.imagem_b64, capacidade: d.capacidade_bytes };
    mostrarPortadora(`imagem de exemplo, ${d.dimensoes[0]}×${d.dimensoes[1]} px`);
  } catch (e) { $('#oc-erro').textContent = e.message; }
  finally { btn.disabled = false; }
});

$('#oc-portadora').addEventListener('change', async () => {
  const arq = await lerB64($('#oc-portadora'));
  if (!arq) return;
  portadora = { b64: arq.b64, capacidade: null };
  mostrarPortadora(arq.nome);
});

$('#btn-ocultar').addEventListener('click', async (ev) => {
  const btn = ev.currentTarget;
  const erro = $('#oc-erro');
  erro.textContent = '';
  if (!portadora) { erro.textContent = 'escolha uma imagem portadora ou use a de exemplo'; return; }
  btn.disabled = true;
  try {
    const d = await api('/api/cofre/cifrar', {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        texto: $('#oc-texto').value, senha: $('#oc-senha').value,
        ocultar_em_imagem: true, imagem_b64: portadora.b64,
      }),
    });
    const e = d.esteganografia;
    const suspeita = e.esteganalise.suspeita === 'alta';
    $('#oc-resultado').innerHTML = `
      <div class="panel"><div class="panel-head"><h2 class="h3">Conteúdo oculto</h2>
        ${suspeita ? tag('detectável por esteganálise', 'tag-warn') : tag('não detectado pela esteganálise', 'tag-ok')}</div>
        <div class="panel-body stack">
          <div class="measures">
            <div><span class="label">PSNR</span><span class="num-lg">${nf(e.qualidade.psnr_db)} dB</span><div class="meta">acima de 40 dB é imperceptível</div></div>
            <div><span class="label">Ocupação</span><span class="num-lg">${pct(e.ocupacao_pct)}</span><div class="meta">de ${ni(e.capacidade_bytes)} bytes disponíveis</div></div>
            <div><span class="label">Subpixels alterados</span><span class="num-lg">${pct(e.qualidade.pct_alterado, 3)}</span><div class="meta">desvio máximo de ${e.qualidade.desvio_maximo} por canal</div></div>
            <div><span class="label">Envelope oculto</span><span class="num-lg">${ni(d.metadados.bytes_cifrados)}</span><div class="meta">bytes, já cifrados</div></div>
          </div>
          <div class="img-compare">
            <figure><img class="ampliavel" data-lado="antes" alt="Imagem portadora original" src="data:image/png;base64,${portadora.b64}">
              <figcaption class="meta">Antes</figcaption></figure>
            <figure><img class="ampliavel" data-lado="depois" alt="Imagem com o conteúdo oculto" src="data:image/png;base64,${e.imagem_b64}">
              <figcaption class="meta">Depois, com a mensagem dentro</figcaption></figure>
          </div>
          <div class="row">
            <button class="btn btn-primary" id="btn-comparar">
              <svg><use href="#ic-image"/></svg>Comparar em tela cheia</button>
            <a class="btn" download="finalpay-oculto.png" href="data:image/png;base64,${e.imagem_b64}">
              <svg><use href="#ic-download"/></svg>Baixar imagem</a>
            <span class="meta">as setas alternam entre antes e depois sem mover a imagem</span>
          </div>
        </div></div>`;
    lupa.antes = portadora.b64;
    lupa.depois = e.imagem_b64;
    lupa.nota = `${ni(d.metadados.bytes_cifrados)} bytes ocultos · PSNR ${nf(e.qualidade.psnr_db)} dB · ` +
                `${pct(e.qualidade.pct_alterado, 3)} dos subpixels mudaram, no máximo ${e.qualidade.desvio_maximo} de 255`;
    $('#btn-comparar').addEventListener('click', () => abrirLupa('antes'));
    $$('#oc-resultado img.ampliavel').forEach((img) =>
      img.addEventListener('click', () => abrirLupa(img.dataset.lado)));
    atualizarLog();
  } catch (e) { erro.textContent = e.message; }
  finally { btn.disabled = false; }
});

/* exemplo pronto para quem quer demonstrar so a extracao */
$('#btn-rev-exemplo').addEventListener('click', async (ev) => {
  const btn = ev.currentTarget;
  const erro = $('#rev-erro');
  erro.textContent = '';
  btn.disabled = true;
  try {
    const senha = $('#rev-senha').value || 'cofre-finalpay-2026';
    const d = await api(`/api/estego/exemplo?senha=${encodeURIComponent(senha)}`);
    exemploRevelar = d.imagem_b64;
    lupa.antes = d.portadora_b64;
    lupa.depois = d.imagem_b64;
    lupa.nota = `${ni(d.bytes_ocultos)} bytes ocultos · PSNR ${nf(d.qualidade.psnr_db)} dB`;
    $('#rev-saida').innerHTML = `<div class="note"><svg><use href="#ic-info"/></svg><div>
      <b>Imagem de exemplo carregada</b>, com ${ni(d.bytes_ocultos)} bytes já escondidos.
      Clique em <b>Revelar</b> para extrair, ou compare as duas versões em tela cheia.</div></div>
      <div class="row" style="margin-top:12px">
        <img class="ampliavel" data-lado="depois" alt="Imagem de exemplo com conteúdo oculto"
             src="data:image/png;base64,${d.imagem_b64}"
             style="width:130px;border:1px solid var(--line);border-radius:var(--r)">
        <button class="btn btn-sm" id="btn-comparar-rev">
          <svg><use href="#ic-image"/></svg>Comparar em tela cheia</button>
      </div>`;
    $('#btn-comparar-rev').addEventListener('click', () => abrirLupa('antes'));
    $$('#rev-saida img.ampliavel').forEach((img) =>
      img.addEventListener('click', () => abrirLupa(img.dataset.lado)));
  } catch (e) { erro.textContent = e.message; }
  finally { btn.disabled = false; }
});

$('#btn-revelar').addEventListener('click', async (ev) => {
  const btn = ev.currentTarget;
  const saida = $('#rev-saida');
  const arq = await lerB64($('#rev-imagem'));
  const imagem = arq ? arq.b64 : exemploRevelar;
  if (!imagem) {
    saida.innerHTML = `<div class="note"><svg><use href="#ic-info"/></svg>Escolha a imagem que contém o conteúdo oculto, ou carregue a de exemplo.</div>`;
    return;
  }
  btn.disabled = true;
  carregando(saida, 'Revelando');
  try {
    const d = await api('/api/cofre/decifrar', {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ imagem_b64: imagem, senha: $('#rev-senha').value }),
    });
    saida.innerHTML = `<div class="note" style="background:var(--ok-bg);border-color:var(--ok-line);color:var(--ok)">
        <svg><use href="#ic-info"/></svg><div><b>Conteúdo recuperado da imagem.</b>
        ${ni(d.bytes)} bytes em ${nf(d.latencia_ms)} ms.</div></div>
      ${d.texto !== null ? `<pre class="code wrap" style="margin-top:12px">${esc(d.texto.slice(0, 1200))}</pre>` : ''}`;
  } catch (e) {
    saida.innerHTML = `<div class="note note-warn"><svg><use href="#ic-alert"/></svg>
      <div><b>Nada revelado.</b> ${esc(e.message)}</div></div>`;
  } finally { btn.disabled = false; }
  atualizarLog();
});

/* ------------------------------------------------------------------ inicio */
$('#btn-bateria').addEventListener('click', async (ev) => {
  const btn = ev.currentTarget;
  btn.disabled = true;
  $('#status-bateria').textContent = 'executando a bateria completa…';
  try {
    // Bateria completa: o botao substitui os resultados atuais, entao tem de
    // produzir os definitivos, nunca uma amostra reduzida.
    await api('/api/experimentos/executar?rapido=false', { method: 'POST' });
    const esperar = setInterval(async () => {
      try {
        const s = await api('/api/status');
        if (s.executando) return;
        clearInterval(esperar);
        btn.disabled = false;
        estado.carregado.clear();
        await iniciar();
        irPara(location.hash.slice(1));
      } catch (e) {
        // Sem isto, uma falha de rede deixaria o botao desativado para sempre.
        clearInterval(esperar);
        btn.disabled = false;
        $('#status-bateria').textContent = `falha ao acompanhar: ${e.message}`;
      }
    }, 1500);
  } catch (e) { $('#status-bateria').textContent = e.message; btn.disabled = false; }
});

async function iniciar() {
  for (const alvo of ['#panorama-medidas', '#bd-medidas', '#ia-medidas', '#estego-medidas']) {
    const el = $(alvo);
    if (el && !el.children.length) el.innerHTML = '';
  }
  try {
    const s = await api('/api/status');
    $('#status-bateria').textContent = s.gerado_em
      ? `bateria ${s.modo} · ${new Date(s.gerado_em).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })}`
      : 'nenhuma bateria executada';
    estado.resultados = await api('/api/resultados');
    estado.nomes = estado.resultados?.bigdata?.nomes_exibicao ?? null;
    estado.nomesCurtos = estado.resultados?.bigdata?.nomes_curtos ?? null;
  } catch (e) {
    // Cada pagina mostra a propria falha quando nao ha resultados; aqui basta
    // o estado no topo, sem apontar para um elemento que nao existe mais.
    $('#status-bateria').textContent = 'sem resultados: rode a bateria';
    console.error('iniciar', e);
  }
}

await iniciar();
irPara(location.hash.slice(1));
atualizarLog();
window.addEventListener('hashchange', () => {
  const alvo = location.hash.slice(1);
  if (PAGINAS.has(alvo)) irPara(alvo);  // ancoras que nao sao pagina rolam normalmente
});
