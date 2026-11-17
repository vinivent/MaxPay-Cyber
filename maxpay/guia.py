"""Gera o roteiro da apresentacao em PDF: o que falar, tela a tela.

Le os titulos do deck ja gerado, para o roteiro nunca descrever uma tela que
nao existe mais, e os numeros da bateria, para nao envelhecer.

    python -m maxpay.slides && python -m maxpay.guia
"""

from __future__ import annotations

import html
import re
import shutil
import subprocess
from pathlib import Path

from maxpay.experiments import carregar
from maxpay.notas import NOTAS
from maxpay.report import DOCS, GRUPO, i, n
from maxpay.slides import DESTINO as DECK

HTML_SAIDA = DOCS / "GUIA-APRESENTACAO.html"
PDF_SAIDA = DOCS / "GUIA-APRESENTACAO.pdf"

CHROME = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome", "chromium",
]

# Quem fala o que. Seis pessoas, seis blocos.
DIVISAO = [
    ("Abertura e arquitetura", "1 a 3"),
    ("A cifra", "4 a 6"),
    ("Esteganografia e antifraude", "7 e 8"),
    ("Avalanche e padrões", "9 a 11"),
    ("Os três ataques", "12 a 14"),
    ("Veredito e fechamento", "15 a 19"),
]

CSS = """
@page { size: A4 portrait; margin: 18mm 16mm 16mm; }
* { box-sizing: border-box; }
body {
  margin: 0; color: #18181B; background: #fff;
  font: 400 10.5pt/1.5 'Geist', ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif;
  letter-spacing: -0.005em;
}
h1 { font-size: 22pt; line-height: 1.1; letter-spacing: -0.03em; margin: 0 0 6pt; font-weight: 600; }
.sub { color: #55555C; font-size: 10pt; margin: 0 0 3pt; }
.regra { border: 0; border-top: 1px solid #D4D4D8; margin: 14pt 0; }
h2 { font-size: 12pt; letter-spacing: -0.015em; margin: 0 0 8pt; font-weight: 600; }
table { width: 100%; border-collapse: collapse; font-size: 9.5pt; }
td { padding: 4pt 8pt 4pt 0; border-bottom: 1px solid #EDEDEF; vertical-align: top; }
td.q { color: #55555C; white-space: nowrap; width: 76pt; }
.aviso { font-size: 9.5pt; color: #55555C; }
.aviso b { color: #18181B; font-weight: 500; }

/* Uma tela por bloco, nunca quebrada no meio da pagina. */
.tela { break-inside: avoid; margin: 0 0 13pt; padding-left: 52pt; position: relative; }
.tela .n {
  position: absolute; left: 0; top: 1pt; width: 42pt;
  font: 500 9pt/1.4 'Geist Mono', ui-monospace, Menlo, monospace;
  color: #8F8F96; letter-spacing: 0.02em;
}
.tela .t { font-weight: 600; font-size: 11pt; letter-spacing: -0.015em; margin: 0 0 1pt; }
.tela .onde { font-size: 8.5pt; color: #8F8F96; margin: 0 0 5pt; letter-spacing: 0.04em; text-transform: uppercase; }
.tela p.fala { margin: 0 0 5pt; }
.tela p.fala:last-child { margin-bottom: 0; }

.pergunta { break-inside: avoid; margin-bottom: 10pt; }
.pergunta .p { font-weight: 600; margin: 0 0 3pt; }
.pergunta .r { margin: 0; color: #3A3A40; }
.rodape { margin-top: 16pt; padding-top: 8pt; border-top: 1px solid #D4D4D8; font-size: 8.5pt; color: #8F8F96; }
"""


def _titulos_do_deck() -> dict[str, tuple[str, str]]:
    """id -> (titulo, secao), lidos do deck gerado."""
    if not DECK.exists():
        return {}
    bruto = DECK.read_text(encoding="utf-8")
    saida = {}
    for m in re.finditer(r'<section class="slide[^"]*" data-id="([a-z0-9]+)">(.*?)</section>', bruto, re.S):
        sid, corpo = m.group(1), m.group(2)
        sec = re.search(r'<span class="secao">(.*?)</span>', corpo)
        tit = re.search(r"<h1[^>]*>(.*?)</h1>|<h2[^>]*>(.*?)</h2>", corpo, re.S)
        texto = ""
        if tit:
            texto = re.sub(r"<[^>]+>", " ", tit.group(1) or tit.group(2) or "")
            texto = html.unescape(re.sub(r"\s+", " ", texto)).strip()
        saida[sid] = (texto, html.unescape(sec.group(1)) if sec else "")
    return saida


