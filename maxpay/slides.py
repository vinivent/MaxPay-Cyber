"""Gera os slides da apresentacao a partir de `results/experimentos.json`.

Arquivo unico, abre direto no navegador, sem servidor. Setas ou espaco navegam,
`N` mostra as notas do apresentador e `P` imprime em paisagem.

Projeto grafico: Swiss design sobre fundo escuro. Campo em doze colunas, tudo
rente a esquerda, hierarquia por tamanho e peso, filete no lugar de moldura,
uma unica cor de acento. Nada centralizado, nada decorativo.

    python -m maxpay.slides
"""

from __future__ import annotations

from pathlib import Path

from maxpay.experiments import carregar
from maxpay.report import GRUPO, i, n, rot, sci

DESTINO = Path(__file__).resolve().parent.parent / "docs" / "slides" / "index.html"
CSS = (Path(__file__).resolve().parent / "slides.css").read_text(encoding="utf-8")

# Preenchido por `notas.py`. Chave = id do slide.
try:
    from maxpay.notas import NOTAS
except ImportError:  # notas ainda nao escritas
    NOTAS = {}

JS = """
const slides=[...document.querySelectorAll('.slide')];
const deck=document.querySelector('.deck');
const barra=document.getElementById('progresso');
let i=0;
const marcar=()=>{
  slides.forEach((s,k)=>k===i?s.setAttribute('data-ativo',''):s.removeAttribute('data-ativo'));
  barra.style.width=((i+1)/slides.length*100).toFixed(2)+'%';
};
const ir=(k)=>{i=Math.max(0,Math.min(slides.length-1,k));slides[i].scrollIntoView({behavior:'smooth'});marcar()};
addEventListener('keydown',(e)=>{
  if(['ArrowRight','ArrowDown',' ','PageDown'].includes(e.key)){e.preventDefault();ir(i+1)}
  if(['ArrowLeft','ArrowUp','PageUp'].includes(e.key)){e.preventDefault();ir(i-1)}
  if(e.key==='Home'){e.preventDefault();ir(0)}
  if(e.key==='End'){e.preventDefault();ir(slides.length-1)}
  if(e.key==='n'||e.key==='N'){document.body.classList.toggle('com-notas')}
  if(e.key==='p'||e.key==='P'){print()}
});
deck.addEventListener('scroll',()=>{
  const meio=deck.scrollTop+innerHeight/2;
  const k=slides.findIndex(s=>s.offsetTop<=meio&&s.offsetTop+s.offsetHeight>meio);
  if(k>=0&&k!==i){i=k;marcar()}
},{passive:true});
marcar();
"""


def _slide(sid: str, secao: str, corpo: str, classe: str = "") -> dict:
    return {"id": sid, "secao": secao, "corpo": corpo, "classe": classe}


def _render(s: dict, numero: int, total: int) -> str:
    nota = NOTAS.get(s["id"], "")
    bloco_nota = ""
    if nota:
        paragrafos = "".join(f"<p>{t.strip()}</p>" for t in nota.split("\n\n") if t.strip())
        bloco_nota = f'<aside class="notas"><span class="rotulo">Para falar</span>{paragrafos}</aside>'
    return f"""<section class="slide {s['classe']}" data-id="{s['id']}">
<header class="cab"><span class="secao">{s['secao']}</span><span class="folio">{numero:02d} / {total:02d}</span></header>
<div class="corpo">{s['corpo']}</div>
{bloco_nota}
</section>"""


def _barra(rotulo: str, valor: float, maximo: float = 60, fraca: bool = False) -> str:
    pct = max(0.0, min(100.0, 100 * valor / maximo))
    return (f'<div class="barra"><span class="rotulo">{rotulo}</span>'
            f'<span class="trilho"><span class="preenche{" fraca" if fraca else ""}" '
            f'style="width:{pct:.1f}%"></span></span>'
            f'<span class="valor">{n(valor)}%</span></div>')


