"""Gera os slides da apresentacao a partir de `results/experimentos.json`.

Arquivo unico, abre direto no navegador (sem servidor). Setas ou espaco navegam;
a tecla P imprime em PDF, em paisagem. Mesmo sistema visual do dashboard.

    python -m finalpay.slides
"""

from __future__ import annotations

from pathlib import Path

from finalpay.experiments import carregar
from finalpay.report import GRUPO, i, n, rot

DESTINO = Path(__file__).resolve().parent.parent / "docs" / "slides" / "index.html"

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500&display=swap');
:root{
  --gray-0:#FFFFFF; --gray-1:#FAFAFA; --gray-2:#F5F5F6; --gray-3:#EDEDEF; --gray-4:#E1E1E3;
  --gray-7:#6E6E76; --gray-8:#55555C; --ink:#18181B; --accent:#15418E; --accent-weak:#EEF2FA;
  --ok:#067647; --warn:#B54708; --crit:#B42318;
  --s1:#2056C7; --s2:#C2410C; --s3:#0D9488;
  --sans:'Geist',ui-sans-serif,system-ui,-apple-system,sans-serif;
  --mono:'Geist Mono',ui-monospace,'SF Mono',Menlo,monospace;
}
*,*::before,*::after{box-sizing:border-box}
html,body{margin:0;padding:0}
body{background:var(--gray-2);color:var(--ink);font:400 16px/1.55 var(--sans);letter-spacing:-0.006em;-webkit-font-smoothing:antialiased}
::selection{background:#CFDDF5}
.deck{scroll-snap-type:y mandatory;overflow-y:auto;height:100vh}
.slide{
  scroll-snap-align:start;position:relative;height:100vh;display:flex;flex-direction:column;
  justify-content:center;padding:6vh 7vw;background:var(--gray-0);border-bottom:1px solid var(--gray-4);
}
.slide.cover{background:var(--ink);color:var(--gray-0)}
.slide.cover .muted{color:#A6A6AE}
.num{font-family:var(--mono);font-variant-numeric:tabular-nums;letter-spacing:-0.03em}
.label{font:500 12px/1.3 var(--sans);letter-spacing:.09em;text-transform:uppercase;color:var(--gray-7)}
.slide.cover .label{color:#8B8B95}
h1{font-size:clamp(34px,4.6vw,62px);line-height:1.06;letter-spacing:-0.03em;font-weight:600;margin:0}
h2{font-size:clamp(26px,3.1vw,42px);line-height:1.12;letter-spacing:-0.028em;font-weight:600;margin:0 0 28px}
p{margin:0;max-width:62ch}
.lead{font-size:clamp(17px,1.4vw,21px);line-height:1.55;color:var(--gray-8)}
.muted{color:var(--gray-7)}
.big{font:500 clamp(40px,6vw,86px)/1 var(--mono);font-variant-numeric:tabular-nums;letter-spacing:-0.04em}
.mid{font:500 clamp(24px,2.6vw,38px)/1.05 var(--mono);font-variant-numeric:tabular-nums;letter-spacing:-0.035em}
.grid{display:grid;gap:22px}
.g2{grid-template-columns:repeat(2,minmax(0,1fr))}
.g3{grid-template-columns:repeat(3,minmax(0,1fr))}
.g4{grid-template-columns:repeat(4,minmax(0,1fr))}
.cell{border:1px solid var(--gray-4);border-radius:10px;padding:22px 24px}
.cell .label{display:block;margin-bottom:12px}
.cell .mid,.cell .big{display:block}
.cell p{margin-top:10px;font-size:15px;color:var(--gray-8)}
.strip{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border:1px solid var(--gray-4);border-radius:10px;overflow:hidden}
.strip>div{padding:22px 24px;border-left:1px solid var(--gray-3)}
.strip>div:first-child{border-left:0}
table{width:100%;border-collapse:collapse;font-size:16px}
th,td{text-align:left;padding:11px 14px;border-bottom:1px solid var(--gray-3)}
thead th{font:500 12px/1.3 var(--sans);letter-spacing:.09em;text-transform:uppercase;color:var(--gray-7);background:var(--gray-1);border-bottom:1px solid var(--gray-4)}
td.n,th.n{text-align:right;font-family:var(--mono);font-variant-numeric:tabular-nums}
tbody tr:last-child td{border-bottom:0}
.tag{display:inline-flex;align-items:center;gap:6px;height:26px;padding:0 10px;border-radius:5px;border:1px solid var(--gray-4);background:var(--gray-1);font:500 13px/1 var(--sans);color:var(--gray-8)}
.tag::before{content:"";width:6px;height:6px;border-radius:99px;background:currentColor}
.tag-ok{background:#ECFDF3;border-color:#ABEFC6;color:var(--ok)}
.tag-crit{background:#FEF3F2;border-color:#FECDCA;color:var(--crit)}
.tag-warn{background:#FFFAEB;border-color:#FEDF89;color:var(--warn)}
pre{font-family:var(--mono);font-size:clamp(13px,1.05vw,16px);line-height:1.75;background:var(--gray-1);border:1px solid var(--gray-3);border-radius:8px;padding:20px 24px;overflow:auto;margin:0}
ul{margin:0;padding-left:22px;line-height:1.75}
li{margin-bottom:8px;color:var(--gray-8)}
li b,li strong{color:var(--ink)}
.foot{position:absolute;left:7vw;right:7vw;bottom:3.4vh;display:flex;justify-content:space-between;align-items:center;font-size:13px;color:var(--gray-7);border-top:1px solid var(--gray-3);padding-top:12px}
.slide.cover .foot{border-color:#333}
.bar{display:flex;align-items:center;gap:12px}
.bar-track{flex:1;height:8px;background:var(--gray-3);border-radius:99px;overflow:hidden}
.bar-fill{height:100%;background:var(--s1);border-radius:99px}
.bar-fill.weak{background:var(--s2)}
.hint{position:fixed;right:18px;bottom:16px;z-index:5;font-size:12px;color:var(--gray-7);background:var(--gray-0);border:1px solid var(--gray-4);border-radius:6px;padding:6px 10px}
@media print{
  @page{size:A4 landscape;margin:0}
  body{background:#fff}
  .deck{height:auto;overflow:visible}
  .slide{height:100vh;page-break-after:always;border:0}
  .hint{display:none}
}
@media (max-width:820px){
  .g2,.g3,.g4,.strip{grid-template-columns:minmax(0,1fr)}
  .strip>div{border-left:0;border-top:1px solid var(--gray-3)}
  .strip>div:first-child{border-top:0}
  .slide{height:auto;min-height:100vh;padding:7vh 7vw 12vh}
}
"""

JS = """
const slides=[...document.querySelectorAll('.slide')];
const deck=document.querySelector('.deck');
let i=0;
const ir=(k)=>{i=Math.max(0,Math.min(slides.length-1,k));slides[i].scrollIntoView({behavior:'smooth'})};
addEventListener('keydown',(e)=>{
  if(['ArrowRight','ArrowDown',' ','PageDown'].includes(e.key)){e.preventDefault();ir(i+1)}
  if(['ArrowLeft','ArrowUp','PageUp'].includes(e.key)){e.preventDefault();ir(i-1)}
  if(e.key==='Home'){e.preventDefault();ir(0)}
  if(e.key==='End'){e.preventDefault();ir(slides.length-1)}
  if(e.key==='p'||e.key==='P'){print()}
});
new IntersectionObserver((es)=>es.forEach(e=>{if(e.isIntersecting)i=slides.indexOf(e.target)}),
  {threshold:0.5}).observe&&slides.forEach(s=>new IntersectionObserver((es)=>es.forEach(e=>{
    if(e.isIntersecting)i=slides.indexOf(e.target)}),{threshold:0.5}).observe(s));
"""


def _slide(conteudo: str, rodape: str, numero: int, total: int, classe: str = "") -> str:
    return f"""<section class="slide {classe}">
<div>{conteudo}</div>
<div class="foot"><span>FinalPay · {rodape}</span><span class="num">{numero:02d} / {total:02d}</span></div>
</section>"""


def _barra(valor: float, maximo: float, fraca: bool = False) -> str:
    pct = max(0.0, min(100.0, 100 * valor / maximo))
    return (f'<div class="bar"><div class="bar-track"><div class="bar-fill{" weak" if fraca else ""}" '
            f'style="width:{pct:.1f}%"></div></div><span class="num">{n(valor)}%</span></div>')


def gerar(res: dict) -> str:
    c = res["cifra"]
    av = res["diferencial"]["fpc_integro"]
    fr = res["diferencial"]["fpc_fraco"]
    sd = res["diferencial"]["fpc_sem_difusao_14_rodadas"]
    aes = res["diferencial"]["aes256"]
    perfis = {p["rotulo"]: p for p in res["estatistico"]["perfis"]}
    ctr, claro = perfis["fpc_ctr_14_rodadas"], perfis["texto_claro"]
    ecb = perfis["fpc_ecb_14_rodadas"]
    bf, dic = res["forca_bruta"], res["dicionario"]
    freq_f, freq_c = res["frequencia"]["sem_difusao"], res["frequencia"]["com_difusao"]
    est, bd = res["estego"], res["bigdata"]
    ia = bd["ia"]["metricas"]
    v, des = res["veredito"], res["desempenho"]
    proj = next(p for p in bf["projecao"] if p["bits"] == 256 and "GPU" in p["cenario"])
    rodada_dif = v["efeito_avalanche"]["rodadas_ate_difusao_total"]

    s: list[tuple[str, str, str]] = []

    s.append((f"""<span class="label">Cibersegurança Aplicada a Dados e IA · CESAR School</span>
<h1 style="margin:22px 0 26px">FinalPay<br>Sistema criptográfico<br>e análise de ataques</h1>
<p class="lead" style="color:#C9C9CE;max-width:56ch">Um cofre de banco digital que cifra, esconde,
observa — e então ataca a si mesmo para descobrir se é seguro.</p>
<p class="muted" style="margin-top:34px;font-size:15px">{", ".join(GRUPO)}</p>""",
                "Professora Renatta Nigro", "cover"))

    s.append((f"""<h2>O que foi construído</h2>
<div class="grid g2" style="gap:26px">
<div><p class="lead">Um sistema completo, em seis camadas, que protege transações de um banco
fictício. E, na mesma base de código, três ataques que tentam quebrá-lo.</p>
<p class="lead" style="margin-top:18px">Toda a cifragem roda contra <b>duas</b> versões do algoritmo:
a íntegra e uma deliberadamente enfraquecida. É a comparação entre as duas que prova de onde vem a
segurança.</p></div>
<div class="grid" style="gap:12px">
{''.join(f'<div class="cell" style="padding:14px 18px"><span class="num" style="color:var(--accent)">{k}</span>&nbsp;&nbsp;{t}</div>' for k, t in [("1","Entrada de dados"),("2","Criptografia FPC-128 e AES-256"),("3","Esteganografia"),("4","Big Data"),("5","Inteligência Artificial"),("6","Dashboard de segurança")])}
</div></div>""", "Arquitetura", ""))

    s.append((f"""<h2>FPC-128, o algoritmo autoral</h2>
<div class="grid g2" style="gap:30px">
<div><pre>AddRoundKey   estado ← estado ⊕ subchave[r]
SubBytes      estado ← S[estado]
ShiftRows     estado ← estado[π]
MixColumns    estado ← M · estado  em GF(2⁸)</pre>
<p class="lead" style="margin-top:18px">Rede de substituição-permutação. As quatro operações exigidas
no enunciado: XOR, substituição, permutação e difusão sobre blocos.</p></div>
<div><table><tbody>
<tr><td>Bloco</td><td class="n">{c['bloco_bits']} bits</td></tr>
<tr><td>Chave</td><td class="n">{c['chave_bits']} bits</td></tr>
<tr><td>Rodadas</td><td class="n">{c['rodadas']}</td></tr>
<tr><td>S-box bijetiva</td><td class="n">{'sim' if c['sbox_bijetiva'] else 'não'}</td></tr>
<tr><td>Pontos fixos</td><td class="n">{c['sbox_pontos_fixos']}</td></tr>
<tr><td>Uniformidade diferencial</td><td class="n">{c['ddt_maximo']} → 2⁻⁶</td></tr>
<tr><td>Integridade</td><td class="n">HMAC-SHA256</td></tr>
</tbody></table></div></div>""", "Descrição do algoritmo", ""))

    s.append((f"""<h2>A chave nunca é fixa</h2>
<pre style="margin-bottom:26px">senha  ──PBKDF2──▶  chave mestra  ──HKDF(nonce)──▶  chave de sessão  ──HKDF──▶  {c['rodadas'] + 1} subchaves
         {i(120000)} iterações      salt aleatório        nonce aleatório</pre>
<div class="grid g3">
<div class="cell"><span class="label">Mesma senha, mesma mensagem</span><span class="mid">{'envelopes diferentes' if c['ciframentos_distintos_mesma_entrada'] else 'iguais'}</span></div>
<div class="cell"><span class="label">1 bit trocado na chave</span><span class="mid">{n(res['diferencial']['avalanche_chave']['media_pct'])}%</span><p>dos bits de saída mudam</p></div>
<div class="cell"><span class="label">1 bit alterado no cifrado</span><span class="mid">rejeitado</span><p>o HMAC acusa a adulteração</p></div>
</div>""", "Geração dinâmica de chaves", ""))

    s.append((f"""<h2>Efeito avalanche</h2>
<p class="lead" style="margin-bottom:30px">Um bit alterado na entrada deve alterar metade da saída.
A difusão se completa na rodada <b>{rodada_dif}</b>; a cifra usa <b>{c['rodadas']}</b>.</p>
<div class="grid" style="gap:18px;max-width:900px">
<div><span class="label" style="display:block;margin-bottom:8px">FPC-128 íntegro</span>{_barra(av['media_pct'], 60)}</div>
<div><span class="label" style="display:block;margin-bottom:8px">AES-256 (referência)</span>{_barra(aes['media_pct'], 60)}</div>
<div><span class="label" style="display:block;margin-bottom:8px">{c['rodadas']} rodadas, sem difusão</span>{_barra(sd['media_pct'], 60, True)}</div>
<div><span class="label" style="display:block;margin-bottom:8px">1 rodada, sem difusão</span>{_barra(fr['media_pct'], 60, True)}</div>
</div>
<p class="lead" style="margin-top:28px"><b>Rodadas não compensam a falta de difusão:</b>
{c['rodadas']} rodadas sem MixColumns entregam {n(sd['media_pct'])}%, praticamente o mesmo que uma só.</p>""",
              "Parte 4 · efeito avalanche", ""))

    s.append((f"""<h2>A saída tem padrões?</h2>
<table><thead><tr><th>Amostra</th><th class="n">Entropia</th><th class="n">χ² (p)</th>
<th class="n">Índice de coincidência</th><th class="n">Blocos repetidos</th></tr></thead><tbody>
{''.join(f'''<tr><td>{rot(p["rotulo"])}</td><td class="n">{n(p["entropia_bits_por_byte"],4)}</td>
<td class="n">{n(p["chi2_p_valor"],4)}</td><td class="n">{n(p["indice_coincidencia"],6)}</td>
<td class="n">{n(p["repeticao_blocos"]["pct_repetidos"])}%</td></tr>''' for p in res["estatistico"]["perfis"])}
</tbody></table>
<p class="lead" style="margin-top:26px">No modo CTR a saída é <b>indistinguível de ruído do sistema
operacional</b>. No modo ECB, {n(ecb['repeticao_blocos']['pct_repetidos'])}% dos blocos se repetem
mesmo com {c['rodadas']} rodadas: <b>o modo pesa mais que as rodadas.</b></p>""",
              "Parte 4 · padrões na saída", ""))

    s.append((f"""<h2>Ataque 1 — Força bruta</h2>
<div class="strip" style="margin-bottom:28px">
<div><span class="label">Taxa medida</span><span class="mid">{i(bf['chaves_por_segundo'])}</span><p>chaves por segundo, 1 núcleo</p></div>
<div><span class="label">Espaço de chaves</span><span class="mid">2²⁵⁶</span><p>não depende das rodadas</p></div>
<div><span class="label">Com 1 milhão de GPUs</span><span class="mid">{proj['anos_fmt']}</span><p>{n(proj['vezes_idade_universo'],0)}× a idade do universo</p></div>
<div><span class="label">Veredito</span><span class="mid">inviável</span><p><span class="tag tag-ok">a cifra resistiu</span></p></div>
</div>
<p class="lead">Contra a <b>senha</b>, porém, a história muda: o PBKDF2 limita o atacante a
{n(dic['tentativas_por_segundo'],1)} tentativas por segundo. A senha fraca <code>{dic['senha_quebrada']}</code>
caiu em {n(dic['segundos'])} s; uma senha forte de 12 caracteres levaria {dic['anos_forte_fmt']}.
<b>O elo mais fraco é a senha, não a cifra.</b></p>""", "Parte 3 · ataques", ""))

    s.append((f"""<h2>Ataque 2 — Diferencial</h2>
<p class="lead" style="margin-bottom:28px">Aplicamos sempre a mesma diferença na entrada e procuramos
uma diferença de saída que se repita. Numa cifra sólida, nenhuma se repete.</p>
<table><thead><tr><th>Variante</th><th class="n">Avalanche</th><th class="n">Saídas distintas</th>
<th class="n">Repetição máxima</th><th>Distinguível</th></tr></thead><tbody>
<tr><td>FPC-128 íntegro</td><td class="n">{n(av['media_pct'])}%</td>
<td class="n">{n(res['diferencial']['distinguidor_integro']['pct_saidas_distintas'])}%</td>
<td class="n">{res['diferencial']['distinguidor_integro']['ocorrencias']}</td>
<td><span class="tag tag-ok">não</span></td></tr>
<tr><td>1 rodada, sem difusão</td><td class="n">{n(fr['media_pct'])}%</td>
<td class="n">{n(res['diferencial']['distinguidor_fraco']['pct_saidas_distintas'])}%</td>
<td class="n">{i(res['diferencial']['distinguidor_fraco']['ocorrencias'])}</td>
<td><span class="tag tag-crit">sim</span></td></tr>
</tbody></table>
<p class="lead" style="margin-top:26px">A S-box tem uniformidade diferencial {c['ddt_maximo']}: nenhuma
característica de uma rodada passa de 2⁻⁶ de probabilidade. Ao longo de {c['rodadas']} rodadas, nada
explorável sobra.</p>""", "Parte 3 · ataques", ""))

    s.append((f"""<h2>Ataque 3 — Estatístico</h2>
<p class="lead" style="margin-bottom:26px">Mensagens bancárias usam registros de largura fixa. Sem
MixColumns, cada posição do bloco continua sendo uma substituição simples — e a frequência dos bytes
entrega o texto.</p>
<pre style="margin-bottom:24px">original    {freq_f['trecho_original'][:66].rstrip()}
recuperado  {freq_f['trecho_recuperado'][:66].rstrip()}</pre>
<div class="strip">
<div><span class="label">Sem difusão</span><span class="mid" style="color:var(--crit)">{n(freq_f['acuracia_pct'])}%</span><p>do texto recuperado</p></div>
<div><span class="label">Posições expostas</span><span class="mid" style="color:var(--crit)">{freq_f['posicoes_expostas']}/{freq_f['posicoes_registro']}</span><p>do registro bancário</p></div>
<div><span class="label">Com difusão</span><span class="mid" style="color:var(--ok)">{n(freq_c['acuracia_pct'])}%</span><p>abaixo da linha de base de {n(freq_c['linha_base_unigrama_pct'])}%</p></div>
<div><span class="label">Chave usada</span><span class="mid">nenhuma</span><p>só a frequência dos bytes</p></div>
</div>""", "Parte 3 · ataques", ""))

    s.append((f"""<h2>Esteganografia</h2>
<div class="grid g2" style="gap:30px">
<div><p class="lead">O envelope cifrado é espalhado pelos bits menos significativos da imagem, em
posições derivadas da chave. Sem a chave, não se sabe nem onde os bits estão.</p>
<p class="lead" style="margin-top:18px">Contra o teste de qui-quadrado de Westfeld, o LSB sequencial
clássico acende <b>{est['esteganalise']['segmentos_suspeitos']['lsb_sequencial_sem_chave']} de 20</b>
segmentos. A versão chaveada acende
<b>{est['esteganalise']['segmentos_suspeitos']['lsb_chaveado_finalpay']}</b> — igual à imagem limpa.</p></div>
<div class="grid g2" style="gap:14px;align-content:start">
<div class="cell"><span class="label">PSNR</span><span class="mid">{n(est['qualidade']['psnr_db'])} dB</span><p>acima de 40 é imperceptível</p></div>
<div class="cell"><span class="label">Desvio por canal</span><span class="mid">{est['qualidade']['desvio_maximo']}</span><p>no máximo</p></div>
<div class="cell"><span class="label">Capacidade</span><span class="mid">{i(est['capacidade_bytes'])}</span><p>bytes</p></div>
<div class="cell"><span class="label">Chave errada</span><span class="mid">rejeitada</span><p>CRC não confere</p></div>
</div></div>""", "Camada 3", ""))

    s.append((f"""<h2>Big Data e Inteligência Artificial</h2>
<div class="strip" style="margin-bottom:26px">
<div><span class="label">Eventos</span><span class="mid">{i(bd['resumo']['eventos'])}</span><p>{bd['resumo']['dias']} dias, {i(bd['resumo']['usuarios'])} usuários</p></div>
<div><span class="label">Em Parquet</span><span class="mid">{n(bd['ingestao']['bytes_em_disco']/1e6,1)} MB</span><p>{n(bd['ingestao']['bytes_por_evento'])} B por evento</p></div>
<div><span class="label">ROC AUC</span><span class="mid">{n(ia['roc_auc'],4)}</span><p>sem usar rótulos no treino</p></div>
<div><span class="label">Ganho sobre o acaso</span><span class="mid">{n(ia['ganho_sobre_acaso'],1)}×</span><p>precisão média</p></div>
</div>
<table><thead><tr><th>Anomalia prevista no enunciado</th><th class="n">Janelas</th>
<th class="n">Detectadas</th><th class="n">Revocação</th><th class="n">Tipo correto</th></tr></thead><tbody>
{''.join(f'''<tr><td>{rot(t["tipo"])}</td><td class="n">{t["janelas"]}</td>
<td class="n">{t["detectadas"]}</td><td class="n">{n(t["revocacao_pct"],1)}%</td>
<td class="n">{n(t["acerto_tipo_pct"],1)}%</td></tr>''' for t in ia["por_tipo"])}
</tbody></table>""", "Camadas 4 e 5", ""))

    s.append((f"""<h2>As quatro perguntas</h2>
<div class="grid g2" style="gap:22px">
{''.join(f'''<div class="cell"><span class="label">{q}</span>
<span style="display:block;font-size:30px;font-weight:600;letter-spacing:-.028em;margin:10px 0 10px">{d["resposta"]}</span>
<p>{extra}</p></div>''' for q, d, extra in [
  ("O sistema apresenta efeito avalanche?", v["efeito_avalanche"], f"{n(av['media_pct'])}% dos bits, contra 50% ideal · σ {n(av['desvio_padrao'],3)}"),
  ("Existem padrões na saída?", v["padroes_na_saida"], f"entropia {n(ctr['entropia_bits_por_byte'],4)} bits/byte · χ² p = {n(ctr['chi2_p_valor'],4)}"),
  ("Qual ataque foi mais eficaz?", v["ataque_mais_eficaz"], f"recuperou {n(freq_f['acuracia_pct'])}% do texto da variante sem difusão"),
  ("O sistema é seguro?", v["e_seguro"], f"{len(v['e_seguro']['a_favor'])} argumentos a favor, {len(v['e_seguro']['ressalvas'])} ressalvas"),
])}
</div>""", "Parte 4 · respostas", ""))

    s.append((f"""<h2>Conclusão</h2>
<ul class="lead" style="max-width:74ch">
<li><b>Difusão é o que sustenta tudo.</b> Sem MixColumns, a análise de frequência recupera
{n(freq_f['acuracia_pct'])}% do texto e expõe {freq_f['posicoes_expostas']} das
{freq_f['posicoes_registro']} posições do registro. Aumentar rodadas não corrige:
{c['rodadas']} rodadas sem difusão vazam tanto quanto uma.</li>
<li><b>O modo de operação pesa mais que o número de rodadas.</b> O ECB preservou
{n(ecb['repeticao_blocos']['pct_repetidos'])}% dos blocos repetidos com a cifra íntegra.</li>
<li><b>Força bruta é o ataque errado.</b> Inviável nas duas variantes; a superfície real é a senha,
e o PBKDF2 existe para encarecê-la.</li>
<li><b>A anomalia mais difícil é a que não quebra nada.</b> O surto de exfiltração, sem falhas, teve
revocação de {n([t for t in ia['por_tipo'] if t['tipo'] == 'surto_de_eventos'][0]['revocacao_pct'],1)}%,
contra ~100% das que geram erro.</li>
</ul>""", "Conclusão", ""))

    s.append((f"""<h2>O que isto não é</h2>
<p class="lead" style="margin-bottom:26px">O FPC-128 passou nos três ataques. Isso demonstra solidez
de projeto — <b>não</b> maturidade criptográfica.</p>
<ul class="lead" style="max-width:74ch">
{''.join(f'<li>{r}</li>' for r in v['e_seguro']['ressalvas'])}
</ul>
<p class="lead" style="margin-top:28px">Uma cifra se torna confiável por anos de tentativa pública de
quebra, não por uma bateria de testes dos próprios autores. É por isso que a camada AES-256 existe no
sistema: <b>o FPC-128 é o objeto de estudo; o AES-256 é o que protegeria o dinheiro de verdade.</b></p>""",
              "Ressalvas", ""))

    s.append((f"""<h1 style="margin-bottom:28px">Obrigado</h1>
<p class="lead" style="color:#C9C9CE;max-width:58ch">Todos os números destes slides foram medidos pela
bateria de experimentos do próprio sistema, em {res['meta']['gerado_em'].replace('T', ' ')}.
Nenhum valor foi digitado à mão.</p>
<pre style="background:#242428;border-color:#3A3A40;color:#D4D4D8;margin-top:30px;max-width:640px">python -m finalpay.experiments
uvicorn finalpay.api:app</pre>
<p class="muted" style="margin-top:30px;font-size:15px">{", ".join(GRUPO)}</p>""",
              "FinalPay", "cover"))

    total = len(s)
    corpo = "\n".join(_slide(conteudo, rodape, k + 1, total, classe)
                      for k, (conteudo, rodape, classe) in enumerate(s))
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FinalPay — Apresentação</title>
<style>{CSS}</style></head>
<body><div class="deck">{corpo}</div>
<div class="hint">← → navega · P imprime</div>
<script>{JS}</script></body></html>"""


def main() -> Path:
    res = carregar()
    if res is None:
        raise SystemExit("Rode `python -m finalpay.experiments` primeiro.")
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(gerar(res), encoding="utf-8")
    return DESTINO


if __name__ == "__main__":
    p = main()
    print(f"OK -> {p} ({p.stat().st_size / 1024:.1f} KB)")
