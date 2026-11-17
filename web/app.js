/* FinalPay — dashboard.
   Busca os resultados medidos pela bateria e os desenha. Nenhum numero e
   escrito aqui: tudo vem de results/experimentos.json via API. */

import { bars, heatmap, line, SERIES } from './charts.js';

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];

const nf = (v, c = 2) =>
  v === null || v === undefined || Number.isNaN(v)
    ? '—'
    : Number(v).toLocaleString('pt-BR', { minimumFractionDigits: c, maximumFractionDigits: c });
const ni = (v) => (v === null || v === undefined ? '—' : Math.round(v).toLocaleString('pt-BR'));
const pct = (v, c = 2) => `${nf(v, c)}%`;
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (m) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[m]));
const rotulo = (s) => estado.nomes?.[s] ?? String(s ?? '').replace(/_/g, ' ');
const sup = (n) => String(n).replace(/-/g, '⁻').replace(/[0-9]/g, (d) => '⁰¹²³⁴⁵⁶⁷⁸⁹'[+d]);

const estado = { resultados: null, carregado: new Set(), nomes: null };

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
  if (!PAGINAS.has(pagina)) pagina = 'panorama';
  $$('.page').forEach((p) => (p.hidden = p.id !== `page-${pagina}`));
  $$('.nav-item').forEach((b) =>
    b.dataset.page === pagina ? b.setAttribute('aria-current', 'page') : b.removeAttribute('aria-current'));
  history.replaceState(null, '', `#${pagina}`);
  window.scrollTo({ top: 0 });
  desenhar(pagina);
}

$$('.nav-item').forEach((b) => b.addEventListener('click', () => irPara(b.dataset.page)));

/* --------------------------------------------------------------- paginas */
const paginas = {
  panorama: desenharPanorama,
  cifra: desenharCifra,
  estego: desenharEstego,
  bigdata: desenharBigData,
  ia: desenharIA,
  veredito: desenharVeredito,
  ataques: desenharAtaques,
};

const PRIMEIRO_SLOT = {
  panorama: '#panorama-verdito', cifra: '#cifra-spec', estego: '#estego-spec',
  bigdata: '#bd-spec', ia: '#ia-medidas', veredito: '#veredito-conteudo', ataques: '#ecb-imagens',
};

