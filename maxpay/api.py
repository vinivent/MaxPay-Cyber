"""API do MaxPay (etapa 6 da arquitetura: serve o dashboard de seguranca).

    uvicorn maxpay.api:app --reload

Entrega tres coisas:
  * o cofre ao vivo (cifrar, decifrar, ocultar e revelar em imagem);
  * o laboratorio de ataques, com parametros escolhidos pelo usuario;
  * os resultados da bateria de experimentos e o veredito da Parte 4.
"""

from __future__ import annotations

import base64
import binascii
import io
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path

import numpy as np
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from maxpay import baseline, cipher, experiments, lake, report, slides, stego
from maxpay.attacks import brute_force, differential, statistical
from maxpay.metrics import shannon_entropy

WEB = Path(__file__).resolve().parent.parent / "web"
MAX_BYTES = 12 * 1024 * 1024

app = FastAPI(title="MaxPay", version="1.0", docs_url="/api/docs")


@app.middleware("http")
async def sem_cache_no_front(request, call_next):
    """Impede o navegador de misturar HTML novo com JavaScript antigo.

    Sem isto, uma versao em cache do app.js convive com um index.html recem
    servido e a tela aparece vazia, sem erro nenhum.
    """
    resposta = await call_next(request)
    if not request.url.path.startswith("/api/"):
        resposta.headers["Cache-Control"] = "no-cache, must-revalidate"
    return resposta

_estado: dict = {"resultados": None, "mtime": None, "executando": False, "erro": None}
_operacoes: deque = deque(maxlen=200)
_trava = threading.Lock()


# --------------------------------------------------------------------------
# Modelos
# --------------------------------------------------------------------------
class PedidoCifrar(BaseModel):
    texto: str | None = None
    conteudo_b64: str | None = None
    nome_arquivo: str | None = None
    senha: str = Field(min_length=1)
    algoritmo: str = "MPC-128"
    modo: str = "CTR"
    rodadas: int = Field(default=cipher.DEFAULT_ROUNDS, ge=1, le=32)
    difusao: bool = True
    ocultar_em_imagem: bool = False
    imagem_b64: str | None = None


class PedidoDecifrar(BaseModel):
    envelope_b64: str | None = None
    imagem_b64: str | None = None
    senha: str = Field(min_length=1)


def _b64_para_bytes(dado: str, rotulo: str) -> bytes:
    try:
        bruto = base64.b64decode(dado, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(400, f"{rotulo} não é base64 válido") from exc
    if len(bruto) > MAX_BYTES:
        raise HTTPException(413, f"{rotulo} excede {MAX_BYTES // 1024 // 1024} MB")
    return bruto


def _registrar(tipo: str, algoritmo: str, resultado: str, bytes_: int, ms: float, detalhe: str = "") -> dict:
    ev = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "tipo": tipo, "algoritmo": algoritmo, "resultado": resultado,
        "bytes": bytes_, "latencia_ms": round(ms, 2), "detalhe": detalhe,
    }
    _operacoes.appendleft(ev)
    return ev


def _histograma(dados: bytes) -> list[int]:
    return np.bincount(np.frombuffer(dados, dtype=np.uint8), minlength=256).tolist()


