# MaxPay: Sistema Criptográfico e Análise de Ataques

Cofre criptográfico de um banco digital fictício que **mede a própria segurança**.
Cifra transações com um algoritmo simétrico próprio (MPC-128), esconde o resultado
dentro de imagens, registra ~2 milhões de eventos num lago de dados, detecta
comportamento anormal com aprendizado de máquina, e então **ataca a si mesmo**
com força bruta, criptanálise diferencial e análise estatística para dizer, com
números, se é seguro.

> **Disciplina:** Cibersegurança Aplicada a Dados e IA, CESAR School
> **Professora:** Renatta Nigro
> **Grupo:** Claudio Alves, Ian Nunes, Maria Augusta, Gabriel Lima, Gabriel Rodrigues, Vinicius Ventura

---

## Como rodar

```bash
python3 -m venv .venv && source .venv/bin/activate     # Python 3.11+
pip install -r requirements.txt

python -m maxpay.experiments      # roda a bateria (~10 s) e grava results/experimentos.json
uvicorn maxpay.api:app --reload   # dashboard em http://127.0.0.1:8000
```

A bateria precisa rodar antes do dashboard: é ela que produz todos os números.
Para uma volta rápida, `python -m maxpay.experiments --rapido` usa amostras
menores. O botão **Executar bateria**, no topo do dashboard, refaz tudo pela
interface, e a tela recarrega sozinha quando o arquivo de resultados muda.

Outros comandos:

```bash
pytest -q                  # 52 testes
python -m maxpay.experiments --bigdata   # refaz só o lago de eventos, a IA e as detecções
python -m maxpay.report    # regera docs/RELATORIO.md a partir dos resultados
python -m maxpay.slides    # regera docs/slides/index.html
python -m maxpay.guia      # regera docs/GUIA-APRESENTACAO.pdf, o roteiro falado
```

### Materiais da apresentação

As figuras de apoio e a versão PowerPoint do deck precisam de duas bibliotecas
a mais, que ficam fora de `requirements.txt` justamente para não pesar em quem
só quer rodar o sistema:

```bash
pip install -r requirements-deck.txt
python -m maxpay.figuras     # docs/figuras/*.png, tudo a partir dos resultados
python -m maxpay.pptx_deck   # docs/MaxPay-apresentacao.pptx, para importar no Canva
```

O deck que vale é `docs/slides/index.html`: ele lê os resultados e nunca
envelhece. O `.pptx` existe porque o Canva importa PowerPoint e não importa
HTML. No Canva: **Criar um design → Importar arquivo**.

---

## O que tem dentro

| # | Camada da arquitetura | Onde está | O que faz |
|---|---|---|---|
| 1 | Entrada de dados | `maxpay/api.py` | texto, arquivos e imagens |
| 2 | Criptografia | `maxpay/cipher.py`, `maxpay/baseline.py` | MPC-128 próprio + AES-256-GCM |
| 3 | Esteganografia | `maxpay/stego.py` | LSB em PNG, posições derivadas da chave |
| 4 | Big Data | `maxpay/registro.py`, `maxpay/events.py`, `maxpay/lake.py` | registro das operações, Parquet particionado e DuckDB |
| 5 | Inteligência Artificial | `maxpay/detect.py` | Isolation Forest sobre janelas |
| 6 | Dashboard | `maxpay/api.py`, `web/` | quatro abas, laudo e slides |

Em volta disso: `maxpay/attacks/` (os três ataques), `maxpay/metrics.py`
(entropia, qui-quadrado, testes NIST), `maxpay/experiments.py` (a bateria) e
`maxpay/report.py` / `maxpay/slides.py` (os entregáveis).

### Do cofre ao alerta, ao vivo

As seis camadas não são só módulos lado a lado: cada operação real percorre
todas elas.

```
Cofre / Ocultar  →  data/vivo/       evento em Parquet, com IP, dispositivo, resultado e integridade
                 →  DuckDB           a janela de 10 minutos do evento é reagregada
                 →  Isolation Forest o mesmo modelo treinado no histórico julga a janela
                 →  data/deteccoes/  janela acima do limiar vira detecção armazenada
                 →  Antifraude       painel "Cofre ao vivo"
```

O lago tem três conjuntos, todos fora do Git e recriados por comando:

| Pasta | Conteúdo | Quem escreve |
|---|---|---|
| `data/lake/` | histórico sintético e rotulado, ~2 milhões de eventos | a bateria |
| `data/vivo/` | operações reais do cofre | a API, a cada operação |
| `data/deteccoes/` | alertas emitidos pela IA, do histórico e ao vivo | a bateria e a API |