function desenhar(pagina) {
  if (!paginas[pagina] || estado.carregado.has(pagina)) return;
  const slot = $(PRIMEIRO_SLOT[pagina]);
  if (!estado.resultados && pagina !== 'ataques') {
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

/* -------------------------------------------------------------- panorama */
async function desenharPanorama() {
  const r = estado.resultados;
  const v = r.veredito;
  const av = r.diferencial.fpc_integro;
  const ctr = r.estatistico.perfis.find((p) => p.rotulo === 'fpc_ctr_14_rodadas');
  const ia = r.bigdata.ia.metricas;
  const seguro = v.e_seguro;

  // O titulo e a moldura ja vivem no HTML: se a bateria nao rodou, a primeira
  // tela continua com cabecalho e com um recado, em vez de ficar em branco.
  $('#verdito-resposta').textContent = seguro.resposta;
  $('#verdito-ressalvas').innerHTML = tag(`${seguro.ressalvas.length} ressalvas`, 'tag-warn');
  $('#verdito-justificativa').textContent = seguro.justificativa;
  $('#verdito-ressalva').innerHTML = `<b>Principal ressalva:</b> ${esc(seguro.ressalvas[0])}`;

  medidas($('#panorama-medidas'), [
    { label: 'Efeito avalanche', valor: pct(av.media_pct), nota: `ideal 50,00% · σ ${nf(av.desvio_padrao, 3)}` },
    { label: 'Entropia da saída', valor: nf(ctr.entropia_bits_por_byte, 4), nota: 'bits por byte, máximo 8' },
    { label: 'Detecção de anomalias', valor: nf(ia.roc_auc, 4), nota: `ROC AUC sobre ${ni(ia.janelas)} janelas` },
    { label: 'Eventos processados', valor: ni(r.bigdata.resumo.eventos), nota: `${r.bigdata.resumo.dias} dias em Parquet` },
  ]);

  const perguntas = [
    { q: 'Apresenta efeito avalanche?', d: v.efeito_avalanche, extra: `variante sem difusão: ${pct(r.diferencial.fpc_fraco.media_pct)}` },
    { q: 'Existem padrões na saída?', d: v.padroes_na_saida, extra: `índice de coincidência ${nf(v.padroes_na_saida.indice_coincidencia, 6)} (uniforme = 0,003906)` },
    { q: 'Qual ataque foi mais eficaz?', d: v.ataque_mais_eficaz, extra: v.ataque_mais_eficaz.ranking[0].contra_fraco },
    { q: 'O sistema é seguro?', d: v.e_seguro, extra: `força bruta inviável por ${r.forca_bruta.projecao.find((p) => p.bits === 256 && p.cenario.includes('GPU'))?.anos_fmt ?? '—'}` },
  ];
  $('#panorama-perguntas').innerHTML = perguntas
    .map(({ q, d, extra }) => `<div class="panel"><div class="panel-body">
        <h3 class="h3" style="margin-bottom:12px">${esc(q)}</h3>
        <p class="answer" style="margin-bottom:10px">${esc(d.resposta)}</p>
        <p class="body">${esc(extra)}</p></div></div>`)
    .join('');

  const camadas = [
    ['1', 'Entrada de dados', 'Texto, arquivos e imagens', 'cofre'],
    ['2', 'Criptografia', `FPC-128 de ${r.cifra.rodadas} rodadas e AES-256`, 'cifra'],
    // Sem numero aqui: a secao de esteganografia nao vem no payload leve, e um
    // zero silencioso seria um numero inventado na tela.
    ['3', 'Esteganografia', 'Ocultação do envelope em imagens', 'estego'],
    ['4', 'Big Data', `${ni(r.bigdata.resumo.eventos)} eventos`, 'bigdata'],
    ['5', 'Inteligência Artificial', `AUC ${nf(ia.roc_auc, 4)}`, 'ia'],
    ['6', 'Dashboard', 'Alertas, gráficos e veredito', 'veredito'],
  ];
  $('#panorama-camadas').innerHTML = camadas
    .map(([n, t, s, pg]) => `<a class="panel" href="#${pg}">
        <div class="panel-body"><div class="row" style="gap:9px;margin-bottom:8px">
          <span class="nav-num">${n}</span><span class="h3">${esc(t)}</span></div>
          <p class="meta">${esc(s)}</p></div></a>`)
    .join('');
}

/* ----------------------------------------------------------------- cifra */
async function desenharCifra() {
  const r = estado.resultados;
  const c = r.cifra;
  const av = r.diferencial.fpc_integro;
  const fr = r.diferencial.fpc_fraco;

  $('#cifra-spec').innerHTML = [
    ['Bloco', `${c.bloco_bits} bits`], ['Chave', `${c.chave_bits} bits`],
    ['Rodadas', c.rodadas], ['Estrutura', 'SPN'],
    ['S-box bijetiva', c.sbox_bijetiva ? 'sim' : 'não'],
    ['Pontos fixos da S-box', c.sbox_pontos_fixos],
    ['Uniformidade diferencial', `${c.ddt_maximo} → 2${sup(nf(c.log2_prob_diferencial, 0))}`],
    ['Integridade', c.integridade_detecta_adulteracao ? 'HMAC-SHA256' : 'ausente'],
    ['Chave por mensagem', c.ciframentos_distintos_mesma_entrada ? 'sim (salt + nonce)' : 'não'],
  ].map(([k, val]) => `<dt>${esc(k)}</dt><dd>${esc(val)}</dd>`).join('');

  const semDif = r.diferencial.fpc_sem_difusao_14_rodadas;
  line($('#chart-avalanche'), {
    height: 250, draw: true, yDomain: [0, 60], refLine: 50, refLabel: 'ideal 50%', xInteiro: true,
    xLabel: 'rodada', yLabel: '% de bits alterados',
    yFormat: (v) => `${nf(v, 0)}%`, tipFormat: (v) => `${nf(v)}%`,
    series: [
      { name: `FPC-128 íntegro (${c.rodadas} rodadas, com difusão)`, color: SERIES[0], points: av.por_rodada.map((p) => [p.rodada, p.pct]) },
      { name: `${c.rodadas} rodadas, sem difusão`, color: SERIES[1], points: semDif.por_rodada.map((p) => [p.rodada, p.pct]) },
    ],
  });
  const completa = av.por_rodada.find((p) => p.pct > 49);
  $('#cifra-avalanche-nota').textContent =
    `A difusão se completa na rodada ${completa?.rodada ?? '—'}; a cifra usa ${c.rodadas}, ` +
    `uma margem de ${nf(c.rodadas / (completa?.rodada || 1), 1)}×. O que sustenta a avalanche é a difusão, ` +
    `não a quantidade de rodadas: com o MixColumns desligado, ${c.rodadas} rodadas entregam ` +
    `${pct(semDif.media_pct)} — praticamente o mesmo que uma única rodada (${pct(fr.media_pct)}).`;

  const hist = av.histograma.map((v, i) => ({ label: String(i), value: v }));
  bars($('#chart-aval-hist'), {
    data: hist, dense: true, height: 210, color: SERIES[0], refLine: undefined,
    xLabel: 'bits alterados (de 128)', yLabel: 'ocorrências',
    tipFormat: (v) => ni(v), xTickEvery: 16,
  });

  bars($('#chart-vazao'), {
    height: 210, yLabel: 'MB/s', tipFormat: (v) => `${nf(v)} MB/s`,
    data: [
      { label: 'FPC-128', value: r.desempenho.fpc128_mb_por_s, color: SERIES[0], nota: 'Python + numpy' },
      { label: 'AES-256', value: r.desempenho.aes256_mb_por_s, color: SERIES[2], nota: 'biblioteca com AES-NI' },
    ],
  });

  for (const [secao, alvoGrafico, alvoResumo] of [
    ['sac', '#chart-sac', '#sac-resumo'], ['sac_fraco', '#chart-sac-fraco', '#sac-fraco-resumo'],
  ]) {
    carregando($(alvoResumo), 'Carregando matriz');
    try {
      const s = await api(`/api/resultados/${secao}`);
      heatmap($(alvoGrafico), {
        matrix: s.matriz, mid: 0.5, span: 0.5, height: 250,
        xLabel: 'bit de saída', yLabel: 'bit de entrada', rotulo: 'P(inversão)',
      });
      $(alvoResumo).innerHTML = `<dl class="spec">
        <dt>Média</dt><dd>${nf(s.media, 5)}</dd>
        <dt>Desvio máximo</dt><dd>${nf(s.desvio_maximo, 5)}</dd>
        <dt>Limite (Bonferroni 5%)</dt><dd>${nf(s.limite_bonferroni, 5)}</dd>
        <dt>Células fora do limite</dt><dd>${ni(s.celulas_fora_do_limite)} de ${ni(s.celulas)}</dd>
        </dl><div style="margin-top:12px">${s.satisfaz_sac ? tag('Satisfaz o SAC', 'tag-ok') : tag('Não satisfaz o SAC', 'tag-crit')}</div>`;
    } catch (e) { falha($(alvoResumo), e); }
  }
}

/* ------------------------------------------------------------ esteganografia */
async function desenharEstego() {
  const alvo = $('#estego-spec');
  carregando(alvo);
  try {
    const s = await api('/api/resultados/estego');
    medidas($('#estego-medidas'), [
      { label: 'PSNR', valor: `${nf(s.qualidade.psnr_db)} dB`, nota: 'acima de 40 dB é imperceptível' },
      { label: 'Capacidade', valor: ni(s.capacidade_bytes), nota: `bytes · ocupação de ${pct(s.ocupacao_pct)}` },
      { label: 'Subpixels alterados', valor: pct(s.qualidade.pct_alterado, 3), nota: `desvio máximo de ${s.qualidade.desvio_maximo} por canal` },
      { label: 'Segmentos suspeitos', valor: `${s.esteganalise.segmentos_suspeitos.lsb_chaveado_finalpay}`, nota: `contra ${s.esteganalise.segmentos_suspeitos.lsb_sequencial_sem_chave} do LSB sequencial` },
    ]);

    $('#estego-imagens').innerHTML = `
      <figure><img alt="Imagem portadora original" src="data:image/png;base64,${s.imagens_base64.original}">
        <figcaption class="meta">Portadora original</figcaption></figure>
      <figure><img alt="Imagem com o envelope cifrado oculto" src="data:image/png;base64,${s.imagens_base64.com_payload}">
        <figcaption class="meta">Com ${ni(s.payload_bytes)} bytes ocultos</figcaption></figure>`;

    alvo.innerHTML = [
      ['Erro quadrático médio', nf(s.qualidade.mse, 6)],
      ['Subpixels alterados', `${ni(s.qualidade.subpixels_alterados)} de ${ni(s.qualidade.subpixels_totais)}`],
      ['Desvio máximo por canal', s.qualidade.desvio_maximo],
      ['Round-trip', s.round_trip_ok ? 'íntegro' : 'falhou'],
      ['Chave errada', s.resiste_chave_errada ? 'rejeitada' : 'aceita'],
    ].map(([k, val]) => `<dt>${esc(k)}</dt><dd>${esc(val)}</dd>`).join('');

    const varre = s.esteganalise.varredura;
    line($('#chart-estegoanalise'), {
      height: 230, yDomain: [0, 1], refLine: 0.5, refLabel: 'limiar de suspeita',
      xLabel: '% da imagem', yLabel: 'probabilidade de ocultação',
      yFormat: (v) => nf(v, 1), tipFormat: (v) => nf(v, 4),
      series: [
        { name: 'LSB sequencial sem chave', color: SERIES[1], points: varre.lsb_sequencial_sem_chave.map((p) => [p.inicio_pct, p.p_estego]) },
        { name: 'LSB chaveado do FinalPay', color: SERIES[0], points: varre.lsb_chaveado_finalpay.map((p) => [p.inicio_pct, p.p_estego]) },
        { name: 'Imagem limpa (controle)', color: SERIES[2], points: varre.imagem_limpa.map((p) => [p.inicio_pct, p.p_estego]) },
      ],
    });
    $('#estego-nota').textContent =
      `Com a mesma carga de ${ni(s.esteganalise.payload_da_comparacao_bytes)} bytes ` +
      `(${pct(s.esteganalise.ocupacao_da_comparacao_pct, 1)} da capacidade), o LSB sequencial acende ` +
      `${s.esteganalise.segmentos_suspeitos.lsb_sequencial_sem_chave} dos 20 segmentos porque concentra os bits no ` +
      `início do arquivo. Espalhando as posições por uma permutação derivada da chave, acendem ` +
      `${s.esteganalise.segmentos_suspeitos.lsb_chaveado_finalpay} — o mesmo que a imagem limpa.`;
  } catch (e) { falha(alvo, e); }
}

/* --------------------------------------------------------------- big data */
async function desenharBigData() {
  const r = estado.resultados.bigdata;
  const res = r.resumo;
  medidas($('#bd-medidas'), [
    { label: 'Eventos', valor: ni(res.eventos), nota: `${res.dias} dias · ${ni(res.usuarios)} usuários` },
    { label: 'Em disco', valor: `${nf(r.ingestao.bytes_em_disco / 1e6, 1)} MB`, nota: `${nf(r.ingestao.bytes_por_evento)} B por evento` },
    { label: 'Taxa de falha', valor: pct(res.taxa_falha_pct, 3), nota: `${ni(res.falhas)} falhas` },
    { label: 'Latência p99', valor: `${nf(res.latencia_p99)} ms`, nota: `mediana de ${nf(res.latencia_mediana)} ms` },
  ]);

  const serie = r.serie_temporal;
  line($('#chart-serie'), {
    height: 240, xLabel: 'dia', yLabel: 'eventos por hora',
    xFormat: (v) => new Date(v).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }),
    yFormat: (v) => ni(v), tipFormat: (v) => ni(v),
    series: [
      { name: 'Todos os eventos', color: SERIES[0], points: serie.map((p) => [new Date(p.instante).getTime(), p.eventos]) },
      { name: 'Eventos anômalos', color: SERIES[1], points: serie.map((p) => [new Date(p.instante).getTime(), p.anomalos]) },
    ],
  });

  tabela($('#tab-tipo'), [
    { titulo: 'Tipo', celula: (l) => esc(rotulo(l.chave)) },
    { titulo: 'Eventos', n: true, celula: (l) => ni(l.eventos) },
    { titulo: 'Falhas', n: true, celula: (l) => ni(l.falhas) },
    { titulo: 'Taxa', n: true, celula: (l) => pct(l.taxa_falha_pct) },
  ], r.por_tipo);

  tabela($('#tab-suspeitos'), [
    { titulo: 'Usuário', celula: (l) => `<span class="num">${esc(l.usuario)}</span>` },
    { titulo: 'Eventos', n: true, celula: (l) => ni(l.eventos) },
    { titulo: 'Falhas', n: true, celula: (l) => ni(l.falhas) },
    { titulo: 'IPs', n: true, celula: (l) => ni(l.ips) },
    { titulo: 'Taxa', n: true, celula: (l) => pct(l.taxa_falha_pct, 1) },
  ], r.top_suspeitos);

  const d = r.desempenho_consultas;
  $('#bd-spec').innerHTML = [
    ['Ingestão', `${nf(r.ingestao.segundos)} s`],
    ['Partições', `${r.ingestao.particoes} dias`],
    ['Consulta de resumo', `${nf(d.resumo_segundos, 3)} s`],
    ['Agregação em janelas', `${nf(d.janelas_segundos, 3)} s`],
    ['Treino e pontuação da IA', `${nf(d.ia_segundos, 3)} s`],
    ['Redução', d.reducao_dimensional],
  ].map(([k, val]) => `<dt>${esc(k)}</dt><dd>${esc(val)}</dd>`).join('');
}

