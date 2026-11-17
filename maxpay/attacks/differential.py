"""Ataque diferencial e efeito avalanche (Parte 3 e Parte 4).

Mede o que acontece com a saida quando um unico bit da entrada (ou da chave)
muda. Uma cifra solida deve responder com ~50% dos bits de saida invertidos e
sem nenhuma diferenca de saida mais provavel que as outras.
"""

from __future__ import annotations

import os

import numpy as np

from maxpay import baseline
from maxpay.cipher import BLOCK, DEFAULT_ROUNDS, SBOX, MaxPayCipher
from maxpay.metrics import hamming_bits

BITS = BLOCK * 8  # 128


def _random_blocks(n: int, rng: np.random.Generator) -> np.ndarray:
    return rng.integers(0, 256, size=(n, BLOCK), dtype=np.uint8)


def _flip(blocks: np.ndarray, bit: int | np.ndarray) -> np.ndarray:
    """Inverte o bit de indice `bit` (0 = MSB do byte 0) em cada bloco."""
    out = blocks.copy()
    idx = np.asarray(bit)
    linhas = np.arange(len(blocks))
    out[linhas, idx // 8] ^= (0x80 >> (idx % 8)).astype(np.uint8)
    return out


def avalanche(
    rounds: int = DEFAULT_ROUNDS,
    diffusion: bool = True,
    amostras: int = 4096,
    semente: int = 2026,
) -> dict:
    """Avalanche de texto claro: 1 bit alterado na entrada -> bits alterados na saida."""
    rng = np.random.default_rng(semente)
    cipher = MaxPayCipher(os.urandom(32), rounds, diffusion)

    p1 = _random_blocks(amostras, rng)
    bits_alterados = rng.integers(0, BITS, size=amostras)
    p2 = _flip(p1, bits_alterados)
    d = hamming_bits(cipher.encrypt_blocks(p1), cipher.encrypt_blocks(p2))

    # Curva por rodada: quando a difusao se completa?
    t1, t2 = cipher.trace_rounds(p1), cipher.trace_rounds(p2)
    por_rodada = [
        {"rodada": r, "bits_alterados": round(float(hamming_bits(a, b).mean()), 3),
         "pct": round(float(hamming_bits(a, b).mean()) / BITS * 100, 2)}
        for r, (a, b) in enumerate(zip(t1, t2))
    ]

    return {
        "rodadas": rounds,
        "difusao": diffusion,
        "amostras": amostras,
        "media_bits": round(float(d.mean()), 3),
        "media_pct": round(float(d.mean()) / BITS * 100, 2),
        "desvio_padrao": round(float(d.std()), 3),
        "minimo": int(d.min()),
        "maximo": int(d.max()),
        "ideal_bits": BITS / 2,
        "histograma": np.bincount(d, minlength=BITS + 1).tolist(),
        "por_rodada": por_rodada,
    }


def key_avalanche(rounds: int = DEFAULT_ROUNDS, diffusion: bool = True, amostras: int = 1024) -> dict:
    """Avalanche de chave: 1 bit alterado na chave -> bits alterados na saida."""
    rng = np.random.default_rng(99)
    blocos = _random_blocks(amostras, rng)
    distancias = []
    for i in range(amostras):
        k1 = bytearray(os.urandom(32))
        k2 = bytearray(k1)
        bit = int(rng.integers(0, 256))
        k2[bit // 8] ^= 0x80 >> (bit % 8)
        c1 = MaxPayCipher(bytes(k1), rounds, diffusion).encrypt_blocks(blocos[i : i + 1])
        c2 = MaxPayCipher(bytes(k2), rounds, diffusion).encrypt_blocks(blocos[i : i + 1])
        distancias.append(int(hamming_bits(c1, c2)[0]))
    d = np.array(distancias)
    return {
        "amostras": amostras,
        "media_bits": round(float(d.mean()), 3),
        "media_pct": round(float(d.mean()) / BITS * 100, 2),
        "desvio_padrao": round(float(d.std()), 3),
    }


def sac_matrix(rounds: int = DEFAULT_ROUNDS, diffusion: bool = True, amostras: int = 512) -> dict:
    """Criterio estrito de avalanche (SAC).

    matriz[i][j] = P(bit j da saida inverte | bit i da entrada invertido).
    O ideal e 0,5 em todas as 16.384 celulas.
    """
    rng = np.random.default_rng(7)
    cipher = MaxPayCipher(os.urandom(32), rounds, diffusion)
    matriz = np.zeros((BITS, BITS), dtype=np.float32)
    for i in range(BITS):
        p1 = _random_blocks(amostras, rng)
        p2 = _flip(p1, np.full(amostras, i))
        diff = cipher.encrypt_blocks(p1) ^ cipher.encrypt_blocks(p2)
        matriz[i] = np.unpackbits(diff, axis=1).mean(axis=0)
    desvio = np.abs(matriz - 0.5)
    # Sao 128x128 testes simultaneos: sem correcao, o maior desvio estoura o
    # limite de 3 sigma so pelo numero de celulas. Usamos Bonferroni a 5%.
    from scipy.stats import norm

    celulas = BITS * BITS
    sigma = 0.5 / np.sqrt(amostras)
    limite = float(norm.ppf(1 - 0.025 / celulas) * sigma)
    return {
        "rodadas": rounds,
        "difusao": diffusion,
        "amostras_por_celula": amostras,
        "matriz": matriz.round(4).tolist(),
        "media": round(float(matriz.mean()), 5),
        "desvio_medio": round(float(desvio.mean()), 5),
        "desvio_maximo": round(float(desvio.max()), 5),
        "sigma": round(float(sigma), 5),
        "limite_bonferroni": round(limite, 5),
        "celulas_fora_do_limite": int((desvio > limite).sum()),
        "celulas": celulas,
        "satisfaz_sac": bool(desvio.max() <= limite),
    }


def sbox_ddt() -> dict:
    """Tabela de distribuicao de diferencas da S-box.

    O maior valor fora da linha 0 limita a probabilidade de qualquer
    caracteristica diferencial de uma rodada.
    """
    x = np.arange(256, dtype=np.uint8)
    tabela = np.zeros((256, 256), dtype=np.int32)
    for dx in range(1, 256):
        dy = SBOX[x] ^ SBOX[x ^ dx]
        tabela[dx] = np.bincount(dy, minlength=256)
    maior = int(tabela[1:].max())
    return {
        "maior_entrada": maior,
        "probabilidade_maxima": maior / 256,
        "log2_probabilidade": round(float(np.log2(maior / 256)), 3),
        "entradas_distintas": sorted(set(tabela[1:].reshape(-1).tolist())),
        "uniformidade_diferencial": maior,
        "linhas_amostra": tabela[1:9, :16].tolist(),
    }


def differential_distinguisher(
    rounds: int = DEFAULT_ROUNDS,
    diffusion: bool = True,
    amostras: int = 200_000,
    delta_byte: int = 0x01,
    semente: int = 11,
) -> dict:
    """Procura uma diferenca de saida mais provavel que o acaso.

    Aplica sempre a mesma diferenca de entrada e verifica se alguma diferenca
    de saida se repete. Num sistema solido a mais frequente aparece ~1 vez em
    `amostras`; se aparecer muito mais, existe uma caracteristica diferencial
    exploravel.
    """
    rng = np.random.default_rng(semente)
    cipher = MaxPayCipher(os.urandom(32), rounds, diffusion)
    delta = np.zeros(BLOCK, dtype=np.uint8)
    delta[0] = delta_byte

    p1 = _random_blocks(amostras, rng)
    diff = cipher.encrypt_blocks(p1) ^ cipher.encrypt_blocks(p1 ^ delta)
    vistos, contagens = np.unique(diff, axis=0, return_counts=True)
    topo = int(contagens.max())
    melhor = vistos[int(contagens.argmax())]

    p_observada = topo / amostras
    p_aleatoria = 1 / 2**BITS
    return {
        "rodadas": rounds,
        "difusao": diffusion,
        "amostras": amostras,
        "delta_entrada": delta.tobytes().hex(),
        "melhor_delta_saida": melhor.tobytes().hex(),
        "ocorrencias": topo,
        "probabilidade_observada": p_observada,
        "diferencas_distintas": int(len(vistos)),
        "pct_saidas_distintas": round(100 * len(vistos) / amostras, 2),
        "log2_vantagem": round(float(np.log2(p_observada / p_aleatoria)), 1),
        # com saida aleatoria o topo fica em 1-2 ocorrencias
        "distinguivel": bool(topo > 8),
    }


def differential_profile(amostras: int = 4096) -> dict:
    """Comparacao completa: MPC-128 integro, variante fraca e AES-256."""
    cheio = avalanche(DEFAULT_ROUNDS, True, amostras)
    fraco = avalanche(1, False, amostras)
    medio = avalanche(3, True, amostras)
    # Mesmas 14 rodadas, so que sem MixColumns: isola o efeito da difusao do
    # efeito do numero de rodadas.
    sem_difusao = avalanche(DEFAULT_ROUNDS, False, amostras)

    # AES-256 nas mesmas condicoes
    rng = np.random.default_rng(2026)
    chave = os.urandom(32)
    p1 = _random_blocks(amostras, rng)
    bits = rng.integers(0, BITS, size=amostras)
    p2 = _flip(p1, bits)
    c1 = np.frombuffer(b"".join(baseline.encrypt_block(chave, b.tobytes()) for b in p1), dtype=np.uint8).reshape(-1, BLOCK)
    c2 = np.frombuffer(b"".join(baseline.encrypt_block(chave, b.tobytes()) for b in p2), dtype=np.uint8).reshape(-1, BLOCK)
    d_aes = hamming_bits(c1, c2)

    return {
        "ataque": "diferencial",
        "mpc_integro": cheio,
        "mpc_3_rodadas": medio,
        "mpc_fraco": fraco,
        "mpc_sem_difusao_14_rodadas": sem_difusao,
        "aes256": {
            "media_bits": round(float(d_aes.mean()), 3),
            "media_pct": round(float(d_aes.mean()) / BITS * 100, 2),
            "desvio_padrao": round(float(d_aes.std()), 3),
            "histograma": np.bincount(d_aes, minlength=BITS + 1).tolist(),
        },
        "avalanche_chave": key_avalanche(),
        "ddt_sbox": sbox_ddt(),
        "distinguidor_integro": differential_distinguisher(DEFAULT_ROUNDS, True, 100_000),
        "distinguidor_fraco": differential_distinguisher(1, False, 100_000),
    }