def gerar_html(res: dict) -> str:
    c, pj = res["cifra"], res["cifra"]["projeto"]
    freq_f, freq_c = res["frequencia"]["sem_difusao"], res["frequencia"]["com_difusao"]
    ia = res["bigdata"]["ia"]["metricas"]
    est = res["estego"]
    v = res["veredito"]
    surto = next(t for t in ia["por_tipo"] if t["tipo"] == "surto_de_eventos")
    titulos = _titulos_do_deck()
    ordem = list(NOTAS)

    telas = []
    for k, sid in enumerate(ordem, 1):
        titulo, secao = titulos.get(sid, (sid, ""))
        falas = "".join(f'<p class="fala">{html.escape(p.strip())}</p>'
                        for p in NOTAS[sid].split("\n\n") if p.strip())
        telas.append(
            f'<div class="tela"><span class="n">Slide {k:02d}</span>'
            f'<p class="t">{html.escape(titulo)}</p>'
            f'<p class="onde">{html.escape(secao)}</p>{falas}</div>'
        )

    perguntas = [
        ("Isso não é só o AES com outro nome?",
         f"A estrutura é a mesma família, de propósito. Os três componentes são nossos: "
         f"afim da S-box {tuple(pj['sbox_rotacoes'])} com {pj['sbox_constante']}, permutação "
         f"{tuple(pj['deslocamentos'])}, difusão {tuple(pj['matriz_difusao'])}. A S-box difere "
         f"da do AES nas 256 posições, e cada escolha passou por verificação matemática."),
        ("Vocês provaram que a cifra é segura?",
         "Não. Provamos que ela resistiu aos três ataques que sabemos executar. Cifra confiável "
         "se faz com anos de tentativa pública de quebra. É por isso que o AES-256 está no sistema."),
        (f"Por que o surto de eventos tem só {n(surto['revocacao_pct'], 1)}% de detecção?",
         f"Porque revocação depende do orçamento de alertas. O modelo põe o surto no "
         f"{n(surto['percentil_mediano'], 2)}% mais arriscado de {i(ia['janelas'])} janelas: ele "
         f"enxerga, mas perde a disputa pelo 1% que a equipe revisa para anomalias que geram falha."),
        ("Os dados são reais?",
         "São sintéticos e rotulados, de propósito. Sem rótulo não haveria como medir precisão "
         "e revocação do detector."),
        (f"Por que {c['rodadas']} rodadas se a difusão fecha na rodada "
         f"{v['efeito_avalanche']['rodadas_ate_difusao_total']}?",
         "Margem de segurança. O resto das rodadas existe para que um ataque que avance algumas "
         "ainda esbarre em muitas pela frente. Mesma lógica do AES-256."),
        ("Qual ataque foi mais eficaz?",
         f"{v['ataque_mais_eficaz']['resposta']}. Recuperou {n(freq_f['acuracia_pct'])}% do texto "
         f"da variante sem difusão, sem usar chave. Contra a cifra íntegra cai para "
         f"{n(freq_c['acuracia_pct'])}%, abaixo da linha de base de "
         f"{n(freq_c['linha_base_unigrama_pct'])}%."),
    ]

    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>MaxPay: roteiro da apresentação</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&family=Geist+Mono:wght@500&display=swap">
<style>{CSS}</style></head><body>

<h1>MaxPay: roteiro da apresentação</h1>
<p class="sub">{html.escape(", ".join(GRUPO))}</p>
<p class="sub">Cibersegurança Aplicada a Dados e IA · CESAR School · Professora Renatta Nigro</p>

<hr class="regra">

<h2>Como usar</h2>
<p class="aviso">São <b>{len(ordem)} telas</b>, cerca de <b>15 minutos</b> de fala mais 4 ou 5 de
demonstração ao vivo. O texto de cada tela abaixo é para ser lido em voz alta. O mesmo texto está
dentro do deck: abra <b>docs/slides/index.html</b> e aperte a tecla <b>N</b>.</p>

<table>{"".join(f'<tr><td class="q">Telas {t}</td><td>{html.escape(b)}</td></tr>' for b, t in DIVISAO)}</table>

<p class="aviso" style="margin-top:10pt">Na demonstração, a parada que não pode ser cortada é a aba
<b>Resistência</b>: rode a análise de frequência com a difusão desligada, mostre os
{n(freq_f['acuracia_pct'])}% de texto recuperado, ligue a difusão e rode de novo.</p>

<hr class="regra">

{"".join(telas)}

<hr class="regra">

<h2>Se perguntarem</h2>
{"".join(f'<div class="pergunta"><p class="p">{html.escape(p)}</p><p class="r">{html.escape(r)}</p></div>' for p, r in perguntas)}

<p class="rodape">Números da bateria de {res['meta']['gerado_em'].replace('T', ' ')}.
Avalanche {n(res['diferencial']['mpc_integro']['media_pct'])}% ·
PSNR {n(est['qualidade']['psnr_db'])} dB ·
ROC AUC {n(ia['roc_auc'], 4)} ·
{i(res['bigdata']['resumo']['eventos'])} eventos.</p>

</body></html>"""


def _para_pdf(origem: Path, destino: Path) -> bool:
    navegador = next((c for c in CHROME if Path(c).exists() or shutil.which(c)), None)
    if not navegador:
        return False
    subprocess.run(
        [navegador, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
         f"--print-to-pdf={destino}", "--virtual-time-budget=10000", origem.as_uri()],
        check=True, capture_output=True, timeout=180,
    )
    return destino.exists()


def main() -> Path:
    res = carregar()
    if res is None:
        raise SystemExit("Rode `python -m maxpay.experiments` primeiro.")
    DOCS.mkdir(parents=True, exist_ok=True)
    HTML_SAIDA.write_text(gerar_html(res), encoding="utf-8")
    if not _para_pdf(HTML_SAIDA, PDF_SAIDA):
        raise SystemExit(f"HTML em {HTML_SAIDA}, mas nao achei o Chrome para gerar o PDF.")
    return PDF_SAIDA


if __name__ == "__main__":
    p = main()
    print(f"OK -> {p} ({p.stat().st_size / 1024:.0f} KB)")