/* --------------------------------------------------------------------- IA */
async function desenharIA() {
  const r = estado.resultados.bigdata.ia;
  const m = r.metricas;
  medidas($('#ia-medidas'), [
    { label: 'ROC AUC', valor: nf(m.roc_auc, 4), nota: `sobre ${ni(m.janelas)} janelas` },
    { label: 'Precisão média', valor: nf(m.average_precision, 4), nota: `${nf(m.ganho_sobre_acaso, 1)}× acima do acaso` },
    { label: 'Revocação', valor: pct(m.revocacao * 100, 1), nota: `${ni(m.alertas)} alertas emitidos` },
    { label: 'Prevalência real', valor: pct(m.prevalencia_pct, 3), nota: `${ni(m.janelas_anomalas)} janelas anômalas` },
  ]);

  bars($('#chart-ia-tipos'), {
    height: 240, yDomain: [0, 100], yLabel: '% detectado', yFormat: (v) => `${nf(v, 0)}%`,
    tipFormat: (v) => pct(v, 1),
    data: m.por_tipo.map((t) => ({
      label: rotulo(t.tipo), value: t.revocacao_pct, color: SERIES[0],
      nota: `${t.detectadas} de ${t.janelas} janelas · tipo correto em ${nf(t.acerto_tipo_pct, 1)}%`,
    })),
  });

  const dist = r.distribuicao_score;
  bars($('#chart-ia-score'), {
    height: 240, dense: true, color: SERIES[0], yLabel: 'janelas', xLabel: 'score de risco',
    tipFormat: (v) => ni(v), xTickEvery: 8,
    data: dist.contagem.map((v, idx) => ({ label: nf(dist.bordas[idx], 2), value: v })),
  });

  tabela($('#tab-operacao'), [
    { titulo: 'Orçamento de alertas', n: true, celula: (l) => ni(l.orcamento_alertas) },
    { titulo: '% das janelas', n: true, celula: (l) => pct(l.orcamento_pct, 2) },
    { titulo: 'Precisão', n: true, celula: (l) => nf(l.precisao, 3) },
    { titulo: 'Revocação', n: true, celula: (l) => nf(l.revocacao, 3) },
  ], m.pontos_de_operacao);

  tabela($('#tab-alertas'), [
    { titulo: 'Usuário', celula: (l) => `<span class="num">${esc(l.usuario)}</span>` },
    { titulo: 'Janela', celula: (l) => `<span class="num">${esc(l.janela.slice(5, 16))}</span>` },
    { titulo: 'Score', n: true, celula: (l) => nf(l.score, 3) },
    { titulo: 'Tipo previsto', celula: (l) => esc(rotulo(l.tipo_previsto)) },
    { titulo: 'Confere', celula: (l) => (l.tipo_previsto === l.rotulo_real ? tag('correto', 'tag-ok') : tag(rotulo(l.rotulo_real), 'tag-warn')) },
    { titulo: 'Por quê', celula: (l) => `<span class="meta">${esc(l.explicacao)}</span>` },
  ], r.alertas);
}

