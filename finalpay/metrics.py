"""Metricas estatisticas usadas nos ataques e na avaliacao da Parte 4."""

from __future__ import annotations

import math

import numpy as np

POPCOUNT = np.array([bin(i).count("1") for i in range(256)], dtype=np.uint8)
# Frequencia de bytes do portugues escrito, usada no ataque de frequencia.
PT_LETTERS = "aeosrindmutcl pvgqbfhzjxkwyAEOSRINDMUTCLPVGQBFHZJXKWY.,\n"


def to_array(data: bytes | np.ndarray) -> np.ndarray:
    if isinstance(data, np.ndarray):
        return data.astype(np.uint8, copy=False).reshape(-1)
    return np.frombuffer(data, dtype=np.uint8)


def hamming_bits(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Numero de bits diferentes por linha entre dois arrays (N, L)."""
    return POPCOUNT[np.asarray(a, np.uint8) ^ np.asarray(b, np.uint8)].sum(axis=-1)


def shannon_entropy(data: bytes | np.ndarray) -> float:
    """Entropia em bits por byte. Maximo teorico = 8,0."""
    arr = to_array(data)
    if arr.size == 0:
        return 0.0
    p = np.bincount(arr, minlength=256) / arr.size
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def chi_square_uniform(data: bytes | np.ndarray) -> dict:
    """Aderencia da distribuicao de bytes a uma uniforme (256 categorias)."""
    arr = to_array(data)
    n = arr.size
    if n == 0:
        return {"chi2": 0.0, "graus_liberdade": 255, "p_valor": 1.0, "uniforme": True}
    observed = np.bincount(arr, minlength=256).astype(float)
    expected = n / 256
    chi2_stat = float(((observed - expected) ** 2 / expected).sum())
    from scipy.stats import chi2

    p = float(chi2.sf(chi2_stat, 255))
    return {
        "chi2": round(chi2_stat, 2),
        "graus_liberdade": 255,
        "p_valor": round(p, 6),
        # p < 0,01 rejeita a hipotese de uniformidade com 99% de confianca
        "uniforme": bool(p >= 0.01),
    }


def index_of_coincidence(data: bytes | np.ndarray) -> float:
    """IC sobre bytes. ~0,0039 (1/256) indica saida indistinguivel de aleatoria."""
    arr = to_array(data)
    n = arr.size
    if n < 2:
        return 0.0
    counts = np.bincount(arr, minlength=256).astype(float)
    return float((counts * (counts - 1)).sum() / (n * (n - 1)))


def monobit(data: bytes | np.ndarray) -> dict:
    """Teste de proporcao de bits 1 (NIST monobit)."""
    bits = np.unpackbits(to_array(data))
    n = bits.size
    if n == 0:
        return {"prop_uns": 0.0, "p_valor": 1.0, "passou": True}
    s = int(bits.sum()) * 2 - n
    p = math.erfc(abs(s) / math.sqrt(2 * n))
    return {"prop_uns": round(float(bits.mean()), 6), "p_valor": round(p, 6), "passou": bool(p >= 0.01)}


def runs_test(data: bytes | np.ndarray) -> dict:
    """Teste de corridas (NIST runs): mede alternancia entre bits."""
    bits = np.unpackbits(to_array(data))
    n = bits.size
    pi = float(bits.mean()) if n else 0.0
    if n < 2 or abs(pi - 0.5) >= 2 / math.sqrt(n):
        return {"corridas": 0, "p_valor": 0.0, "passou": False}
    runs = 1 + int(np.count_nonzero(bits[1:] != bits[:-1]))
    num = abs(runs - 2 * n * pi * (1 - pi))
    p = math.erfc(num / (2 * math.sqrt(2 * n) * pi * (1 - pi)))
    return {"corridas": runs, "p_valor": round(p, 6), "passou": bool(p >= 0.01)}


def serial_correlation(data: bytes | np.ndarray) -> float:
    """Correlacao serial entre bytes consecutivos. ~0 indica ausencia de padrao."""
    arr = to_array(data).astype(np.float64)
    if arr.size < 3:
        return 0.0
    a, b = arr[:-1], arr[1:]
    sa, sb = a.std(), b.std()
    if sa == 0 or sb == 0:
        return 0.0
    return float(np.mean((a - a.mean()) * (b - b.mean())) / (sa * sb))


def block_repetition(data: bytes | np.ndarray, block: int = 16) -> dict:
    """Blocos de 16 B repetidos: evidencia direta de modo ECB."""
    arr = to_array(data)
    n = arr.size // block
    if n == 0:
        return {"blocos": 0, "unicos": 0, "repetidos": 0, "pct_repetidos": 0.0}
    view = arr[: n * block].reshape(n, block)
    unique = len(np.unique(view, axis=0))
    return {
        "blocos": n,
        "unicos": unique,
        "repetidos": n - unique,
        "pct_repetidos": round(100 * (n - unique) / n, 2),
    }


def full_profile(data: bytes | np.ndarray, label: str = "") -> dict:
    """Perfil estatistico completo de uma amostra."""
    arr = to_array(data)
    chi = chi_square_uniform(arr)
    return {
        "rotulo": label,
        "bytes": int(arr.size),
        "entropia_bits_por_byte": round(shannon_entropy(arr), 4),
        "chi2": chi["chi2"],
        "chi2_p_valor": chi["p_valor"],
        "distribuicao_uniforme": chi["uniforme"],
        "indice_coincidencia": round(index_of_coincidence(arr), 6),
        "monobit": monobit(arr),
        "corridas": runs_test(arr),
        "correlacao_serial": round(serial_correlation(arr), 6),
        "repeticao_blocos": block_repetition(arr),
        "histograma": np.bincount(arr, minlength=256).tolist(),
    }
