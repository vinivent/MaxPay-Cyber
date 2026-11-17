"""Camada de IA do FinalPay (etapa 5 da arquitetura).

Recebe as janelas ja agregadas pelo data lake e aponta comportamento anormal
com Isolation Forest, sem usar os rotulos no treino. Os rotulos existem apenas
para medir a qualidade da deteccao.

Cada alerta recebe uma explicacao: quais atributos sairam do padrao e a qual
dos cinco tipos de anomalia previstos no projeto a janela corresponde.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score, roc_auc_score

ATRIBUTOS = [
    "eventos", "ips_distintos", "dispositivos", "taxa_falha", "falhas_auth",
    "falhas_decifragem", "falhas_integridade", "acessos_arquivo", "eventos_ip_novo",
    "log_bytes", "bytes_por_evento", "latencia_media", "eventos_madrugada",
]

# Assinatura de cada anomalia prevista no projeto: os atributos que sobem juntos.
# O tipo atribuido a um alerta e aquele cuja assinatura mais se destaca.
ASSINATURAS = {
    "forca_bruta_login": (
        ["falhas_auth", "taxa_falha", "eventos_ip_novo"],
        "tentativas de autenticação falhando em rajada, a partir de IP não habitual",
    ),
    "falhas_decifragem": (
        ["falhas_decifragem", "taxa_falha"],
        "sequência anormal de falhas de descriptografia",
    ),
    "adulteracao_arquivo": (
        ["falhas_integridade", "acessos_arquivo"],
        "verificações de integridade falhando: conteúdo alterado após a cifragem",
    ),
    "acesso_atipico": (
        ["eventos_madrugada", "eventos_ip_novo", "ips_distintos"],
        "acesso concentrado na madrugada e a partir de origem não habitual",
    ),
    "surto_de_eventos": (
        ["log_bytes", "bytes_por_evento", "eventos"],
        "volume e taxa de geração de eventos muito acima do habitual",
    ),
}


def montar_atributos(janelas: pd.DataFrame) -> pd.DataFrame:
    df = janelas.copy()
    eventos = df["eventos"].clip(lower=1)
    df["taxa_falha"] = df["falhas"] / eventos
    df["log_bytes"] = np.log1p(df["bytes_total"])
    df["bytes_por_evento"] = df["bytes_total"] / eventos
    return df


class DetectorAnomalias:
    """Isolation Forest sobre janelas de comportamento.

    `contaminacao` e a fatia de janelas que a operacao aceita revisar por dia:
    e uma decisao de capacidade da equipe, nao sai dos rotulos.
    """

    def __init__(self, contaminacao: float = 0.01, n_arvores: int = 200, semente: int = 2026):
        self.contaminacao = contaminacao
        self.modelo = IsolationForest(
            n_estimators=n_arvores, contamination=contaminacao,
            random_state=semente, n_jobs=-1,
        )
        self.media_: pd.Series | None = None
        self.desvio_: pd.Series | None = None

    def treinar(self, janelas: pd.DataFrame) -> "DetectorAnomalias":
        df = montar_atributos(janelas)
        X = df[ATRIBUTOS]
        self.media_, self.desvio_ = X.mean(), X.std().replace(0, 1)
        self.modelo.fit(X)
        return self

    def pontuar(self, janelas: pd.DataFrame) -> pd.DataFrame:
        df = montar_atributos(janelas)
        X = df[ATRIBUTOS]
        # score_samples: quanto menor, mais anomalo. Invertemos para virar "risco".
        df["score"] = -self.modelo.score_samples(X)
        df["alerta"] = self.modelo.predict(X) == -1

        # Explicabilidade: desvios positivos, em desvios-padrao.
        z = ((X - self.media_) / self.desvio_).clip(lower=0)
        forca = pd.DataFrame(
            {tipo: z[cols].mean(axis=1) for tipo, (cols, _) in ASSINATURAS.items()},
            index=df.index,
        )
        df["tipo_previsto"] = forca.idxmax(axis=1)
        df["forca_assinatura"] = forca.max(axis=1).round(2)
        df["atributo_dominante"] = z.idxmax(axis=1)
        df["z_dominante"] = z.max(axis=1).round(2)
        df["explicacao"] = [ASSINATURAS[t][1] for t in df["tipo_previsto"]]
        # Sem desvio relevante nao ha assinatura a nomear.
        fraco = df["forca_assinatura"] < 1.0
        df.loc[fraco, "tipo_previsto"] = "comportamento_incomum"
        df.loc[fraco, "explicacao"] = "desvio difuso, sem assinatura dominante"
        return df


def _ponto_de_operacao(y: np.ndarray, score: np.ndarray, k: int) -> dict:
    """Precisao e revocacao se a equipe revisar as `k` janelas mais arriscadas."""
    k = max(1, min(k, len(y)))
    corte = np.argsort(-score)[:k]
    vp = int(y[corte].sum())
    return {
        "orcamento_alertas": k,
        "orcamento_pct": round(100 * k / len(y), 3),
        "verdadeiros_positivos": vp,
        "precisao": round(vp / k, 4),
        "revocacao": round(vp / max(y.sum(), 1), 4),
    }


def avaliar(pontuadas: pd.DataFrame) -> dict:
    """Qualidade da deteccao contra os rotulos reais (nunca vistos no treino)."""
    y = pontuadas["anomala"].astype(int).to_numpy()
    score = pontuadas["score"].to_numpy()
    pred = pontuadas["alerta"].to_numpy()

    vp = int((pred & (y == 1)).sum())
    fp = int((pred & (y == 0)).sum())
    fn = int((~pred & (y == 1)).sum())
    vn = int((~pred & (y == 0)).sum())
    precisao = vp / (vp + fp) if vp + fp else 0.0
    revocacao = vp / (vp + fn) if vp + fn else 0.0
    f1 = 2 * precisao * revocacao / (precisao + revocacao) if precisao + revocacao else 0.0
    ap = float(average_precision_score(y, score))

    por_tipo = []
    for rotulo, grupo in pontuadas[pontuadas["anomala"] == 1].groupby("rotulo_real"):
        detectadas = int(grupo["alerta"].sum())
        acertou = int((grupo.loc[grupo["alerta"], "tipo_previsto"] == rotulo).sum())
        por_tipo.append({
            "tipo": rotulo,
            "janelas": int(len(grupo)),
            "detectadas": detectadas,
            "revocacao_pct": round(100 * detectadas / len(grupo), 1),
            "tipo_correto": acertou,
            "acerto_tipo_pct": round(100 * acertou / detectadas, 1) if detectadas else 0.0,
        })

    return {
        "janelas": int(len(pontuadas)),
        "janelas_anomalas": int(y.sum()),
        "prevalencia_pct": round(100 * y.mean(), 3),
        "alertas": int(pred.sum()),
        "verdadeiros_positivos": vp,
        "falsos_positivos": fp,
        "falsos_negativos": fn,
        "verdadeiros_negativos": vn,
        "precisao": round(precisao, 4),
        "revocacao": round(revocacao, 4),
        "f1": round(f1, 4),
        "roc_auc": round(float(roc_auc_score(y, score)), 4),
        "average_precision": round(ap, 4),
        "ganho_sobre_acaso": round(ap / max(y.mean(), 1e-9), 1),
        "pontos_de_operacao": [
            _ponto_de_operacao(y, score, int(len(y) * frac)) for frac in (0.0025, 0.005, 0.01, 0.02)
        ],
        "precisao_no_k_ideal": _ponto_de_operacao(y, score, int(y.sum())),
        "por_tipo": sorted(por_tipo, key=lambda r: -r["revocacao_pct"]),
    }


def principais_alertas(pontuadas: pd.DataFrame, limite: int = 25) -> list[dict]:
    cols = ["usuario", "janela", "score", "tipo_previsto", "explicacao", "atributo_dominante",
            "z_dominante", "forca_assinatura", "eventos", "falhas", "ips_distintos",
            "eventos_ip_novo", "rotulo_real", "anomala"]
    top = pontuadas.nlargest(limite, "score")[cols].copy()
    top["janela"] = top["janela"].astype(str)
    top["score"] = top["score"].round(4)
    return top.to_dict(orient="records")


def analisar(janelas: pd.DataFrame, contaminacao: float = 0.01) -> dict:
    det = DetectorAnomalias(contaminacao).treinar(janelas)
    pontuadas = det.pontuar(janelas)
    contagem, bordas = np.histogram(pontuadas["score"], bins=40)
    return {
        "contaminacao": contaminacao,
        "atributos": ATRIBUTOS,
        "metricas": avaliar(pontuadas),
        "alertas": principais_alertas(pontuadas),
        "distribuicao_score": {
            "contagem": contagem.tolist(),
            "bordas": [round(float(b), 4) for b in bordas],
        },
    }
