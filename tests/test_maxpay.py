"""Testes do MaxPay.

Cobrem o que nao pode quebrar sem ninguem perceber: round-trip da cifra,
deteccao de adulteracao, esteganografia, e o fato de que os tres ataques
falham contra a cifra integra e funcionam contra a variante enfraquecida.

    pytest -q
"""

from __future__ import annotations

import io
import itertools
import os

import numpy as np
import pandas as pd
import pytest
from PIL import Image

from maxpay import baseline, cipher, detect, events, lake, metrics, registro, stego
from maxpay.attacks import brute_force, differential, statistical


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
    c = cipher.MaxPayCipher(os.urandom(32), rodadas, difusao)
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
    assert not any((i ^ 0xFF) == v for i, v in enumerate(cipher.SBOX)), "sem pontos fixos opostos"
    assert np.array_equal(cipher.INV_SBOX[cipher.SBOX], np.arange(256))


def test_sbox_e_propria_e_nao_a_do_aes():
    """A S-box e nossa, nao a do AES. Este teste existe para que ninguem
    reintroduza a construcao do AES sem perceber."""
    aes_inicio = [0x63, 0x7C, 0x77, 0x7B, 0xF2, 0x6B, 0x6F, 0xC5]
    assert cipher.SBOX[:8].tolist() != aes_inicio
    assert cipher.SBOX_ROTACOES != (0, 1, 2, 3, 4) or cipher.SBOX_CONSTANTE != 0x63
    assert cipher.MDS != (2, 3, 1, 1), "a matriz de difusao tambem e nossa"
    assert cipher.DESLOCAMENTOS != (0, 1, 2, 3), "a permutacao tambem e nossa"


def test_matriz_de_difusao_e_mds():
    """MDS: toda submatriz quadrada inversivel, o que da numero de ramificacao 5."""
    import itertools

    def det(M):
        M = [linha[:] for linha in M]
        n, d = len(M), 1
        for col in range(n):
            piv = next((r for r in range(col, n) if M[r][col]), None)
            if piv is None:
                return 0
            if piv != col:
                M[col], M[piv] = M[piv], M[col]
            d = cipher.gf_mul(d, M[col][col])
            inv = 0 if M[col][col] == 0 else int(cipher.GF_EXP[255 - int(cipher.GF_LOG[M[col][col]])])
            for r in range(col + 1, n):
                if M[r][col]:
                    f = cipher.gf_mul(M[r][col], inv)
                    for j in range(col, n):
                        M[r][j] ^= cipher.gf_mul(f, M[col][j])
        return d

    M = [[cipher.MDS[(j - i) % 4] for j in range(4)] for i in range(4)]
    for k in (1, 2, 3, 4):
        for linhas in itertools.combinations(range(4), k):
            for colunas in itertools.combinations(range(4), k):
                menor = [[M[r][c] for c in colunas] for r in linhas]
                assert det(menor) != 0, f"submatriz {linhas}x{colunas} singular: nao e MDS"


