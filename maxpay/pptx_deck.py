"""Gera `docs/MaxPay-apresentacao.pptx`, a versao do deck para importar no Canva.

O deck oficial continua sendo `docs/slides/index.html`, que e quem le os
resultados e nunca envelhece. Este .pptx existe por um motivo so: o Canva
importa PowerPoint e nao importa HTML. Entao ele carrega o mesmo conteudo, as
mesmas figuras e as mesmas notas, num formato que o Canva abre editavel.

    python -m maxpay.experiments
    python -m maxpay.figuras
    python -m maxpay.pptx_deck

Depois, no Canva: Criar um design > Importar arquivo, e escolher o .pptx.

Fonte: o Canva nao tem Geist. O deck usa Helvetica Neue aqui, que o Canva
substitui por algo proximo sem quebrar o layout.
"""

from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

from maxpay.experiments import carregar
from maxpay.notas import NOTAS
from maxpay.report import GRUPO, i, n

RAIZ = Path(__file__).resolve().parent.parent
FIGURAS = RAIZ / "docs" / "figuras"
DESTINO = RAIZ / "docs" / "MaxPay-apresentacao.pptx"

from maxpay import paleta

# Cores amostradas do template do Canva que o grupo escolheu, para o deck
# importado cair casado com ele. Ver maxpay/paleta.py.
def _c(hexa: str) -> RGBColor:
    return RGBColor(*paleta.rgb(hexa))

TINTA = _c(paleta.NAVY)
SUPERFICIE = _c(paleta.NAVY_ESCURO)
LINHA = _c(paleta.NAVY_CLARO)
TEXTO = _c(paleta.CREME)
TEXTO_2 = _c(paleta.CREME_2)
TEXTO_3 = _c(paleta.CREME_3)
ACENTO = _c(paleta.CREME)
OK = _c(paleta.SERIE_ALERTA)
CRIT = _c(paleta.SERIE_RUIM)

FONTE = "Helvetica Neue"

L, A = Inches(13.333), Inches(7.5)
MARGEM = Inches(0.95)
UTIL = L - 2 * MARGEM


def _fundo(slide) -> None:
    """Fundo do slide E um retangulo de sangria por baixo de tudo.

    Os dois, porque o importador do Canva costuma descartar o fundo de nivel de
    slide. Sem o retangulo, um deck escuro chega la branco, com texto branco
    por cima: invisivel.
    """
    from pptx.enum.shapes import MSO_SHAPE

    f = slide.background.fill
    f.solid()
    f.fore_color.rgb = TINTA

    r = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, L, A)
    r.fill.solid()
    r.fill.fore_color.rgb = TINTA
    r.line.fill.background()
    r.shadow.inherit = False
    r.name = "fundo"
    # Primeiro no z-order: add_shape joga no topo, entao desce para o fundo.
    arvore = slide.shapes._spTree
    arvore.remove(r._element)
    arvore.insert(2, r._element)


def _caixa(slide, x, y, w, h, texto, *, tam=18, cor=TEXTO, negrito=False,
           espaco=1.18, alinha=PP_ALIGN.LEFT, fonte=FONTE):
    cx = slide.shapes.add_textbox(x, y, w, h)
    tf = cx.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    linhas = texto.split("\n")
    for k, linha in enumerate(linhas):
        p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
        p.alignment = alinha
        p.line_spacing = espaco
        r = p.add_run()
        r.text = linha
        r.font.size = Pt(tam)
        r.font.bold = negrito
        r.font.color.rgb = cor
        r.font.name = fonte
    return cx


def _cabecalho(slide, secao: str, titulo: str, folio: str) -> Emu:
    """Eyebrow, titulo e numero. Devolve o y onde o conteudo pode comecar."""
    _caixa(slide, MARGEM, Inches(0.52), UTIL - Inches(1.2), Inches(0.3),
           secao.upper(), tam=11, cor=TEXTO_3)
    _caixa(slide, L - MARGEM - Inches(1.1), Inches(0.52), Inches(1.1), Inches(0.3),
           folio, tam=11, cor=TEXTO_3, alinha=PP_ALIGN.RIGHT)
    _caixa(slide, MARGEM, Inches(0.92), UTIL, Inches(0.72), titulo,
           tam=32, negrito=True)
    return Inches(1.82)