/* --------------------------------------------------------------- veredito */
async function desenharVeredito() {
  const v = estado.resultados.veredito;
  const bloco = (titulo, d, corpo) => `
    <div class="panel"><div class="panel-body" style="padding:24px 28px">
      <h2 class="h2" style="margin-bottom:14px">${esc(titulo)}</h2>
      <p class="answer" style="margin-bottom:14px">${esc(d.resposta)}</p>
      <p class="body measure">${esc(d.justificativa)}</p>${corpo || ''}</div></div>`;

  const ranking = `<div class="table-wrap auto" style="margin-top:20px"><table>
    <thead><tr><th>Ataque</th><th>O que o atacante obtém</th><th>Contra a cifra íntegra</th><th>Contra a variante enfraquecida</th></tr></thead>
    <tbody>${v.ataque_mais_eficaz.ranking.map((x) => `<tr>
      <td><b>${esc(x.ataque)}</b></td><td>${esc(x.ganho)}</td>
      <td class="meta">${esc(x.contra_integro)}</td><td class="meta">${esc(x.contra_fraco)}</td></tr>`).join('')}</tbody></table></div>`;

  const listas = `<div class="grid grid-2" style="margin-top:22px">
    <div><p class="label" style="margin-bottom:10px">A favor</p>
      <ul class="small" style="margin:0;padding-left:18px;line-height:1.7">${v.e_seguro.a_favor.map((x) => `<li>${esc(x)}</li>`).join('')}</ul></div>
    <div><p class="label" style="margin-bottom:10px">Ressalvas</p>
      <ul class="small" style="margin:0;padding-left:18px;line-height:1.7">${v.e_seguro.ressalvas.map((x) => `<li>${esc(x)}</li>`).join('')}</ul></div></div>`;

  $('#veredito-conteudo').innerHTML =
    bloco('O sistema apresenta efeito avalanche?', v.efeito_avalanche) +
    bloco('Existem padrões na saída?', v.padroes_na_saida) +
    bloco('Qual ataque foi mais eficaz?', v.ataque_mais_eficaz, ranking) +
    bloco('O sistema é seguro?', v.e_seguro, listas);
}

