"""Gera o guia de apresentacao: texto corrido de como conduzir a defesa.

Sai em `docs/GUIA-APRESENTACAO.md`, com os numeros lidos da bateria, para nao
envelhecer quando os experimentos rodarem de novo.

    python -m finalpay.guia
"""

from __future__ import annotations

from pathlib import Path

from finalpay.experiments import carregar
from finalpay.notas import NOTAS
from finalpay.report import DOCS, GRUPO, i, n, rot, sci

DESTINO = DOCS / "GUIA-APRESENTACAO.md"

# Quem fala o que. Seis pessoas, cinco blocos de fala e a demonstracao.
DIVISAO = [
    ("Abertura e arquitetura", "telas 1 a 3", ["capa", "ato1", "construido"],
     "Abre, diz o que é o projeto e por que ele tem duas metades. Não entra em detalhe técnico: "
     "o trabalho dessa pessoa é fazer a professora entender a aposta do grupo em trinta segundos."),
    ("A cifra", "telas 4 a 6", ["algoritmo", "projeto", "chave"],
     "A parte mais exposta a pergunta. Precisa saber responder o que é nosso e o que vem do AES "
     "sem hesitar, porque essa é a pergunta mais provável da banca."),
    ("Esteganografia e antifraude", "telas 7 e 8", ["estego", "antifraude"],
     "Duas camadas em duas telas. Segura a explicação do surto de eventos, que é o número fraco "
     "da tabela e precisa do contexto do posto de risco para não parecer falha de projeto."),
    ("Avalanche e padrões", "telas 9 a 11", ["ato2", "avalanche", "padroes"],
     "Carrega a virada do argumento: a comparação entre a cifra íntegra e a enfraquecida. "
     "É aqui que o trabalho deixa de afirmar e passa a demonstrar."),
    ("Os três ataques", "telas 12 a 14", ["bruta", "diferencial", "estatistico"],
     "O núcleo da Parte 3 do enunciado. Fecha com a análise de frequência, que é o ataque que "
     "funcionou, e entrega para o veredito."),
    ("Veredito e fechamento", "telas 15 a 19", ["ato3", "perguntas", "conclusao", "limites", "obrigado"],
     "Responde as quatro perguntas da Parte 4 e assume os limites. A honestidade dessa parte vale "
     "mais que o resultado positivo das anteriores."),
]


