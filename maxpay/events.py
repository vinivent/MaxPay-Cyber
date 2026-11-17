"""Gerador de eventos de seguranca do MaxPay (etapa 4 da arquitetura).

Produz o fluxo que a camada de Big Data armazena e a IA analisa:
operacoes criptograficas, tentativas de autenticacao, acessos a arquivos e
transferencias. Os cinco tipos de anomalia previstos no projeto sao injetados
em episodios rotulados, o que permite medir precisao e revocacao do detector.

Tudo e vetorizado para gerar milhoes de eventos em segundos.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

NORMAL = "normal"
ANOMALIAS = {
    "forca_bruta_login": "Número incomum de tentativas de autenticação",
    "falhas_decifragem": "Frequência elevada de falhas de descriptografia",
    "adulteracao_arquivo": "Alterações inesperadas em arquivos",
    "acesso_atipico": "Padrões atípicos de acesso",
    "surto_de_eventos": "Comportamentos incomuns na geração de eventos",
}

# Nomes de exibicao. As chaves sao identificadores internos sem acento; a
# interface e os relatorios usam estes rotulos.
NOMES_EXIBICAO = {
    "cifragem": "Cifragem",
    "decifragem": "Decifragem",
    "autenticacao": "Autenticação",
    "esteganografia": "Esteganografia",
    "acesso_arquivo": "Acesso a arquivo",
    "transferencia": "Transferência",
    "sucesso": "Sucesso",
    "falha": "Falha",
}
NOMES_CURTOS = {
    "forca_bruta_login": "Força bruta",
    "falhas_decifragem": "Decifragem",
    "adulteracao_arquivo": "Adulteração",
    "acesso_atipico": "Acesso atípico",
    "surto_de_eventos": "Surto",
    "normal": "Normal",
    "comportamento_incomum": "Incomum",
}
# Nome completo, usado em tabela, relatorio e slide. O curto fica so no eixo
# de grafico, onde nao cabe mais. Os dois precisam dizer a mesma coisa.
NOMES_LONGOS = {
    "forca_bruta_login": "Força bruta de login",
    "falhas_decifragem": "Falhas de decifragem",
    "adulteracao_arquivo": "Adulteração de arquivo",
    "acesso_atipico": "Acesso atípico",
    "surto_de_eventos": "Surto de eventos",
    "comportamento_incomum": "Comportamento incomum",
    "normal": "Normal",
}
NOMES_EXIBICAO.update(NOMES_LONGOS)

TIPOS = ["cifragem", "decifragem", "autenticacao", "esteganografia", "acesso_arquivo", "transferencia"]
TIPO_P = [0.26, 0.24, 0.20, 0.06, 0.12, 0.12]
ALGORITMOS = ["MPC-128", "AES-256"]
DISPOSITIVOS = ["app-android", "app-ios", "web-chrome", "web-safari", "caixa-eletronico", "api-parceiro"]

# Perfil diurno: pico comercial, vale de madrugada.
PERFIL_HORA = np.array(
    [0.6, 0.4, 0.3, 0.3, 0.4, 0.8, 2.0, 4.0, 6.5, 8.0, 8.5, 8.0,
     7.0, 7.5, 8.2, 8.0, 7.2, 6.0, 5.0, 4.2, 3.4, 2.6, 1.6, 1.0]
)
PERFIL_HORA = PERFIL_HORA / PERFIL_HORA.sum()


def _pools(n_usuarios: int, semente: int) -> dict:
    """Perfis dos usuarios.

    Cada usuario tem IPs e dispositivos habituais. Sem essa estabilidade nao
    existe "fora do padrao" a detectar: e ela que torna o acesso atipico
    identificavel.
    """
    rng = np.random.default_rng(semente)
    ips = np.array([f"189.{rng.integers(1, 255)}.{rng.integers(1, 255)}.{i % 255}" for i in range(4000)])
    return {
        "usuarios": np.array([f"u{i:05d}" for i in range(n_usuarios)]),
        "ips": ips,
        "ips_suspeitos": np.array([f"45.{rng.integers(1, 255)}.{rng.integers(1, 255)}.{i % 255}" for i in range(120)]),
        "contas": np.array([f"CT{rng.integers(1000, 9999):04d}-{i % 10}" for i in range(n_usuarios)]),
        "ips_habituais": rng.integers(0, len(ips), size=(n_usuarios, 2)),
        "dispositivos_habituais": rng.integers(0, len(DISPOSITIVOS), size=(n_usuarios, 2)),
    }


def gerar(
    n_eventos: int = 2_000_000,
    dias: int = 30,
    n_usuarios: int = 800,
    taxa_anomalia: float = 0.012,
    fim: str = "2026-11-16",
    semente: int = 2026,
) -> pd.DataFrame:
    """Gera o fluxo de eventos com episodios de anomalia rotulados."""
    rng = np.random.default_rng(semente)
    pools = _pools(n_usuarios, semente)
    fim_ts = pd.Timestamp(fim).normalize() + pd.Timedelta(days=1)
    inicio_ts = fim_ts - pd.Timedelta(days=dias)

    n_anomalos = int(n_eventos * taxa_anomalia)
    n_normais = n_eventos - n_anomalos

    partes = [_lote_normal(n_normais, dias, inicio_ts, pools, rng)]
    partes += _lotes_anomalos(n_anomalos, dias, inicio_ts, pools, rng)

    df = pd.concat(partes, ignore_index=True)
    df = df.sort_values("ts", ignore_index=True)
    df["evento_id"] = np.arange(1, len(df) + 1, dtype=np.int64)
    df["dia"] = df["ts"].dt.strftime("%Y-%m-%d")
    df["hora"] = df["ts"].dt.hour.astype(np.int16)
    return df[
        ["evento_id", "ts", "dia", "hora", "usuario", "ip", "dispositivo", "tipo",
         "algoritmo", "resultado", "latencia_ms", "bytes", "conta", "valor",
         "integridade_ok", "rotulo"]
    ]


def _timestamps(n: int, dias: int, inicio: pd.Timestamp, rng, horas=None) -> pd.Series:
    dia = rng.integers(0, dias, size=n)
    hora = rng.choice(24, size=n, p=PERFIL_HORA) if horas is None else rng.choice(horas, size=n)
    seg = rng.integers(0, 3600, size=n)
    offsets = (dia * 86400 + hora * 3600 + seg).astype("int64")
    return pd.to_datetime(inicio.value + offsets * 1_000_000_000)


def _lote_normal(n: int, dias: int, inicio: pd.Timestamp, pools: dict, rng) -> pd.DataFrame:
    # Atividade por usuario segue lei de potencia: poucos muito ativos.
    peso = rng.pareto(1.6, size=len(pools["usuarios"])) + 1
    u_idx = rng.choice(len(pools["usuarios"]), size=n, p=peso / peso.sum())
    tipo = rng.choice(TIPOS, size=n, p=TIPO_P)
    falha = rng.random(n) < 0.018  # taxa de falha de fundo
    bytes_ = (rng.lognormal(7.6, 1.3, size=n)).astype(np.int64).clip(16, 50_000_000)

    # 95% dos acessos vem de um IP habitual do proprio usuario; 93% de um
    # dispositivo habitual. O restante e viagem, troca de aparelho, rede nova.
    qual = rng.integers(0, 2, size=n)
    ip_idx = np.where(
        rng.random(n) < 0.95,
        pools["ips_habituais"][u_idx, qual],
        rng.integers(0, len(pools["ips"]), size=n),
    )
    dev_idx = np.where(
        rng.random(n) < 0.93,
        pools["dispositivos_habituais"][u_idx, qual],
        rng.integers(0, len(DISPOSITIVOS), size=n),
    )

    return pd.DataFrame({
        "ts": _timestamps(n, dias, inicio, rng),
        "usuario": pools["usuarios"][u_idx],
        "ip": pools["ips"][ip_idx],
        "dispositivo": np.array(DISPOSITIVOS)[dev_idx],
        "tipo": tipo,
        "algoritmo": rng.choice(ALGORITMOS, size=n, p=[0.62, 0.38]),
        "resultado": np.where(falha, "falha", "sucesso"),
        "latencia_ms": (rng.lognormal(2.6, 0.5, size=n)).round(2),
        "bytes": bytes_,
        "conta": pools["contas"][u_idx],
        "valor": np.where(tipo == "transferencia", rng.lognormal(6.4, 1.2, size=n).round(2), 0.0),
        "integridade_ok": rng.random(n) > 0.0008,
        "rotulo": NORMAL,
    })


def _lotes_anomalos(total: int, dias: int, inicio: pd.Timestamp, pools: dict, rng) -> list[pd.DataFrame]:
    """Episodios concentrados: um usuario, uma janela curta, assinatura propria."""
    por_tipo = total // len(ANOMALIAS)
    saidas = []

    for rotulo in ANOMALIAS:
        n_episodios = max(1, por_tipo // 250)
        tamanhos = rng.integers(120, 420, size=n_episodios)
        tamanhos = (tamanhos * por_tipo / tamanhos.sum()).astype(int).clip(20)
        for tam in tamanhos:
            u = int(rng.integers(0, len(pools["usuarios"])))
            dia = int(rng.integers(0, dias))
            base = inicio + pd.Timedelta(days=dia)
            saidas.append(_episodio(rotulo, int(tam), u, base, pools, rng))
    return saidas


def _episodio(rotulo: str, n: int, u: int, base: pd.Timestamp, pools: dict, rng) -> pd.DataFrame:
    usuario = pools["usuarios"][u]
    conta = pools["contas"][u]
    # Rajada concentrada em poucos minutos; o acesso atipico se espalha pela madrugada.
    atipico = rotulo == "acesso_atipico"
    duracao = 5400 if atipico else int(rng.integers(120, 900))
    # O acesso atipico e noturno por definicao; os demais ataques se escondem
    # no horario de maior trafego, seguindo o mesmo perfil diurno dos usuarios.
    hora_ini = int(rng.integers(0, 4)) if atipico else int(rng.choice(24, p=PERFIL_HORA))
    t0 = base + pd.Timedelta(hours=hora_ini)
    ts = pd.to_datetime(t0.value + np.sort(rng.integers(0, max(duracao, 1), size=n)).astype("int64") * 1_000_000_000)

    # Por padrao o episodio ocorre a partir do ambiente habitual do usuario
    # (credencial roubada, falha interna); so alguns ataques trocam de origem.
    habitual_ip = pools["ips"][pools["ips_habituais"][u, rng.integers(0, 2, size=n)]]
    habitual_dev = np.array(DISPOSITIVOS)[pools["dispositivos_habituais"][u, rng.integers(0, 2, size=n)]]
    d = {
        "ts": ts, "usuario": usuario, "conta": conta, "rotulo": rotulo,
        "algoritmo": rng.choice(ALGORITMOS, size=n),
        "latencia_ms": rng.lognormal(2.6, 0.5, size=n).round(2),
        "bytes": rng.lognormal(7.6, 1.3, size=n).astype(np.int64).clip(16),
        "valor": np.zeros(n), "integridade_ok": np.ones(n, dtype=bool),
        "ip": habitual_ip,
        "dispositivo": habitual_dev,
        "tipo": np.full(n, "autenticacao"),
        "resultado": np.full(n, "falha"),
    }

    if rotulo == "forca_bruta_login":
        # Muitas tentativas, quase todas falhando, de poucos IPs estrangeiros.
        d["ip"] = pools["ips_suspeitos"][rng.integers(0, 6, size=n)]
        d["resultado"] = np.where(rng.random(n) < 0.97, "falha", "sucesso")
        d["latencia_ms"] = rng.lognormal(1.9, 0.4, size=n).round(2)
    elif rotulo == "falhas_decifragem":
        d["tipo"] = np.full(n, "decifragem")
        d["resultado"] = np.where(rng.random(n) < 0.93, "falha", "sucesso")
        d["integridade_ok"] = rng.random(n) > 0.85
        d["latencia_ms"] = rng.lognormal(3.4, 0.6, size=n).round(2)
    elif rotulo == "adulteracao_arquivo":
        d["tipo"] = np.full(n, "acesso_arquivo")
        d["resultado"] = np.where(rng.random(n) < 0.55, "falha", "sucesso")
        d["integridade_ok"] = rng.random(n) > 0.78  # falha de HMAC: conteudo alterado
        d["bytes"] = rng.lognormal(9.5, 1.0, size=n).astype(np.int64)
    elif rotulo == "acesso_atipico":
        # Volume normal, porem de madrugada, por IP estrangeiro e dispositivo novo.
        d["ip"] = pools["ips_suspeitos"][rng.integers(0, len(pools["ips_suspeitos"]), size=n)]
        d["tipo"] = rng.choice(TIPOS, size=n, p=TIPO_P)
        d["resultado"] = np.where(rng.random(n) < 0.12, "falha", "sucesso")
        d["dispositivo"] = np.full(n, "api-parceiro")
    elif rotulo == "surto_de_eventos":
        # Exfiltracao: taxa e volume de dados muito acima do normal, sem erros.
        d["tipo"] = rng.choice(["cifragem", "esteganografia"], size=n, p=[0.5, 0.5])
        d["resultado"] = np.where(rng.random(n) < 0.03, "falha", "sucesso")
        d["bytes"] = rng.lognormal(11.5, 0.8, size=n).astype(np.int64)
        d["latencia_ms"] = rng.lognormal(4.0, 0.5, size=n).round(2)

    e_transf = d["tipo"] == "transferencia"
    d["valor"] = np.where(e_transf, rng.lognormal(7.8, 1.1, size=n).round(2), 0.0)
    return pd.DataFrame(d)
