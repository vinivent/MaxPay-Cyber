"""Ataque de forca bruta (Parte 3).

Duas frentes, porque um sistema bancario tem duas superficies distintas:

  1. `brute_force`      - busca exaustiva no espaco de chaves da cifra, com
                          entropia reduzida artificialmente para que o ataque
                          termine e possamos medir a taxa real de chaves/s.
  2. `dictionary_attack` - ataque de dicionario sobre a senha do usuario, que
                          passa pelo PBKDF2 e portanto tem custo muito maior.

A taxa medida em (1) e extrapolada em `keyspace_projection` para os espacos
reais de 128 e 256 bits.
"""

from __future__ import annotations

import math
import os
import secrets
import time

import numpy as np

from maxpay.cipher import (
    DEFAULT_ROUNDS,
    KDF_ITERATIONS,
    MaxPayCipher,
    derive_keys,
    encrypt_many_keys,
    expand_round_keys,
)

KNOWN_PLAINTEXT = b"MaxPay::TX000001"
SEGUNDOS_POR_ANO = 365.25 * 24 * 3600
IDADE_DO_UNIVERSO_ANOS = 1.38e10

SENHAS_COMUNS = [
    "123456", "senha", "123456789", "12345678", "qwerty", "admin", "banco123",
    "abc123", "maxpay", "password", "1234", "master", "pix2026", "caixa",
    "000000", "102030", "bradesco", "itau2026", "santander", "nubank",
]


def taxa_de_busca(
    rounds: int = DEFAULT_ROUNDS, diffusion: bool = True, amostra: int = 50_000, batch: int = 2048
) -> float:
    """Chaves testadas por segundo, medidas fora da busca.

    A busca para assim que encontra a chave, e onde ela caiu no espaco e
    aleatorio: medir a taxa por ali daria um numero instavel. Aqui o custo e
    cronometrado sobre uma quantidade fixa de candidatas.
    """
    prefixo = os.urandom(28)
    inicio = time.perf_counter()
    testadas = 0
    while testadas < amostra:
        n = min(batch, amostra - testadas)
        rks = np.stack([expand_round_keys(prefixo + (testadas + i).to_bytes(4, "big"), rounds) for i in range(n)])
        encrypt_many_keys(KNOWN_PLAINTEXT, rks, rounds, diffusion)
        testadas += n
    return testadas / (time.perf_counter() - inicio)


def brute_force(
    bits: int = 16,
    rounds: int = DEFAULT_ROUNDS,
    diffusion: bool = True,
    batch: int = 2048,
    tempo_limite: float = 30.0,
) -> dict:
    """Busca exaustiva com texto claro conhecido sobre `bits` de entropia.

    Cenario: o atacante capturou um par (claro, cifrado) e conhece todos os
    bits da chave menos `bits`. Mede a taxa real de chaves testadas por segundo.
    """
    if not 1 <= bits <= 28:
        raise ValueError("bits deve estar entre 1 e 28 para o ataque terminar")

    prefixo = os.urandom(28)
    espaco = 1 << bits
    alvo_idx = secrets.randbelow(espaco)
    chave_real = prefixo + alvo_idx.to_bytes(4, "big")
    alvo = MaxPayCipher(chave_real, rounds, diffusion).encrypt_block(KNOWN_PLAINTEXT)
    alvo_arr = np.frombuffer(alvo, dtype=np.uint8)

    inicio = time.perf_counter()
    testadas = 0
    encontrada: int | None = None
    progresso: list[dict] = []

    for base in range(0, espaco, batch):
        n = min(batch, espaco - base)
        rks = np.stack(
            [expand_round_keys(prefixo + (base + i).to_bytes(4, "big"), rounds) for i in range(n)]
        )
        saidas = encrypt_many_keys(KNOWN_PLAINTEXT, rks, rounds, diffusion)
        testadas += n
        acertos = np.flatnonzero((saidas == alvo_arr).all(axis=1))
        decorrido = time.perf_counter() - inicio
        progresso.append({"testadas": testadas, "segundos": round(decorrido, 4)})
        if acertos.size:
            encontrada = base + int(acertos[0])
            break
        if decorrido > tempo_limite:
            break

    decorrido = time.perf_counter() - inicio
    taxa = taxa_de_busca(rounds, diffusion)
    return {
        "ataque": "forca_bruta",
        "bits_entropia": bits,
        "rodadas": rounds,
        "difusao": diffusion,
        "espaco_chaves": espaco,
        "chaves_testadas": testadas,
        "segundos": round(decorrido, 4),
        "chaves_por_segundo": round(taxa, 1),
        "chaves_esperadas_ate_achar": espaco // 2,
        "chave_encontrada": encontrada is not None,
        "indice_real": alvo_idx,
        "indice_encontrado": encontrada,
        "cobertura_pct": round(100 * testadas / espaco, 2),
        "progresso": progresso[-60:],
        "projecao": keyspace_projection(taxa),
    }