def test_permutacao_espalha_entre_colunas():
    """Cada coluna de saida precisa puxar um byte de cada coluna de entrada."""
    for coluna in range(4):
        origens = {cipher.SHIFT_ROWS[linha + 4 * coluna] // 4 for linha in range(4)}
        assert origens == {0, 1, 2, 3}


def test_permutacao_e_bijetiva():
    assert sorted(cipher.SHIFT_ROWS.tolist()) == list(range(16))
    assert np.array_equal(cipher.SHIFT_ROWS[cipher.INV_SHIFT_ROWS], np.arange(16))


def test_chave_invalida():
    with pytest.raises(ValueError):
        cipher.MaxPayCipher(b"curta", 14)
    with pytest.raises(ValueError):
        cipher.MaxPayCipher(os.urandom(32), 0)


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
    """Amostra fixa de proposito.

    Monobit e corridas sao testes de hipotese com p < 0,01: sobre uma amostra
    nova a cada execucao, eles reprovariam ~1% das vezes sem que nada estivesse
    errado. Com chave e nonce fixos o resultado e reproduzivel, que e o que um
    teste de regressao precisa ser.
    """
    claro = statistical.sample_ledger(600)
    cp = cipher.MaxPayCipher(bytes(range(32)))
    n_blocos = (len(claro) + cipher.BLOCK - 1) // cipher.BLOCK
    fluxo = cp.keystream(b"nonce-fixo01", n_blocos).reshape(-1)[: len(claro)]
    corpo = (np.frombuffer(claro, dtype=np.uint8) ^ fluxo).tobytes()
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
def lago(tmp_path_factory):
    # Volume suficiente para que janelas normais tambem passem do minimo de
    # eventos. Com uma amostra pequena so as rajadas de anomalia sobrevivem ao
    # filtro e a prevalencia sobe artificialmente para dezenas de por cento.
    df = events.gerar(600_000, n_usuarios=200, semente=5)
    destino = tmp_path_factory.mktemp("lake")
    lake.gravar(df, destino)
    return destino


@pytest.fixture(scope="module")
def janelas(lago):
    return lake.janelas(lake.conectar(lago), min_eventos=5)


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


# --------------------------------------------------------------------------
# Registro ao vivo
# --------------------------------------------------------------------------
@pytest.fixture
def instalacao(lago, tmp_path, monkeypatch):
    monkeypatch.setattr(lake, "DATA_DIR", lago)
    monkeypatch.setattr(lake, "VIVO_DIR", tmp_path / "vivo")
    monkeypatch.setattr(lake, "DETECCOES_DIR", tmp_path / "deteccoes")
    segundos = itertools.count()
    inicio = pd.Timestamp("2026-11-17 14:02:00")
    monkeypatch.setattr(registro, "_agora", lambda: inicio + pd.Timedelta(seconds=next(segundos)))
    return tmp_path


@pytest.fixture
def cliente(instalacao):
    from fastapi.testclient import TestClient

    from maxpay.api import app

    return TestClient(app)


def test_deteccoes_do_lote_sao_armazenadas(janelas, tmp_path):
    _, pontuadas = detect.treinar_e_pontuar(janelas)
    emitidos = detect.alertas_emitidos(pontuadas)
    gravacao = lake.gravar_deteccoes(emitidos, lake.ORIGEM_LOTE, tmp_path)
    assert gravacao["registros"] == len(emitidos) == int(pontuadas["alerta"].sum()) > 0
    assert lake.contar_deteccoes(tmp_path) == {lake.ORIGEM_LOTE: len(emitidos)}
    mais_arriscada = lake.consultar_deteccoes(lake.ORIGEM_LOTE, 1, tmp_path)[0]
    assert mais_arriscada["score"] == pytest.approx(emitidos["score"].max())
    assert mais_arriscada["explicacao"] and mais_arriscada["rotulo_real"]


def test_operacao_registrada_sobrevive_em_parquet(instalacao):
    registro.registrar("cifragem", "MPC-128", "sucesso", 70, 41.5, ip="10.0.0.7", dispositivo="web-chrome")
    registro.registrar("decifragem", "MPC-128", "falha", 157, 9.8, integridade_ok=False, detalhe="chave incorreta")
    assert list((instalacao / "vivo").rglob("*.parquet")), "o evento precisa estar em disco, não só na memória"
    ultima, primeira = registro.operacoes()
    assert (primeira["tipo"], primeira["ip"], primeira["dispositivo"]) == ("cifragem", "10.0.0.7", "web-chrome")
    assert (ultima["tipo"], ultima["resultado"], ultima["detalhe"]) == ("decifragem", "falha", "chave incorreta")
    assert registro.total_de_eventos() == 2


def test_registro_compacta_sem_perder_eventos(instalacao, monkeypatch):
    monkeypatch.setattr(lake, "DATA_DIR", instalacao / "sem-historico")
    monkeypatch.setattr(lake, "MAX_PARTES_POR_DIA", 8)
    for _ in range(30):
        registro.registrar("cifragem", "AES-256", "sucesso", 64, 30.0)
    assert registro.total_de_eventos() == 30
    assert len(list((instalacao / "vivo").rglob("*.parquet"))) <= 9


def test_uso_normal_nao_gera_alerta(instalacao):
    for _ in range(8):
        registro.registrar("cifragem", "MPC-128", "sucesso", 90, 45.0)
    painel = registro.painel()
    assert painel["modelo_pronto"] and painel["janelas_julgadas"] >= 1
    assert not any(j["alerta"] for j in painel["janelas"])
    assert painel["deteccoes"] == []


def test_sem_historico_o_evento_e_registrado_mas_nao_julgado(instalacao, monkeypatch):
    monkeypatch.setattr(lake, "DATA_DIR", instalacao / "sem-historico")
    for _ in range(6):
        registro.registrar("decifragem", "MPC-128", "falha", 157, 10.0, integridade_ok=False)
    painel = registro.painel()
    assert painel["eventos"]["total"] == 6 and painel["eventos"]["falhas"] == 6
    assert not painel["modelo_pronto"] and painel["janelas"] == []


def test_senha_errada_em_rajada_vira_deteccao_armazenada(cliente, instalacao):
    envelope = cliente.post("/api/cofre/cifrar", json={"texto": "PIX 250,00", "senha": "certa"}).json()["envelope_b64"]
    for _ in range(12):
        recusa = cliente.post("/api/cofre/decifrar", json={"envelope_b64": envelope, "senha": "errada"})
        assert recusa.status_code == 400
    painel = cliente.get("/api/antifraude/ao-vivo").json()
    assert painel["eventos"]["falhas_integridade"] == 12
    assert any(j["alerta"] for j in painel["janelas"])
    assert painel["deteccoes"] and painel["deteccoes"][0]["tipo_previsto"] == "falhas_decifragem"
    assert list((instalacao / "deteccoes" / f"origem={lake.ORIGEM_AO_VIVO}").glob("*.parquet"))
    assert cliente.get("/api/status").json()["deteccoes_armazenadas"] == {lake.ORIGEM_AO_VIVO: 1}


def test_ataque_simulado_passa_pelo_caminho_real(cliente):
    resposta = cliente.post("/api/antifraude/simular-ataque?tentativas=12").json()
    assert resposta["recusadas"] == 12
    assert any(j["alerta"] for j in resposta["painel"]["janelas"])
    operacoes = cliente.get("/api/cofre/operacoes").json()
    assert operacoes["total"] == 12
    assert all(o["tipo"] == "decifragem" and o["resultado"] == "falha" for o in operacoes["operacoes"])
    assert not any({"ip", "dispositivo"} & o.keys() for o in operacoes["operacoes"])


def test_julgamento_ignora_eventos_fora_do_horizonte(instalacao, monkeypatch):
    antigo = pd.Timestamp("2026-11-17 14:02:00") - pd.Timedelta(days=registro.HORIZONTE_DIAS + 5)
    monkeypatch.setattr(registro, "_agora", lambda: antigo)
    for _ in range(8):
        registro.registrar("decifragem", "MPC-128", "falha", 70, 40.0, integridade_ok=False)
    monkeypatch.setattr(registro, "_agora", lambda: pd.Timestamp("2026-11-17 14:02:00"))
    registro.registrar("cifragem", "MPC-128", "sucesso", 70, 40.0)
    painel = registro.painel()
    assert painel["eventos"]["total"] == 9
    assert painel["janelas_julgadas"] == 0 and painel["janelas"] == []
