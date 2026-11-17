# FinalPay — Sistema Criptográfico e Análise de Ataques

Cofre criptográfico de um banco digital fictício que **mede a própria segurança**.
Cifra transações com um algoritmo simétrico autoral (FPC-128), esconde o resultado
dentro de imagens, registra ~2 milhões de eventos num lago de dados, detecta
comportamento anormal com aprendizado de máquina — e então **ataca a si mesmo**
com força bruta, criptanálise diferencial e análise estatística para dizer, com
números, se é seguro.

> **Disciplina:** Cibersegurança Aplicada a Dados e IA — CESAR School
> **Professora:** Renatta Nigro
> **Grupo:** Claudio Alves, Ian Nunes, Maria Augusta, Gabriel Lima, Gabriel Rodrigues, Vinicius Ventura

---

## Como rodar

```bash
python3 -m venv .venv && source .venv/bin/activate     # Python 3.11+
pip install -r requirements.txt

python -m finalpay.experiments      # roda a bateria (~10 s) e grava results/experimentos.json
uvicorn finalpay.api:app --reload   # dashboard em http://127.0.0.1:8000
```

A bateria precisa rodar antes do dashboard: é ela que produz todos os números.
Para uma volta rápida, `python -m finalpay.experiments --rapido` usa amostras
menores. O botão **Executar bateria**, no topo do dashboard, refaz tudo pela
interface, e a tela recarrega sozinha quando o arquivo de resultados muda.

Outros comandos:

```bash
pytest -q                 # 42 testes
python -m finalpay.report # regera docs/RELATORIO.md a partir dos resultados
python -m finalpay.slides # regera docs/slides/index.html
```

---

## O que tem dentro

| # | Camada da arquitetura | Onde está | O que faz |
|---|---|---|---|
| 1 | Entrada de dados | `finalpay/api.py` | texto, arquivos e imagens |
| 2 | Criptografia | `finalpay/cipher.py`, `finalpay/baseline.py` | FPC-128 autoral + AES-256-GCM |
| 3 | Esteganografia | `finalpay/stego.py` | LSB em PNG, posições derivadas da chave |
| 4 | Big Data | `finalpay/events.py`, `finalpay/lake.py` | Parquet particionado + DuckDB |
| 5 | Inteligência Artificial | `finalpay/detect.py` | Isolation Forest sobre janelas |
| 6 | Dashboard | `finalpay/api.py`, `web/` | painel, laboratório e veredito |

Em volta disso: `finalpay/attacks/` (os três ataques), `finalpay/metrics.py`
(entropia, qui-quadrado, testes NIST), `finalpay/experiments.py` (a bateria) e
`finalpay/report.py` / `finalpay/slides.py` (os entregáveis).

### FPC-128, em uma tela

Rede de substituição-permutação, bloco de 128 bits, chave de 256 bits, 14 rodadas.
Cada rodada aplica as quatro operações exigidas no enunciado:

```
AddRoundKey   estado ← estado ⊕ subchave[r]        XOR / confusão
SubBytes      estado ← S[estado]                   substituição não-linear em GF(2⁸)
ShiftRows     estado ← estado[π]                   permutação de bytes
MixColumns    estado ← M · estado  em GF(2⁸)       difusão (matriz MDS)
```

A chave nunca é fixa: `PBKDF2(senha, salt aleatório)` → `HKDF(nonce aleatório)` →
subchaves de rodada. Cifrar a mesma mensagem duas vezes com a mesma senha produz
envelopes diferentes. O envelope é autenticado com HMAC-SHA256.

---

## Onde cada requisito do enunciado está

| Requisito | Arquivo | Como verificar |
|---|---|---|
| Criptografia simétrica, chave dinâmica | `finalpay/cipher.py` | `pytest -k chave_dinamica` |
| XOR, substituição, permutação, blocos | `finalpay/cipher.py` | dashboard → Cifragem FPC-128 |
| Difusão / confusão | `finalpay/cipher.py` | `pytest -k difusao` |
| Esteganografia em imagens | `finalpay/stego.py` | dashboard → Esteganografia |
| Big Data de eventos | `finalpay/events.py`, `lake.py` | dashboard → Big Data |
| IA para anomalias (5 tipos) | `finalpay/detect.py` | dashboard → Inteligência Artificial |
| Ataque de força bruta | `attacks/brute_force.py` | Laboratório → Força bruta |
| Ataque diferencial | `attacks/differential.py` | Laboratório → Diferencial |
| Ataque estatístico | `attacks/statistical.py` | Laboratório → Estatístico |
| Efeito avalanche | `attacks/differential.py` | `pytest -k avalanche` |
| Dashboard | `web/`, `finalpay/api.py` | `uvicorn finalpay.api:app` |
| Respostas da Parte 4 | `finalpay/experiments.py` | dashboard → Veredito |

---

## O resultado, em resumo

| Medida | FPC-128 íntegro | Variante enfraquecida |
|---|---|---|
| Efeito avalanche | ~50% dos bits | ~3% dos bits |
| Entropia da saída | ~7,998 bits/byte | ~6,5 bits/byte |
| Texto recuperado por análise de frequência | abaixo do acaso | ~65% |
| Distinguível de permutação aleatória | não | sim |

Os três ataques falham contra a cifra íntegra e funcionam contra a variante sem
difusão. É dessa comparação que sai a conclusão: **o que sustenta a segurança é a
difusão e o modo de operação, não o número de rodadas.**

### A ressalva que vale mais que o resultado

O FPC-128 **não é uma cifra de produção**. Não passou por criptanálise
independente, não é de tempo constante e não recebeu análise linear nem prova
formal de resistência. Uma cifra só se torna confiável depois de anos de
tentativa pública de quebra. É exatamente por isso que a camada AES-256 existe no
sistema: o FPC-128 é o objeto de estudo, o AES-256 é o que protegeria o dinheiro.

Os eventos de segurança são **sintéticos e rotulados** — é o que permite medir
precisão e revocação do detector. Não há dados de usuários reais.

---

## Entregáveis

- `docs/RELATORIO.md` — relatório técnico completo (gerado dos resultados)
- `docs/slides/index.html` — slides da apresentação (abra no navegador; `P` imprime em PDF)
- `results/experimentos.json` — todas as medições, regeneráveis por comando
- `DESIGN.md` — o sistema visual do dashboard