def keyspace_projection(taxa_chaves_por_segundo: float) -> list[dict]:
    """Extrapola a taxa medida para espacos de chave reais."""
    linhas = []
    for bits, rotulo in [
        (32, "entropia reduzida (didática)"),
        (56, "DES legado"),
        (64, "chave curta"),
        (128, "MPC-128 / AES-128"),
        (256, "MPC-128 / AES-256"),
    ]:
        esperado = (2.0**bits) / 2  # metade do espaco, em media
        for fator, cenario in [(1, "1 núcleo (medido)"), (1e6, "1 milhão de GPUs")]:
            if fator != 1 and bits < 128:
                continue
            taxa = max(taxa_chaves_por_segundo * fator, 1e-9)
            anos = esperado / taxa / SEGUNDOS_POR_ANO
            linhas.append(
                {
                    "bits": bits,
                    "rotulo": rotulo,
                    "cenario": cenario,
                    "chaves_esperadas": f"2^{bits - 1}",
                    "anos": anos,
                    "anos_fmt": _fmt_anos(anos),
                    "vezes_idade_universo": anos / IDADE_DO_UNIVERSO_ANOS,
                    "viavel": anos < 1,
                }
            )
    return linhas


SUPERESCRITO = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


def _fmt_anos(anos: float) -> str:
    """Tempo em formato brasileiro; acima de um milhao de anos, potencia de dez."""
    if anos < 1 / 365:
        return f"{anos * 365.25 * 24 * 3600:.2f} s".replace(".", ",")
    if anos < 1:
        return f"{anos * 365.25:.1f} dias".replace(".", ",")
    if anos < 1e6:
        return f"{anos:,.0f} anos".replace(",", ".")
    expoente = int(math.floor(math.log10(anos)))
    mantissa = anos / 10**expoente
    return f"{mantissa:.3f}".replace(".", ",") + f"×10{str(expoente).translate(SUPERESCRITO)} anos"


def dictionary_attack(senha_real: str, tentativas: list[str] | None = None) -> dict:
    """Ataque de dicionario contra a senha do cofre (passa pelo PBKDF2).

    Mede o custo por tentativa imposto pelo alongamento de chave.
    """
    lista = list(tentativas or SENHAS_COMUNS)
    if senha_real in lista:
        lista = lista[: lista.index(senha_real) + 1]
    salt, nonce = os.urandom(16), os.urandom(12)
    alvo = derive_keys(senha_real, salt, nonce)[0]

    inicio = time.perf_counter()
    quebrada = None
    for i, tentativa in enumerate(lista, 1):
        if derive_keys(tentativa, salt, nonce)[0] == alvo:
            quebrada = tentativa
            break
    decorrido = time.perf_counter() - inicio
    testadas = i if lista else 0
    por_tentativa = decorrido / testadas if testadas else 0.0

    # Espaco de uma senha forte de 12 caracteres sobre 94 simbolos imprimiveis.
    espaco_forte = 94.0**12
    anos_forte = (espaco_forte / 2) * por_tentativa / SEGUNDOS_POR_ANO

    return {
        "ataque": "dicionario",
        "senhas_testadas": testadas,
        "segundos": round(decorrido, 4),
        "segundos_por_tentativa": round(por_tentativa, 6),
        "tentativas_por_segundo": round(1 / por_tentativa, 1) if por_tentativa else 0.0,
        "senha_quebrada": quebrada,
        "sucesso": quebrada is not None,
        "iteracoes_pbkdf2": KDF_ITERATIONS,
        "custo_relativo_vs_hash_simples": KDF_ITERATIONS,
        "anos_para_senha_forte_12_chars": anos_forte,
        "anos_forte_fmt": _fmt_anos(anos_forte),
    }
