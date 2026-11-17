"""Ataque estatistico: analise de frequencia e deteccao de padroes (Parte 3).

Tres frentes:
  1. `statistical_profile`  - perfil de entropia, qui-quadrado, IC e testes NIST
                              para texto claro, MPC-128 integro, variante fraca e AES-256.
  2. `frequency_attack`     - recuperacao de texto por analise de frequencia,
                              explorando o fato de que a variante sem difusao e
                              uma substituicao com periodo de 16 bytes.
  3. `ecb_pattern_demo`     - demonstracao visual de padroes remanescentes no modo ECB.
"""

from __future__ import annotations

import base64
import io
import os

import numpy as np
from PIL import Image, ImageDraw

from maxpay import baseline
from maxpay.cipher import BLOCK, DEFAULT_ROUNDS, MODE_CTR, MODE_ECB, SHIFT_ROWS, MaxPayCipher, encrypt
from maxpay.metrics import block_repetition, full_profile

BANCOS = ["Itau", "Bradesco", "Caixa", "Santander", "Nubank", "BB", "Inter", "Safra"]
TIPOS = ["PIX", "TED", "DOC", "BOLETO", "DEBITO", "CREDITO"]


RECORD_LEN = 80  # registro de largura fixa (5 blocos de 16 B), como em mensageria bancaria real
STATUS = ["APROVADO", "PENDENTE", "RECUSADO", "LIQUIDAD"]


def sample_ledger(linhas: int = 400, semente: int = 1) -> bytes:
    """Mensageria bancaria simulada: a carga util que o cofre protege.

    Registros de 80 bytes, multiplo do bloco de 16 B. O layout fixo e o padrao
    de arquivos de remessa bancaria e tambem o que torna o ataque de frequencia
    viavel contra cifras sem difusao.
    """
    rng = np.random.default_rng(semente)
    out = []
    for _ in range(linhas):
        linha = "TX{:06d} {:<7} R${:>12.2f} CT{:04d}-{} {:<9} 2026-11-{:02d} {}".format(
            int(rng.integers(1, 999999)),
            TIPOS[int(rng.integers(0, len(TIPOS)))],
            float(rng.uniform(10, 50000)),
            int(rng.integers(1000, 9999)),
            int(rng.integers(0, 10)),
            BANCOS[int(rng.integers(0, len(BANCOS)))],
            int(rng.integers(1, 29)),
            STATUS[int(rng.integers(0, len(STATUS)))],
        )
        out.append(linha.ljust(RECORD_LEN - 1)[: RECORD_LEN - 1] + "\n")
    return "".join(out).encode()


def _ecb(data: bytes, chave: bytes, rounds: int, diffusion: bool) -> bytes:
    resto = (-len(data)) % BLOCK
    blocos = np.frombuffer(data + b"\x00" * resto, dtype=np.uint8).reshape(-1, BLOCK)
    return MaxPayCipher(chave, rounds, diffusion).encrypt_blocks(blocos).tobytes()


def statistical_profile(linhas: int = 1200) -> dict:
    """Perfil estatistico comparado das varias cifragens do mesmo texto."""
    claro = sample_ledger(linhas)
    senha = "cofre-maxpay-2026"
    chave = os.urandom(32)

    amostras = {
        "texto_claro": claro,
        "mpc_ctr_14_rodadas": encrypt(claro, senha, mode=MODE_CTR)[45:-32],
        "mpc_ecb_14_rodadas": encrypt(claro, senha, mode=MODE_ECB)[45:-32],
        "mpc_ecb_1_rodada_sem_difusao": _ecb(claro, chave, 1, False),
        "aes256_gcm": baseline.encrypt(claro, senha)[42:],
        "urandom": os.urandom(len(claro)),
    }
    return {
        "ataque": "estatistico",
        "bytes_analisados": len(claro),
        "perfis": [full_profile(v, k) for k, v in amostras.items()],
    }


def _posicoes_de_origem(rounds: int) -> np.ndarray:
    """De qual posicao clara vem cada posicao cifrada, sem o MixColumns.

    Kerckhoffs: o atacante conhece o algoritmo, logo conhece o ShiftRows e
    pode compo-lo `rounds` vezes. Com MixColumns ligado esse mapeamento deixa
    de existir, porque cada byte de saida passa a depender de quatro bytes.
    """
    origem = np.arange(BLOCK)
    for _ in range(rounds):
        origem = SHIFT_ROWS[origem]
    return origem


def _ranking(data: bytes, col: int) -> np.ndarray:
    counts = np.bincount(np.frombuffer(data, dtype=np.uint8)[col::BLOCK], minlength=256)
    return np.argsort(-counts, kind="stable")


