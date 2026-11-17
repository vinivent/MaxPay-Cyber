from __future__ import annotations

import threading
import time

import duckdb
import pandas as pd

from maxpay import detect, lake

USUARIO_LOCAL = "operador"
SEM_ROTULO = "nao_rotulado"
MIN_EVENTOS_JANELA = 5

_trava = threading.RLock()
_detector: dict = {"assinatura": None, "modelo": None}


def dispositivo(user_agent: str | None) -> str:
    ua = (user_agent or "").lower()
    if "android" in ua:
        return "app-android"
    if "iphone" in ua or "ipad" in ua:
        return "app-ios"
    if "firefox" in ua:
        return "web-firefox"
    if "chrome" in ua or "chromium" in ua or "edg" in ua:
        return "web-chrome"
    if "safari" in ua:
        return "web-safari"
    return "cliente-api"


def _agora() -> pd.Timestamp:
    return pd.Timestamp.now().floor("ms")


def registrar(
    tipo: str,
    algoritmo: str,
    resultado: str,
    bytes_: int,
    latencia_ms: float,
    *,
    ip: str = "127.0.0.1",
    dispositivo: str = "cliente-api",
    integridade_ok: bool = True,
    detalhe: str = "",
) -> dict:
    agora = _agora()
    evento = {
        "evento_id": time.time_ns(),
        "ts": agora,
        "dia": agora.strftime("%Y-%m-%d"),
        "hora": agora.hour,
        "usuario": USUARIO_LOCAL,
        "ip": ip,
        "dispositivo": dispositivo,
        "tipo": tipo,
        "algoritmo": algoritmo,
        "resultado": resultado,
        "latencia_ms": round(float(latencia_ms), 2),
        "bytes": int(bytes_),
        "conta": "",
        "valor": 0.0,
        "integridade_ok": bool(integridade_ok),
        "rotulo": SEM_ROTULO,
        "detalhe": detalhe,
    }
    quadro = pd.DataFrame([evento]).astype({"evento_id": "int64", "hora": "int16", "bytes": "int64"})
    with _trava:
        lake.anexar(quadro, lake.VIVO_DIR)
        _julgar_janela(agora)
    return {**evento, "ts": agora.isoformat(timespec="seconds")}


def detector() -> detect.DetectorAnomalias | None:
    if not lake.tem_dados(lake.DATA_DIR):
        return None
    with _trava:
        try:
            assinatura = (
                str(lake.DATA_DIR),
                max(a.stat().st_mtime_ns for a in lake.DATA_DIR.rglob("*.parquet")),
            )
            if _detector["assinatura"] != assinatura:
                historico = lake.janelas(lake.conectar(lake.DATA_DIR))
                modelo = detect.DetectorAnomalias().treinar(historico)
                modelo.modelo.n_jobs = 1
                _detector["modelo"], _detector["assinatura"] = modelo, assinatura
        except (duckdb.Error, OSError, ValueError):
            return None
        return _detector["modelo"]


def _pontuar_janelas(det: detect.DetectorAnomalias) -> pd.DataFrame:
    if not lake.tem_dados(lake.VIVO_DIR):
        return pd.DataFrame()
    janelas = lake.janelas(lake.conectar(lake.VIVO_DIR), min_eventos=MIN_EVENTOS_JANELA)
    if janelas.empty:
        return janelas
    return det.pontuar(janelas.drop(columns=["anomala", "rotulo_real"]))


def _julgar_janela(instante: pd.Timestamp) -> None:
    det = detector()
    if det is None:
        return
    pontuadas = _pontuar_janelas(det)
    if pontuadas.empty:
        return
    atual = pontuadas["janela"] == instante.floor(f"{lake.JANELA_MINUTOS}min")
    alertas = detect.alertas_emitidos(pontuadas[atual])
    if not alertas.empty:
        lake.gravar_deteccoes(alertas, lake.ORIGEM_AO_VIVO, lake.DETECCOES_DIR)


def operacoes(limite: int = 200) -> list[dict]:
    with _trava:
        if not lake.tem_dados(lake.VIVO_DIR):
            return []
        linhas = lake.q(
            lake.conectar(lake.VIVO_DIR),
            """
            SELECT ts, tipo, algoritmo, resultado, bytes, latencia_ms, detalhe, ip, dispositivo
            FROM eventos ORDER BY ts DESC, evento_id DESC LIMIT ?
            """,
            [limite],
        )
    for linha in linhas:
        linha["ts"] = linha["ts"].isoformat(timespec="seconds")
    return linhas


def total_de_eventos() -> int:
    with _trava:
        if not lake.tem_dados(lake.VIVO_DIR):
            return 0
        return int(lake.conectar(lake.VIVO_DIR).execute("SELECT count(*) FROM eventos").fetchone()[0])


def painel(limite_janelas: int = 20) -> dict:
    with _trava:
        det = detector()
        eventos = {"total": 0, "falhas": 0, "falhas_integridade": 0, "primeiro": None, "ultimo": None}
        janelas: list[dict] = []
        janelas_julgadas = 0
        if lake.tem_dados(lake.VIVO_DIR):
            linha = lake.conectar(lake.VIVO_DIR).execute(
                """
                SELECT count(*), count(*) FILTER (WHERE resultado = 'falha'),
                       count(*) FILTER (WHERE NOT integridade_ok), min(ts), max(ts)
                FROM eventos
                """
            ).fetchone()
            eventos = {
                "total": int(linha[0]),
                "falhas": int(linha[1]),
                "falhas_integridade": int(linha[2]),
                "primeiro": linha[3].isoformat(timespec="seconds"),
                "ultimo": linha[4].isoformat(timespec="seconds"),
            }
        if det is not None:
            pontuadas = _pontuar_janelas(det)
            if not pontuadas.empty:
                janelas_julgadas = len(pontuadas)
                recentes = pontuadas.sort_values("janela", ascending=False).head(limite_janelas)
                janelas = [
                    {
                        "usuario": j.usuario,
                        "janela": str(j.janela),
                        "eventos": int(j.eventos),
                        "falhas": int(j.falhas),
                        "score": round(float(j.score), 4),
                        "alerta": bool(j.alerta),
                        "tipo_previsto": j.tipo_previsto,
                        "explicacao": j.explicacao,
                    }
                    for j in recentes.itertuples()
                ]
        return {
            "modelo_pronto": det is not None,
            "limiar": round(det.limiar, 4) if det is not None else None,
            "janela_minutos": lake.JANELA_MINUTOS,
            "min_eventos_janela": MIN_EVENTOS_JANELA,
            "eventos": eventos,
            "janelas_julgadas": janelas_julgadas,
            "janelas": janelas,
            "deteccoes": lake.consultar_deteccoes(lake.ORIGEM_AO_VIVO, 50, lake.DETECCOES_DIR),
            "deteccoes_armazenadas": lake.contar_deteccoes(lake.DETECCOES_DIR),
        }
