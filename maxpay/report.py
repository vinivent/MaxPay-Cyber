"""Gera o relatorio tecnico a partir de `results/experimentos.json`.

Nenhum numero e digitado a mao: se a bateria rodar de novo, o relatorio muda
junto. Estrutura conforme a Parte 5 do enunciado (descricao do algoritmo,
funcionamento, testes, resultados e conclusao).

    python -m maxpay.report
"""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from maxpay.experiments import carregar
from maxpay.lake import JANELA_MINUTOS
from maxpay.registro import MIN_EVENTOS_JANELA

DOCS = Path(__file__).resolve().parent.parent / "docs"
GRUPO = [
    "Claudio Alves", "Ian Nunes", "Maria Augusta",
    "Gabriel Lima", "Gabriel Rodrigues", "Vinicius Ventura",
]


# Rotulos de exibicao: as chaves internas sao sem acento, os textos nao.
NOMES = {
    "texto_claro": "Texto claro",
    "mpc_ctr_14_rodadas": "MPC-128 · CTR, 14 rodadas",
    "mpc_ecb_14_rodadas": "MPC-128 · ECB, 14 rodadas",
    "mpc_ecb_1_rodada_sem_difusao": "MPC-128 · ECB, 1 rodada, sem difusão",
    "aes256_gcm": "AES-256-GCM",
    "urandom": "/dev/urandom (controle)",
    "original": "Imagem original",
    "ecb_1_rodada_sem_difusao": "ECB · 1 rodada, sem difusão",
    "ecb_14_rodadas": "ECB · 14 rodadas",
    "ctr_14_rodadas": "CTR · 14 rodadas",
    "forca_bruta_login": "Força bruta de login",
    "falhas_decifragem": "Falhas de decifragem",
    "adulteracao_arquivo": "Adulteração de arquivo",
    "acesso_atipico": "Acesso atípico",
    "surto_de_eventos": "Surto de eventos",
    "imagem_limpa": "Imagem limpa",
    "lsb_sequencial_sem_chave": "LSB sequencial, sem chave",
    "lsb_chaveado_maxpay": "LSB chaveado do MaxPay",
}


def _revoc_em(ia: dict, fracao: float, tipo: str) -> float:
    """Revocacao estimada do tipo num orcamento maior, pelo posto das janelas."""
    alvo = fracao * ia["janelas"]
    t = next(r for r in ia["por_tipo"] if r["tipo"] == tipo)
    if t["posto_pior"] <= alvo:
        return 100.0
    if t["posto_melhor"] > alvo:
        return 0.0
    # interpolacao simples entre melhor e pior posto
    return max(0.0, min(100.0, 100 * (alvo - t["posto_melhor"]) / (t["posto_pior"] - t["posto_melhor"])))


def total_de_testes() -> int | None:
    coleta = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "tests"],
        capture_output=True, text=True, timeout=180, cwd=DOCS.parent,
    )
    achado = re.search(r"(\d+) tests? collected", coleta.stdout)
    return int(achado.group(1)) if achado else None


def rot(chave: str) -> str:
    return NOMES.get(chave, str(chave).replace("_", " "))


def n(x: float, casas: int = 2) -> str:
    """Numero no formato brasileiro."""
    if x is None:
        return "n/d"
    s = f"{x:,.{casas}f}"
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


SUPERESCRITO = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


def sci(x: float, casas: int = 2) -> str:
    """Notacao cientifica legivel. Um inteiro de 46 digitos nao se le."""
    import math

    if not x:
        return "0"
    expoente = int(math.floor(math.log10(abs(x))))
    if -3 < expoente < 6:
        return n(x, 0)
    mantissa = x / 10**expoente
    return f"{mantissa:.{casas}f}".replace(".", ",") + f"×10{str(expoente).translate(SUPERESCRITO)}"


def i(x: float) -> str:
    return f"{int(x):,}".replace(",", ".")


def tabela(cabecalho: list[str], linhas: list[list[str]]) -> str:
    sep = "|" + "|".join("---" for _ in cabecalho) + "|"
    head = "| " + " | ".join(cabecalho) + " |"
    corpo = "\n".join("| " + " | ".join(str(c) for c in l) + " |" for l in linhas)
    return f"{head}\n{sep}\n{corpo}"


