"""MPC-128: cifra de bloco do MaxPay (rede SPN, blocos de 128 bits).

Projeto proprio dentro de uma familia conhecida. A estrutura (SPN com S-box
baseada em inverso multiplicativo, permutacao de bytes e difusao por matriz MDS)
e a mesma do AES, porque e ela que garante as boas propriedades. Os tres
componentes, porem, sao escolha nossa e nao coincidem com os do AES:

  * S-box      inverso em GF(2^8) com transformacao afim propria
               (rotacoes 0,1,2,3,5 e constante 0x0D). Difere da do AES nas 256
               posicoes, mantendo uniformidade diferencial 4 e zero ponto fixo.
  * Permutacao deslocamentos de linha (0,2,3,1), contra (0,1,2,3) do AES.
  * Difusao    matriz circulante (1,1,3,2), verificada MDS, contra (2,3,1,1).

Cada escolha foi encontrada por busca e so adotada apos verificacao: bijecao,
ausencia de ponto fixo, uniformidade diferencial e propriedade MDS.
O escalonamento de chaves e inteiramente diferente do Rijndael (HKDF sobre
HMAC-SHA256), assim como a derivacao por mensagem e o envelope autenticado.

Estrutura por rodada, atendendo aos requisitos da Parte 2 do projeto:
  AddRoundKey  -> XOR com a subchave (confusao dependente da chave)
  SubBytes     -> substituicao nao-linear via S-box em GF(2^8)
  ShiftRows    -> permutacao de bytes
  MixColumns   -> difusao linear em GF(2^8) (matriz MDS)

A chave nunca e fixa: cada mensagem gera salt e nonce aleatorios que alimentam
a derivacao das subchaves (ver `derive_keys` e `expand_round_keys`).

Tudo opera sobre arrays numpy (N, 16) para que os experimentos de ataque
consigam cifrar milhoes de blocos em tempo util.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import struct

import numpy as np

BLOCK = 16
DEFAULT_ROUNDS = 14

# Parametros do projeto da cifra. Ver `scripts` do relatorio para a busca que
# os produziu; cada um e verificado no proprio modulo de testes.
SBOX_ROTACOES = (0, 1, 2, 3, 5)
SBOX_CONSTANTE = 0x0D
DESLOCAMENTOS = (0, 2, 3, 1)
MDS = (1, 1, 3, 2)
INV_MDS = (11, 14, 9, 13)
MAGIC = b"MPAY01"
HEADER = struct.Struct(">6sBBB16s12sQ")  # magic, modo, rodadas, flags, salt, nonce, tamanho
TAG_LEN = 32
KDF_ITERATIONS = 120_000

MODE_CTR = 1
MODE_ECB = 2
FLAG_DIFFUSION = 1


# --------------------------------------------------------------------------
# GF(2^8): tabelas de log/antilog usadas na S-box e no MixColumns
# --------------------------------------------------------------------------
def _gf_tables() -> tuple[np.ndarray, np.ndarray]:
    exp = np.zeros(512, dtype=np.uint8)
    log = np.zeros(256, dtype=np.uint8)
    x = 1
    for i in range(255):
        exp[i] = x
        log[x] = i
        x ^= (x << 1) ^ (0x1B if x & 0x80 else 0)  # x <- x * 3 no corpo
        x &= 0xFF
    exp[255:] = exp[:257]
    return exp, log


GF_EXP, GF_LOG = _gf_tables()


def gf_mul(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return int(GF_EXP[(int(GF_LOG[a]) + int(GF_LOG[b])) % 255])


def _build_sbox() -> np.ndarray:
    """Inverso multiplicativo em GF(2^8) seguido de transformacao afim propria.

    O inverso e o que da a nao-linearidade e a uniformidade diferencial 4; a
    afim embaralha a estrutura algebrica e elimina pontos fixos. As rotacoes e
    a constante sao escolha nossa, verificadas em `tests/`.
    """
    sbox = np.zeros(256, dtype=np.uint8)
    for i in range(256):
        inv = 0 if i == 0 else int(GF_EXP[255 - int(GF_LOG[i])])
        y = 0
        for k in SBOX_ROTACOES:
            y ^= ((inv << k) | (inv >> (8 - k))) & 0xFF
        sbox[i] = y ^ SBOX_CONSTANTE
    return sbox


def _invert(table: np.ndarray) -> np.ndarray:
    inv = np.zeros(256, dtype=np.uint8)
    inv[table] = np.arange(256, dtype=np.uint8)
    return inv


SBOX = _build_sbox()
INV_SBOX = _invert(SBOX)

def _permutacao() -> np.ndarray:
    """Permutacao de bytes sobre o estado 4x4 em ordem coluna-maior.

    Cada linha desliza por `DESLOCAMENTOS[linha]` colunas. Como os quatro
    deslocamentos sao distintos, cada coluna de saida recebe um byte de cada
    coluna de entrada, que e o que permite a difusao se completar em 2 rodadas.
    """
    perm = np.zeros(16, dtype=np.intp)
    for coluna in range(4):
        for linha in range(4):
            perm[linha + 4 * coluna] = linha + 4 * ((coluna + DESLOCAMENTOS[linha]) % 4)
    return perm


SHIFT_ROWS = _permutacao()
INV_SHIFT_ROWS = np.argsort(SHIFT_ROWS).astype(np.intp)


def _tabela_multiplicacao() -> np.ndarray:
    """Tabela 256x256 de multiplicacao em GF(2^8), para o MixColumns vetorizado."""
    log = GF_LOG.astype(np.int32)
    tab = GF_EXP[(log[:, None] + log[None, :]) % 255].astype(np.uint8)
    tab[0, :] = 0
    tab[:, 0] = 0
    return tab


MUL = _tabela_multiplicacao()


def _mix(state: np.ndarray, coeffs: tuple[int, int, int, int]) -> np.ndarray:
    a, b, c, d = (MUL[k] for k in coeffs)
    s = state.reshape(*state.shape[:-1], 4, 4)  # (..., coluna, linha)
    r0, r1, r2, r3 = s[..., 0], s[..., 1], s[..., 2], s[..., 3]
    out = np.empty_like(s)
    out[..., 0] = a[r0] ^ b[r1] ^ c[r2] ^ d[r3]
    out[..., 1] = d[r0] ^ a[r1] ^ b[r2] ^ c[r3]
    out[..., 2] = c[r0] ^ d[r1] ^ a[r2] ^ b[r3]
    out[..., 3] = b[r0] ^ c[r1] ^ d[r2] ^ a[r3]
    return out.reshape(state.shape)


def mix_columns(state: np.ndarray) -> np.ndarray:
    return _mix(state, MDS)


def inv_mix_columns(state: np.ndarray) -> np.ndarray:
    return _mix(state, INV_MDS)


# --------------------------------------------------------------------------
# Derivacao de chaves (dinamica: depende do salt e do nonce da mensagem)
# --------------------------------------------------------------------------
def _hkdf(key: bytes, info: bytes, length: int) -> bytes:
    out, block, counter = b"", b"", 1
    while len(out) < length:
        block = hmac.new(key, block + info + bytes([counter]), hashlib.sha256).digest()
        out += block
        counter += 1
    return out[:length]


def derive_keys(secret: str | bytes, salt: bytes, nonce: bytes) -> tuple[bytes, bytes]:
    """Material de chave da mensagem: (chave de cifragem, chave de integridade)."""
    raw = secret.encode() if isinstance(secret, str) else secret
    master = hashlib.pbkdf2_hmac("sha256", raw, salt, KDF_ITERATIONS, dklen=32)
    material = _hkdf(master, b"maxpay/v1/" + nonce, 64)
    return material[:32], material[32:]


def expand_round_keys(enc_key: bytes, rounds: int) -> np.ndarray:
    """Subchaves de rodada: array (rounds + 1, 16)."""
    raw = _hkdf(enc_key, b"maxpay/v1/rk/%d" % rounds, (rounds + 1) * BLOCK)
    return np.frombuffer(raw, dtype=np.uint8).reshape(rounds + 1, BLOCK)


# --------------------------------------------------------------------------
# Primitiva de bloco
# --------------------------------------------------------------------------
class MaxPayCipher:
    """Cifra de bloco de 128 bits.

    `diffusion=False` desliga o MixColumns e produz a variante didatica
    vulneravel usada nos experimentos de ataque.
    """

    def __init__(self, enc_key: bytes, rounds: int = DEFAULT_ROUNDS, diffusion: bool = True):
        if len(enc_key) != 32:
            raise ValueError("a chave de cifragem precisa ter 32 bytes")
        if not 1 <= rounds <= 32:
            raise ValueError("rounds deve estar entre 1 e 32")
        self.rounds = rounds
        self.diffusion = diffusion
        self.round_keys = expand_round_keys(enc_key, rounds)

    # -- nucleo vetorizado -------------------------------------------------
    def _encrypt(self, state: np.ndarray, rk: np.ndarray) -> np.ndarray:
        state = state ^ rk[..., 0, :]
        for r in range(1, self.rounds + 1):
            state = SBOX[state]
            state = state[..., SHIFT_ROWS]
            if self.diffusion and r != self.rounds:
                state = mix_columns(state)
            state = state ^ rk[..., r, :]
        return state

    def _decrypt(self, state: np.ndarray, rk: np.ndarray) -> np.ndarray:
        for r in range(self.rounds, 0, -1):
            state = state ^ rk[..., r, :]
            if self.diffusion and r != self.rounds:
                state = inv_mix_columns(state)
            state = state[..., INV_SHIFT_ROWS]
            state = INV_SBOX[state]
        return state ^ rk[..., 0, :]

    def encrypt_blocks(self, blocks: np.ndarray) -> np.ndarray:
        return self._encrypt(np.asarray(blocks, dtype=np.uint8), self.round_keys)

    def decrypt_blocks(self, blocks: np.ndarray) -> np.ndarray:
        return self._decrypt(np.asarray(blocks, dtype=np.uint8), self.round_keys)

    def encrypt_block(self, block: bytes) -> bytes:
        return self.encrypt_blocks(np.frombuffer(block, dtype=np.uint8)[None, :])[0].tobytes()

    def decrypt_block(self, block: bytes) -> bytes:
        return self.decrypt_blocks(np.frombuffer(block, dtype=np.uint8)[None, :])[0].tobytes()

    def trace_rounds(self, blocks: np.ndarray) -> list[np.ndarray]:
        """Estado apos cada rodada (inclui a rodada 0 = AddRoundKey inicial).

        Usado para medir a avalanche rodada a rodada.
        """
        state = np.atleast_2d(np.asarray(blocks, dtype=np.uint8)) ^ self.round_keys[0]
        out = [state.copy()]
        for r in range(1, self.rounds + 1):
            state = SBOX[state][..., SHIFT_ROWS]
            if self.diffusion and r != self.rounds:
                state = mix_columns(state)
            state = state ^ self.round_keys[r]
            out.append(state.copy())
        return out

    # -- modo contador -----------------------------------------------------
    def keystream(self, nonce: bytes, n_blocks: int, offset: int = 0) -> np.ndarray:
        counters = np.arange(offset, offset + n_blocks, dtype=">u8")
        ctr = np.zeros((n_blocks, BLOCK), dtype=np.uint8)
        ctr[:, :8] = np.frombuffer(nonce[:8], dtype=np.uint8)
        ctr[:, 8:] = counters.view(np.uint8).reshape(n_blocks, 8)
        return self.encrypt_blocks(ctr)


def encrypt_many_keys(block: bytes, round_keys: np.ndarray, rounds: int, diffusion: bool = True) -> np.ndarray:
    """Cifra o mesmo bloco sob N conjuntos de subchaves ((N, rounds+1, 16))."""
    cipher = MaxPayCipher.__new__(MaxPayCipher)
    cipher.rounds, cipher.diffusion = rounds, diffusion
    state = np.broadcast_to(np.frombuffer(block, dtype=np.uint8), (len(round_keys), BLOCK))
    return cipher._encrypt(state.copy(), round_keys)


# --------------------------------------------------------------------------
# Envelope de mensagem (cifragem autenticada)
# --------------------------------------------------------------------------
def _xor_stream(data: bytes, cipher: MaxPayCipher, nonce: bytes) -> bytes:
    n_blocks = (len(data) + BLOCK - 1) // BLOCK
    if n_blocks == 0:
        return b""
    stream = cipher.keystream(nonce, n_blocks).reshape(-1)[: len(data)]
    return (np.frombuffer(data, dtype=np.uint8) ^ stream).tobytes()


def _pad(data: bytes) -> bytes:
    n = BLOCK - (len(data) % BLOCK)
    return data + bytes([n]) * n


def _unpad(data: bytes) -> bytes:
    if not data or len(data) % BLOCK:
        raise ValueError("texto cifrado com tamanho inválido")
    n = data[-1]
    if not 1 <= n <= BLOCK or data[-n:] != bytes([n]) * n:
        raise ValueError("padding inválido")
    return data[:-n]


def encrypt(
    data: bytes,
    secret: str | bytes,
    *,
    mode: int = MODE_CTR,
    rounds: int = DEFAULT_ROUNDS,
    diffusion: bool = True,
) -> bytes:
    """Cifra `data` e devolve o envelope autenticado (cabecalho + ct + tag)."""
    salt, nonce = os.urandom(16), os.urandom(12)
    enc_key, mac_key = derive_keys(secret, salt, nonce)
    cipher = MaxPayCipher(enc_key, rounds, diffusion)

    if mode == MODE_CTR:
        ct = _xor_stream(data, cipher, nonce)
    elif mode == MODE_ECB:
        blocks = np.frombuffer(_pad(data), dtype=np.uint8).reshape(-1, BLOCK)
        ct = cipher.encrypt_blocks(blocks).tobytes()
    else:
        raise ValueError("modo desconhecido")

    flags = FLAG_DIFFUSION if diffusion else 0
    header = HEADER.pack(MAGIC, mode, rounds, flags, salt, nonce, len(data))
    tag = hmac.new(mac_key, header + ct, hashlib.sha256).digest()
    return header + ct + tag


def decrypt(blob: bytes, secret: str | bytes) -> bytes:
    """Verifica a integridade e decifra o envelope. Levanta ValueError se adulterado."""
    if len(blob) < HEADER.size + TAG_LEN:
        raise ValueError("envelope truncado")
    header = blob[: HEADER.size]
    ct, tag = blob[HEADER.size : -TAG_LEN], blob[-TAG_LEN:]
    magic, mode, rounds, flags, salt, nonce, length = HEADER.unpack(header)
    if magic != MAGIC:
        raise ValueError("formato não reconhecido")

    enc_key, mac_key = derive_keys(secret, salt, nonce)
    if not hmac.compare_digest(hmac.new(mac_key, header + ct, hashlib.sha256).digest(), tag):
        raise ValueError("falha de integridade: chave incorreta ou conteúdo adulterado")

    cipher = MaxPayCipher(enc_key, rounds, bool(flags & FLAG_DIFFUSION))
    if mode == MODE_CTR:
        return _xor_stream(ct, cipher, nonce)[:length]
    blocks = np.frombuffer(ct, dtype=np.uint8).reshape(-1, BLOCK)
    return _unpad(cipher.decrypt_blocks(blocks).tobytes())


def describe(blob: bytes) -> dict:
    """Metadados publicos do envelope, sem precisar da chave."""
    magic, mode, rounds, flags, salt, nonce, length = HEADER.unpack(blob[: HEADER.size])
    return {
        "formato": magic.decode(),
        "modo": "CTR" if mode == MODE_CTR else "ECB",
        "rodadas": rounds,
        "difusao": bool(flags & FLAG_DIFFUSION),
        "salt": salt.hex(),
        "nonce": nonce.hex(),
        "bytes_claros": length,
        "bytes_cifrados": len(blob),
    }
