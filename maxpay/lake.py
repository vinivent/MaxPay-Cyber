"""Camada de Big Data do MaxPay (etapa 4 da arquitetura).

Armazena os eventos em Parquet particionado por dia e consulta com DuckDB.
A agregacao pesada acontece aqui, em SQL colunar; a camada de IA recebe
apenas as janelas ja resumidas.
"""

from __future__ import annotations

import re
import shutil
import time
from pathlib import Path

import duckdb
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "data"
DATA_DIR = DADOS / "lake"
VIVO_DIR = DADOS / "vivo"
DETECCOES_DIR = DADOS / "deteccoes"
JANELA_MINUTOS = 10
MAX_PARTES_POR_DIA = 64
ORIGEM_LOTE = "lote"
ORIGEM_AO_VIVO = "ao_vivo"
COLUNAS_DETECCAO = [
    "detectado_em", "usuario", "janela", "score", "tipo_previsto", "explicacao",
    "atributo_dominante", "z_dominante", "forca_assinatura", "eventos", "falhas",
    "ips_distintos", "eventos_ip_novo",
]


def tem_dados(origem: Path | str) -> bool:
    origem = Path(origem)
    return origem.exists() and any(origem.rglob("*.parquet"))


def caminho_relativo(caminho: Path | str) -> str:
    caminho = Path(caminho)
    try:
        return str(caminho.relative_to(RAIZ))
    except ValueError:
        return caminho.name


def _bytes_em_disco(pasta: Path) -> int:
    return sum(a.stat().st_size for a in pasta.rglob("*.parquet"))


def gravar(df: pd.DataFrame, destino: Path | str = DATA_DIR, limpar: bool = True) -> dict:
    """Escreve o lote em Parquet particionado por dia."""
    destino = Path(destino)
    if limpar and destino.exists():
        shutil.rmtree(destino)
    destino.mkdir(parents=True, exist_ok=True)
    df.to_parquet(destino, partition_cols=["dia"], index=False)
    arquivos = sorted(destino.rglob("*.parquet"))
    return {
        "caminho": caminho_relativo(destino),
        "eventos": len(df),
        "particoes": len({a.parent for a in arquivos}),
        "arquivos": len(arquivos),
        "bytes_em_disco": sum(a.stat().st_size for a in arquivos),
        "bytes_por_evento": round(sum(a.stat().st_size for a in arquivos) / max(len(df), 1), 2),
    }


def anexar(df: pd.DataFrame, destino: Path | str = VIVO_DIR) -> None:
    destino = Path(destino)
    for dia, lote in df.groupby("dia"):
        particao = destino / f"dia={dia}"
        particao.mkdir(parents=True, exist_ok=True)
        lote.drop(columns="dia").to_parquet(particao / f"parte-{time.time_ns()}.parquet", index=False)
        _compactar(particao)


def _compactar(particao: Path) -> None:
    partes = sorted(particao.glob("*.parquet"))
    if len(partes) <= MAX_PARTES_POR_DIA:
        return
    unido = pd.concat([pd.read_parquet(a) for a in partes], ignore_index=True)
    temporario = particao / f"compacto-{time.time_ns()}.tmp"
    unido.to_parquet(temporario, index=False)
    temporario.rename(temporario.with_suffix(".parquet"))
    for a in partes:
        a.unlink()