# --------------------------------------------------------------------------
# Cofre
# --------------------------------------------------------------------------
@app.post("/api/cofre/cifrar")
def cifrar(p: PedidoCifrar) -> dict:
    if p.texto is None and p.conteudo_b64 is None:
        raise HTTPException(400, "informe texto ou conteudo_b64")
    claro = p.texto.encode() if p.texto is not None else _b64_para_bytes(p.conteudo_b64, "conteudo")
    if not claro:
        raise HTTPException(400, "nada para cifrar")

    t0 = time.perf_counter()
    try:
        if p.algoritmo == "AES-256":
            envelope = baseline.encrypt(claro, p.senha)
            meta = baseline.describe(envelope)
            corpo = envelope[baseline.HEADER.size :]
        else:
            modo = cipher.MODE_ECB if p.modo.upper() == "ECB" else cipher.MODE_CTR
            envelope = cipher.encrypt(claro, p.senha, mode=modo, rounds=p.rodadas, diffusion=p.difusao)
            meta = cipher.describe(envelope)
            corpo = envelope[cipher.HEADER.size : -cipher.TAG_LEN]
    except ValueError as exc:
        _registrar("cifragem", p.algoritmo, "falha", len(claro), 0, str(exc))
        raise HTTPException(400, str(exc)) from exc
    ms = (time.perf_counter() - t0) * 1000

    resposta = {
        "envelope_b64": base64.b64encode(envelope).decode(),
        "metadados": meta,
        "nome_arquivo": p.nome_arquivo,
        "latencia_ms": round(ms, 2),
        "vazao_mb_s": round(len(claro) / 1e6 / max(time.perf_counter() - t0, 1e-9), 2),
        "entropia_clara": round(shannon_entropy(claro), 4),
        "entropia_cifrada": round(shannon_entropy(corpo), 4),
        # Abaixo de ~1 KB a entropia amostral subestima muito a real.
        "entropia_confiavel": len(corpo) >= 1024,
        "histograma_claro": _histograma(claro),
        "histograma_cifrado": _histograma(corpo),
        "esteganografia": None,
    }

    if p.ocultar_em_imagem:
        if not p.imagem_b64:
            raise HTTPException(400, "envie imagem_b64 para ocultar o envelope")
        portadora = _b64_para_bytes(p.imagem_b64, "imagem")
        try:
            marcada = stego.embed(portadora, envelope, p.senha)
        except (ValueError, OSError) as exc:
            raise HTTPException(400, str(exc)) from exc
        resposta["esteganografia"] = {
            "imagem_b64": base64.b64encode(marcada).decode(),
            "capacidade_bytes": stego.capacity(portadora),
            "ocupacao_pct": round(100 * len(envelope) / max(stego.capacity(portadora), 1), 2),
            "qualidade": stego.metrics(portadora, marcada),
            "esteganalise": stego.chi_square_attack(marcada),
        }
        _registrar("esteganografia", p.algoritmo, "sucesso", len(envelope), ms, "payload oculto em imagem")

    _registrar("cifragem", p.algoritmo, "sucesso", len(claro), ms, f"{meta['modo']} / {meta['rodadas']} rodadas")
    return resposta


@app.post("/api/cofre/decifrar")
def decifrar(p: PedidoDecifrar) -> dict:
    t0 = time.perf_counter()
    origem = "envelope"
    if p.imagem_b64:
        origem = "imagem"
        try:
            envelope = stego.extract(_b64_para_bytes(p.imagem_b64, "imagem"), p.senha)
        except (ValueError, OSError) as exc:
            _registrar("esteganografia", "-", "falha", 0, 0, str(exc))
            raise HTTPException(400, str(exc)) from exc
    elif p.envelope_b64:
        envelope = _b64_para_bytes(p.envelope_b64, "envelope")
    else:
        raise HTTPException(400, "informe envelope_b64 ou imagem_b64")

    eh_aes = envelope[:6] == baseline.MAGIC
    algoritmo = "AES-256" if eh_aes else "MPC-128"
    try:
        claro = (baseline if eh_aes else cipher).decrypt(envelope, p.senha)
        meta = (baseline if eh_aes else cipher).describe(envelope)
    except (ValueError, Exception) as exc:
        ms = (time.perf_counter() - t0) * 1000
        _registrar("decifragem", algoritmo, "falha", len(envelope), ms, str(exc))
        raise HTTPException(400, str(exc)) from exc

    ms = (time.perf_counter() - t0) * 1000
    _registrar("decifragem", algoritmo, "sucesso", len(claro), ms, f"origem: {origem}")
    try:
        texto = claro.decode("utf-8")
    except UnicodeDecodeError:
        texto = None
    return {
        "texto": texto,
        "conteudo_b64": base64.b64encode(claro).decode(),
        "bytes": len(claro),
        "metadados": meta,
        "origem": origem,
        "latencia_ms": round(ms, 2),
    }


