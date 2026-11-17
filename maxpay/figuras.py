"""Gera as figuras de apoio da apresentacao, a partir da bateria ja executada.

Tudo em `docs/figuras/`, PNG a 200 dpi, na mesma paleta do deck. Sao as imagens
que entram no .pptx e, por ele, no Canva.

Nenhuma figura e ilustrativa: toda curva, barra e imagem vem de
`results/experimentos.json`. As duas unicas excecoes sao os dois diagramas de
arquitetura (a rodada da cifra e a derivacao da chave), que desenham estrutura e
nao medicao.

    python -m maxpay.experiments && python -m maxpay.figuras

matplotlib e python-pptx nao estao em requirements.txt de proposito: quem so
quer rodar o sistema nao precisa delas. Veja requirements-deck.txt.
"""

from __future__ import annotations

import base64
import io
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from maxpay.experiments import carregar

SAIDA = Path(__file__).resolve().parent.parent / "docs" / "figuras"

from maxpay import paleta

# Cores do template do Canva que o grupo escolheu. Ver maxpay/paleta.py.
TINTA = paleta.NAVY
SUPERFICIE = paleta.NAVY_ESCURO
LINHA = paleta.NAVY_CLARO
LINHA_FORTE = paleta.CREME_3
TEXTO = paleta.CREME
TEXTO_2 = paleta.CREME_2
TEXTO_3 = paleta.CREME_3
ACENTO = paleta.SERIE_BOA
OK = paleta.SERIE_BOA
AVISO = paleta.SERIE_ALERTA
CRIT = paleta.SERIE_RUIM
REF = paleta.SERIE_REF

DPI = 200


def _estilo() -> None:
    plt.rcParams.update({
        "figure.facecolor": TINTA,
        "axes.facecolor": TINTA,
        "savefig.facecolor": TINTA,
        "text.color": TEXTO,
        "axes.labelcolor": TEXTO_2,
        "axes.edgecolor": LINHA_FORTE,
        "xtick.color": TEXTO_2,
        "ytick.color": TEXTO_2,
        "grid.color": LINHA,
        "font.family": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.titlepad": 14,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.autolayout": False,
    })


def _salvar(fig, nome: str) -> Path:
    SAIDA.mkdir(parents=True, exist_ok=True)
    caminho = SAIDA / nome
    fig.savefig(caminho, dpi=DPI, bbox_inches="tight", pad_inches=0.28)
    plt.close(fig)
    return caminho


def _br(x: float, casas: int = 2) -> str:
    return f"{x:,.{casas}f}".replace(",", "~").replace(".", ",").replace("~", ".")


# ---------------------------------------------------------------- medicoes

def difusao_por_rodada(res: dict) -> Path:
    """A curva que mais explica o projeto: a difusao fecha na rodada 2."""
    d = res["diferencial"]
    integro = d["mpc_integro"]["por_rodada"]
    sem = d["mpc_sem_difusao_14_rodadas"]["por_rodada"]

    fig, ax = plt.subplots(figsize=(8.4, 4.3))
    rod_i = [p["rodada"] for p in integro]
    pct_i = [p["pct"] for p in integro]
    rod_s = [p["rodada"] for p in sem]
    pct_s = [p["pct"] for p in sem]

    ax.axhline(50, color=LINHA_FORTE, lw=1, ls=(0, (4, 4)), zorder=1)
    # A esquerda: a direita e onde a legenda cabe sem bater nas curvas.
    ax.annotate("50%, o alvo", (0, 50), xytext=(2, 7), textcoords="offset points",
                ha="left", color=TEXTO_3, fontsize=10)

    ax.plot(rod_i, pct_i, color=ACENTO, lw=2.4, marker="o", ms=4.5,
            label="MPC-128 com difusão", zorder=3)
    ax.plot(rod_s, pct_s, color=CRIT, lw=2.4, marker="o", ms=4.5,
            label="sem MixColumns", zorder=3)

    ax.axvline(2, color=AVISO, lw=1.4, alpha=0.85, zorder=2)
    ax.annotate("difusão completa\nna rodada 2", (2, 36), xytext=(10, 0),
                textcoords="offset points", color=AVISO, fontsize=10, va="top")

    ax.set_xlabel("rodada")
    ax.set_ylabel("bits de saída alterados (%)")
    ax.set_title("Um bit de entrada se espalha em duas rodadas")
    ax.set_ylim(-4, 104)
    ax.set_xticks(range(0, len(rod_i), 2))
    ax.grid(axis="y", lw=0.8)
    leg = ax.legend(frameon=False, loc="upper right", labelcolor=TEXTO_2)
    for t in leg.get_texts():
        t.set_fontsize(10)
    return _salvar(fig, "difusao-por-rodada.png")