def gerar(res: dict) -> str:
    c, pj = res["cifra"], res["cifra"]["projeto"]
    av = res["diferencial"]["fpc_integro"]
    fr = res["diferencial"]["fpc_fraco"]
    sd = res["diferencial"]["fpc_sem_difusao_14_rodadas"]
    perfis = {p["rotulo"]: p for p in res["estatistico"]["perfis"]}
    ctr, ecb = perfis["fpc_ctr_14_rodadas"], perfis["fpc_ecb_14_rodadas"]
    bf, dic = res["forca_bruta"], res["dicionario"]
    freq_f, freq_c = res["frequencia"]["sem_difusao"], res["frequencia"]["com_difusao"]
    est, bd = res["estego"], res["bigdata"]
    ia = bd["ia"]["metricas"]
    v = res["veredito"]
    proj = next(p for p in bf["projecao"] if p["bits"] == 256 and "GPU" in p["cenario"])
    rodada_dif = v["efeito_avalanche"]["rodadas_ate_difusao_total"]
    surto = next(t for t in ia["por_tipo"] if t["tipo"] == "surto_de_eventos")

    blocos_fala = "\n\n".join(
        f"### {k + 1}. {titulo} ({telas})\n\n{papel}\n\n"
        f"O que essa pessoa fala, tela a tela:\n\n"
        + "\n\n".join(f"**Tela de {sid}.** " + NOTAS.get(sid, "").replace("\n\n", " ")
                      for sid in ids)
        for k, (titulo, telas, ids, papel) in enumerate(DIVISAO)
    )

    return f"""# Como apresentar o FinalPay

Guia de condução da defesa do Projeto 2 de Cibersegurança Aplicada a Dados e IA,
CESAR School. Grupo: {", ".join(GRUPO)}. Professora Renatta Nigro.

Este texto explica o que é o projeto, como a apresentação está montada, quem fala
o quê, o que mostrar ao vivo e o que responder quando a pergunta vier. Os números
foram lidos da bateria de experimentos executada em
{res["meta"]["gerado_em"].replace("T", " ")}.

---

## 1. O que vocês construíram, em um parágrafo

O FinalPay é o cofre criptográfico de um banco digital fictício. Ele protege
transações com uma cifra de bloco que vocês mesmos projetaram, a FPC-128, esconde
o resultado dentro de imagens comuns, registra {i(bd["resumo"]["eventos"])} eventos
de segurança num lago de dados e usa aprendizado de máquina para apontar
comportamento anormal. Até aqui é o que o enunciado pede. O que torna o trabalho
diferente é a segunda metade: o mesmo sistema **ataca a si próprio**. Os três
ataques exigidos rodam contra duas versões da mesma cifra, a íntegra e uma
deliberadamente enfraquecida, e é a comparação entre as duas que prova de onde vem
a segurança.

Essa é a frase que vocês precisam que a professora leve embora: **o trabalho não
afirma que o sistema é seguro, ele mede.**

## 2. A aposta do grupo, e por que ela é arriscada

A maior parte dos trabalhos desta disciplina implementa uma cifra **ou** ataca uma
cifra. Vocês fizeram as duas coisas na mesma base de código, e deixaram o resultado
cair do lado que os números mandassem. Isso é arriscado porque obriga a mostrar onde
o sistema falha. E ele falha: a análise de frequência recupera
{n(freq_f["acuracia_pct"])}% do texto da variante enfraquecida, e o modo ECB vaza
estrutura mesmo com a cifra íntegra.

Assumir essas falhas não enfraquece a apresentação, fortalece. Elas são o que
transforma "nossa cifra é boa" em "medimos de onde vem a segurança, e é da difusão
e do modo de operação, não do número de rodadas".

## 3. Como a apresentação está montada

São 19 telas em três atos, pensadas para cerca de **quinze minutos de fala** mais
**quatro a cinco minutos de demonstração ao vivo**.

| Ato | Telas | O que ele faz |
|---|---|---|
| 01 · O sistema | 2 a 8 | mostra as seis camadas e a cifra que vocês projetaram |
| 02 · Os ataques | 9 a 14 | mede o que acontece quando o sistema é atacado |
| 03 · O veredito | 15 a 19 | responde as quatro perguntas e assume os limites |

Cada tela tem uma **nota de apresentador** embutida no próprio deck. Abra
`docs/slides/index.html` no navegador e aperte a tecla **N**: aparece uma faixa na
parte de baixo com o texto para ler em voz alta. A tecla **N** esconde de novo, e a
tecla **P** imprime em paisagem, com as notas junto se elas estiverem visíveis.

As setas navegam. Cada tela diz, no canto superior esquerdo, em que aba da
plataforma aquilo roda ao vivo.

## 4. Quem fala o quê

A divisão abaixo distribui as 19 telas entre as seis pessoas, com blocos de tamanho
parecido. Cada pessoa fica com um assunto inteiro, para não haver troca de voz no
meio de um raciocínio.

{blocos_fala}

## 5. A demonstração ao vivo

Suba a plataforma antes de começar, com `uvicorn finalpay.api:app`, e deixe aberta
em `http://127.0.0.1:8000` numa aba separada dos slides. São quatro paradas, nessa
ordem, e a terceira é a que convence.

**Primeira parada, aba Cofre.** Proteja o texto que já vem preenchido. Mostre os
dois histogramas de bytes lado a lado: o da entrada tem picos, o da saída é plano.
Depois clique em Proteger de novo, com a mesma senha e o mesmo texto, e mostre que
o envelope saiu diferente. É a prova visual de que a chave não é fixa.

**Segunda parada, aba Ocultar.** Clique em "Usar imagem de exemplo", oculte a
mensagem, e abra "Comparar em tela cheia". Alterne entre antes e depois com as
setas. A imagem não muda aos olhos, e o PSNR de {n(est["qualidade"]["psnr_db"])} dB
explica por quê. Depois use o botão de exemplo do painel da direita e revele.
Troque a senha e tente revelar de novo: a extração é recusada.

**Terceira parada, aba Resistência.** Esta é a demonstração que justifica o
trabalho. Rode o ataque de análise de frequência com a difusão **desligada**: ele
recupera {n(freq_f["acuracia_pct"])}% do texto e expõe
{freq_f["posicoes_expostas"]} das {freq_f["posicoes_registro"]} posições do registro
bancário, sem usar chave nenhuma. Deixe a professora ler o texto recuperado na
tela. Depois marque "Difusão ligada" e rode outra vez: cai para
{n(freq_c["acuracia_pct"])}%, abaixo da linha de base de
{n(freq_c["linha_base_unigrama_pct"])}% de quem simplesmente chuta o byte mais
comum. É o mesmo ataque, a mesma máquina, a mesma mensagem. Só mudou uma operação
da cifra.

**Quarta parada, aba Antifraude.** Mostre a tabela de alertas. Cada linha traz a
suspeita, o motivo em português e se o tipo bateu com o caso conhecido. Vale dizer
que o modelo foi treinado **sem rótulos** e que os rótulos só existem para medir a
qualidade depois.

Se o tempo apertar, corte a quarta parada. Não corte a terceira.

## 6. As perguntas que provavelmente virão

**"Isso não é só o AES com outro nome?"**
Não, e a tela 5 existe para essa pergunta. A estrutura é a mesma família do AES, e
isso foi escolha deliberada: é a rede SPN com S-box de inverso multiplicativo que
garante as boas propriedades, e reinventá-la daria um resultado pior, não mais
original. Os três componentes concretos são do grupo: a transformação afim da S-box
usa rotações {tuple(pj["sbox_rotacoes"])} com constante {pj["sbox_constante"]}
contra {tuple(pj["sbox_rotacoes_aes"])} e {pj["sbox_constante_aes"]} do AES; a
permutação é {tuple(pj["deslocamentos"])} contra {tuple(pj["deslocamentos_aes"])};
a matriz de difusão é {tuple(pj["matriz_difusao"])} contra
{tuple(pj["matriz_difusao_aes"])}. A S-box resultante difere da do AES nas 256
posições. Nenhum desses valores foi escolhido por gosto: cada um saiu de uma busca
que só aceitou o que passou na verificação matemática, e existe um teste automatizado
que falha se alguém reintroduzir a construção do AES sem perceber.

**"Vocês provaram que a cifra é segura?"**
Não, e a tela 18 diz isso com todas as letras. O que foi provado é que ela resistiu
aos três ataques que o grupo sabe executar. Uma cifra se torna confiável por anos de
tentativa pública de quebra, não por uma bateria de testes dos próprios autores. É
por isso que a camada AES-256 existe no sistema.

**"Por que a detecção do surto de eventos é de só {n(surto["revocacao_pct"], 1)}%?"**
Porque a revocação depende do orçamento de alertas, e o posto de risco não. O modelo
coloca o surto no {n(surto["percentil_mediano"], 2)}% mais arriscado de
{i(ia["janelas"])} janelas, ou seja, ele enxerga a anomalia. O que acontece é que ela
perde a disputa pelo 1% de janelas que a equipe aceita revisar, porque compete com
anomalias que geram falha de autenticação ou de integridade. Dobrando o orçamento
para 2%, a detecção sobe. É um problema de política de operação, não de modelo cego.

**"Os dados são reais?"**
Não, e isso é proposital. Os eventos são sintéticos e **rotulados**, e é justamente
por isso que dá para medir precisão e revocação. Com dados reais sem rótulo, não
haveria como dizer se o modelo acertou.

**"Por que {c["rodadas"]} rodadas, se a difusão fecha na rodada {rodada_dif}?"**
Margem de segurança. A difusão se completa cedo, e o resto das rodadas existe para
que um ataque que avance algumas rodadas ainda esbarre em muitas pela frente. É a
mesma lógica do AES, que usa 14 rodadas na versão de 256 bits.

**"Qual foi o ataque mais eficaz?"**
{v["ataque_mais_eficaz"]["resposta"]}, e vale explicar o critério: os três ataques
produzem resultados de naturezas diferentes e não se comparam por um número único.
Ordenamos pela severidade do que o atacante obtém. Ler o texto claro vale mais que
distinguir a cifra de aleatório, que por sua vez vale mais que não conseguir nada.

## 7. O que não dizer

Evitem três frases, porque todas três são indefensáveis:

- "Nossa cifra é segura." Diga "resistiu aos três ataques que fizemos".
- "Criamos um algoritmo do zero." Diga "projetamos uma instância própria dentro da
  família do AES, e estes são os três componentes que escolhemos".
- "O sistema detecta todas as anomalias." Diga os números da tabela, inclusive o
  ruim, e explique o posto de risco.

## 8. Antes de começar

- Rode `python -m finalpay.experiments` uma vez e confirme que terminou sem erro.
- Suba `uvicorn finalpay.api:app` e abra `http://127.0.0.1:8000`, já na aba Cofre.
- Abra `docs/slides/index.html` numa aba separada e teste a tecla **N**.
- Tenha `docs/RELATORIO.md` aberto num editor, caso a professora peça um número que
  não está no slide.
- Se o projetor estiver ruim, lembre que o deck é escuro: peça para apagar a luz da
  frente da sala, ou aumente o brilho antes de começar.

---

## Resumo dos números que vocês vão citar

| Medida | Valor |
|---|---|
| Efeito avalanche, cifra íntegra | {n(av["media_pct"])}% |
| Efeito avalanche, {c["rodadas"]} rodadas sem difusão | {n(sd["media_pct"])}% |
| Efeito avalanche, 1 rodada sem difusão | {n(fr["media_pct"])}% |
| Entropia da saída em modo CTR | {n(ctr["entropia_bits_por_byte"], 4)} bits por byte |
| Blocos repetidos em modo ECB | {n(ecb["repeticao_blocos"]["pct_repetidos"])}% |
| Força bruta, 256 bits, 1 milhão de GPUs | {proj["anos_fmt"]} |
| Senha fraca pelo dicionário | caiu em {n(dic["segundos"])} s |
| Análise de frequência, sem difusão | {n(freq_f["acuracia_pct"])}% do texto |
| Análise de frequência, com difusão | {n(freq_c["acuracia_pct"])}% |
| PSNR da esteganografia | {n(est["qualidade"]["psnr_db"])} dB |
| Segmentos suspeitos, LSB chaveado | {est["esteganalise"]["segmentos_suspeitos"]["lsb_chaveado_finalpay"]} de 20 |
| Eventos processados | {i(bd["resumo"]["eventos"])} |
| ROC AUC do detector | {n(ia["roc_auc"], 4)} |
"""


def main() -> Path:
    res = carregar()
    if res is None:
        raise SystemExit("Rode `python -m finalpay.experiments` primeiro.")
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(gerar(res), encoding="utf-8")
    return DESTINO


if __name__ == "__main__":
    p = main()
    print(f"OK -> {p} ({p.stat().st_size / 1024:.1f} KB, {len(p.read_text().splitlines())} linhas)")