@app.get("/api/estego/portadora")
def estego_portadora(tamanho: int = Query(360, ge=64, le=1024)) -> dict:
    """Imagem de exemplo para quem quer testar a ocultacao sem ter um arquivo."""
    from maxpay.attacks.statistical import _imagem_estruturada

    buf = io.BytesIO()
    _imagem_estruturada(tamanho).save(buf, "PNG")
    bruto = buf.getvalue()
    return {
        "imagem_b64": base64.b64encode(bruto).decode(),
        "bytes": len(bruto),
        "capacidade_bytes": stego.capacity(bruto),
        "dimensoes": [tamanho, tamanho],
    }


@app.get("/api/estego/exemplo")
def estego_exemplo(
    senha: str = Query("cofre-maxpay-2026", min_length=1),
    tamanho: int = Query(360, ge=64, le=1024),
) -> dict:
    """Imagem de exemplo ja com uma mensagem escondida, pronta para revelar.

    Serve para demonstrar a extracao sem precisar ter feito a ocultacao antes.
    """
    from maxpay.attacks.statistical import _imagem_estruturada

    buf = io.BytesIO()
    _imagem_estruturada(tamanho).save(buf, "PNG")
    portadora = buf.getvalue()
    mensagem = "TX884120 TED R$ 9.350,00 CT7781-4 Bradesco 17/11/2026 APROVADO"
    envelope = cipher.encrypt(mensagem.encode(), senha)
    marcada = stego.embed(portadora, envelope, senha)
    _registrar("esteganografia", "MPC-128", "sucesso", len(envelope), 0, "exemplo para demonstração")
    return {
        "imagem_b64": base64.b64encode(marcada).decode(),
        "portadora_b64": base64.b64encode(portadora).decode(),
        "senha": senha,
        "bytes_ocultos": len(envelope),
        "dimensoes": [tamanho, tamanho],
        "qualidade": stego.metrics(portadora, marcada),
    }


@app.get("/api/cofre/operacoes")
def operacoes() -> dict:
    return {"operacoes": list(_operacoes), "total": len(_operacoes)}


# --------------------------------------------------------------------------
# Laboratorio de ataques (ao vivo)
# --------------------------------------------------------------------------
@app.get("/api/laboratorio/avalanche")
def lab_avalanche(
    rodadas: int = Query(cipher.DEFAULT_ROUNDS, ge=1, le=32),
    difusao: bool = True,
    amostras: int = Query(4096, ge=256, le=20000),
) -> dict:
    return differential.avalanche(rodadas, difusao, amostras)


@app.get("/api/laboratorio/forca-bruta")
def lab_forca_bruta(
    bits: int = Query(16, ge=8, le=22),
    rodadas: int = Query(cipher.DEFAULT_ROUNDS, ge=1, le=32),
) -> dict:
    return brute_force.brute_force(bits=bits, rounds=rodadas, tempo_limite=25.0)


@app.get("/api/laboratorio/frequencia")
def lab_frequencia(
    rodadas: int = Query(1, ge=1, le=32),
    difusao: bool = False,
    linhas: int = Query(1500, ge=200, le=6000),
) -> dict:
    return statistical.frequency_attack(linhas, rodadas, difusao)


@app.get("/api/laboratorio/distinguidor")
def lab_distinguidor(
    rodadas: int = Query(cipher.DEFAULT_ROUNDS, ge=1, le=32),
    difusao: bool = True,
    amostras: int = Query(100_000, ge=10_000, le=500_000),
) -> dict:
    return differential.differential_distinguisher(rodadas, difusao, amostras)


# --------------------------------------------------------------------------
# Resultados da bateria e Big Data ao vivo
# --------------------------------------------------------------------------
def _resultados() -> dict:
    """Resultados da bateria, recarregados quando o arquivo muda no disco.

    O avaliador pode rodar `python -m maxpay.experiments` noutro terminal com
    o servidor de pe; sem esta checagem a tela continuaria mostrando a bateria
    anterior.
    """
    try:
        mtime = experiments.ARQUIVO.stat().st_mtime
    except OSError:
        mtime = None
    if mtime is not None and mtime != _estado["mtime"]:
        _estado["resultados"] = experiments.carregar()
        _estado["mtime"] = mtime
    if _estado["resultados"] is None:
        raise HTTPException(
            503, "nenhum resultado disponível: rode `python -m maxpay.experiments` primeiro"
        )
    return _estado["resultados"]


