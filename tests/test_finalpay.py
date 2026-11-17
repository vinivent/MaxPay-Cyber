"""Testes do FinalPay.

Cobrem o que nao pode quebrar sem ninguem perceber: round-trip da cifra,
deteccao de adulteracao, esteganografia, e o fato de que os tres ataques
falham contra a cifra integra e funcionam contra a variante enfraquecida.

    pytest -q
"""

from __future__ import annotations

import io
import os

import numpy as np
import pytest
from PIL import Image

from finalpay import baseline, cipher, detect, events, lake, metrics, stego
from finalpay.attacks import brute_force, differential, statistical


# --------------------------------------------------------------------------
# Cifra
# --------------------------------------------------------------------------
@pytest.mark.parametrize("modo", [cipher.MODE_CTR, cipher.MODE_ECB])
@pytest.mark.parametrize("n", [0, 1, 15, 16, 17, 4096])
def test_round_trip(modo, n):
    dados = os.urandom(n)
    assert cipher.decrypt(cipher.encrypt(dados, "senha", mode=modo), "senha") == dados


@pytest.mark.parametrize("rodadas,difusao", [(14, True), (3, True), (1, False), (32, True)])
def test_bloco_e_inverso(rodadas, difusao):
    c = cipher.FinalPayCipher(os.urandom(32), rodadas, difusao)
    b = os.urandom(16)
    assert c.decrypt_block(c.encrypt_block(b)) == b


def test_chave_dinamica():
    """Mesma senha e mesmo texto devem produzir envelopes diferentes."""
    a = cipher.encrypt(b"PIX 250,00", "senha")
    b = cipher.encrypt(b"PIX 250,00", "senha")
    assert a != b
    assert cipher.decrypt(a, "senha") == cipher.decrypt(b, "senha") == b"PIX 250,00"


def test_adulteracao_detectada():
    blob = bytearray(cipher.encrypt(b"transferencia de 1500 reais", "senha"))
    blob[-40] ^= 0x01  # um bit no texto cifrado
    with pytest.raises(ValueError, match="integridade"):
        cipher.decrypt(bytes(blob), "senha")


def test_chave_errada_rejeitada():
    with pytest.raises(ValueError):
        cipher.decrypt(cipher.encrypt(b"x", "certa"), "errada")


def test_sbox_bem_formada():
    assert len(set(cipher.SBOX.tolist())) == 256, "S-box precisa ser bijetiva"
    assert not any(i == v for i, v in enumerate(cipher.SBOX)), "sem pontos fixos"
    assert np.array_equal(cipher.INV_SBOX[cipher.SBOX], np.arange(256))


def test_permutacao_e_bijetiva():
    assert sorted(cipher.SHIFT_ROWS.tolist()) == list(range(16))
    assert np.array_equal(cipher.SHIFT_ROWS[cipher.INV_SHIFT_ROWS], np.arange(16))


def test_chave_invalida():
    with pytest.raises(ValueError):
        cipher.FinalPayCipher(b"curta", 14)
    with pytest.raises(ValueError):
        cipher.FinalPayCipher(os.urandom(32), 0)


def test_aes_round_trip_e_integridade():
    dados = os.urandom(2000)
    assert baseline.decrypt(baseline.encrypt(dados, "s"), "s") == dados
    with pytest.raises(ValueError):
        baseline.decrypt(baseline.encrypt(dados, "s"), "outra")


# --------------------------------------------------------------------------
# Esteganografia
# --------------------------------------------------------------------------
@pytest.fixture(scope="module")
def imagem() -> bytes:
    arr = np.random.default_rng(7).integers(0, 256, (160, 220, 3), dtype=np.uint8)
    buf = io.BytesIO()
    Image.fromarray(arr, "RGB").save(buf, "PNG")
    return buf.getvalue()


def test_estego_round_trip(imagem):
    carga = cipher.encrypt(b"segredo bancario", "k")
    marcada = stego.embed(imagem, carga, "k")
    assert stego.extract(marcada, "k") == carga