def avalanche_barras(res: dict) -> Path:
    d = res["diferencial"]
    itens = [
        ("MPC-128 íntegro", d["mpc_integro"]["media_pct"], ACENTO),
        ("AES-256 (referência)", d["aes256"]["media_pct"], REF),
        ("14 rodadas, sem difusão", d["mpc_sem_difusao_14_rodadas"]["media_pct"], CRIT),
        ("1 rodada, sem difusão", d["mpc_fraco"]["media_pct"], CRIT),
    ]
    fig, ax = plt.subplots(figsize=(8.4, 3.8))
    y = np.arange(len(itens))[::-1]
    ax.barh(y, [v for _, v, _ in itens], height=0.56,
            color=[c for _, _, c in itens])
    for yi, (rot, v, _) in zip(y, itens):
        ax.text(v + 1.4, yi, f"{_br(v)}%", va="center", color=TEXTO, fontsize=11.5)
    ax.axvline(50, color=LINHA_FORTE, lw=1, ls=(0, (4, 4)))
    ax.set_yticks(y, [rot for rot, _, _ in itens], fontsize=11)
    ax.set_xlim(0, 60)
    ax.set_xlabel("bits de saída alterados por 1 bit de entrada (%)")
    ax.set_title("Efeito avalanche")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", lw=0.8)
    ax.set_axisbelow(True)
    return _salvar(fig, "avalanche-barras.png")


def avalanche_histograma(res: dict) -> Path:
    """A distribuicao medida contra a binomial(128; 0,5) esperada."""
    d = res["diferencial"]["mpc_integro"]
    h = np.array(d["histograma"], dtype=float)
    k = np.arange(h.size)
    amostras = h.sum()

    from math import comb
    esperado = np.array([comb(128, int(j)) for j in k], dtype=float)
    esperado = esperado / esperado.sum() * amostras

    fig, ax = plt.subplots(figsize=(8.4, 4.0))
    ax.bar(k, h, width=1.0, color=ACENTO, alpha=0.85, label="medido")
    ax.plot(k, esperado, color=AVISO, lw=2.0,
            label="binomial(128; 0,5) esperada")
    ax.set_xlim(40, 90)
    ax.set_xlabel("bits alterados em um bloco de 128")
    ax.set_ylabel(f"blocos (de {_br(amostras, 0)})")
    ax.set_title("A saída se comporta como moeda honesta, bit a bit")
    ax.grid(axis="y", lw=0.8)
    ax.set_axisbelow(True)
    leg = ax.legend(frameon=False, labelcolor=TEXTO_2)
    for t in leg.get_texts():
        t.set_fontsize(10)
    return _salvar(fig, "avalanche-histograma.png")


def frequencia_por_posicao(res: dict) -> Path:
    """Onde o registro bancario vaza, posicao por posicao."""
    f = res["frequencia"]["sem_difusao"]
    c = res["frequencia"]["com_difusao"]
    sem = np.array(f["acuracia_por_posicao"], dtype=float) * 100
    com = np.array(c["acuracia_por_posicao"], dtype=float) * 100
    x = np.arange(sem.size)

    # Dois paineis empilhados, nao barras sobrepostas: sobreposta, a serie de
    # tras some atras da da frente e o grafico passa a ler como empilhado.
    fig, (cima, baixo) = plt.subplots(
        2, 1, figsize=(8.8, 5.0), sharex=True,
        gridspec_kw={"hspace": 0.22, "height_ratios": [1, 1]})
    base = f["linha_base_unigrama_pct"]

    for ax, serie, cor, titulo in (
        (cima, sem, CRIT, f"Sem difusão: {_br(f['acuracia_pct'])}% do texto recuperado"),
        (baixo, com, ACENTO, f"Com difusão: {_br(c['acuracia_pct'])}% recuperado"),
    ):
        ax.bar(x, serie, width=0.92, color=cor)
        ax.axhline(base, color=AVISO, lw=1.3, ls=(0, (5, 3)), zorder=4)
        ax.set_ylim(0, 105)
        ax.set_ylabel("recuperado (%)", fontsize=10)
        ax.set_title(titulo, fontsize=11.5)
        ax.grid(axis="y", lw=0.8)
        ax.set_axisbelow(True)

    # O rotulo da linha de base vai no painel de baixo, que esta vazio: no de
    # cima ele cairia em cima das barras.
    baixo.annotate(f"linha de base por frequência: {_br(base)}%", (2, base),
                   xytext=(0, 8), textcoords="offset points", ha="left",
                   color=AVISO, fontsize=9.5)
    baixo.set_xlabel(f"posição no registro bancário de {f['posicoes_registro']} caracteres")
    baixo.set_xlim(-1, sem.size)
    fig.suptitle(f"Sem difusão, {f['posicoes_expostas']} das "
                 f"{f['posicoes_registro']} posições abrem",
                 x=0.09, y=1.015, ha="left", fontsize=13.5, fontweight="bold",
                 color=TEXTO)
    return _salvar(fig, "frequencia-por-posicao.png")