Para ver funcionando: abra a aba **Antifraude** e clique em **Simular ataque ao
cofre**. O botão dispara 12 tentativas reais de abrir um envelope com senhas de
dicionário; todas são recusadas, registradas, julgadas e a janela aparece como
alerta. Errar a senha à mão na aba Cofre, cinco vezes ou mais em dez minutos,
tem o mesmo efeito. O modelo só julga depois que a bateria gerou o histórico.

### MPC-128, em uma tela

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

A plataforma tem quatro abas: **Cofre**, **Ocultar**, **Antifraude** e
**Resistência**. É nelas que cada requisito pode ser visto rodando.

| Requisito | Arquivo | Como verificar |
|---|---|---|
| Criptografia simétrica, chave dinâmica | `maxpay/cipher.py` | `pytest -k chave_dinamica` |
| XOR, substituição, permutação, blocos | `maxpay/cipher.py` | aba Cofre |
| Difusão / confusão | `maxpay/cipher.py` | `pytest -k difusao` |
| Esteganografia em imagens | `maxpay/stego.py` | aba Ocultar |
| Big Data de eventos | `maxpay/events.py`, `lake.py` | aba Antifraude |
| Logs das operações criptográficas | `maxpay/registro.py` | aba Cofre, "Operações registradas" |
| Tentativas de acesso e falhas de autenticação | `maxpay/registro.py`, `events.py` | `pytest -k senha_errada` |
| Armazenamento das detecções de anomalia | `maxpay/lake.py` | `pytest -k deteccoes` |
| IA para anomalias (5 tipos) | `maxpay/detect.py` | aba Antifraude |
| IA julgando operações reais | `maxpay/registro.py` | aba Antifraude, "Cofre ao vivo" |
| Ataque de força bruta | `attacks/brute_force.py` | aba Resistência |
| Ataque diferencial | `attacks/differential.py` | aba Resistência |
| Ataque estatístico | `attacks/statistical.py` | aba Resistência |
| Efeito avalanche | `attacks/differential.py` | `pytest -k avalanche` |
| Dashboard | `web/`, `maxpay/api.py` | `uvicorn maxpay.api:app` |
| Respostas da Parte 4 | `maxpay/experiments.py` | `docs/RELATORIO.md` §7 |

---

## O resultado, em resumo

| Medida | MPC-128 íntegro | Variante enfraquecida |
|---|---|---|
| Efeito avalanche | metade dos bits, como o AES-256 | praticamente nenhum bit |
| Entropia da saída | no teto de 8 bits/byte | bem abaixo do teto |
| Texto recuperado por análise de frequência | abaixo da linha de base | mais da metade do texto |
| Distinguível de permutação aleatória | não | sim |

Os valores exatos não estão escritos aqui de propósito: eles mudam a cada
execução da bateria, e número copiado à mão envelhece sem avisar. Rode
`python -m maxpay.experiments` e leia `docs/RELATORIO.md`, que é gerado a partir
de `results/experimentos.json`.

Os três ataques falham contra a cifra íntegra e funcionam contra a variante sem
difusão. É dessa comparação que sai a conclusão: **o que sustenta a segurança é a
difusão e o modo de operação, não o número de rodadas.**

### A ressalva que vale mais que o resultado

O MPC-128 **não é uma cifra de produção**. Não passou por criptanálise
independente, não é de tempo constante e não recebeu análise linear nem prova
formal de resistência. Uma cifra só se torna confiável depois de anos de
tentativa pública de quebra. É exatamente por isso que a camada AES-256 existe no
sistema: o MPC-128 é o objeto de estudo, o AES-256 é o que protegeria o dinheiro.

Os eventos do histórico são **sintéticos e rotulados**, é o que permite medir
precisão e revocação do detector. Não há dados de usuários reais. As operações
feitas no cofre são registradas de verdade, mas sem rótulo: o sistema roda local,
sem cadastro de usuários, e a única credencial é a senha do cofre.

---

## Entregáveis

- `docs/RELATORIO.md`, relatório técnico completo (gerado dos resultados)
- `docs/slides/index.html`, slides da apresentação (abra no navegador; `P` imprime em PDF)
- `docs/GUIA-APRESENTACAO.pdf`, roteiro da apresentação, tela a tela
- `results/experimentos.json`, todas as medições, regeneráveis por comando
- `DESIGN.md`, o sistema visual do dashboard
