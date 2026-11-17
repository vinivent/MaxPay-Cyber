"""Esteganografia LSB com posicoes derivadas da chave (etapa 3 da arquitetura).

O payload cifrado e espalhado pelos bits menos significativos dos canais RGB
numa ordem pseudoaleatoria derivada do segredo. Sem a chave nao se sabe nem
onde os bits estao, o que separa esta implementacao do LSB sequencial classico.
"""

from __future__ import annotations

import hashlib
import io
import zlib

import numpy as np
from PIL import Image

MAGIC = b"FP"
HEADER_BYTES = 10  # magic(2) + tamanho(4) + crc32(4)


def _order(secret: str | bytes, n_slots: int) -> np.ndarray:
    raw = secret.encode() if isinstance(secret, str) else secret
    seed = int.from_bytes(hashlib.sha256(b"finalpay/stego/" + raw).digest()[:8], "big")
    return np.random.default_rng(seed).permutation(n_slots)


def _load(image: bytes | str) -> np.ndarray:
    img = Image.open(io.BytesIO(image) if isinstance(image, bytes) else image).convert("RGB")
    return np.array(img, dtype=np.uint8)


def capacity(image: bytes | str) -> int:
    """Bytes de payload que cabem na imagem."""
    return _load(image).size // 8 - HEADER_BYTES


def embed(image: bytes | str, payload: bytes, secret: str | bytes) -> bytes:
    pixels = _load(image)
    flat = pixels.reshape(-1)
    frame = MAGIC + len(payload).to_bytes(4, "big") + zlib.crc32(payload).to_bytes(4, "big") + payload
    bits = np.unpackbits(np.frombuffer(frame, dtype=np.uint8))
    if bits.size > flat.size:
        raise ValueError(f"payload de {len(payload)} B excede a capacidade de {flat.size // 8 - HEADER_BYTES} B")

    slots = _order(secret, flat.size)[: bits.size]
    flat[slots] = (flat[slots] & 0xFE) | bits
    out = io.BytesIO()
    Image.fromarray(flat.reshape(pixels.shape), "RGB").save(out, format="PNG", optimize=False)
    return out.getvalue()


def extract(image: bytes | str, secret: str | bytes) -> bytes:
    flat = _load(image).reshape(-1)
    slots = _order(secret, flat.size)
    head = np.packbits(flat[slots[: HEADER_BYTES * 8]] & 1).tobytes()
    if head[:2] != MAGIC:
        raise ValueError("nenhum payload FinalPay encontrado (ou chave incorreta)")
    length = int.from_bytes(head[2:6], "big")
    crc = int.from_bytes(head[6:10], "big")
    total = (HEADER_BYTES + length) * 8
    if total > flat.size:
        raise ValueError("cabeçalho inconsistente: imagem truncada ou alterada")
    payload = np.packbits(flat[slots[HEADER_BYTES * 8 : total]] & 1).tobytes()
    if zlib.crc32(payload) != crc:
        raise ValueError("payload corrompido: a imagem foi alterada após a ocultação")
    return payload


def embed_sequencial(image: bytes | str, payload: bytes) -> bytes:
    """LSB sequencial sem chave: a versao ingenua, usada so para comparacao.

    Preenche os bits a partir do primeiro pixel, o que cria a assinatura que o
    ataque de qui-quadrado procura.
    """
    pixels = _load(image)
    flat = pixels.reshape(-1)
    bits = np.unpackbits(np.frombuffer(payload, dtype=np.uint8))
    if bits.size > flat.size:
        raise ValueError("payload maior que a capacidade")
    flat[: bits.size] = (flat[: bits.size] & 0xFE) | bits
    out = io.BytesIO()
    Image.fromarray(flat.reshape(pixels.shape), "RGB").save(out, format="PNG")
    return out.getvalue()


def metrics(original: bytes | str, stego: bytes | str) -> dict:
    a, b = _load(original).astype(np.int32), _load(stego).astype(np.int32)
    if a.shape != b.shape:
        raise ValueError("as imagens precisam ter as mesmas dimensões")
    mse = float(np.mean((a - b) ** 2))
    changed = int(np.count_nonzero(a != b))
    return {
        "mse": round(mse, 6),
        "psnr_db": round(float("inf") if mse == 0 else 10 * np.log10(255**2 / mse), 2),
        "subpixels_alterados": changed,
        "subpixels_totais": int(a.size),
        "pct_alterado": round(100 * changed / a.size, 3),
        "desvio_maximo": int(np.max(np.abs(a - b))),
    }


def _chi(flat: np.ndarray) -> dict:
    counts = np.bincount(flat, minlength=256).astype(float)
    even, odd = counts[0::2], counts[1::2]
    pares = even + odd
    valido = pares > 4
    esperado = pares[valido] / 2
    chi = float(np.sum((even[valido] - esperado) ** 2 / esperado))
    df = int(valido.sum())
    from scipy.stats import chi2

    p_estego = float(chi2.sf(chi, df)) if df else 0.0
    return {
        "qui_quadrado": round(chi, 2),
        "graus_liberdade": df,
        "p_estego": round(p_estego, 6),
        "suspeita": "alta" if p_estego > 0.5 else "baixa",
    }


def chi_square_attack(image: bytes | str) -> dict:
    """Esteganalise de Westfeld: compara a frequencia dos pares (2k, 2k+1).

    Em LSB aleatorio os dois membros de cada par tendem a se igualar. Quanto
    maior `p_estego`, maior a suspeita de ocultacao.
    """
    return _chi(_load(image).reshape(-1))


def chi_square_scan(image: bytes | str, segmentos: int = 20) -> list[dict]:
    """Varredura por segmento: e assim que o ataque real encontra LSB sequencial.

    O payload sequencial se concentra no inicio da imagem e deixa os primeiros
    segmentos com suspeita alta e o restante limpo. O payload espalhado por
    chave nao produz esse degrau.
    """
    flat = _load(image).reshape(-1)
    n = flat.size // segmentos
    saida = []
    for i in range(segmentos):
        r = _chi(flat[i * n : (i + 1) * n])
        saida.append({"segmento": i, "inicio_pct": round(100 * i / segmentos, 1), **r})
    return saida
