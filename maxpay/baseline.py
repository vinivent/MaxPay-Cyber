"""Camada AES-256 do MaxPay (etapa 2 da arquitetura) e referencia de comparacao.

O AES-256-GCM e usado de duas formas:
  1. como algoritmo selecionavel do cofre (cifragem + integridade);
  2. como linha de base nos experimentos, para dizer se o MPC-128 se comporta
     como uma cifra moderna ou nao.
"""

from __future__ import annotations

import hashlib
import os
import struct

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC = b"MPAES1"
HEADER = struct.Struct(">6s16s12sQ")  # magic, salt, nonce, tamanho
KDF_ITERATIONS = 120_000


def derive_key(secret: str | bytes, salt: bytes) -> bytes:
    raw = secret.encode() if isinstance(secret, str) else secret
    return hashlib.pbkdf2_hmac("sha256", raw, salt, KDF_ITERATIONS, dklen=32)


def encrypt(data: bytes, secret: str | bytes) -> bytes:
    salt, nonce = os.urandom(16), os.urandom(12)
    header = HEADER.pack(MAGIC, salt, nonce, len(data))
    ct = AESGCM(derive_key(secret, salt)).encrypt(nonce, data, header)
    return header + ct


def decrypt(blob: bytes, secret: str | bytes) -> bytes:
    if len(blob) < HEADER.size:
        raise ValueError("envelope truncado")
    header = blob[: HEADER.size]
    magic, salt, nonce, length = HEADER.unpack(header)
    if magic != MAGIC:
        raise ValueError("formato não reconhecido")
    try:
        return AESGCM(derive_key(secret, salt)).decrypt(nonce, blob[HEADER.size :], header)[:length]
    except Exception as exc:  # InvalidTag e afins
        raise ValueError("falha de integridade: chave incorreta ou conteúdo adulterado") from exc


def encrypt_block(key: bytes, block: bytes) -> bytes:
    """AES-256 cru sobre um unico bloco: usado nos testes de avalanche."""
    enc = Cipher(algorithms.AES(key), modes.ECB()).encryptor()
    return enc.update(block) + enc.finalize()


def describe(blob: bytes) -> dict:
    magic, salt, nonce, length = HEADER.unpack(blob[: HEADER.size])
    return {
        "formato": magic.decode(),
        "modo": "GCM",
        "rodadas": 14,
        "difusao": True,
        "salt": salt.hex(),
        "nonce": nonce.hex(),
        "bytes_claros": length,
        "bytes_cifrados": len(blob),
    }
