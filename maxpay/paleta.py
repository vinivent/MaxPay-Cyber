"""Paleta dos materiais da apresentacao.

As tres primeiras cores sao do template do Canva que o grupo escolheu, o "Blue
and Beige Bold Creative Brief". Foram amostradas do proprio design, nao
escolhidas no olho, para que o .pptx importado caia casado com o template em
vez de brigar com ele.

As cores de dado abaixo foram escolhidas para funcionar SOBRE o navy. O
template nao traz paleta de grafico, entao ela e nossa: creme para a serie
principal, terracota para a variante quebrada, azul claro para a referencia
externa e ouro para linha de base.

O deck HTML (`slides.css`) segue a paleta Swiss escura da plataforma e nao usa
este modulo. Sao dois destinos diferentes de proposito: a plataforma e um
produto, o Canva e a apresentacao.
"""

from __future__ import annotations

# Do template do Canva.
NAVY = "#253985"
CREME = "#F3E8CB"
PRETO = "#1F1F1F"

# Derivadas, para hierarquia de texto sobre o navy.
CREME_2 = "#C9BFA6"   # texto secundario
CREME_3 = "#9A927D"   # texto terciario, rotulos
NAVY_CLARO = "#354CA6"  # linhas e preenchimentos sutis
NAVY_ESCURO = "#1B2A66"  # faixas de tabela

# Series de dados sobre o navy.
SERIE_BOA = CREME           # a cifra integra
SERIE_REF = "#8A96C8"       # referencia externa, AES e urandom
SERIE_RUIM = "#E2703A"      # a variante enfraquecida
SERIE_ALERTA = "#E8B84B"    # linha de base, limiares


def rgb(hexa: str) -> tuple[int, int, int]:
    """'#253985' -> (37, 57, 133)."""
    h = hexa.lstrip("#")
    return tuple(int(h[k:k + 2], 16) for k in (0, 2, 4))