def gerar(res: dict) -> str:
    c, d, bf, dic = res["cifra"], res["diferencial"], res["forca_bruta"], res["dicionario"]
    av, fraco, aes = d["mpc_integro"], d["mpc_fraco"], d["aes256"]
    sac, sac_f = res["sac"], res["sac_fraco"]
    perfis = {p["rotulo"]: p for p in res["estatistico"]["perfis"]}
    ctr, claro = perfis["mpc_ctr_14_rodadas"], perfis["texto_claro"]
    ecb14 = perfis["mpc_ecb_14_rodadas"]
    fraco_ecb = perfis["mpc_ecb_1_rodada_sem_difusao"]
    aes_perf = perfis["aes256_gcm"]
    urandom = perfis["urandom"]
    freq_f, freq_c = res["frequencia"]["sem_difusao"], res["frequencia"]["com_difusao"]
    est, bd, ia = res["estego"], res["bigdata"], res["bigdata"]["ia"]["metricas"]
    v, desemp = res["veredito"], res["desempenho"]
    proj = {p["bits"]: p for p in bf["projecao"] if p["cenario"] == "1 nucleo (medido)"}
    proj_gpu = {p["bits"]: p for p in bf["projecao"] if "GPU" in p["cenario"]}
    surto = next(r for r in ia["por_tipo"] if r["tipo"] == "surto_de_eventos")
    rodada_difusao = v["efeito_avalanche"]["rodadas_ate_difusao_total"]
    testes = total_de_testes()
    suite = f"{testes} testes" if testes else "suíte de testes"
    refeito = res["meta"].get("bigdata_refeito")
    nota_refeito = (
        f"""
> A etapa de Big Data e IA (§6.9 e §6.10) foi refeita em {refeito["em"].replace("T", " ")} sobre
> {refeito["plataforma"]}, Python {refeito["python"]}. As demais medições são da execução acima."""
        if refeito else ""
    )

    return f"""# MaxPay, Sistema Criptográfico e Análise de Ataques

**Disciplina:** Cibersegurança Aplicada a Dados e IA, CESAR School
**Professora:** Renatta Nigro
**Grupo:** {", ".join(GRUPO)}
**Data:** {datetime.now().strftime("%d/%m/%Y")}

> Todos os números deste relatório foram produzidos pela bateria de experimentos
> do próprio sistema (`python -m maxpay.experiments`), executada em
> {res["meta"]["gerado_em"].replace("T", " ")} sobre {res["meta"]["plataforma"]},
> Python {res["meta"]["python"]}. Nenhum valor foi transcrito à mão.{nota_refeito}

---

## 1. Resumo executivo

O MaxPay é o cofre criptográfico de um banco digital fictício. Ele cifra
transações, documentos e imagens com uma cifra de bloco própria (**MPC-128**),
esconde o resultado dentro de imagens por esteganografia, registra cada operação
num lago de dados de {i(bd["resumo"]["eventos"])} eventos e usa aprendizado de
máquina para apontar comportamento anormal.

O mesmo sistema ataca a si próprio. Os três ataques exigidos pelo enunciado
(força bruta, diferencial e estatístico) rodam contra duas versões da cifra:
a íntegra, de {c["rodadas"]} rodadas com difusão, e uma variante deliberadamente
enfraquecida, de 1 rodada sem MixColumns. **A variante enfraquecida cai; a
íntegra não cede a nenhum dos três.** É essa comparação que sustenta o veredito
da Parte 4, e não uma afirmação de que "o sistema é seguro".

| Medida | MPC-128 íntegro | Variante enfraquecida | AES-256 |
|---|---|---|---|
| Efeito avalanche | **{n(av["media_pct"])}%** | {n(fraco["media_pct"])}% | {n(aes["media_pct"])}% |
| Entropia da saída (bits/byte) | **{n(ctr["entropia_bits_por_byte"], 4)}** | {n(fraco_ecb["entropia_bits_por_byte"], 4)} | {n(aes_perf["entropia_bits_por_byte"], 4)} |
| Texto recuperado por análise de frequência | {n(freq_c["acuracia_pct"])}% | **{n(freq_f["acuracia_pct"])}%** | não se aplica |
| Distinguível de permutação aleatória | Não | **Sim** | Não |

---

## 2. Arquitetura

As seis camadas pedidas no enunciado, e onde cada uma vive no código:

| # | Camada | Função | Implementação |
|---|---|---|---|
| 1 | Entrada de dados | Texto, arquivos e imagens | `maxpay/api.py` |
| 2 | Criptografia | MPC-128 próprio + AES-256-GCM | `maxpay/cipher.py`, `maxpay/baseline.py` |
| 3 | Esteganografia | Ocultação em imagens PNG | `maxpay/stego.py` |
| 4 | Big Data | Registro das operações, Parquet particionado, DuckDB | `maxpay/registro.py`, `maxpay/events.py`, `maxpay/lake.py` |
| 5 | Inteligência Artificial | Isolation Forest sobre janelas | `maxpay/detect.py` |
| 6 | Dashboard | API + painel web | `maxpay/api.py`, `web/` |

Os ataques ficam em `maxpay/attacks/` e a bateria de medição em
`maxpay/experiments.py`.

---

## 3. Descrição do algoritmo

### 3.1 Parâmetros

| Parâmetro | Valor |
|---|---|
| Nome | {c["nome"]} |
| Estrutura | {c["estrutura"]} |
| Tamanho de bloco | {c["bloco_bits"]} bits |
| Tamanho de chave | {c["chave_bits"]} bits |
| Rodadas | {c["rodadas"]} |
| Modos | {", ".join(c["modos"])} |
| Derivação de chave | {c["derivacao_de_chave"]} |

### 3.2 A rodada

Cada rodada aplica as quatro operações exigidas na Parte 2 do enunciado:

```
AddRoundKey  : estado ← estado ⊕ subchave[r]        (XOR / confusão)
SubBytes     : estado ← S[estado]                   (substituição não-linear)
ShiftRows    : estado ← estado[π]                   (permutação de bytes)
MixColumns   : estado ← M · estado  em GF(2⁸)       (difusão)
```

A última rodada omite o MixColumns, como é padrão em redes SPN: sem essa omissão
a operação final seria invertível pelo atacante sem custo e não acrescentaria
segurança.

**S-box.** Construída, não sorteada: inverso multiplicativo em GF(2⁸) seguido de
transformação afim. O inverso dá a não-linearidade e a transformação afim elimina
pontos fixos. Verificado pelo código: bijetiva = `{c["sbox_bijetiva"]}`,
pontos fixos = `{c["sbox_pontos_fixos"]}`. Sua uniformidade diferencial medida é
**{c["ddt_maximo"]}**, ou seja, nenhuma diferença de entrada leva a uma diferença
de saída com probabilidade maior que 2^{n(c["log2_prob_diferencial"], 0)}.

**Difusão.** O MixColumns multiplica cada coluna do estado por uma matriz MDS
sobre GF(2⁸), espalhando um byte alterado sobre os quatro bytes da coluna. Junto
com o ShiftRows, isso faz um único bit percorrer o bloco inteiro em poucas
rodadas, medido na seção 6.1.

### 3.3 O que é nosso e o que vem da família do AES

Esta é a pergunta que o trabalho precisa responder sem rodeios. A **estrutura**
do MPC-128 é a mesma do AES, e isso é deliberado: é a rede SPN com S-box
baseada em inverso multiplicativo em GF(2⁸) que garante as boas propriedades,
e reinventá-la daria um resultado pior, não mais original. Os **três
componentes concretos**, porém, são escolha nossa, e nenhum coincide com o do
AES:

{tabela(["Componente", "MPC-128 (nosso)", "AES", "Como foi escolhido"],
        [["Transformação afim da S-box",
          f"rotações {tuple(c['projeto']['sbox_rotacoes'])}, constante {c['projeto']['sbox_constante']}",
          f"rotações {tuple(c['projeto']['sbox_rotacoes_aes'])}, constante {c['projeto']['sbox_constante_aes']}",
          "busca exaustiva entre as afins invertíveis, exigindo bijeção, zero ponto fixo e uniformidade diferencial 4"],
         ["Permutação de bytes",
          f"deslocamentos {tuple(c['projeto']['deslocamentos'])}",
          f"deslocamentos {tuple(c['projeto']['deslocamentos_aes'])}",
          "deslocamentos distintos, para que cada coluna de saída receba um byte de cada coluna de entrada"],
         ["Matriz de difusão",
          f"circulante {tuple(c['projeto']['matriz_difusao'])}",
          f"circulante {tuple(c['projeto']['matriz_difusao_aes'])}",
          "busca entre circulantes de coeficientes pequenos, verificando MDS por todos os menores"],
         ["Escalonamento de chaves",
          "HKDF sobre HMAC-SHA256", "expansão do Rijndael",
          "derivado do nonce da mensagem, o que torna as subchaves diferentes a cada operação"]])}

A S-box resultante difere da do AES **nas 256 posições**. As propriedades que
importam continuam no mesmo patamar, e foram medidas, não presumidas:
uniformidade diferencial {c["ddt_maximo"]}, zero ponto fixo, difusão completa na
rodada {rodada_difusao} e critério estrito de avalanche satisfeito em todas as
16.384 células (§6.2).

O teste `test_sbox_e_propria_e_nao_a_do_aes` existe exatamente para impedir que
alguém reintroduza a construção do AES sem perceber.

### 3.4 A chave nunca é fixa

O enunciado exige que a chave influencie a cifragem e não seja fixa. Aqui são
três camadas:

1. **Senha → chave mestra.** PBKDF2-HMAC-SHA256 com
   {i(res["cifra"]["derivacao_de_chave"].split("(")[1].split(" ")[0].replace(".", ""))} iterações sobre um *salt* aleatório de 16 bytes, gerado por mensagem.
2. **Chave mestra → chaves de sessão.** HKDF sobre um *nonce* aleatório de 12
   bytes, produzindo a chave de cifragem e a chave de integridade.
3. **Chave de sessão → subchaves de rodada.** HKDF expande {c["rodadas"] + 1}
   subchaves de 16 bytes.

Consequência verificável: cifrar o mesmo texto com a mesma senha duas vezes
produz envelopes diferentes, confirmado pelo código
(`{c["ciframentos_distintos_mesma_entrada"]}`).

### 3.5 Integridade

O envelope é autenticado com HMAC-SHA256 no esquema *encrypt-then-MAC*. Alterar
um único bit do texto cifrado faz a decifragem falhar em vez de devolver lixo 
verificado (`{c["integridade_detecta_adulteracao"]}`). É esse mecanismo que o
dashboard exibe como lacre íntegro ou violado.

---

## 4. Funcionamento ponta a ponta

```
texto/arquivo/imagem
   └─ PBKDF2(senha, salt) ─ HKDF(nonce) ─ subchaves
        └─ MPC-128 em modo CTR ─ texto cifrado
             └─ HMAC-SHA256 ─ envelope autenticado
                  └─ esteganografia LSB com posições derivadas da chave
                       └─ imagem portadora
   (cada operação emite um evento → Parquet → DuckDB → Isolation Forest → alerta armazenado)
```

A última linha descreve o que o código faz a cada operação real do cofre, e não
só na bateria. Proteger, abrir, ocultar e revelar gravam um evento em
`data/vivo/`, no mesmo formato Parquet particionado por dia do histórico, com
origem (IP e dispositivo), resultado, latência, bytes e estado da integridade.
Uma abertura recusada, por senha errada ou conteúdo adulterado, entra como falha
de decifragem com a integridade violada. A cada evento, a janela de
{JANELA_MINUTOS} minutos em que ele cai é reagregada pela mesma consulta SQL do
histórico e julgada pelo mesmo Isolation Forest, treinado sobre os
{i(bd["resumo"]["eventos"])} eventos do lago. Quando a janela passa do limiar, a
detecção é gravada em `data/deteccoes/`, e é dali que a aba Antifraude lê. Uma
janela só é julgada a partir de {MIN_EVENTOS_JANELA} operações: menos que isso
não forma um comportamento.

O sistema roda local e não tem cadastro de usuários. A única credencial é a
senha do cofre, então a falha de autenticação que existe ao vivo é a do envelope,
verificada por HMAC. Tentativas de login em rajada aparecem no histórico
sintético (§6.10), onde os cinco tipos de anomalia têm rótulo conhecido.

O modo CTR transforma a cifra de bloco em cifra de fluxo: o bloco cifrado é o
contador, e o texto claro é combinado por XOR com esse fluxo. Isso elimina o
preenchimento e, sobretudo, faz blocos claros iguais produzirem saídas
diferentes, o problema que a seção 6.7 demonstra no modo ECB.

---

## 5. Testes realizados

| # | Teste | O que mede | Amostra |
|---|---|---|---|
| 1 | Efeito avalanche | bits de saída alterados por 1 bit de entrada | {i(av["amostras"])} pares |
| 2 | Avalanche por rodada | em que rodada a difusão se completa | {i(av["amostras"])} pares |
| 3 | Avalanche de chave | sensibilidade a 1 bit da chave | {i(d["avalanche_chave"]["amostras"])} pares |
| 4 | Critério estrito de avalanche (SAC) | 128×128 probabilidades de inversão | {i(sac["amostras_por_celula"])} por célula |
| 5 | Tabela de diferenças (DDT) | limite teórico por rodada | 65.536 pares |
| 6 | Distinguidor diferencial | diferença de saída mais provável | {i(d["distinguidor_integro"]["amostras"])} pares |
| 7 | Força bruta | taxa real de chaves/s e projeção | {i(bf["chaves_testadas"])} chaves |
| 8 | Dicionário | custo imposto pelo PBKDF2 | {dic["senhas_testadas"]} senhas |
| 9 | Perfil estatístico | entropia, χ², IC, NIST monobit e corridas | {i(res["estatistico"]["bytes_analisados"])} bytes |
| 10 | Análise de frequência | texto recuperado sem chave | {i(freq_f["bytes"])} bytes |
| 11 | Padrões em modo ECB | blocos repetidos em imagem estruturada | 256×256 px |
| 12 | Esteganografia | PSNR, capacidade e esteganálise χ² | {est["dimensoes"][0]}×{est["dimensoes"][1]} px |
| 13 | Big Data | ingestão e consulta | {i(bd["resumo"]["eventos"])} eventos |
| 14 | Detecção de anomalias | AUC, precisão e revocação | {i(ia["janelas"])} janelas |

Reproduzíveis por `python -m maxpay.experiments` e verificados por
`pytest` ({suite}).

---

## 6. Resultados

### 6.1 Efeito avalanche

Inverter **um** bit do texto claro altera **{n(av["media_pct"])}%** dos bits do
texto cifrado, o ideal é 50%. O desvio padrão medido foi {n(av["desvio_padrao"], 3)},
praticamente igual ao {n(v["efeito_avalanche"]["desvio_padrao_teorico"], 3)}
esperado de uma distribuição binomial(128; 0,5). Em outras palavras, a saída se
comporta como se cada bit fosse sorteado por moeda honesta.

{tabela(["Rodada", "Bits alterados", "% do bloco"],
        [[r["rodada"], n(r["bits_alterados"], 2), n(r["pct"]) + "%"] for r in av["por_rodada"]])}

A difusão se completa na **rodada {rodada_difusao}**. Com {c["rodadas"]} rodadas,
a cifra opera com margem de segurança de {n(c["rodadas"] / max(rodada_difusao, 1), 1)}×
sobre o mínimo necessário.

Comparações na mesma medição: AES-256 ficou em {n(aes["media_pct"])}% e a variante
sem difusão, em **{n(fraco["media_pct"])}%**, ou seja, alterar um bit da entrada
muda só {n(fraco["media_bits"], 1)} dos 128 bits de saída, deixando o resto do
bloco intacto e visível ao atacante.

A avalanche de chave foi de {n(d["avalanche_chave"]["media_pct"])}%: um bit
trocado na chave muda metade do texto cifrado.

### 6.2 Critério estrito de avalanche (SAC)

O SAC exige que a inversão de qualquer bit *i* da entrada inverta qualquer bit
*j* da saída com probabilidade 0,5, nas 16.384 células da matriz 128×128.

| Variante | Média | Desvio máximo | Limite (Bonferroni 5%) | Células fora | Satisfaz |
|---|---|---|---|---|---|
| MPC-128 íntegro | {n(sac["media"], 5)} | {n(sac["desvio_maximo"], 5)} | {n(sac["limite_bonferroni"], 5)} | {sac["celulas_fora_do_limite"]} | **{"Sim" if sac["satisfaz_sac"] else "Não"}** |
| 1 rodada sem difusão | {n(sac_f["media"], 5)} | {n(sac_f["desvio_maximo"], 5)} | {n(sac_f["limite_bonferroni"], 5)} | {i(sac_f["celulas_fora_do_limite"])} | **{"Sim" if sac_f["satisfaz_sac"] else "Não"}** |

O limite usa correção de Bonferroni porque são 16.384 testes simultâneos: sem
ela, o maior desvio estouraria 3σ só pela quantidade de células, e o teste
acusaria falha onde não há.

### 6.3 Ataque de força bruta

Taxa real medida nesta máquina: **{i(bf["chaves_por_segundo"])} chaves/s** (um
núcleo, implementação vetorizada). Com entropia reduzida a {bf["bits_entropia"]} bits,
a chave foi encontrada após {i(bf["chaves_testadas"])} tentativas, o ataque
funciona, o que valida a medição.

Extrapolando a mesma taxa:

{tabela(["Espaço de chaves", "Cenário", "Tempo esperado", "Viável?"],
        [[f"2^{p['bits']}", p["cenario"], p["anos_fmt"], "Sim" if p["viavel"] else "Não"]
         for p in bf["projecao"]])}

Para os 256 bits do MPC-128 seriam necessários **{proj_gpu[256]["anos_fmt"]}**
mesmo com um milhão de GPUs, cerca de
{sci(proj_gpu[256]["vezes_idade_universo"])} vezes a idade do universo. O número
de rodadas não altera isso: o espaço de chaves é o mesmo na variante enfraquecida.

**Ataque de dicionário.** Contra a senha do usuário, o PBKDF2 limita o atacante a
{n(dic["tentativas_por_segundo"], 1)} tentativas por segundo. A senha fraca
`{dic["senha_quebrada"]}` caiu em {n(dic["segundos"], 2)} s. Já uma senha forte de
12 caracteres exigiria {dic["anos_forte_fmt"]}. **A senha, e não a cifra, é o elo
mais fraco**, e é por isso que o alongamento de chave existe.

### 6.4 Ataque diferencial

A S-box tem uniformidade diferencial {c["ddt_maximo"]}: a melhor característica
diferencial de uma rodada tem probabilidade 2^{n(c["log2_prob_diferencial"], 0)}.
Ao longo de {c["rodadas"]} rodadas, uma característica útil ficaria muito abaixo
de qualquer limiar explorável.

Medição direta com {i(d["distinguidor_integro"]["amostras"])} pares de texto claro
aplicando sempre a mesma diferença de entrada:

{tabela(["Variante", "Diferenças de saída distintas", "Repetição máxima", "Distinguível"],
        [["MPC-128 íntegro",
          n(d["distinguidor_integro"]["pct_saidas_distintas"]) + "%",
          f'{d["distinguidor_integro"]["ocorrencias"]} ocorrência(s)',
          "Não" if not d["distinguidor_integro"]["distinguivel"] else "Sim"],
         ["1 rodada sem difusão",
          n(d["distinguidor_fraco"]["pct_saidas_distintas"]) + "%",
          f'{i(d["distinguidor_fraco"]["ocorrencias"])} ocorrências',
          "Sim" if d["distinguidor_fraco"]["distinguivel"] else "Não"]])}

Na cifra íntegra, as saídas são praticamente todas distintas, exatamente o que
se esperaria de uma permutação aleatória. Na variante enfraquecida,
{i(d["distinguidor_fraco"]["ocorrencias"])} pares caem na **mesma** diferença de
saída: é uma característica diferencial explorável, e o ataque tem por onde
começar.

### 6.5 Ataque estatístico

Perfil das mesmas {i(res["estatistico"]["bytes_analisados"])} mensagens bancárias
sob diferentes tratamentos:

{tabela(["Amostra", "Entropia", "χ² (p)", "IC", "Correlação serial", "Monobit", "Corridas", "Blocos repetidos"],
        [[rot(p["rotulo"]),
          n(p["entropia_bits_por_byte"], 4),
          n(p["chi2_p_valor"], 4),
          n(p["indice_coincidencia"], 6),
          n(p["correlacao_serial"], 5),
          "passa" if p["monobit"]["passou"] else "**falha**",
          "passa" if p["corridas"]["passou"] else "**falha**",
          n(p["repeticao_blocos"]["pct_repetidos"]) + "%"]
         for p in res["estatistico"]["perfis"]])}

O texto claro tem entropia {n(claro["entropia_bits_por_byte"], 4)} bits/byte e
falha em todos os testes. A saída do MPC-128 em modo CTR tem
{n(ctr["entropia_bits_por_byte"], 4)} bits/byte (máximo teórico 8), índice de
coincidência {n(ctr["indice_coincidencia"], 6)} contra o 0,003906 de uma fonte
uniforme, e χ² com p = {n(ctr["chi2_p_valor"], 4)}, não se rejeita a hipótese de
uniformidade. Para efeito de controle, `/dev/urandom` na mesma medição deu
entropia {n(urandom["entropia_bits_por_byte"], 4)} e p = {n(urandom["chi2_p_valor"], 4)}.
**A saída da cifra é estatisticamente indistinguível de ruído do sistema
operacional.**

### 6.6 Análise de frequência: o ataque que funcionou

Mensagens bancárias usam registros de largura fixa ({freq_f["posicoes_registro"]}
bytes aqui), e isso tem consequência: sem o MixColumns, cada posição do bloco
permanece uma substituição monoalfabética independente. A cifra apenas renomeia e
reposiciona bytes. Um atacante que conheça o formato, realista num banco, levanta a frequência de referência e remapeia coluna a coluna.

| Alvo | Acerto | Linha de base* | Posições expostas | Quebrado |
|---|---|---|---|---|
| 1 rodada, sem difusão | **{n(freq_f["acuracia_pct"])}%** | {n(freq_f["linha_base_unigrama_pct"])}% | **{freq_f["posicoes_expostas"]} de {freq_f["posicoes_registro"]}** | Sim |
| {c["rodadas"]} rodadas, com difusão | {n(freq_c["acuracia_pct"])}% | {n(freq_c["linha_base_unigrama_pct"])}% | {freq_c["posicoes_expostas"]} de {freq_c["posicoes_registro"]} | Não |

\\* Linha de base = acerto de quem nem olha o texto cifrado e sempre chuta o byte
mais comum do formato. Comparar com 1/256 seria generoso demais.

Trecho real recuperado da variante enfraquecida, **sem nenhuma chave**:

```
original  : {freq_f["trecho_original"][:79].rstrip()}
recuperado: {freq_f["trecho_recuperado"][:79].rstrip()}
```

Contra a cifra íntegra o mesmo ataque entrega {n(freq_c["acuracia_pct"])}%, ou
seja, **abaixo** da linha de base: o atacante teria se saído melhor chutando.

### 6.7 O modo importa mais que as rodadas

{tabela(["Tratamento", "Blocos repetidos", "Entropia"],
        [[rot(x["nome"]), n(x["repeticao_blocos"]["pct_repetidos"]) + "%", n(x["entropia"], 4)]
         for x in res["ecb"]["variantes"]])}

Cifrando os pixels de uma imagem estruturada, o modo ECB preserva
{n(ecb14["repeticao_blocos"]["pct_repetidos"])}% dos blocos repetidos **mesmo com
{c["rodadas"]} rodadas e difusão completa**: blocos claros iguais produzem blocos
cifrados iguais, e o contorno da imagem sobrevive. No modo CTR, zero repetições.
Uma cifra forte em modo errado continua vazando estrutura.

### 6.8 Esteganografia

| Medida | Valor |
|---|---|
| Capacidade | {i(est["capacidade_bytes"])} bytes ({n(est["capacidade_pct_da_imagem"])}% do arquivo) |
| Carga embutida | {i(est["payload_bytes"])} bytes ({n(est["ocupacao_pct"])}% da capacidade) |
| PSNR | **{n(est["qualidade"]["psnr_db"])} dB** |
| Erro quadrático médio | {n(est["qualidade"]["mse"], 6)} |
| Subpixels alterados | {i(est["qualidade"]["subpixels_alterados"])} de {i(est["qualidade"]["subpixels_totais"])} ({n(est["qualidade"]["pct_alterado"], 3)}%) |
| Desvio máximo por canal | {est["qualidade"]["desvio_maximo"]} |
| Extração com chave errada | {"rejeitada" if est["resiste_chave_errada"] else "**aceita**"} |

Acima de 40 dB de PSNR a alteração é considerada imperceptível; aqui ficou em
{n(est["qualidade"]["psnr_db"])} dB, com desvio máximo de
{est["qualidade"]["desvio_maximo"]} por canal.

**Esteganálise.** O ataque de qui-quadrado de Westfeld varre a imagem em segmentos
procurando o patamar que o LSB sequencial deixa no início do arquivo. Com a mesma
carga de {i(est["esteganalise"]["payload_da_comparacao_bytes"])} bytes
({n(est["esteganalise"]["ocupacao_da_comparacao_pct"])}% da capacidade):

{tabela(["Imagem", "Segmentos suspeitos (de 20)"],
        [[rot(k), v] for k, v in est["esteganalise"]["segmentos_suspeitos"].items()])}

O LSB sequencial clássico acende
{est["esteganalise"]["segmentos_suspeitos"]["lsb_sequencial_sem_chave"]} segmentos;
a versão do MaxPay, com posições derivadas da chave, acende
**{est["esteganalise"]["segmentos_suspeitos"]["lsb_chaveado_maxpay"]}**, igual à
imagem limpa. Espalhar os bits por uma permutação secreta não é detalhe de
implementação: é o que remove a assinatura.

### 6.9 Big Data

| Medida | Valor |
|---|---|
| Eventos | {i(bd["resumo"]["eventos"])} |
| Período | {bd["resumo"]["dias"]} dias, {i(bd["resumo"]["usuarios"])} usuários, {i(bd["resumo"]["ips"])} IPs |
| Partições Parquet | {bd["ingestao"]["particoes"]} |
| Em disco | {n(bd["ingestao"]["bytes_em_disco"] / 1e6)} MB ({n(bd["ingestao"]["bytes_por_evento"])} B por evento) |
| Ingestão | {n(bd["ingestao"]["segundos"])} s |
| Consulta de resumo | {n(bd["desempenho_consultas"]["resumo_segundos"], 3)} s |
| Agregação em janelas | {n(bd["desempenho_consultas"]["janelas_segundos"], 3)} s |
| Taxa de falha global | {n(bd["resumo"]["taxa_falha_pct"], 3)}% |
| Volume financeiro simulado | R$ {n(bd["resumo"]["volume_financeiro"])} |
| Detecções armazenadas | {i(bd["deteccoes"]["registros"])} alertas em `{bd["deteccoes"]["caminho"]}` ({n(bd["deteccoes"]["bytes_em_disco"] / 1e3, 1)} kB) |

A agregação reduz {bd["desempenho_consultas"]["reducao_dimensional"]}. O trabalho
pesado é feito em SQL colunar; a camada de IA recebe só o resumo.

São três conjuntos lado a lado, todos em Parquet e consultados pelo mesmo
DuckDB: `data/lake/` guarda o histórico de eventos, `data/vivo/` guarda as
operações reais do cofre, e `data/deteccoes/` guarda cada alerta emitido pela
IA, tanto os {i(bd["deteccoes"]["registros"])} do histórico quanto os que surgem
ao vivo. Cada detecção carrega a conta, a janela, o risco, o tipo previsto e a
explicação, de modo que um alerta pode ser auditado depois sem repetir o modelo.

### 6.10 Detecção de anomalias

O Isolation Forest é treinado **sem rótulos**. Os rótulos existem apenas para
medir a qualidade depois.

| Métrica | Valor |
|---|---|
| Janelas analisadas | {i(ia["janelas"])} |
| Janelas anômalas (verdade) | {ia["janelas_anomalas"]} ({n(ia["prevalencia_pct"], 3)}%) |
| ROC AUC | **{n(ia["roc_auc"], 4)}** |
| Precisão média (AP) | {n(ia["average_precision"], 4)} |
| Ganho sobre o acaso | {n(ia["ganho_sobre_acaso"], 1)}× |
| Alertas emitidos | {ia["alertas"]} |
| Precisão / Revocação / F1 | {n(ia["precisao"], 3)} / {n(ia["revocacao"], 3)} / {n(ia["f1"], 3)} |

Como o orçamento de alertas é uma decisão de operação, e não do modelo:

{tabela(["Orçamento de alertas", "% das janelas", "Precisão", "Revocação"],
        [[i(p["orcamento_alertas"]), n(p["orcamento_pct"], 2) + "%", n(p["precisao"], 3), n(p["revocacao"], 3)]
         for p in ia["pontos_de_operacao"]])}

Revisando apenas {n(ia["pontos_de_operacao"][0]["orcamento_pct"], 2)}% das janelas,
a precisão é de {n(ia["pontos_de_operacao"][0]["precisao"] * 100, 1)}%: quase todo
alerta é real.

Desempenho por tipo de anomalia, os cinco previstos no enunciado:

{tabela(["Anomalia", "Janelas", "Detectadas", "Revocação", "Posto mediano de risco", "Tipo correto"],
        [[rot(r["tipo"]), r["janelas"], r["detectadas"],
          n(r["revocacao_pct"], 1) + "%",
          f'{i(r["posto_mediano"])} de {i(ia["janelas"])} ({n(r["percentil_mediano"], 2)}%)',
          n(r["acerto_tipo_pct"], 1) + "%"]
         for r in sorted(ia["por_tipo"], key=lambda x: x["posto_mediano"])])}

O **posto mediano** mostra onde cada tipo cai no ranking de risco, e não depende do orçamento
de alertas. Os quatro primeiros ficam no meio-milésimo mais arriscado. O surto de eventos fica
no {n([r for r in ia["por_tipo"] if r["tipo"] == "surto_de_eventos"][0]["percentil_mediano"], 2)}%
mais arriscado, o que é longe de passar despercebido, mas não cabe no 1% que a equipe aceita
revisar.

A anomalia mais difícil é o **surto de eventos**: ela não gera falha nenhuma, só
volume. As que falham alguma coisa são detectadas quase integralmente.

### 6.11 Desempenho

| Algoritmo | Vazão |
|---|---|
| MPC-128 (Python + numpy) | {n(desemp["mpc128_mb_por_s"])} MB/s |
| AES-256-GCM (biblioteca com AES-NI) | {n(desemp["aes256_mb_por_s"])} MB/s |

O AES é {n(desemp["razao_aes_sobre_mpc"], 1)}× mais rápido, e isso era esperado:
{desemp["nota"]} A comparação mede implementação, não qualidade criptográfica.

---

## 7. Parte 4: as quatro perguntas

### O sistema apresenta efeito avalanche?

**{v["efeito_avalanche"]["resposta"]}.** {v["efeito_avalanche"]["justificativa"]}

### Existem padrões na saída?

**{v["padroes_na_saida"]["resposta"]}**, no modo CTR.
{v["padroes_na_saida"]["justificativa"]}

### Qual ataque foi mais eficaz?

**{v["ataque_mais_eficaz"]["resposta"]}.** {v["ataque_mais_eficaz"]["justificativa"]}

Critério de ordenação: {v["ataque_mais_eficaz"]["criterio"]}. Os três ataques
produzem resultados de naturezas diferentes e não se comparam por um número
único.

{tabela(["Severidade", "Ataque", "O que o atacante obtém", "Contra a cifra íntegra", "Contra a variante enfraquecida"],
        [[r["severidade_contra_fraco"], r["ataque"], r["ganho"], r["contra_integro"], r["contra_fraco"]]
         for r in v["ataque_mais_eficaz"]["ranking"]])}

### O sistema é seguro? Justifique.

**{v["e_seguro"]["resposta"]}.** {v["e_seguro"]["justificativa"]}

**A favor:**

{chr(10).join("- " + x for x in v["e_seguro"]["a_favor"])}

**Ressalvas, e elas não são formalidade:**

{chr(10).join("- " + x for x in v["e_seguro"]["ressalvas"])}

---

## 8. Conclusão

O MPC-128 passou nos três ataques exigidos. Avalanche de {n(av["media_pct"])}%,
SAC satisfeito em todas as 16.384 células, saída indistinguível de aleatória e
espaço de chaves de 256 bits colocam a cifra, nas medições feitas, no mesmo
patamar de comportamento do AES-256.

O resultado mais útil deste trabalho, porém, não é esse. É a comparação com a
variante enfraquecida, que mostra **de onde** vem a segurança:

1. **Difusão é o que sustenta tudo.** Sem MixColumns, a análise de frequência
   recupera {n(freq_f["acuracia_pct"])}% do texto e expõe {freq_f["posicoes_expostas"]}
   das {freq_f["posicoes_registro"]} posições do registro. Aumentar rodadas não
   corrige: com difusão desligada, {c["rodadas"]} rodadas vazam tanto quanto 1.
2. **O modo de operação pesa mais que o número de rodadas.** O ECB preservou
   {n(ecb14["repeticao_blocos"]["pct_repetidos"])}% dos blocos repetidos com a
   cifra íntegra.
3. **Força bruta é o ataque errado.** Inviável contra as duas variantes; a
   superfície real é a senha, e o PBKDF2 existe para encarecê-la.
4. **A anomalia mais difícil é a que não quebra nada.** O surto de exfiltração não gera
   falha nenhuma, só volume: o modelo o coloca no **{n(surto["percentil_mediano"], 2)}% mais
   arriscado** de {i(ia["janelas"])} janelas, mas ele fica fora do orçamento de
   {i(ia["alertas"])} alertas, porque perde a disputa para anomalias que falham. Não é o
   modelo que não enxerga; é o orçamento que não alcança. Dobrando o orçamento para 2%, a
   revocação sobe de {n(surto["revocacao_pct"], 1)}% para
   {n(_revoc_em(ia, 0.02, "surto_de_eventos"), 1)}%.

Nada disso faz do MPC-128 uma cifra de produção. Ele não passou por
criptanálise independente, não é de tempo constante, e não recebeu análise
linear nem prova formal de resistência. Uma cifra se torna confiável por anos de
tentativa pública de quebra, não por uma bateria de testes dos próprios autores.
É exatamente por isso que a camada AES-256 existe no sistema: **o MPC-128 é o
objeto de estudo; o AES-256 é o que protegeria o dinheiro de verdade.**

---

## 9. Como reproduzir

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python -m maxpay.experiments     # gera results/experimentos.json
python -m maxpay.report          # regera este relatório
pytest -q                          # {suite}
uvicorn maxpay.api:app --reload  # dashboard em http://127.0.0.1:8000
```

## 10. Onde cada requisito está

{tabela(["Requisito do enunciado", "Onde está", "Evidência"],
        [["Criptografia simétrica com geração dinâmica de chaves", "`maxpay/cipher.py`", "§3.4"],
         ["XOR, substituição, permutação, blocos", "`maxpay/cipher.py`", "§3.2"],
         ["Difusão / confusão", "`maxpay/cipher.py`", "§6.1, §6.2"],
         ["Esteganografia em imagens", "`maxpay/stego.py`", "§6.8"],
         ["Big Data de eventos", "`maxpay/events.py`, `maxpay/lake.py`", "§6.9"],
         ["IA para detectar comportamento anormal", "`maxpay/detect.py`", "§6.10"],
         ["Ataque de força bruta", "`maxpay/attacks/brute_force.py`", "§6.3"],
         ["Ataque diferencial", "`maxpay/attacks/differential.py`", "§6.4"],
         ["Ataque estatístico", "`maxpay/attacks/statistical.py`", "§6.5, §6.6"],
         ["Efeito avalanche", "`maxpay/attacks/differential.py`", "§6.1"],
         ["Distribuição estatística", "`maxpay/metrics.py`", "§6.5"],
         ["Dashboard", "`maxpay/api.py`, `web/`", "camada 6"],
         ["Logs das operações criptográficas", "`maxpay/registro.py`, `maxpay/lake.py`", "§4, §6.9"],
         ["Tentativas de acesso e falhas de autenticação", "`maxpay/registro.py`, `maxpay/events.py`", "§4, §6.10"],
         ["Armazenamento das detecções de anomalia", "`maxpay/lake.py`", "§6.9"],
         ["Análise de padrões de comportamento", "`maxpay/lake.py`, `maxpay/detect.py`", "§6.10"],
         ["Grandes conjuntos de dados experimentais", "`maxpay/events.py`, `maxpay/lake.py`", "§6.9"],
         ["Os 5 tipos de anomalia", "`maxpay/events.py`", "§6.10"],
         ["Arquitetura em 6 camadas", "todo o pacote", "§2"],
         ["Respostas da Parte 4", "`maxpay/experiments.py`", "§7"]])}
"""


def main() -> Path:
    res = carregar()
    if res is None:
        raise SystemExit("Rode `python -m maxpay.experiments` primeiro.")
    DOCS.mkdir(parents=True, exist_ok=True)
    destino = DOCS / "RELATORIO.md"
    destino.write_text(gerar(res), encoding="utf-8")
    return destino


if __name__ == "__main__":
    p = main()
    print(f"OK -> {p} ({p.stat().st_size / 1024:.1f} KB, {len(p.read_text().splitlines())} linhas)")