/* ---------------------------------------------------------------- ataques */
async function desenharAtaques() {
  const alvo = $('#ecb-imagens');
  carregando(alvo, 'Carregando imagens');
  try {
    const e = await api('/api/resultados/ecb');
    const nomeEcb = {
      original: 'Imagem original', ecb_1_rodada_sem_difusao: 'ECB · 1 rodada, sem difusão',
      ecb_14_rodadas: 'ECB · 14 rodadas', ctr_14_rodadas: 'CTR · 14 rodadas',
    };
    alvo.innerHTML = e.variantes.map((x) => `<figure style="margin:0">
        <img alt="${esc(nomeEcb[x.nome] ?? rotulo(x.nome))}" src="data:image/png;base64,${x.png_base64}"
             style="width:100%;display:block;border:1px solid var(--line);border-radius:var(--r)">
        <figcaption class="meta" style="margin-top:8px">${esc(nomeEcb[x.nome] ?? rotulo(x.nome))}<br>
          <span class="num">${nf(x.repeticao_blocos.pct_repetidos)}%</span> de blocos repetidos</figcaption></figure>`).join('');
    const ecb14 = e.variantes.find((x) => x.nome === 'ecb_14_rodadas');
    $('#ecb-nota').textContent =
      `Mesmo com 14 rodadas e difusão completa, o modo ECB preserva ${nf(ecb14.repeticao_blocos.pct_repetidos)}% ` +
      `dos blocos repetidos e o contorno da imagem sobrevive à cifragem: blocos claros iguais produzem blocos ` +
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
ligaSlider('#cofre-rodadas', '#cofre-rodadas-v');

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
$('#cofre-ocultar').addEventListener('change', (e) => ($('#campo-portadora').hidden = !e.target.checked));

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
    const corpo = {
      senha: $('#cofre-senha').value,
      algoritmo: $('#cofre-algo').value,
      modo: $('#cofre-modo').value,
      rodadas: +$('#cofre-rodadas').value,
      difusao: $('#cofre-difusao').checked,
      ocultar_em_imagem: $('#cofre-ocultar').checked,
      ...(texto ? { texto: $('#cofre-texto').value } : { conteudo_b64: arq.b64, nome_arquivo: arq.nome }),
    };
    if (corpo.ocultar_em_imagem) {
      const port = await lerB64($('#cofre-portadora'));
      if (!port) throw new Error('escolha uma imagem portadora');
      corpo.imagem_b64 = port.b64;
    }
    const d = await api('/api/cofre/cifrar', {
      method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(corpo),
    });
    $('#dec-envelope').value = d.envelope_b64;
    mostrarCifragem(d);
    atualizarLog();
  } catch (e) { erro.textContent = e.message; }
  finally { btn.disabled = false; }
});