def frequency_attack(linhas: int = 1500, rounds: int = 1, diffusion: bool = False) -> dict:
    """Recupera texto por analise de frequencia, posicao a posicao dentro do bloco.

    Sem MixColumns cada posicao do bloco permanece uma substituicao
    monoalfabetica independente: a cifra apenas renomeia os bytes e os
    reposiciona. O atacante conhece o formato das mensagens (realista num banco
    que usa registros de largura fixa), levanta a frequencia de referencia e
    remapeia cada coluna por ordem de frequencia.
    """
    alvo = sample_ledger(linhas, semente=1)
    referencia = sample_ledger(linhas, semente=2)  # mesmo formato, conteudo diferente
    chave = os.urandom(32)
    ct = _ecb(alvo, chave, rounds, diffusion)
    n = len(ct)

    origem = _posicoes_de_origem(rounds)
    recuperado = np.zeros(n, dtype=np.uint8)
    ct_arr = np.frombuffer(ct, dtype=np.uint8)
    for col in range(BLOCK):
        mapa = np.zeros(256, dtype=np.uint8)
        mapa[_ranking(ct, col)] = _ranking(referencia, int(origem[col]))
        # o byte recuperado volta para a posicao de onde saiu, nao para a do cifrado
        recuperado[int(origem[col]) :: BLOCK] = mapa[ct_arr[col::BLOCK]]

    claro_arr = np.frombuffer(alvo.ljust(n, b"\x00"), dtype=np.uint8)
    certo = claro_arr == recuperado
    acertos = int(np.count_nonzero(certo))

    # Linha de base honesta: um atacante que nem olha o cifrado e sempre chuta
    # o byte mais comum do formato (espaco). So supera-la indica vazamento real.
    unigrama = float(np.bincount(claro_arr, minlength=256).max()) / n

    # Posicoes do registro de 80 B que ficaram totalmente expostas
    usable = (n // RECORD_LEN) * RECORD_LEN
    por_posicao = certo[:usable].reshape(-1, RECORD_LEN).mean(axis=0)
    expostas = int(np.count_nonzero(por_posicao > 0.9))

    return {
        "ataque": "frequencia",
        "rodadas": rounds,
        "difusao": diffusion,
        "bytes": n,
        "caracteres_corretos": acertos,
        "acuracia_pct": round(100 * acertos / n, 2),
        "linha_base_acaso_pct": round(100 / 256, 2),
        "linha_base_unigrama_pct": round(100 * unigrama, 2),
        "ganho_sobre_unigrama_pp": round(100 * (acertos / n - unigrama), 2),
        "supera_linha_base": bool(acertos / n > unigrama),
        "posicoes_registro": RECORD_LEN,
        "posicoes_expostas": expostas,
        "pct_registro_exposto": round(100 * expostas / RECORD_LEN, 1),
        "acuracia_por_posicao": [round(float(v), 3) for v in por_posicao],
        "trecho_original": alvo[:240].decode("latin-1"),
        "trecho_recuperado": bytes(recuperado[:240]).decode("latin-1"),
        "quebrado": bool(expostas > RECORD_LEN * 0.25),
    }


def _imagem_estruturada(tamanho: int = 256) -> Image.Image:
    img = Image.new("RGB", (tamanho, tamanho), (242, 243, 245))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, tamanho, 54], fill=(16, 28, 48))
    d.rectangle([24, 92, tamanho - 24, 150], fill=(16, 28, 48))
    d.ellipse([96, 176, 160, 240], fill=(0, 102, 204))
    d.text((70, 20), "MAXPAY", fill=(255, 255, 255))
    d.text((40, 112), "COFRE  CRIPTOGRAFICO", fill=(255, 255, 255))
    return img


def _png_b64(arr: np.ndarray, shape: tuple) -> str:
    buf = io.BytesIO()
    Image.fromarray(arr[: shape[0] * shape[1] * 3].reshape(shape), "RGB").save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()


def ecb_pattern_demo(tamanho: int = 256) -> dict:
    """Cifra os pixels de uma imagem estruturada e mostra o que sobrevive.

    O modo ECB preserva a estrutura porque blocos claros iguais produzem blocos
    cifrados iguais. E a prova visual de que confusao sem difusao nao basta.
    """
    img = _imagem_estruturada(tamanho)
    raw = np.array(img, dtype=np.uint8)
    shape = raw.shape
    data = raw.tobytes()
    chave = os.urandom(32)
    senha = "cofre-maxpay-2026"

    variantes = {
        "original": data,
        "ecb_1_rodada_sem_difusao": _ecb(data, chave, 1, False),
        "ecb_14_rodadas": _ecb(data, chave, DEFAULT_ROUNDS, True),
        "ctr_14_rodadas": encrypt(data, senha, mode=MODE_CTR)[45:-32],
    }
    return {
        "ataque": "padroes_ecb",
        "dimensoes": [shape[1], shape[0]],
        "variantes": [
            {
                "nome": nome,
                "png_base64": _png_b64(np.frombuffer(v, dtype=np.uint8), shape),
                "repeticao_blocos": block_repetition(v),
                "entropia": round(full_profile(v)["entropia_bits_por_byte"], 4),
            }
            for nome, v in variantes.items()
        ],
    }