def _regua(slide, y) -> None:
    from pptx.enum.shapes import MSO_SHAPE
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, MARGEM, y, UTIL, Emu(9525))
    s.fill.solid()
    s.fill.fore_color.rgb = LINHA
    s.line.fill.background()
    s.shadow.inherit = False


def _figura(slide, nome: str, y, *, altura=None, largura=None, x=None) -> Emu:
    """Insere a figura e devolve a base dela.

    Devolver a base importa: quando eu chutava a altura para posicionar o que
    vem embaixo, a tabela entrava por baixo da imagem.
    """
    caminho = FIGURAS / nome
    if not caminho.exists():
        raise SystemExit(f"Figura ausente: {caminho}. Rode `python -m maxpay.figuras`.")
    xx = x if x is not None else MARGEM
    if altura is not None:
        f = slide.shapes.add_picture(str(caminho), xx, y, height=altura)
    else:
        f = slide.shapes.add_picture(str(caminho), xx, y, width=largura or UTIL)
    return f.top + f.height


def _tabela(slide, y, colunas: list[str], linhas: list[list[str]], *,
            larguras: list[float] | None = None, altura_linha=0.36):
    n_col, n_lin = len(colunas), len(linhas) + 1
    alt = Inches(altura_linha * n_lin)
    forma = slide.shapes.add_table(n_lin, n_col, MARGEM, y, UTIL, alt)
    tabela = forma.table
    if larguras:
        total = sum(larguras)
        for c, frac in enumerate(larguras):
            tabela.columns[c].width = Emu(int(UTIL * frac / total))
    for c, titulo in enumerate(colunas):
        cel = tabela.cell(0, c)
        cel.text = titulo or " "
        cel.fill.solid()
        cel.fill.fore_color.rgb = TINTA
        cel.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = cel.text_frame.paragraphs[0]
        p.runs[0].font.size = Pt(12)
        p.runs[0].font.bold = True
        p.runs[0].font.color.rgb = TEXTO_3
        p.runs[0].font.name = FONTE
        if c:
            p.alignment = PP_ALIGN.RIGHT
    for r, linha in enumerate(linhas, start=1):
        for c, valor in enumerate(linha):
            cel = tabela.cell(r, c)
            cel.text = str(valor) or " "
            cel.fill.solid()
            cel.fill.fore_color.rgb = SUPERFICIE if r % 2 else TINTA
            cel.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = cel.text_frame.paragraphs[0]
            p.runs[0].font.size = Pt(13)
            p.runs[0].font.color.rgb = TEXTO if c == 0 else TEXTO_2
            p.runs[0].font.name = FONTE
            if c:
                p.alignment = PP_ALIGN.RIGHT
    return forma


def _notas(slide, sid: str) -> None:
    slide.notes_slide.notes_text_frame.text = NOTAS.get(sid, "")


# ------------------------------------------------------------------ slides