function mostrarCifragem(d) {
  const m = d.metadados;
  const confiavel = d.entropia_confiavel;
  $('#cofre-resultado').innerHTML = `
    <div class="panel"><div class="panel-head"><h3 class="h3">Envelope gerado</h3>
      ${tag(`${m.modo} · ${m.rodadas} rodadas`, 'tag-info')}
      ${m.difusao ? tag('difusão ligada', 'tag-ok') : tag('difusão desligada', 'tag-crit')}</div>
      <div class="panel-body stack">
        <div class="measures">
          <div><span class="label">Entropia do claro</span><span class="num-lg">${nf(d.entropia_clara, 3)}</span><div class="meta">bits por byte</div></div>
          <div><span class="label">Entropia do cifrado</span><span class="num-lg">${nf(d.entropia_cifrada, 3)}</span>
            <div class="meta">${confiavel ? 'máximo 8,000' : 'amostra curta demais para ser conclusiva'}</div></div>
          <div><span class="label">Latência</span><span class="num-lg">${nf(d.latencia_ms)} ms</span><div class="meta">${nf(d.vazao_mb_s)} MB/s</div></div>
          <div><span class="label">Tamanho</span><span class="num-lg">${ni(m.bytes_cifrados)}</span><div class="meta">de ${ni(m.bytes_claros)} bytes claros</div></div>
        </div>
        <div class="grid grid-2">
          <div><p class="label" style="margin-bottom:10px">Distribuição de bytes — claro</p><div id="hist-claro"></div></div>
          <div><p class="label" style="margin-bottom:10px">Distribuição de bytes — cifrado</p><div id="hist-cifrado"></div></div>
        </div>
        <dl class="spec">
          <dt>Salt</dt><dd>${esc(m.salt)}</dd>
          <dt>Nonce</dt><dd>${esc(m.nonce)}</dd>
        </dl>
        ${d.esteganografia ? `
        <div class="divider"></div>
        <p class="label">Oculto na imagem</p>
        <div class="row">
          ${tag(`PSNR ${nf(d.esteganografia.qualidade.psnr_db)} dB`, 'tag-ok')}
          ${tag(`ocupa ${pct(d.esteganografia.ocupacao_pct)} da capacidade`)}
          ${tag(`suspeita ${d.esteganografia.esteganalise.suspeita}`, d.esteganografia.esteganalise.suspeita === 'alta' ? 'tag-warn' : 'tag-ok')}
        </div>
        <img alt="Imagem com o envelope oculto" src="data:image/png;base64,${d.esteganografia.imagem_b64}"
             style="max-width:320px;border:1px solid var(--line);border-radius:var(--r)">
        <a class="btn btn-sm" download="finalpay-estego.png" href="data:image/png;base64,${d.esteganografia.imagem_b64}">
          <svg><use href="#ic-download"/></svg>Baixar imagem</a>` : ''}
      </div></div>`;

  const hist = (sel, dados, cor) => bars($(sel), {
    data: dados.map((v, idx) => ({ label: String(idx), value: v })),
    dense: true, height: 150, color: cor, xTickEvery: 64, tipFormat: (v) => ni(v),
    yLabel: 'ocorrências',
  });
  hist('#hist-claro', d.histograma_claro, SERIES[1]);
  hist('#hist-cifrado', d.histograma_cifrado, SERIES[0]);
}