def _celula(rotulo: str, valor: str, nota: str = "", cor: str = "") -> str:
    return (f'<div><span class="rotulo">{rotulo}</span>'
            f'<span class="grande {cor}">{valor}</span>'
            f'{f"<p>{nota}</p>" if nota else ""}</div>')


def gerar(res: dict) -> str:
    c = res["cifra"]
    pj = c["projeto"]
    av = res["diferencial"]["mpc_integro"]
    fr = res["diferencial"]["mpc_fraco"]
    sd = res["diferencial"]["mpc_sem_difusao_14_rodadas"]
    aes = res["diferencial"]["aes256"]
    perfis = {p["rotulo"]: p for p in res["estatistico"]["perfis"]}
    ctr, ecb = perfis["mpc_ctr_14_rodadas"], perfis["mpc_ecb_14_rodadas"]
    bf, dic = res["forca_bruta"], res["dicionario"]
    freq_f, freq_c = res["frequencia"]["sem_difusao"], res["frequencia"]["com_difusao"]
    est, bd = res["estego"], res["bigdata"]
    ia = bd["ia"]["metricas"]
    v, des = res["veredito"], res["desempenho"]
    proj = next(p for p in bf["projecao"] if p["bits"] == 256 and "GPU" in p["cenario"])
    rodada_dif = v["efeito_avalanche"]["rodadas_ate_difusao_total"]
    surto = next(t for t in ia["por_tipo"] if t["tipo"] == "surto_de_eventos")

    s = []

    s.append(_slide("capa", "CESAR School · Cibersegurança Aplicada a Dados e IA", f"""
<div class="sp8">
  <h1>MaxPay</h1>
  <p class="lead" style="margin-top:26px;font-size:clamp(17px,1.5vw,24px);color:var(--texto)">
    Um cofre de banco digital que cifra, esconde e observa. E então ataca a si mesmo
    para descobrir se é seguro.</p>
</div>
<div class="sp4" style="align-self:end">
  <span class="rotulo">Grupo</span>
  <p class="lead" style="font-size:15px;line-height:1.9">{"<br>".join(GRUPO)}</p>
  <p class="lead" style="margin-top:22px;font-size:14px;color:var(--texto-3)">
    Professora Renatta Nigro</p>
</div>""", "capa"))

    s.append(_slide("ato1", "Enunciado · partes 1 e 2", """
<div class="sp9"><span class="ato-num">01</span><h1>O sistema</h1>
<p class="lead" style="margin-top:28px">Seis camadas que protegem uma transação, da entrada
do dado até o painel de quem vigia.</p></div>""", "ato"))

    camadas = [
        ("1", "Entrada de dados", "texto, arquivos e imagens", "aba Cofre"),
        ("2", "Criptografia", "MPC-128 próprio e AES-256", "aba Cofre"),
        ("3", "Esteganografia", "ocultação em imagem", "aba Ocultar"),
        ("4", "Big Data", "Parquet particionado e DuckDB", "aba Antifraude"),
        ("5", "Inteligência Artificial", "Isolation Forest sobre janelas", "aba Antifraude"),
        ("6", "Dashboard", "alertas, gráficos e laudo", "as quatro abas"),
    ]
    s.append(_slide("construido", "Arquitetura", f"""
<div class="sp5">
  <h2>O que foi construído</h2>
  <p class="lead">Um sistema em seis camadas que protege transações de um banco fictício.
  E, na mesma base de código, três ataques que tentam quebrá-lo.</p>
  <p class="lead">Toda a cifragem roda contra <b>duas</b> versões do algoritmo: a íntegra e uma
  deliberadamente enfraquecida. É a comparação entre as duas que prova de onde vem a segurança.</p>
</div>
<div class="sp7">
  <table><thead><tr><th>Camada</th><th>O que faz</th><th>Onde se vê</th></tr></thead><tbody>
  {"".join(f'<tr><td><span class="num muted">{k}</span>&nbsp;&nbsp;<b>{t}</b></td><td>{d}</td><td class="muted">{o}</td></tr>' for k, t, d, o in camadas)}
  </tbody></table>
</div>""")) 

    s.append(_slide("algoritmo", "Descrição do algoritmo · aba Cofre", f"""
<div class="sp7">
  <h2>MPC-128, a cifra que projetamos</h2>
  <pre>AddRoundKey   estado ← estado ⊕ subchave[r]
SubBytes      estado ← S[estado]
ShiftRows     estado ← estado[π]
MixColumns    estado ← M · estado  em GF(2⁸)</pre>
  <p class="lead" style="margin-top:22px">Rede de substituição-permutação. As quatro operações
  exigidas no enunciado: XOR, substituição, permutação e difusão sobre blocos.</p>
</div>
<div class="sp5">
  <table><tbody>
  <tr><td>Bloco</td><td class="n">{c['bloco_bits']} bits</td></tr>
  <tr><td>Chave</td><td class="n">{c['chave_bits']} bits</td></tr>
  <tr><td>Rodadas</td><td class="n">{c['rodadas']}</td></tr>
  <tr><td>S-box bijetiva</td><td class="n">sim</td></tr>
  <tr><td>Pontos fixos</td><td class="n">{c['sbox_pontos_fixos']}</td></tr>
  <tr><td>Uniformidade diferencial</td><td class="n">{c['ddt_maximo']} → 2⁻⁶</td></tr>
  <tr><td>Integridade</td><td class="n">HMAC-SHA256</td></tr>
  </tbody></table>
</div>"""))

    s.append(_slide("projeto", "Projeto da cifra", f"""
<div class="sp8">
  <h2>O que é nosso, e o que vem do AES</h2>
  <p class="lead">A estrutura é a mesma família do AES, e isso é de propósito: é a rede SPN com
  S-box de inverso multiplicativo que garante as boas propriedades. Os três componentes
  concretos são escolha nossa.</p>
</div>
<div class="sp12 linha-acima">
  <table><thead><tr><th>Componente</th><th>MPC-128</th><th>AES</th><th>Como foi verificado</th></tr></thead><tbody>
  <tr><td>Afim da S-box</td><td class="num">{tuple(pj['sbox_rotacoes'])} ⊕ {pj['sbox_constante']}</td>
      <td class="num muted">{tuple(pj['sbox_rotacoes_aes'])} ⊕ {pj['sbox_constante_aes']}</td>
      <td>bijetiva, zero ponto fixo, uniformidade {c['ddt_maximo']}</td></tr>
  <tr><td>Permutação</td><td class="num">{tuple(pj['deslocamentos'])}</td>
      <td class="num muted">{tuple(pj['deslocamentos_aes'])}</td>
      <td>cada coluna puxa das quatro colunas</td></tr>
  <tr><td>Difusão</td><td class="num">{tuple(pj['matriz_difusao'])}</td>
      <td class="num muted">{tuple(pj['matriz_difusao_aes'])}</td>
      <td>MDS por todos os menores</td></tr>
  <tr><td>Escalonamento de chaves</td><td class="num">HKDF/HMAC-SHA256</td>
      <td class="num muted">Rijndael</td><td>subchaves novas a cada mensagem</td></tr>
  </tbody></table>
  <p class="lead" style="margin-top:26px">A S-box resultante difere da do AES nas
  <b class="destaque">256 posições</b>. Cada parâmetro saiu de uma busca que só aceitou o que
  passou na verificação matemática.</p>
</div>"""))

    s.append(_slide("chave", "Geração dinâmica de chaves · aba Cofre", f"""
<div class="sp12"><h2>A chave nunca é fixa</h2></div>
<div class="sp12">
<pre>senha  ──PBKDF2──▶  chave mestra  ──HKDF(nonce)──▶  chave de sessão  ──HKDF──▶  <b>{c['rodadas'] + 1} subchaves</b>
       {i(120000)} iterações       salt aleatório           nonce aleatório</pre>
</div>
<div class="faixa" style="margin-top:34px">
  {_celula("Mesma senha, mesma mensagem", "envelopes<br>diferentes", "salt e nonce novos a cada operação")}
  {_celula("1 bit trocado na chave", f"{n(res['diferencial']['avalanche_chave']['media_pct'])}%", "dos bits de saída mudam")}
  {_celula("1 bit alterado no cifrado", "recusado", "o HMAC acusa a adulteração")}
  {_celula("Chave guardada em disco", "nenhuma", "tudo deriva da senha")}
</div>"""))

    s.append(_slide("estego", "Camada 3 · aba Ocultar", f"""
<div class="sp6">
  <h2>Esteganografia</h2>
  <p class="lead">O envelope cifrado é espalhado pelos bits menos significativos da imagem, em
  posições derivadas da chave. Sem ela, não se sabe nem onde os bits estão.</p>
  <p class="lead">Contra o teste de qui-quadrado de Westfeld, o LSB sequencial clássico acende
  <b>{est['esteganalise']['segmentos_suspeitos']['lsb_sequencial_sem_chave']} de 20</b> segmentos.
  A versão chaveada acende <b class="destaque">{est['esteganalise']['segmentos_suspeitos']['lsb_chaveado_maxpay']}</b>,
  igual à imagem limpa.</p>
</div>
<div class="sp6">
  <div class="ficha"><span class="rotulo">PSNR</span><span class="grande destaque">{n(est['qualidade']['psnr_db'])} dB</span><p>acima de 40 dB é imperceptível</p></div>
  <div class="ficha"><span class="rotulo">Desvio máximo por canal</span><span class="medio">{est['qualidade']['desvio_maximo']}</span><p>de 0 a 255</p></div>
  <div class="ficha"><span class="rotulo">Capacidade da portadora</span><span class="medio">{i(est['capacidade_bytes'])} bytes</span><p>extração com chave errada: rejeitada</p></div>
</div>"""))

    s.append(_slide("antifraude", "Camadas 4 e 5 · aba Antifraude", f"""
<div class="sp12"><h2>Big Data e detecção de anomalias</h2></div>
<div class="faixa">
  {_celula("Eventos monitorados", i(bd['resumo']['eventos']), f"{bd['resumo']['dias']} dias, {i(bd['resumo']['usuarios'])} contas")}
  {_celula("Em Parquet", f"{n(bd['ingestao']['bytes_em_disco']/1e6,1)} MB", f"{n(bd['ingestao']['bytes_por_evento'])} B por evento")}
  {_celula("ROC AUC", n(ia['roc_auc'], 4), "modelo treinado sem rótulos", "destaque")}
  {_celula("Ganho sobre o acaso", f"{n(ia['ganho_sobre_acaso'], 1)}×", "precisão média")}
</div>
<div class="sp12" style="margin-top:34px">
  <table><thead><tr><th>Anomalia prevista no enunciado</th><th class="n">Janelas</th>
  <th class="n">Revocação</th><th class="n">Posto de risco</th><th class="n">Tipo correto</th></tr></thead><tbody>
  {"".join(f'<tr><td>{rot(t["tipo"])}</td><td class="n">{t["janelas"]}</td><td class="n">{n(t["revocacao_pct"],1)}%</td><td class="n">{n(t["percentil_mediano"],2)}%</td><td class="n">{n(t["acerto_tipo_pct"],1)}%</td></tr>' for t in sorted(ia["por_tipo"], key=lambda t: t["posto_mediano"]))}
  </tbody></table>
  <p class="lead" style="margin-top:20px;font-size:14px">O posto de risco é o percentil mediano
  no ranking de {i(ia['janelas'])} janelas, e não depende do orçamento de alertas.</p>
</div>"""))

    s.append(_slide("ato2", "Enunciado · parte 3 · aba Resistência", """
<div class="sp9"><span class="ato-num">02</span><h1>Os ataques</h1>
<p class="lead" style="margin-top:28px">Três ataques contra duas versões da mesma cifra: a íntegra
e uma enfraquecida de propósito. Todos rodam ao vivo na aba Resistência, com os parâmetros
que a plateia escolher.</p></div>""", "ato"))

    s.append(_slide("avalanche", "Enunciado · parte 4 · efeito avalanche", f"""
<div class="sp5">
  <h2>Efeito avalanche</h2>
  <p class="lead">Um bit alterado na entrada deve alterar metade da saída. A difusão se completa
  na rodada <b>{rodada_dif}</b> e a cifra usa <b>{c['rodadas']}</b>.</p>
  <p class="lead linha-acima"><b>Rodadas não compensam a falta de difusão.</b>
  {c['rodadas']} rodadas sem MixColumns entregam {n(sd['media_pct'])}%, praticamente o mesmo
  que uma única rodada.</p>
</div>
<div class="sp7">
  {_barra(f"MPC-128 íntegro", av['media_pct'])}
  {_barra("AES-256 (referência)", aes['media_pct'])}
  {_barra(f"{c['rodadas']} rodadas, sem difusão", sd['media_pct'], fraca=True)}
  {_barra("1 rodada, sem difusão", fr['media_pct'], fraca=True)}
  <p class="lead" style="margin-top:26px;font-size:14px">Desvio padrão medido
  {n(av['desvio_padrao'], 3)}, contra {n(v['efeito_avalanche']['desvio_padrao_teorico'], 3)}
  esperado de uma binomial(128; 0,5).</p>
</div>"""))

    s.append(_slide("padroes", "Enunciado · parte 4 · padrões na saída", f"""
<div class="sp12"><h2>A saída tem padrões?</h2></div>
<div class="sp12">
  <table><thead><tr><th>Amostra</th><th class="n">Entropia</th><th class="n">χ² (p)</th>
  <th class="n">Índice de coincidência</th><th class="n">Blocos repetidos</th></tr></thead><tbody>
  {"".join(f'<tr><td>{rot(p["rotulo"])}</td><td class="n">{n(p["entropia_bits_por_byte"],4)}</td><td class="n">{n(p["chi2_p_valor"],4)}</td><td class="n">{n(p["indice_coincidencia"],6)}</td><td class="n">{n(p["repeticao_blocos"]["pct_repetidos"])}%</td></tr>' for p in res["estatistico"]["perfis"])}
  </tbody></table>
  <p class="lead linha-acima">No modo CTR a saída é <b>indistinguível de ruído do sistema
  operacional</b>. No modo ECB, {n(ecb['repeticao_blocos']['pct_repetidos'])}% dos blocos se repetem
  mesmo com {c['rodadas']} rodadas: <b class="destaque">o modo pesa mais que as rodadas</b>.</p>
</div>"""))

    s.append(_slide("bruta", "Ataque 1 · aba Resistência", f"""
<div class="sp12"><h2>Força bruta</h2></div>
<div class="faixa">
  {_celula("Taxa medida", i(bf['chaves_por_segundo']), "chaves por segundo, 1 núcleo")}
  {_celula("Espaço de chaves", "2²⁵⁶", "não depende das rodadas")}
  {_celula("Com 1 milhão de GPUs", proj['anos_fmt'], f"{sci(proj['vezes_idade_universo'])} vezes a idade do universo", "destaque")}
  {_celula("Veredito", "inviável", "<span class='marca marca-ok'>a cifra resistiu</span>")}
</div>
<div class="sp12 linha-acima">
  <p class="lead">Contra a <b>senha</b>, porém, a história muda: o PBKDF2 limita o atacante a
  {n(dic['tentativas_por_segundo'],1)} tentativas por segundo. A senha fraca
  <span class="num">{dic['senha_quebrada']}</span> caiu em {n(dic['segundos'])} s; uma senha forte
  de 12 caracteres levaria {dic['anos_forte_fmt']}.
  <b class="destaque">O elo mais fraco é a senha, não a cifra.</b></p>
</div>"""))

    di, df = res["diferencial"]["distinguidor_integro"], res["diferencial"]["distinguidor_fraco"]
    s.append(_slide("diferencial", "Ataque 2 · aba Resistência", f"""
<div class="sp12"><h2>Diferencial</h2></div>
<div class="sp12">
  <p class="lead">Aplicamos sempre a mesma diferença na entrada e procuramos uma diferença de
  saída que se repita. Numa cifra sólida, nenhuma se repete.</p>
  <table style="margin-top:28px"><thead><tr><th>Variante</th><th class="n">Avalanche</th>
  <th class="n">Saídas distintas</th><th class="n">Repetição máxima</th><th>Distinguível</th></tr></thead><tbody>
  <tr><td>MPC-128 íntegro</td><td class="n">{n(av['media_pct'])}%</td>
      <td class="n">{n(di['pct_saidas_distintas'])}%</td><td class="n">{di['ocorrencias']}</td>
      <td><span class="marca marca-ok">não</span></td></tr>
  <tr><td>1 rodada, sem difusão</td><td class="n">{n(fr['media_pct'])}%</td>
      <td class="n">{n(df['pct_saidas_distintas'])}%</td><td class="n">{i(df['ocorrencias'])}</td>
      <td><span class="marca marca-crit">sim</span></td></tr>
  </tbody></table>
  <p class="lead linha-acima">A S-box tem uniformidade diferencial {c['ddt_maximo']}: nenhuma
  característica de uma rodada passa de 2⁻⁶ de probabilidade. Ao longo de {c['rodadas']} rodadas,
  nada explorável sobra.</p>
</div>"""))

    s.append(_slide("estatistico", "Ataque 3 · aba Resistência", f"""
<div class="sp12"><h2>Análise de frequência</h2></div>
<div class="sp12">
  <p class="lead">Mensagens bancárias usam registros de largura fixa. Sem MixColumns, cada posição
  do bloco continua sendo uma substituição simples, e a frequência dos bytes entrega o texto.</p>
</div>
<div class="sp12" style="margin-top:26px">
<pre>original    {freq_f['trecho_original'][:62].rstrip()}
recuperado  <b>{freq_f['trecho_recuperado'][:62].rstrip()}</b></pre>
</div>
<div class="faixa" style="margin-top:30px">
  {_celula("Sem difusão", f"{n(freq_f['acuracia_pct'])}%", "do texto recuperado", "vermelho")}
  {_celula("Posições expostas", f"{freq_f['posicoes_expostas']}/{freq_f['posicoes_registro']}", "do registro bancário", "vermelho")}
  {_celula("Com difusão", f"{n(freq_c['acuracia_pct'])}%", f"abaixo da linha de base de {n(freq_c['linha_base_unigrama_pct'])}%", "verde")}
  {_celula("Chave usada", "nenhuma", "só a frequência dos bytes")}
</div>"""))

    s.append(_slide("ato3", "Enunciado · parte 4", """
<div class="sp9"><span class="ato-num">03</span><h1>O veredito</h1>
<p class="lead" style="margin-top:28px">O que os números respondem, e o que eles não
autorizam a afirmar.</p></div>""", "ato"))

    perguntas = [
        ("O sistema apresenta efeito avalanche?", v["efeito_avalanche"],
         f"{n(av['media_pct'])}% dos bits, contra 50% ideal"),
        ("Existem padrões na saída?", v["padroes_na_saida"],
         f"entropia {n(ctr['entropia_bits_por_byte'],4)} bits por byte"),
        ("Qual ataque foi mais eficaz?", v["ataque_mais_eficaz"],
         f"recuperou {n(freq_f['acuracia_pct'])}% do texto da variante sem difusão"),
        ("O sistema é seguro?", v["e_seguro"],
         f"força bruta inviável por {proj['anos_fmt']}"),
    ]
    s.append(_slide("perguntas", "Enunciado · parte 4 · as respostas", f"""
<div class="sp12"><h2>As quatro perguntas</h2></div>
{"".join(f'''<div class="sp6 ficha"><span class="rotulo">{q}</span>
<span style="display:block;font-size:clamp(22px,2.3vw,34px);font-weight:600;letter-spacing:-.03em;margin:4px 0 12px">{d["resposta"]}</span>
<p>{extra}</p></div>''' for q, d, extra in perguntas)}"""))

    s.append(_slide("conclusao", "Conclusão", f"""
<div class="sp12"><h2>O que os números ensinam</h2></div>
<div class="sp6"><ul>
<li><b>Difusão é o que sustenta tudo.</b> Sem MixColumns, a análise de frequência recupera
{n(freq_f['acuracia_pct'])}% do texto e expõe {freq_f['posicoes_expostas']} das
{freq_f['posicoes_registro']} posições do registro. Aumentar rodadas não corrige.</li>
<li><b>O modo de operação pesa mais que o número de rodadas.</b> O ECB preservou
{n(ecb['repeticao_blocos']['pct_repetidos'])}% dos blocos repetidos com a cifra íntegra.</li>
</ul></div>
<div class="sp6"><ul>
<li><b>Força bruta é o ataque errado.</b> Inviável nas duas variantes. A superfície real é a
senha, e o PBKDF2 existe para encarecê-la.</li>
<li><b>A anomalia mais difícil é a que não quebra nada.</b> O surto de exfiltração só gera
volume: o modelo o põe no {n(surto['percentil_mediano'],2)}% mais arriscado, mas ele não cabe
no orçamento de 1% de alertas. Não é cegueira do modelo, é limite de orçamento.</li>
</ul></div>"""))

    s.append(_slide("limites", "Limites", f"""
<div class="sp5">
  <h2>O que não podemos afirmar</h2>
  <p class="lead">O MPC-128 passou nos três ataques. Isso demonstra solidez de projeto,
  <b>não</b> maturidade criptográfica.</p>
  <p class="lead linha-acima">Uma cifra se torna confiável por anos de tentativa pública de
  quebra, não por uma bateria de testes dos próprios autores. É por isso que a camada AES-256
  existe no sistema: <b class="destaque">o MPC-128 é o objeto de estudo; o AES-256 é o que
  protegeria o dinheiro de verdade.</b></p>
</div>
<div class="sp7"><ul>
{"".join(f"<li>{r}</li>" for r in v["e_seguro"]["ressalvas"])}
</ul></div>"""))

    s.append(_slide("obrigado", "MaxPay", f"""
<div class="sp8">
  <h1>Obrigado</h1>
  <p class="lead" style="margin-top:30px;font-size:clamp(17px,1.4vw,22px)">Perguntas?</p>
</div>
<div class="sp4" style="align-self:end">
  <span class="rotulo">Grupo</span>
  <p class="lead" style="font-size:15px;line-height:1.9">{"<br>".join(GRUPO)}</p>
</div>""", "capa"))

    total = len(s)
    corpo = "\n".join(_render(x, k + 1, total) for k, x in enumerate(s))
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MaxPay: apresentação</title>
<style>{CSS}</style></head>
<body><div class="deck">{corpo}</div>
<div class="progresso" id="progresso"></div>
<div class="dica">← → navega · N notas · P imprime</div>
<script>{JS}</script></body></html>"""


def main() -> Path:
    res = carregar()
    if res is None:
        raise SystemExit("Rode `python -m maxpay.experiments` primeiro.")
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(gerar(res), encoding="utf-8")
    return DESTINO


if __name__ == "__main__":
    p = main()
    print(f"OK -> {p} ({p.stat().st_size / 1024:.1f} KB)")