def construir(res: dict) -> Presentation:
    c = res["cifra"]
    pj = c["projeto"]
    d = res["diferencial"]
    freq_f, freq_c = res["frequencia"]["sem_difusao"], res["frequencia"]["com_difusao"]
    est = res["estego"]
    ia = res["bigdata"]["ia"]["metricas"]
    bd = res["bigdata"]["resumo"]
    dic = res["dicionario"]
    gpu = next(p for p in res["forca_bruta"]["projecao"]
               if p["bits"] == 256 and "GPU" in p["cenario"])
    perfis = {p["rotulo"]: p for p in res["estatistico"]["perfis"]}
    v = res["veredito"]

    prs = Presentation()
    prs.slide_width, prs.slide_height = L, A
    branco = prs.slide_layouts[6]
    ordem = list(NOTAS)

    def nova(sid: str):
        s = prs.slides.add_slide(branco)
        _fundo(s)
        _notas(s, sid)
        return s, f"{ordem.index(sid) + 1:02d} / {len(ordem):02d}"

    # 01 capa
    s, _ = nova("capa")
    _caixa(s, MARGEM, Inches(0.6), UTIL, Inches(0.3),
           "CESAR SCHOOL · CIBERSEGURANÇA APLICADA A DADOS E IA", tam=11, cor=TEXTO_3)
    _caixa(s, MARGEM, Inches(2.25), UTIL, Inches(1.2), "MaxPay", tam=72, negrito=True)
    _caixa(s, MARGEM, Inches(3.5), Inches(8.2), Inches(1.0),
           "Um cofre de banco digital que cifra, esconde e observa.\n"
           "E então ataca a si mesmo para descobrir se é seguro.",
           tam=19, cor=TEXTO_2)
    _regua(s, Inches(5.1))
    _caixa(s, MARGEM, Inches(5.35), Inches(7.4), Inches(0.9),
           "  ·  ".join(GRUPO), tam=13, cor=TEXTO_2)
    _caixa(s, MARGEM, Inches(6.25), UTIL, Inches(0.3),
           "Professora Renatta Nigro", tam=13, cor=TEXTO_3)

    # 02 ato 1
    s, folio = nova("ato1")
    _caixa(s, MARGEM, Inches(0.52), UTIL, Inches(0.3), "ENUNCIADO · PARTES 1 E 2",
           tam=11, cor=TEXTO_3)
    _caixa(s, L - MARGEM - Inches(1.1), Inches(0.52), Inches(1.1), Inches(0.3),
           folio, tam=11, cor=TEXTO_3, alinha=PP_ALIGN.RIGHT)
    _caixa(s, MARGEM, Inches(2.6), UTIL, Inches(0.38), "01", tam=20, cor=ACENTO, negrito=True)
    _caixa(s, MARGEM, Inches(3.05), UTIL, Inches(1.0), "O sistema", tam=54, negrito=True)
    _caixa(s, MARGEM, Inches(4.3), Inches(8.0), Inches(0.8),
           "Seis camadas que protegem uma transação, da entrada do dado até o "
           "painel de quem vigia.", tam=18, cor=TEXTO_2)

    # 03 o que foi construido
    s, folio = nova("construido")
    y = _cabecalho(s, "Arquitetura", "O que foi construído", folio)
    _caixa(s, MARGEM, y, Inches(9.6), Inches(0.9),
           "Um sistema em seis camadas, e na mesma base de código três ataques que "
           "tentam quebrá-lo.\nToda a cifragem roda contra duas versões do algoritmo: "
           "a íntegra e uma deliberadamente enfraquecida.", tam=15, cor=TEXTO_2)
    _tabela(s, y + Inches(1.0),
            ["Camada", "O que faz", "Onde se vê"],
            [["1 Entrada de dados", "texto, arquivos e imagens", "aba Cofre"],
             ["2 Criptografia", f"{c['nome']} próprio e AES-256", "aba Cofre"],
             ["3 Esteganografia", "ocultação em imagem", "aba Ocultar"],
             ["4 Big Data", "Parquet particionado e DuckDB", "aba Antifraude"],
             ["5 Inteligência Artificial", "Isolation Forest", "aba Antifraude"],
             ["6 Dashboard", "as quatro abas", "a plataforma"]],
            larguras=[3, 5, 2.4])

    # 04 algoritmo
    s, folio = nova("algoritmo")
    y = _cabecalho(s, "Descrição do algoritmo · aba Cofre",
                   f"{c['nome']}, a cifra que projetamos", folio)
    base = _figura(s, "diagrama-rodada.png", y + Inches(0.1), largura=Inches(9.2),
                   x=MARGEM + Inches(1.1))
    _tabela(s, base + Inches(0.18),
            ["Parâmetro", "Valor"],
            [["Bloco e chave", f"{c['bloco_bits']} e {c['chave_bits']} bits"],
             ["Rodadas", str(c["rodadas"])],
             ["S-box bijetiva, pontos fixos", f"sim, {c['sbox_pontos_fixos']}"],
             ["Uniformidade diferencial", f"{c['ddt_maximo']} → 2^{int(c['log2_prob_diferencial'])}"],
             ["Integridade", "HMAC-SHA256"]],
            larguras=[6, 4], altura_linha=0.3)

    # 05 o que e nosso
    s, folio = nova("projeto")
    y = _cabecalho(s, "Projeto da cifra", "O que é nosso, e o que vem do AES", folio)
    _caixa(s, MARGEM, y, Inches(10.2), Inches(0.7),
           "A estrutura é da mesma família do AES, e isso é de propósito: é a rede SPN "
           "com S-box de inverso multiplicativo que garante as boas propriedades.",
           tam=15, cor=TEXTO_2)
    _tabela(s, y + Inches(0.85),
            ["Componente", c["nome"], "AES", "Como foi verificado"],
            [["Afim da S-box", f"{tuple(pj['sbox_rotacoes'])} ⊕ {pj['sbox_constante']}",
              f"{tuple(pj['sbox_rotacoes_aes'])} ⊕ {pj['sbox_constante_aes']}",
              "bijetiva, zero ponto fixo"],
             ["Permutação", str(tuple(pj["deslocamentos"])),
              str(tuple(pj["deslocamentos_aes"])), "puxa das quatro colunas"],
             ["Difusão", str(tuple(pj["matriz_difusao"])),
              str(tuple(pj["matriz_difusao_aes"])), "MDS por todos os menores"],
             ["Escalonamento", "HKDF/HMAC-SHA256", "Rijndael", "subchaves por mensagem"]],
            larguras=[2.6, 2.8, 2.4, 3.4], altura_linha=0.44)
    _caixa(s, MARGEM, y + Inches(3.1), UTIL, Inches(0.4),
           "A S-box difere da do AES nas 256 posições.", tam=14, cor=OK)

    # 06 chave
    s, folio = nova("chave")
    y = _cabecalho(s, "Geração dinâmica de chaves · aba Cofre", "A chave nunca é fixa", folio)
    base = _figura(s, "diagrama-chave.png", y, largura=UTIL)
    _tabela(s, base + Inches(0.2),
            ["Propriedade", "Medida"],
            [["Mesma senha e mesma mensagem", "envelopes diferentes"],
             ["1 bit trocado na chave", f"{n(d['avalanche_chave']['media_pct'])}% dos bits mudam"],
             ["1 bit alterado no cifrado", "recusado, o HMAC acusa"],
             ["Chave guardada em disco", "nenhuma"]],
            larguras=[6, 4], altura_linha=0.38)

    # 07 esteganografia
    s, folio = nova("estego")
    y = _cabecalho(s, "Camada 3 · aba Ocultar", "Esteganografia", folio)
    _figura(s, "estego-antes-depois.png", y, altura=Inches(3.5), x=MARGEM)
    seg = est["esteganalise"]["segmentos_suspeitos"]
    _caixa(s, Inches(7.9), y + Inches(0.1), Inches(4.5), Inches(3.4),
           f"Os bits vão para posições derivadas da chave.\n\n"
           f"Qui-quadrado de Westfeld\n"
           f"LSB sequencial: {seg['lsb_sequencial_sem_chave']} de 20 segmentos\n"
           f"chaveado: {seg['lsb_chaveado_maxpay']}, igual à imagem limpa\n\n"
           f"Capacidade: {i(est['capacidade_bytes'])} bytes\n"
           f"Chave errada: extração rejeitada",
           tam=15, cor=TEXTO_2, espaco=1.3)

    # 08 antifraude
    s, folio = nova("antifraude")
    y = _cabecalho(s, "Camadas 4 e 5 · aba Antifraude",
                   "Big Data e detecção de anomalias", folio)
    _caixa(s, MARGEM, y, UTIL, Inches(0.5),
           f"{i(bd['eventos'])} eventos  ·  {bd['dias']} dias  ·  {i(bd['usuarios'])} contas  ·  "
           f"ROC AUC {n(ia['roc_auc'], 4)}, sem rótulos  ·  "
           f"{n(ia['ganho_sobre_acaso'], 1)}× sobre o acaso",
           tam=15, cor=ACENTO)
    # Altura explicita: por largura, a nota de rodape da figura empurra a base
    # para fora do slide.
    _figura(s, "anomalias-revocacao-posto.png", y + Inches(0.6),
            altura=Inches(4.5), x=MARGEM + Inches(1.0))

    # 09 ato 2
    s, folio = nova("ato2")
    _caixa(s, MARGEM, Inches(0.52), UTIL, Inches(0.3),
           "ENUNCIADO · PARTE 3 · ABA RESISTÊNCIA", tam=11, cor=TEXTO_3)
    _caixa(s, L - MARGEM - Inches(1.1), Inches(0.52), Inches(1.1), Inches(0.3),
           folio, tam=11, cor=TEXTO_3, alinha=PP_ALIGN.RIGHT)
    _caixa(s, MARGEM, Inches(2.6), UTIL, Inches(0.38), "02", tam=20, cor=ACENTO, negrito=True)
    _caixa(s, MARGEM, Inches(3.05), UTIL, Inches(1.0), "Os ataques", tam=54, negrito=True)
    _caixa(s, MARGEM, Inches(4.3), Inches(8.6), Inches(1.0),
           "Três ataques contra duas versões da mesma cifra: a íntegra e uma "
           "enfraquecida de propósito. Todos rodam ao vivo, com os parâmetros que a "
           "plateia escolher.", tam=18, cor=TEXTO_2)

    # 10 avalanche
    s, folio = nova("avalanche")
    y = _cabecalho(s, "Enunciado · parte 4 · efeito avalanche", "Efeito avalanche", folio)
    meia = Inches(5.7)
    _figura(s, "avalanche-barras.png", y + Inches(0.3), largura=meia, x=MARGEM)
    _figura(s, "avalanche-histograma.png", y + Inches(0.1), largura=meia,
            x=MARGEM + meia + Inches(0.3))
    _caixa(s, MARGEM, Inches(6.5), UTIL, Inches(0.5),
           f"A difusão se completa na rodada {v['efeito_avalanche']['rodadas_ate_difusao_total']} "
           f"e a cifra usa {c['rodadas']}. O resto é margem de segurança.",
           tam=14, cor=TEXTO_2)

    # 11 padroes
    s, folio = nova("padroes")
    y = _cabecalho(s, "Enunciado · parte 4 · padrões na saída", "A saída tem padrões?", folio)
    rot = {"texto_claro": "Texto claro",
           "mpc_ctr_14_rodadas": f"{c['nome']} · CTR, {c['rodadas']} rodadas",
           "mpc_ecb_14_rodadas": f"{c['nome']} · ECB, {c['rodadas']} rodadas",
           "mpc_ecb_1_rodada_sem_difusao": f"{c['nome']} · ECB, 1 rodada, sem difusão",
           "aes256_gcm": "AES-256-GCM", "urandom": "/dev/urandom (controle)"}
    _tabela(s, y,
            ["Amostra", "Entropia", "Índice de coincidência", "Blocos repetidos"],
            [[rot.get(p["rotulo"], p["rotulo"]),
              n(p["entropia_bits_por_byte"], 4),
              n(p["indice_coincidencia"], 6),
              f"{n(p['repeticao_blocos']['pct_repetidos'])}%"]
             for p in res["estatistico"]["perfis"]],
            larguras=[4.4, 1.8, 2.4, 2.2], altura_linha=0.42)
    ecb = perfis["mpc_ecb_14_rodadas"]
    _caixa(s, MARGEM, y + Inches(3.35), UTIL, Inches(0.9),
           f"Em CTR, nenhum bloco se repete e a entropia encosta no teto de 8.\n"
           f"Em ECB, {n(ecb['repeticao_blocos']['pct_repetidos'])}% dos blocos se repetem "
           f"mesmo com {c['rodadas']} rodadas: o modo pesa mais que as rodadas.",
           tam=15, cor=TEXTO_2)

    # 12 forca bruta
    s, folio = nova("bruta")
    y = _cabecalho(s, "Ataque 1 · aba Resistência", "Força bruta", folio)
    _tabela(s, y,
            ["Contra a chave", ""],
            [["Taxa medida", f"{i(res['forca_bruta']['chaves_por_segundo'])} chaves/s, 1 núcleo"],
             ["Espaço de chaves", f"2^{c['chave_bits']}, não depende das rodadas"],
             ["Com 1 milhão de GPUs", gpu["anos_fmt"]],
             ["Veredito", "inviável, a cifra resistiu"]],
            larguras=[4, 6], altura_linha=0.38)
    _caixa(s, MARGEM, y + Inches(2.3), UTIL, Inches(0.4),
           "Contra a senha, porém, a história muda.", tam=17, cor=CRIT, negrito=True)
    _tabela(s, y + Inches(2.8),
            ["Contra a senha", ""],
            [["PBKDF2 limita o atacante a", f"{n(dic['tentativas_por_segundo'], 1)} tentativas/s"],
             [f"Senha fraca ({dic['senha_quebrada']})", f"caiu em {n(dic['segundos'])} s"],
             ["Senha forte de 12 caracteres", dic["anos_forte_fmt"]]],
            larguras=[4, 6], altura_linha=0.38)

    # 13 diferencial
    s, folio = nova("diferencial")
    y = _cabecalho(s, "Ataque 2 · aba Resistência", "Diferencial", folio)
    _caixa(s, MARGEM, y, Inches(10.4), Inches(0.6),
           "Aplicamos sempre a mesma diferença na entrada e procuramos uma diferença "
           "de saída que se repita. Numa cifra sólida, nenhuma se repete.",
           tam=15, cor=TEXTO_2)
    di, df = d["distinguidor_integro"], d["distinguidor_fraco"]
    _tabela(s, y + Inches(0.8),
            ["Variante", "Avalanche", "Saídas distintas", "Repetição máxima", "Distinguível"],
            [[f"{c['nome']} íntegro", f"{n(d['mpc_integro']['media_pct'])}%",
              f"{n(di['pct_saidas_distintas'])}%", str(di["ocorrencias"]), "não"],
             ["1 rodada, sem difusão", f"{n(d['mpc_fraco']['media_pct'])}%",
              f"{n(df['pct_saidas_distintas'])}%", i(df["ocorrencias"]), "sim"]],
            larguras=[3.4, 1.8, 2.2, 2.2, 1.6], altura_linha=0.44)
    _caixa(s, MARGEM, y + Inches(2.2), UTIL, Inches(0.9),
           f"A S-box tem uniformidade diferencial {c['ddt_maximo']}: nenhuma característica "
           f"de uma rodada passa de 2^{int(c['log2_prob_diferencial'])} de probabilidade.\n"
           f"Ao longo de {c['rodadas']} rodadas, nada explorável sobra.",
           tam=15, cor=TEXTO_2)

    # 14 estatistico
    s, folio = nova("estatistico")
    y = _cabecalho(s, "Ataque 3 · aba Resistência", "Análise de frequência", folio)
    _figura(s, "frequencia-por-posicao.png", y, largura=Inches(7.6), x=MARGEM)
    _caixa(s, Inches(9.0), y + Inches(0.2), Inches(3.5), Inches(3.6),
           f"Registros de largura fixa.\nSem MixColumns, cada posição do bloco vira "
           f"uma substituição simples.\n\n"
           f"Sem difusão: {n(freq_f['acuracia_pct'])}%\n"
           f"{freq_f['posicoes_expostas']} de {freq_f['posicoes_registro']} posições\n\n"
           f"Com difusão: {n(freq_c['acuracia_pct'])}%\n"
           f"linha de base: {n(freq_c['linha_base_unigrama_pct'])}%\n\n"
           f"Chave usada: nenhuma",
           tam=14, cor=TEXTO_2, espaco=1.28)

    # 15 ato 3
    s, folio = nova("ato3")
    _caixa(s, MARGEM, Inches(0.52), UTIL, Inches(0.3), "ENUNCIADO · PARTE 4",
           tam=11, cor=TEXTO_3)
    _caixa(s, L - MARGEM - Inches(1.1), Inches(0.52), Inches(1.1), Inches(0.3),
           folio, tam=11, cor=TEXTO_3, alinha=PP_ALIGN.RIGHT)
    _caixa(s, MARGEM, Inches(2.6), UTIL, Inches(0.38), "03", tam=20, cor=ACENTO, negrito=True)
    _caixa(s, MARGEM, Inches(3.05), UTIL, Inches(1.0), "O veredito", tam=54, negrito=True)
    _caixa(s, MARGEM, Inches(4.3), Inches(8.6), Inches(0.8),
           "O que os números respondem, e o que eles não autorizam a afirmar.",
           tam=18, cor=TEXTO_2)

    # 16 as quatro perguntas
    s, folio = nova("perguntas")
    y = _cabecalho(s, "Enunciado · parte 4 · as respostas", "As quatro perguntas", folio)
    _tabela(s, y,
            ["Pergunta", "Resposta", "O número"],
            [["O sistema apresenta efeito avalanche?", v["efeito_avalanche"]["resposta"],
              f"{n(d['mpc_integro']['media_pct'])}% dos bits, contra 50% ideal"],
             ["Existem padrões na saída?", v["padroes_na_saida"]["resposta"],
              f"entropia {n(perfis['mpc_ctr_14_rodadas']['entropia_bits_por_byte'], 4)} bits/byte"],
             ["Qual ataque foi mais eficaz?", "Estatístico",
              f"{n(freq_f['acuracia_pct'])}% do texto da variante fraca"],
             ["O sistema é seguro?", "Sim, com ressalvas",
              f"força bruta inviável por {gpu['anos_fmt']}"]],
            larguras=[4.6, 2.4, 4.2], altura_linha=0.52)

    # 17 conclusao
    s, folio = nova("conclusao")
    y = _cabecalho(s, "Conclusão", "O que os números ensinam", folio)
    _figura(s, "difusao-por-rodada.png", y, largura=Inches(6.6), x=MARGEM)
    _caixa(s, Inches(8.0), y + Inches(0.05), Inches(4.5), Inches(3.8),
           f"Difusão é o que sustenta tudo.\nSem MixColumns a frequência recupera "
           f"{n(freq_f['acuracia_pct'])}% do texto.\n\n"
           f"O modo pesa mais que as rodadas.\nO ECB preservou "
           f"{n(perfis['mpc_ecb_14_rodadas']['repeticao_blocos']['pct_repetidos'])}% "
           f"dos blocos repetidos.\n\n"
           f"Força bruta é o ataque errado.\nA superfície real é a senha.\n\n"
           f"A anomalia mais difícil é a que não quebra nada.",
           tam=14, cor=TEXTO_2, espaco=1.26)

    # 18 limites
    s, folio = nova("limites")
    y = _cabecalho(s, "Limites", "O que não podemos afirmar", folio)
    _caixa(s, MARGEM, y, Inches(10.6), Inches(1.0),
           f"O {c['nome']} passou nos três ataques. Isso demonstra solidez de projeto, "
           f"não maturidade criptográfica. Uma cifra se torna confiável por anos de "
           f"tentativa pública de quebra, não por uma bateria dos próprios autores.",
           tam=16, cor=TEXTO_2)
    _regua(s, y + Inches(1.15))
    _caixa(s, MARGEM, y + Inches(1.4), Inches(11.4), Inches(2.6),
           "Cifra própria sem análise pública: S-box, matriz de difusão e permutação "
           "nunca passaram por criptanálise independente. Em produção, use AES-256.\n\n"
           f"O modo ECB continua vazando estrutura mesmo com {c['rodadas']} rodadas.\n\n"
           "A implementação não é de tempo constante: existe canal lateral de temporização.\n\n"
           "A análise é empírica. Não há criptanálise linear nem prova formal.",
           tam=15, cor=TEXTO_2, espaco=1.3)

    # 19 obrigado
    s, _ = nova("obrigado")
    _caixa(s, MARGEM, Inches(0.6), UTIL, Inches(0.3), "MAXPAY", tam=11, cor=TEXTO_3)
    _caixa(s, MARGEM, Inches(2.6), UTIL, Inches(1.2), "Obrigado", tam=64, negrito=True)
    _caixa(s, MARGEM, Inches(3.9), UTIL, Inches(0.6), "Perguntas?", tam=24, cor=TEXTO_2)
    _regua(s, Inches(5.1))
    _caixa(s, MARGEM, Inches(5.35), Inches(9.0), Inches(0.9),
           "  ·  ".join(GRUPO), tam=13, cor=TEXTO_2)

    return prs


def main() -> Path:
    res = carregar()
    if res is None:
        raise SystemExit("Rode `python -m maxpay.experiments` primeiro.")
    if not NOTAS:
        raise SystemExit("NOTAS vazio: a bateria precisa existir antes.")
    prs = construir(res)
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    prs.save(DESTINO)
    return DESTINO


if __name__ == "__main__":
    p = main()
    print(f"OK -> {p} ({p.stat().st_size / 1024:.0f} KB)")