async function decifrar(usarImagem) {
  const saida = $('#dec-saida');
  carregando(saida, 'Decifrando');
  try {
    const corpo = { senha: $('#dec-senha').value };
    if (usarImagem) {
      const input = Object.assign(document.createElement('input'), { type: 'file', accept: 'image/png' });
      const arq = await new Promise((ok) => { input.onchange = () => ok(lerB64(input)); input.click(); });
      const port = await arq;
      if (!port) { saida.innerHTML = ''; return; }
      corpo.imagem_b64 = port.b64;
    } else {
      corpo.envelope_b64 = $('#dec-envelope').value.trim();
      if (!corpo.envelope_b64) throw new Error('cole um envelope base64');
    }
    const d = await api('/api/cofre/decifrar', {
      method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(corpo),
    });
    saida.innerHTML = `<div class="note" style="background:var(--ok-bg);border-color:var(--ok-line);color:var(--ok)">
        <svg><use href="#ic-info"/></svg><div><b>Integridade verificada.</b>
        ${ni(d.bytes)} bytes recuperados de ${esc(d.origem)} em ${nf(d.latencia_ms)} ms.</div></div>
      ${d.texto !== null ? `<pre class="code" style="margin-top:12px">${esc(d.texto.slice(0, 1200))}</pre>`
        : `<p class="small" style="margin-top:12px">Conteúdo binário — <a download="finalpay.bin" href="data:application/octet-stream;base64,${d.conteudo_b64}">baixar arquivo</a>.</p>`}`;
    atualizarLog();
  } catch (e) {
    saida.innerHTML = `<div class="note note-warn"><svg><use href="#ic-alert"/></svg>
      <div><b>Falha ao decifrar.</b> ${esc(e.message)}</div></div>`;
    atualizarLog();
  }
}
$('#btn-decifrar').addEventListener('click', () => decifrar(false));
$('#btn-decifrar-img').addEventListener('click', () => decifrar(true));

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

/* ------------------------------------------------------------------ inicio */
$('#btn-bateria').addEventListener('click', async (ev) => {
  const btn = ev.currentTarget;
  btn.disabled = true;
  $('#status-bateria').textContent = 'executando…';
  try {
    await api('/api/experimentos/executar?rapido=true', { method: 'POST' });
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
  } catch (e) {
    $('#status-bateria').textContent = 'sem resultados';
    falha($('#panorama-verdito'), e);
  }
}

await iniciar();
irPara(location.hash.slice(1));
atualizarLog();
window.addEventListener('hashchange', () => {
  const alvo = location.hash.slice(1);
  if (PAGINAS.has(alvo)) irPara(alvo);  // ancoras que nao sao pagina rolam normalmente
});