@app.get("/api/resultados")
def resultados() -> dict:
    r = _resultados()
    # Sem as cargas pesadas (matrizes e imagens), que tem rota propria.
    leve = {k: v for k, v in r.items() if k not in {"sac", "sac_fraco", "ecb", "estego"}}
    leve["secoes_pesadas"] = ["sac", "sac_fraco", "ecb", "estego"]
    return leve


@app.get("/api/resultados/{secao}")
def resultados_secao(secao: str) -> dict:
    r = _resultados()
    if secao not in r:
        raise HTTPException(404, f"seção '{secao}' inexistente. Disponíveis: {sorted(r)}")
    valor = r[secao]
    return valor if isinstance(valor, dict) else {"secao": secao, "valor": valor}


@app.get("/api/status")
def status() -> dict:
    try:
        r = _resultados()
    except HTTPException:
        r = None
    return {
        "executando": _estado["executando"],
        "erro": _estado["erro"],
        "tem_resultados": r is not None,
        "gerado_em": (r or {}).get("meta", {}).get("gerado_em"),
        "modo": (r or {}).get("meta", {}).get("modo"),
        "lake_pronto": lake.DATA_DIR.exists() and any(lake.DATA_DIR.rglob("*.parquet")),
    }


def _executar(rapido: bool, n_eventos: int | None) -> None:
    with _trava:
        _estado["executando"], _estado["erro"] = True, None
        try:
            res = experiments.run_all(rapido=rapido, n_eventos=n_eventos)
            experiments.salvar(res)
            _estado["resultados"] = res
            _estado["mtime"] = experiments.ARQUIVO.stat().st_mtime
        except Exception as exc:  # a falha precisa chegar ao dashboard
            _estado["erro"] = f"{type(exc).__name__}: {exc}"
        finally:
            _estado["executando"] = False


@app.post("/api/experimentos/executar")
def executar(
    tarefas: BackgroundTasks,
    rapido: bool = True,
    n_eventos: int | None = Query(None, ge=10_000, le=20_000_000),
) -> dict:
    if _estado["executando"]:
        raise HTTPException(409, "já existe uma bateria em execução")
    tarefas.add_task(_executar, rapido, n_eventos)
    return {"iniciado": True, "rapido": rapido, "n_eventos": n_eventos}


# --------------------------------------------------------------------------
# Relatorio e slides
# --------------------------------------------------------------------------
@app.get("/api/relatorio/markdown")
def relatorio_markdown() -> FileResponse:
    caminho = report.DOCS / "RELATORIO.md"
    if not caminho.exists():
        raise HTTPException(404, "relatório ainda não gerado: use 'Regerar a partir dos dados'")
    return FileResponse(caminho, media_type="text/markdown", filename="MaxPay-relatorio.md")


@app.get("/api/relatorio/slides")
def relatorio_slides() -> FileResponse:
    caminho = slides.DESTINO
    if not caminho.exists():
        raise HTTPException(404, "slides ainda não gerados: use 'Regerar a partir dos dados'")
    return FileResponse(caminho, media_type="text/html")


@app.post("/api/relatorio/regerar")
def relatorio_regerar() -> dict:
    """Regera relatorio e slides a partir da bateria atual."""
    _resultados()  # 404/503 claro se ainda nao houver medicoes
    r, s = report.main(), slides.main()
    return {
        "relatorio": str(r), "slides": str(s),
        "relatorio_kb": round(r.stat().st_size / 1024, 1),
        "slides_kb": round(s.stat().st_size / 1024, 1),
    }


@app.get("/api/saude")
def saude() -> dict:
    return {"ok": True, "projeto": "MaxPay", "versao": app.version}


# --------------------------------------------------------------------------
# Frontend
# --------------------------------------------------------------------------
if WEB.exists():
    app.mount("/assets", StaticFiles(directory=WEB / "assets"), name="assets") if (WEB / "assets").exists() else None

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(WEB / "index.html")

    app.mount("/", StaticFiles(directory=WEB, html=True), name="web")