def test_estego_exige_a_chave(imagem):
    marcada = stego.embed(imagem, b"conteudo", "certa")
    with pytest.raises(ValueError):
        stego.extract(marcada, "errada")


def test_estego_detecta_imagem_alterada(imagem):
    """O CRC precisa acusar adulteracao e recompressao com perdas.

    Virar um pixel escolhido a dedo nao serve de teste: as posicoes do payload
    sao derivadas da chave, entao um pixel qualquer quase certamente nao guarda
    bit nenhum. Alteramos uma fracao da imagem e, depois, a recomprimimos.
    """
    marcada = stego.embed(imagem, b"conteudo sensivel do cofre", "k")
    arr = np.array(Image.open(io.BytesIO(marcada)).convert("RGB"))

    rng = np.random.default_rng(1)
    plano = arr.reshape(-1)
    alvos = rng.choice(plano.size, size=plano.size // 5, replace=False)
    plano[alvos] ^= 1
    buf = io.BytesIO()
    Image.fromarray(plano.reshape(arr.shape), "RGB").save(buf, "PNG")
    with pytest.raises(ValueError):
        stego.extract(buf.getvalue(), "k")

    jpeg = io.BytesIO()
    Image.open(io.BytesIO(marcada)).convert("RGB").save(jpeg, "JPEG", quality=85)
    with pytest.raises(ValueError):
        stego.extract(jpeg.getvalue(), "k")


def test_estego_respeita_capacidade(imagem):
    with pytest.raises(ValueError, match="excede"):
        stego.embed(imagem, os.urandom(stego.capacity(imagem) + 1), "k")


def test_estego_quase_imperceptivel(imagem):
    marcada = stego.embed(imagem, os.urandom(400), "k")
    q = stego.metrics(imagem, marcada)
    assert q["desvio_maximo"] == 1, "LSB nunca deve mudar um canal em mais de 1"
    assert q["psnr_db"] > 50


# --------------------------------------------------------------------------
# Ataques: devem falhar contra a cifra integra
# --------------------------------------------------------------------------
def test_avalanche_integra_vs_fraca():
    integra = differential.avalanche(cipher.DEFAULT_ROUNDS, True, 2048)
    fraca = differential.avalanche(1, False, 2048)
    assert abs(integra["media_pct"] - 50) < 1.5, "deve ficar colado em 50%"
    assert fraca["media_pct"] < 10, "sem difusao a avalanche precisa falhar"


def test_difusao_se_completa_em_poucas_rodadas():
    curva = differential.avalanche(cipher.DEFAULT_ROUNDS, True, 2048)["por_rodada"]
    assert curva[1]["pct"] < 20, "uma rodada ainda nao difunde"
    assert curva[3]["pct"] > 45, "em tres rodadas a difusao deve estar completa"


def test_sac_satisfeito_apenas_com_difusao():
    assert differential.sac_matrix(cipher.DEFAULT_ROUNDS, True, 256)["satisfaz_sac"]
    assert not differential.sac_matrix(1, False, 256)["satisfaz_sac"]


def test_ddt_da_sbox():
    ddt = differential.sbox_ddt()
    assert ddt["maior_entrada"] == 4, "uniformidade diferencial esperada da construcao"
    assert ddt["log2_probabilidade"] == pytest.approx(-6.0)


def test_distinguidor_so_funciona_na_variante_fraca():
    assert not differential.differential_distinguisher(cipher.DEFAULT_ROUNDS, True, 50_000)["distinguivel"]
    assert differential.differential_distinguisher(1, False, 50_000)["distinguivel"]


def test_forca_bruta_encontra_chave_curta_e_projeta_inviabilidade():
    r = brute_force.brute_force(bits=12)
    assert r["chave_encontrada"]
    assert r["chaves_por_segundo"] > 0
    projecao_256 = [p for p in r["projecao"] if p["bits"] == 256]
    assert projecao_256 and all(not p["viavel"] for p in projecao_256)


def test_pbkdf2_encarece_dicionario():
    d = brute_force.dictionary_attack("banco123")
    assert d["sucesso"], "senha fraca da lista deve cair"
    assert d["tentativas_por_segundo"] < 5000, "o alongamento de chave precisa doer"


def test_frequencia_quebra_sem_difusao_e_falha_com():
    fraca = statistical.frequency_attack(800, rounds=1, diffusion=False)
    forte = statistical.frequency_attack(800, rounds=cipher.DEFAULT_ROUNDS, diffusion=True)
    assert fraca["quebrado"] and fraca["supera_linha_base"]
    assert not forte["quebrado"] and not forte["supera_linha_base"]


def test_saida_passa_nos_testes_estatisticos():
    claro = statistical.sample_ledger(600)
    corpo = cipher.encrypt(claro, "senha")[cipher.HEADER.size : -cipher.TAG_LEN]
    p = metrics.full_profile(corpo)
    assert p["entropia_bits_por_byte"] > 7.99
    assert p["distribuicao_uniforme"] and p["monobit"]["passou"] and p["corridas"]["passou"]
    assert abs(p["indice_coincidencia"] - 1 / 256) < 2e-4
    assert p["repeticao_blocos"]["repetidos"] == 0
    assert metrics.full_profile(claro)["entropia_bits_por_byte"] < 6


def test_ecb_preserva_padrao_mesmo_integro():
    """O modo importa mais que as rodadas: e a licao da Parte 4."""
    repetido = b"TRANSFERENCIA123" * 400
    ecb = cipher.encrypt(repetido, "s", mode=cipher.MODE_ECB)[cipher.HEADER.size : -cipher.TAG_LEN]
    ctr = cipher.encrypt(repetido, "s", mode=cipher.MODE_CTR)[cipher.HEADER.size : -cipher.TAG_LEN]
    assert metrics.block_repetition(ecb)["pct_repetidos"] > 90
    assert metrics.block_repetition(ctr)["pct_repetidos"] == 0


# --------------------------------------------------------------------------
# Big Data e IA
# --------------------------------------------------------------------------
@pytest.fixture(scope="module")
def janelas(tmp_path_factory):
    # Volume suficiente para que janelas normais tambem passem do minimo de
    # eventos. Com uma amostra pequena so as rajadas de anomalia sobrevivem ao
    # filtro e a prevalencia sobe artificialmente para dezenas de por cento.
    df = events.gerar(600_000, n_usuarios=200, semente=5)
    destino = tmp_path_factory.mktemp("lake")
    lake.gravar(df, destino)
    return lake.janelas(lake.conectar(destino), min_eventos=5)


def test_eventos_cobrem_as_cinco_anomalias():
    df = events.gerar(100_000, semente=3)
    assert set(df["rotulo"].unique()) == {events.NORMAL} | set(events.ANOMALIAS)


def test_anomalias_tem_assinatura_distinta_do_normal(janelas):
    media = janelas.groupby("rotulo_real")[["falhas_auth", "falhas_decifragem",
                                            "falhas_integridade", "eventos_ip_novo"]].mean()
    normal = media.loc["normal"]
    assert media.loc["forca_bruta_login", "falhas_auth"] > normal["falhas_auth"] * 20
    assert media.loc["falhas_decifragem", "falhas_decifragem"] > normal["falhas_decifragem"] * 20
    assert media.loc["adulteracao_arquivo", "falhas_integridade"] > normal["falhas_integridade"] * 20
    assert media.loc["acesso_atipico", "eventos_ip_novo"] > normal["eventos_ip_novo"] * 20


def test_detector_separa_anomalias(janelas):
    r = detect.analisar(janelas)
    m = r["metricas"]
    prevalencia = m["prevalencia_pct"] / 100
    assert prevalencia < 0.05, "amostra pequena demais: prevalencia irreal"
    assert m["roc_auc"] > 0.95, f"AUC caiu para {m['roc_auc']}"
    # A precisao media de um detector aleatorio e a propria prevalencia.
    assert m["average_precision"] > 10 * prevalencia
    assert m["revocacao"] > 0.5


def test_alertas_vem_explicados(janelas):
    alertas = detect.analisar(janelas)["alertas"]
    assert alertas
    for a in alertas[:5]:
        assert a["explicacao"] and a["tipo_previsto"]