def gravar_deteccoes(alertas: pd.DataFrame, origem: str, destino: Path | str = DETECCOES_DIR) -> dict:
    pasta = Path(destino) / f"origem={origem}"
    if origem == ORIGEM_LOTE and pasta.exists():
        shutil.rmtree(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    registros = alertas.copy()
    registros["detectado_em"] = pd.Timestamp.now().floor("s")
    extras = [c for c in ("rotulo_real", "anomala") if c in registros.columns]
    registros = registros[COLUNAS_DETECCAO + extras]
    if origem == ORIGEM_LOTE:
        registros.to_parquet(pasta / "alertas.parquet", index=False)
    else:
        for n in range(len(registros)):
            linha = registros.iloc[[n]]
            chave = f"{linha['usuario'].iloc[0]}-{linha['janela'].iloc[0]:%Y%m%dT%H%M}"
            linha.to_parquet(pasta / (re.sub(r"[^A-Za-z0-9_.-]", "_", chave) + ".parquet"), index=False)
    return {
        "caminho": caminho_relativo(pasta),
        "registros": len(registros),
        "bytes_em_disco": _bytes_em_disco(pasta),
    }


def consultar_deteccoes(
    origem: str | None = None, limite: int = 50, destino: Path | str = DETECCOES_DIR
) -> list[dict]:
    if not tem_dados(destino):
        return []
    con = duckdb.connect()
    filtro, params = ("WHERE origem = ?", [origem]) if origem else ("", [])
    df = con.execute(f"""
        SELECT * FROM read_parquet('{Path(destino)}/**/*.parquet', hive_partitioning=1, union_by_name=1)
        {filtro} ORDER BY score DESC, janela DESC LIMIT ?
    """, params + [limite]).df()
    df["janela"], df["detectado_em"] = df["janela"].astype(str), df["detectado_em"].astype(str)
    return df.astype(object).where(df.notna(), None).to_dict(orient="records")


def contar_deteccoes(destino: Path | str = DETECCOES_DIR) -> dict:
    if not tem_dados(destino):
        return {}
    con = duckdb.connect()
    linhas = con.execute(f"""
        SELECT origem, count(*) FROM read_parquet('{Path(destino)}/**/*.parquet', hive_partitioning=1, union_by_name=1)
        GROUP BY 1
    """).fetchall()
    return {origem: int(total) for origem, total in linhas}


def conectar(origem: Path | str = DATA_DIR) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute(
        f"CREATE OR REPLACE VIEW eventos AS SELECT * FROM read_parquet('{Path(origem)}/**/*.parquet', hive_partitioning=1)"
    )
    return con


def q(con, sql: str, params: list | None = None) -> list[dict]:
    return con.execute(sql, params or []).df().to_dict(orient="records")


def resumo(con) -> dict:
    """Indicadores de topo do dashboard."""
    linha = con.execute(
        """
        SELECT count(*) AS eventos,
               count(DISTINCT usuario) AS usuarios,
               count(DISTINCT ip) AS ips,
               count(DISTINCT dia) AS dias,
               sum(CASE WHEN resultado='falha' THEN 1 ELSE 0 END) AS falhas,
               sum(CASE WHEN NOT integridade_ok THEN 1 ELSE 0 END) AS falhas_integridade,
               sum(bytes) AS bytes_processados,
               sum(valor) AS volume_financeiro,
               median(latencia_ms) AS latencia_mediana,
               quantile_cont(latencia_ms, 0.99) AS latencia_p99,
               min(ts) AS inicio, max(ts) AS fim
        FROM eventos
        """
    ).df().iloc[0]
    d = linha.to_dict()
    d["taxa_falha_pct"] = round(100 * d["falhas"] / max(d["eventos"], 1), 3)
    d["inicio"], d["fim"] = str(d["inicio"]), str(d["fim"])
    return d


def serie_temporal(con, bucket: str = "hour") -> list[dict]:
    return q(con, f"""
        SELECT date_trunc('{bucket}', ts) AS instante,
               count(*) AS eventos,
               sum(CASE WHEN resultado='falha' THEN 1 ELSE 0 END) AS falhas,
               sum(CASE WHEN rotulo <> 'normal' THEN 1 ELSE 0 END) AS anomalos
        FROM eventos GROUP BY 1 ORDER BY 1
    """)


def por_dimensao(con, coluna: str) -> list[dict]:
    if coluna not in {"tipo", "algoritmo", "dispositivo", "resultado", "rotulo", "hora"}:
        raise ValueError("coluna nao permitida")
    return q(con, f"""
        SELECT {coluna} AS chave, count(*) AS eventos,
               sum(CASE WHEN resultado='falha' THEN 1 ELSE 0 END) AS falhas,
               round(100.0*sum(CASE WHEN resultado='falha' THEN 1 ELSE 0 END)/count(*), 2) AS taxa_falha_pct,
               round(avg(latencia_ms), 2) AS latencia_media
        FROM eventos GROUP BY 1 ORDER BY eventos DESC
    """)


def top_suspeitos(con, limite: int = 12) -> list[dict]:
    return q(con, """
        SELECT usuario,
               count(*) AS eventos,
               sum(CASE WHEN resultado='falha' THEN 1 ELSE 0 END) AS falhas,
               count(DISTINCT ip) AS ips,
               sum(CASE WHEN NOT integridade_ok THEN 1 ELSE 0 END) AS falhas_integridade,
               round(100.0*sum(CASE WHEN resultado='falha' THEN 1 ELSE 0 END)/count(*), 1) AS taxa_falha_pct
        FROM eventos GROUP BY 1 HAVING count(*) > 30
        ORDER BY falhas DESC, taxa_falha_pct DESC LIMIT ?
    """, [limite])


def janelas(con, minutos: int = JANELA_MINUTOS, min_eventos: int = 5) -> pd.DataFrame:
    """Agrega o fluxo em janelas (usuario x tempo): a entrada da camada de IA.

    E aqui que o volume cai de milhoes de eventos para milhares de janelas.
    Janelas com menos de `min_eventos` sao descartadas: uma ou duas acoes
    isoladas nao formam um comportamento a ser julgado.
    """
    return con.execute(f"""
        WITH atividade AS (
            SELECT usuario, count(DISTINCT dia) AS dias_ativos FROM eventos GROUP BY 1
        ),
        habitual_ip AS (
            SELECT e.usuario, e.ip
            FROM eventos e JOIN atividade a ON a.usuario = e.usuario
            GROUP BY e.usuario, e.ip, a.dias_ativos
            HAVING count(DISTINCT e.dia) >= least(3, a.dias_ativos)
        )
        SELECT e.usuario,
               time_bucket(INTERVAL '{minutos} minutes', e.ts) AS janela,
               count(*) AS eventos,
               count(DISTINCT e.ip) AS ips_distintos,
               count(DISTINCT e.dispositivo) AS dispositivos,
               sum(CASE WHEN e.resultado='falha' THEN 1 ELSE 0 END) AS falhas,
               sum(CASE WHEN e.tipo='autenticacao' AND e.resultado='falha' THEN 1 ELSE 0 END) AS falhas_auth,
               sum(CASE WHEN e.tipo='decifragem' AND e.resultado='falha' THEN 1 ELSE 0 END) AS falhas_decifragem,
               sum(CASE WHEN NOT e.integridade_ok THEN 1 ELSE 0 END) AS falhas_integridade,
               sum(CASE WHEN e.tipo='acesso_arquivo' THEN 1 ELSE 0 END) AS acessos_arquivo,
               sum(CASE WHEN hi.ip IS NULL THEN 1 ELSE 0 END) AS eventos_ip_novo,
               sum(e.bytes) AS bytes_total,
               avg(e.latencia_ms) AS latencia_media,
               avg(e.hora) AS hora_media,
               sum(CASE WHEN e.hora BETWEEN 0 AND 5 THEN 1 ELSE 0 END) AS eventos_madrugada,
               max(CASE WHEN e.rotulo <> 'normal' THEN 1 ELSE 0 END) AS anomala,
               coalesce(max(e.rotulo) FILTER (WHERE e.rotulo <> 'normal'), 'normal') AS rotulo_real
        FROM eventos e
        LEFT JOIN habitual_ip hi ON hi.usuario = e.usuario AND hi.ip = e.ip
        GROUP BY 1, 2
        HAVING count(*) >= {min_eventos}
        -- Ordem fixa de proposito. O DuckDB agrega em paralelo e devolve as
        -- linhas em ordem arbitraria; o Isolation Forest subamostra por indice,
        -- entao a mesma base daria resultados diferentes a cada execucao.
        ORDER BY e.usuario, janela
    """).df()