def anomalias(res: dict) -> Path:
    """Revocacao contra posto de risco: o paradoxo do surto fica visivel."""
    from maxpay.events import NOMES_EXIBICAO

    tipos = res["bigdata"]["ia"]["metricas"]["por_tipo"]
    tipos = sorted(tipos, key=lambda t: -t["revocacao_pct"])
    rot = [NOMES_EXIBICAO.get(t["tipo"], t["tipo"]) for t in tipos]
    rev = [t["revocacao_pct"] for t in tipos]
    pos = [t["percentil_mediano"] for t in tipos]
    y = np.arange(len(tipos))[::-1]

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.4, 3.9), sharey=True,
                                 gridspec_kw={"wspace": 0.08})

    cores = [paleta.SERIE_BOA if v >= 50 else CRIT for v in rev]
    a1.barh(y, rev, height=0.56, color=cores)
    for yi, v in zip(y, rev):
        a1.text(v + 2, yi, f"{_br(v, 1)}%", va="center", color=TEXTO, fontsize=10.5)
    a1.set_xlim(0, 118)
    a1.set_title("Revocação: quanto foi alertado")
    a1.set_yticks(y, rot, fontsize=10.5)
    a1.spines["left"].set_visible(False)
    a1.tick_params(axis="y", length=0)
    a1.grid(axis="x", lw=0.8)
    a1.set_axisbelow(True)

    a2.barh(y, pos, height=0.56, color=ACENTO)
    for yi, v in zip(y, pos):
        a2.text(v + 0.04, yi, f"{_br(v)}%", va="center", color=TEXTO, fontsize=10.5)
    a2.set_xlim(0, 2.3)
    # Barra maior = pior posicao. Sem dizer isso, o grafico se le ao contrario.
    a2.set_title("Posto no ranking (barra menor = mais arriscado)")
    a2.spines["left"].set_visible(False)
    a2.tick_params(axis="y", length=0)
    a2.grid(axis="x", lw=0.8)
    a2.set_axisbelow(True)

    fig.text(0.5, -0.07,
             "O surto de eventos quase não é alertado, mas o modelo o coloca entre os mais "
             "arriscados.\nEle perde a disputa pelo orçamento de alertas, não a detecção.",
             ha="center", color=TEXTO_2, fontsize=10.5)
    return _salvar(fig, "anomalias-revocacao-posto.png")


def estego_antes_depois(res: dict) -> Path:
    """As duas imagens reais da bateria, lado a lado."""
    from PIL import Image

    imgs = res["estego"]["imagens_base64"]
    a = Image.open(io.BytesIO(base64.b64decode(imgs["original"])))
    b = Image.open(io.BytesIO(base64.b64decode(imgs["com_payload"])))
    q = res["estego"]["qualidade"]

    fig, (x1, x2) = plt.subplots(1, 2, figsize=(8.8, 4.6),
                                 gridspec_kw={"wspace": 0.06})
    for ax, img, titulo in ((x1, a, "portadora original"), (x2, b, "com a mensagem dentro")):
        ax.imshow(img)
        ax.set_title(titulo, fontsize=11.5, color=TEXTO)
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(True); s.set_color(LINHA_FORTE)

    fig.text(0.5, 0.015,
             f"PSNR {_br(q['psnr_db'])} dB, desvio máximo de {q['desvio_maximo']} em 255. "
             f"{_br(res['estego']['payload_bytes'], 0)} bytes escondidos.",
             ha="center", color=TEXTO_2, fontsize=10.5)
    return _salvar(fig, "estego-antes-depois.png")


# ---------------------------------------------------------------- diagramas

def _caixa(ax, x, y, w, h, texto, *, cor=SUPERFICIE, borda=LINHA_FORTE,
           cor_texto=TEXTO, tamanho=11, negrito=False):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0,rounding_size=0.06",
        linewidth=1.3, edgecolor=borda, facecolor=cor, zorder=2))
    ax.text(x + w / 2, y + h / 2, texto, ha="center", va="center",
            color=cor_texto, fontsize=tamanho, zorder=3,
            fontweight="bold" if negrito else "normal")


def _seta(ax, x1, y1, x2, y2, cor=LINHA_FORTE):
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=13,
        linewidth=1.3, color=cor, zorder=2, shrinkA=0, shrinkB=0))


def diagrama_rodada(res: dict) -> Path:
    c = res["cifra"]
    fig, ax = plt.subplots(figsize=(9.2, 2.9))
    ax.set_xlim(0, 10); ax.set_ylim(0, 3); ax.axis("off")

    etapas = [
        ("AddRoundKey", "estado ⊕ subchave", ACENTO),
        ("SubBytes", "S-box, byte a byte", TEXTO_3),
        ("ShiftRows", "troca as posições", TEXTO_3),
        ("MixColumns", "mistura as colunas", AVISO),
    ]
    w, h, lac = 2.0, 1.05, 0.33
    x = 0.12
    for nome, sub, cor in etapas:
        _caixa(ax, x, 1.15, w, h, "", borda=cor)
        ax.text(x + w / 2, 1.95, nome, ha="center", va="center",
                color=TEXTO, fontsize=11.5, fontweight="bold", zorder=3)
        ax.text(x + w / 2, 1.48, sub, ha="center", va="center",
                color=TEXTO_2, fontsize=9.8, zorder=3)
        if nome != etapas[-1][0]:
            _seta(ax, x + w, 1.675, x + w + lac, 1.675)
        x += w + lac

    ax.text(0.12, 0.52, f"×  {c['rodadas']} rodadas", color=TEXTO,
            fontsize=12, fontweight="bold")
    ax.text(1.75, 0.54,
            f"bloco {c['bloco_bits']} bits  ·  chave {c['chave_bits']} bits  ·  "
            f"GF(2⁸)  ·  a última rodada não tem MixColumns",
            color=TEXTO_3, fontsize=10)
    ax.text(0.12, 2.68, "A rodada da MPC-128", color=TEXTO, fontsize=13,
            fontweight="bold")
    return _salvar(fig, "diagrama-rodada.png")


def diagrama_chave(res: dict) -> Path:
    dic = res["dicionario"]
    fig, ax = plt.subplots(figsize=(9.2, 2.6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 2.7); ax.axis("off")

    passos = [
        ("senha", "digitada por quem opera", 1.55, CRIT),
        ("chave mestra", f"PBKDF2, {_br(dic['iteracoes_pbkdf2'], 0)} iterações", 2.35, AVISO),
        ("chave de sessão", "HKDF sobre um nonce novo", 2.35, ACENTO),
        ("15 subchaves", "uma por rodada", 1.85, AVISO),
    ]
    x, h = 0.12, 1.05
    for nome, sub, w, cor in passos:
        _caixa(ax, x, 0.78, w, h, "", borda=cor)
        ax.text(x + w / 2, 1.56, nome, ha="center", va="center", color=TEXTO,
                fontsize=11.5, fontweight="bold", zorder=3)
        ax.text(x + w / 2, 1.09, sub, ha="center", va="center", color=TEXTO_2,
                fontsize=9.4, zorder=3)
        if nome != passos[-1][0]:
            _seta(ax, x + w, 1.305, x + w + 0.3, 1.305)
        x += w + 0.3

    ax.text(0.12, 2.42, "A chave nunca é fixa", color=TEXTO, fontsize=13,
            fontweight="bold")
    ax.text(0.12, 0.28,
            "Nada disso fica em disco. Salt e nonce são novos a cada operação, "
            "então a mesma senha e a mesma mensagem geram envelopes diferentes.",
            color=TEXTO_3, fontsize=10)
    return _salvar(fig, "diagrama-chave.png")


FIGURAS = [
    diagrama_rodada,
    diagrama_chave,
    difusao_por_rodada,
    avalanche_barras,
    avalanche_histograma,
    frequencia_por_posicao,
    anomalias,
    estego_antes_depois,
]


def main() -> list[Path]:
    res = carregar()
    if res is None:
        raise SystemExit("Rode `python -m maxpay.experiments` primeiro.")
    _estilo()
    feitas = []
    for f in FIGURAS:
        caminho = f(res)
        feitas.append(caminho)
        print(f"  {caminho.name:<36} {caminho.stat().st_size / 1024:>6.0f} KB")
    return feitas


if __name__ == "__main__":
    print(f"Figuras em {SAIDA}:")
    fs = main()
    print(f"OK, {len(fs)} figuras.")
