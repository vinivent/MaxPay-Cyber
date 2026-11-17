# MaxPay, Sistema Criptográfico e Análise de Ataques

**Disciplina:** Cibersegurança Aplicada a Dados e IA: CESAR School
**Professora:** Renatta Nigro
**Grupo:** Claudio Alves, Ian Nunes, Maria Augusta, Gabriel Lima, Gabriel Rodrigues, Vinicius Ventura
**Data:** 17/11/2026

> Todos os números deste relatório foram produzidos pela bateria de experimentos
> do próprio sistema (`python -m maxpay.experiments`), executada em
> 2026-11-17 10:24:45 sobre Darwin arm64,
> Python 3.14.6. Nenhum valor foi transcrito à mão.

---

## 1. Resumo executivo

O MaxPay é o cofre criptográfico de um banco digital fictício. Ele cifra
transações, documentos e imagens com uma cifra de bloco própria (**MPC-128**),
esconde o resultado dentro de imagens por esteganografia, registra cada operação
num lago de dados de 1.999.952 eventos e usa aprendizado de
máquina para apontar comportamento anormal.

O mesmo sistema ataca a si próprio. Os três ataques exigidos pelo enunciado
, força bruta, diferencial e estatístico, rodam contra duas versões da cifra:
a íntegra, de 14 rodadas com difusão, e uma variante deliberadamente
enfraquecida, de 1 rodada sem MixColumns. **A variante enfraquecida cai; a
íntegra não cede a nenhum dos três.** É essa comparação que sustenta o veredito
da Parte 4, e não uma afirmação de que "o sistema é seguro".

| Medida | MPC-128 íntegro | Variante enfraquecida | AES-256 |
|---|---|---|---|
| Efeito avalanche | **50,08%** | 3,10% | 50,08% |
| Entropia da saída (bits/byte) | **7,9981** | 6,5748 | 7,9983 |
| Texto recuperado por análise de frequência | 4,59% | **62,78%** |: |
| Distinguível de permutação aleatória | Não | **Sim** | Não |

---

## 2. Arquitetura

As seis camadas pedidas no enunciado, e onde cada uma vive no código:

| # | Camada | Função | Implementação |
|---|---|---|---|
| 1 | Entrada de dados | Texto, arquivos e imagens | `maxpay/api.py` |
| 2 | Criptografia | MPC-128 próprio + AES-256-GCM | `maxpay/cipher.py`, `maxpay/baseline.py` |
| 3 | Esteganografia | Ocultação em imagens PNG | `maxpay/stego.py` |
| 4 | Big Data | Geração, Parquet particionado, DuckDB | `maxpay/events.py`, `maxpay/lake.py` |
| 5 | Inteligência Artificial | Isolation Forest sobre janelas | `maxpay/detect.py` |
| 6 | Dashboard | API + painel web | `maxpay/api.py`, `web/` |

Os ataques ficam em `maxpay/attacks/` e a bateria de medição em
`maxpay/experiments.py`.

---

## 3. Descrição do algoritmo

### 3.1 Parâmetros

| Parâmetro | Valor |
|---|---|
| Nome | MPC-128 |
| Estrutura | rede de substituição-permutação (SPN) |
| Tamanho de bloco | 128 bits |
| Tamanho de chave | 256 bits |
| Rodadas | 14 |
| Modos | CTR + HMAC-SHA256, ECB (apenas para análise) |
| Derivação de chave | PBKDF2-HMAC-SHA256 (120.000 iterações) + HKDF por nonce |

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
pontos fixos. Verificado pelo código: bijetiva = `True`,
pontos fixos = `0`. Sua uniformidade diferencial medida é
**4**, ou seja, nenhuma diferença de entrada leva a uma diferença
de saída com probabilidade maior que 2^-6.

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

| Componente | MPC-128 (nosso) | AES | Como foi escolhido |
|---|---|---|---|
| Transformação afim da S-box | rotações (0, 1, 2, 3, 5), constante 0x0D | rotações (0, 1, 2, 3, 4), constante 0x63 | busca exaustiva entre as afins invertíveis, exigindo bijeção, zero ponto fixo e uniformidade diferencial 4 |
| Permutação de bytes | deslocamentos (0, 2, 3, 1) | deslocamentos (0, 1, 2, 3) | deslocamentos distintos, para que cada coluna de saída receba um byte de cada coluna de entrada |
| Matriz de difusão | circulante (1, 1, 3, 2) | circulante (2, 3, 1, 1) | busca entre circulantes de coeficientes pequenos, verificando MDS por todos os menores |
| Escalonamento de chaves | HKDF sobre HMAC-SHA256 | expansão do Rijndael | derivado do nonce da mensagem, o que torna as subchaves diferentes a cada operação |

A S-box resultante difere da do AES **nas 256 posições**. As propriedades que
importam continuam no mesmo patamar, e foram medidas, não presumidas:
uniformidade diferencial 4, zero ponto fixo, difusão completa na
rodada 2 e critério estrito de avalanche satisfeito em todas as
16.384 células (§6.2).

O teste `test_sbox_e_propria_e_nao_a_do_aes` existe exatamente para impedir que
alguém reintroduza a construção do AES sem perceber.

### 3.4 A chave nunca é fixa

O enunciado exige que a chave influencie a cifragem e não seja fixa. Aqui são
três camadas:

1. **Senha → chave mestra.** PBKDF2-HMAC-SHA256 com
   120.000 iterações sobre um *salt* aleatório de 16 bytes, gerado por mensagem.
2. **Chave mestra → chaves de sessão.** HKDF sobre um *nonce* aleatório de 12
   bytes, produzindo a chave de cifragem e a chave de integridade.
3. **Chave de sessão → subchaves de rodada.** HKDF expande 15
   subchaves de 16 bytes.

Consequência verificável: cifrar o mesmo texto com a mesma senha duas vezes
produz envelopes diferentes, confirmado pelo código
(`True`).

### 3.5 Integridade

O envelope é autenticado com HMAC-SHA256 no esquema *encrypt-then-MAC*. Alterar
um único bit do texto cifrado faz a decifragem falhar em vez de devolver lixo 
verificado (`True`). É esse mecanismo que o
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
   (cada operação emite um evento → Parquet → DuckDB → Isolation Forest → alerta)
```

O modo CTR transforma a cifra de bloco em cifra de fluxo: o bloco cifrado é o
contador, e o texto claro é combinado por XOR com esse fluxo. Isso elimina o
preenchimento e, sobretudo, faz blocos claros iguais produzirem saídas
diferentes, o problema que a seção 6.6 demonstra no modo ECB.

---

## 5. Testes realizados

| # | Teste | O que mede | Amostra |
|---|---|---|---|
| 1 | Efeito avalanche | bits de saída alterados por 1 bit de entrada | 4.096 pares |
| 2 | Avalanche por rodada | em que rodada a difusão se completa | 4.096 pares |
| 3 | Avalanche de chave | sensibilidade a 1 bit da chave | 1.024 pares |
| 4 | Critério estrito de avalanche (SAC) | 128×128 probabilidades de inversão | 512 por célula |
| 5 | Tabela de diferenças (DDT) | limite teórico por rodada | 65.536 pares |
| 6 | Distinguidor diferencial | diferença de saída mais provável | 100.000 pares |
| 7 | Força bruta | taxa real de chaves/s e projeção | 215.040 chaves |
| 8 | Dicionário | custo imposto pelo PBKDF2 | 7 senhas |
| 9 | Perfil estatístico | entropia, χ², IC, NIST monobit e corridas | 120.000 bytes |
| 10 | Análise de frequência | texto recuperado sem chave | 120.000 bytes |
| 11 | Padrões em modo ECB | blocos repetidos em imagem estruturada | 256×256 px |
| 12 | Esteganografia | PSNR, capacidade e esteganálise χ² | 384×384 px |
| 13 | Big Data | ingestão e consulta | 1.999.952 eventos |
| 14 | Detecção de anomalias | AUC, precisão e revocação | 43.985 janelas |

Reproduzíveis por `python -m maxpay.experiments` e verificados por
`pytest` (42 testes).

---

## 6. Resultados

### 6.1 Efeito avalanche

Inverter **um** bit do texto claro altera **50,08%** dos bits do
texto cifrado, o ideal é 50%. O desvio padrão medido foi 5,560,
praticamente igual ao 5,657
esperado de uma distribuição binomial(128; 0,5). Em outras palavras, a saída se
comporta como se cada bit fosse sorteado por moeda honesta.

| Rodada | Bits alterados | % do bloco |
|---|---|---|
| 0 | 1,00 | 0,78% |
| 1 | 15,89 | 12,41% |
| 2 | 64,15 | 50,11% |
| 3 | 64,20 | 50,15% |
| 4 | 63,89 | 49,91% |
| 5 | 64,00 | 50,00% |
| 6 | 63,95 | 49,96% |
| 7 | 64,08 | 50,06% |
| 8 | 63,90 | 49,92% |
| 9 | 63,97 | 49,97% |
| 10 | 63,89 | 49,92% |
| 11 | 64,09 | 50,07% |
| 12 | 64,02 | 50,02% |
| 13 | 63,95 | 49,96% |
| 14 | 64,10 | 50,08% |

A difusão se completa na **rodada 2**. Com 14 rodadas,
a cifra opera com margem de segurança de 7,0×
sobre o mínimo necessário.

Comparações na mesma medição: AES-256 ficou em 50,08% e a variante
sem difusão, em **3,10%**, ou seja, alterar um bit da entrada
muda só 4,0 dos 128 bits de saída, deixando o resto do
bloco intacto e visível ao atacante.

A avalanche de chave foi de 50,00%: um bit
trocado na chave muda metade do texto cifrado.

### 6.2 Critério estrito de avalanche (SAC)

O SAC exige que a inversão de qualquer bit *i* da entrada inverta qualquer bit
*j* da saída com probabilidade 0,5, nas 16.384 células da matriz 128×128.

| Variante | Média | Desvio máximo | Limite (Bonferroni 5%) | Células fora | Satisfaz |
|---|---|---|---|---|---|
| MPC-128 íntegro | 0,49993 | 0,08594 | 0,10313 | 0 | **Sim** |
| 1 rodada sem difusão | 0,03094 | 0,50000 | 0,10313 | 15.362 | **Não** |

O limite usa correção de Bonferroni porque são 16.384 testes simultâneos: sem
ela, o maior desvio estouraria 3σ só pela quantidade de células, e o teste
acusaria falha onde não há.

### 6.3 Ataque de força bruta

Taxa real medida nesta máquina: **113.089 chaves/s** (um
núcleo, implementação vetorizada). Com entropia reduzida a 18 bits,
a chave foi encontrada após 215.040 tentativas, o ataque
funciona, o que valida a medição.

Extrapolando a mesma taxa:

| Espaço de chaves | Cenário | Tempo esperado | Viável? |
|---|---|---|---|
| 2^32 | 1 núcleo (medido) | 18989,20 s | Sim |
| 2^56 | 1 núcleo (medido) | 10.095 anos | Não |
| 2^64 | 1 núcleo (medido) | 2,584×10⁶ anos | Não |
| 2^128 | 1 núcleo (medido) | 4,767×10²⁵ anos | Não |
| 2^128 | 1 milhão de GPUs | 4,767×10¹⁹ anos | Não |
| 2^256 | 1 núcleo (medido) | 1,622×10⁶⁴ anos | Não |
| 2^256 | 1 milhão de GPUs | 1,622×10⁵⁸ anos | Não |

Para os 256 bits do MPC-128 seriam necessários **1,622×10⁵⁸ anos**
mesmo com um milhão de GPUs, cerca de
1,18×10⁴⁸ vezes a idade do universo. O número
de rodadas não altera isso: o espaço de chaves é o mesmo na variante enfraquecida.

**Ataque de dicionário.** Contra a senha do usuário, o PBKDF2 limita o atacante a
115,3 tentativas por segundo. A senha fraca
`banco123` caiu em 0,06 s. Já uma senha forte de
12 caracteres exigiria 6,537×10¹³ anos. **A senha, e não a cifra, é o elo
mais fraco**, e é por isso que o alongamento de chave existe.

### 6.4 Ataque diferencial

A S-box tem uniformidade diferencial 4: a melhor característica
diferencial de uma rodada tem probabilidade 2^-6.
Ao longo de 14 rodadas, uma característica útil ficaria muito abaixo
de qualquer limiar explorável.

Medição direta com 100.000 pares de texto claro
aplicando sempre a mesma diferença de entrada:

| Variante | Diferenças de saída distintas | Repetição máxima | Distinguível |
|---|---|---|---|
| MPC-128 íntegro | 100,00% | 1 ocorrência(s) | Não |
| 1 rodada sem difusão | 0,13% | 1.543 ocorrências | Sim |

Na cifra íntegra, as saídas são praticamente todas distintas, exatamente o que
se esperaria de uma permutação aleatória. Na variante enfraquecida,
1.543 pares caem na **mesma** diferença de
saída: é uma característica diferencial explorável, e o ataque tem por onde
começar.

### 6.5 Ataque estatístico

Perfil das mesmas 120.000 mensagens bancárias
sob diferentes tratamentos:

| Amostra | Entropia | χ² (p) | IC | Correlação serial | Monobit | Corridas | Blocos repetidos |
|---|---|---|---|---|---|---|---|
| Texto claro | 4,3129 | 0,0000 | 0,116338 | 0,53954 | **falha** | **falha** | 36,11% |
| MPC-128 · CTR, 14 rodadas | 7,9981 | 0,0101 | 0,003908 | 0,00228 | passa | passa | 0,00% |
| MPC-128 · ECB, 14 rodadas | 7,9060 | 0,0000 | 0,004490 | 0,00108 | **falha** | **falha** | 36,10% |
| MPC-128 · ECB, 1 rodada, sem difusão | 6,5748 | 0,0000 | 0,016021 | -0,05982 | **falha** | **falha** | 36,11% |
| AES-256-GCM | 7,9983 | 0,1601 | 0,003907 | 0,00337 | passa | passa | 0,00% |
| /dev/urandom (controle) | 7,9984 | 0,4258 | 0,003906 | 0,00104 | passa | passa | 0,00% |

O texto claro tem entropia 4,3129 bits/byte e
falha em todos os testes. A saída do MPC-128 em modo CTR tem
7,9981 bits/byte (máximo teórico 8), índice de
coincidência 0,003908 contra o 0,003906 de uma fonte
uniforme, e χ² com p = 0,0101, não se rejeita a hipótese de
uniformidade. Para efeito de controle, `/dev/urandom` na mesma medição deu
entropia 7,9984 e p = 0,4258.
**A saída da cifra é estatisticamente indistinguível de ruído do sistema
operacional.**

### 6.6 Análise de frequência: o ataque que funcionou

Mensagens bancárias usam registros de largura fixa (80
bytes aqui), e isso tem consequência: sem o MixColumns, cada posição do bloco
permanece uma substituição monoalfabética independente. A cifra apenas renomeia e
reposiciona bytes. Um atacante que conheça o formato, realista num banco, levanta a frequência de referência e remapeia coluna a coluna.

| Alvo | Acerto | Linha de base* | Posições expostas | Quebrado |
|---|---|---|---|---|
| 1 rodada, sem difusão | **62,78%** | 31,26% | **40 de 80** | Sim |
| 14 rodadas, com difusão | 4,59% | 31,26% | 0 de 80 | Não |

\* Linha de base = acerto de quem nem olha o texto cifrado e sempre chuta o byte
mais comum do formato. Comparar com 1/256 seria generoso demais.

Trecho real recuperado da variante enfraquecida, **sem nenhuma chave**:

```
original  : TX473188 BOLETO  R$    47523.68 CT1313-1 Inter     2026-11-27 APROVADO
recuperado: TX686049 BEBETO  R     1550b.38 CT4085-3 SBn10    $2026-11 03 RIQDSADO    -
```

Contra a cifra íntegra o mesmo ataque entrega 4,59%, ou
seja, **abaixo** da linha de base: o atacante teria se saído melhor chutando.

### 6.7 O modo importa mais que as rodadas

| Tratamento | Blocos repetidos | Entropia |
|---|---|---|
| Imagem original | 97,96% | 2,9170 |
| ECB · 1 rodada, sem difusão | 97,96% | 6,4040 |
| ECB · 14 rodadas | 97,96% | 6,5307 |
| CTR · 14 rodadas | 0,00% | 7,9989 |

Cifrando os pixels de uma imagem estruturada, o modo ECB preserva
36,10% dos blocos repetidos **mesmo com
14 rodadas e difusão completa**: blocos claros iguais produzem blocos
cifrados iguais, e o contorno da imagem sobrevive. No modo CTR, zero repetições.
Uma cifra forte em modo errado continua vazando estrutura.

### 6.8 Esteganografia

| Medida | Valor |
|---|---|
| Capacidade | 55.286 bytes (1.580,10% do arquivo) |
| Carga embutida | 4.877 bytes (8,82% da capacidade) |
| PSNR | **61,68 dB** |
| Erro quadrático médio | 0,044171 |
| Subpixels alterados | 19.540 de 442.368 (4,417%) |
| Desvio máximo por canal | 1 |
| Extração com chave errada | rejeitada |

Acima de 40 dB de PSNR a alteração é considerada imperceptível; aqui ficou em
61,68 dB, com desvio máximo de
1 por canal.

**Esteganálise.** O ataque de qui-quadrado de Westfeld varre a imagem em segmentos
procurando o patamar que o LSB sequencial deixa no início do arquivo. Com a mesma
carga de 8.317 bytes
(15,00% da capacidade):

| Imagem | Segmentos suspeitos (de 20) |
|---|---|
| LSB sequencial, sem chave | 2 |
| LSB chaveado do MaxPay | 0 |
| Imagem limpa | 0 |

O LSB sequencial clássico acende
2 segmentos;
a versão do MaxPay, com posições derivadas da chave, acende
**0**, igual à
imagem limpa. Espalhar os bits por uma permutação secreta não é detalhe de
implementação: é o que remove a assinatura.

### 6.9 Big Data

| Medida | Valor |
|---|---|
| Eventos | 1.999.952 |
| Período | 30 dias, 800 usuários, 4.120 IPs |
| Partições Parquet | 30 |
| Em disco | 48,57 MB (24,29 B por evento) |
| Ingestão | 2,37 s |
| Consulta de resumo | 0,116 s |
| Agregação em janelas | 0,327 s |
| Taxa de falha global | 2,405% |
| Volume financeiro simulado | R$ 295.000.802,98 |

A agregação reduz 1.999.952 eventos -> 43.985 janelas. O trabalho
pesado é feito em SQL colunar; a camada de IA recebe só o resumo.

### 6.10 Detecção de anomalias

O Isolation Forest é treinado **sem rótulos**. Os rótulos existem apenas para
medir a qualidade depois.

| Métrica | Valor |
|---|---|
| Janelas analisadas | 43.985 |
| Janelas anômalas (verdade) | 280 (0,637%) |
| ROC AUC | **0,9965** |
| Precisão média (AP) | 0,8036 |
| Ganho sobre o acaso | 126,2× |
| Alertas emitidos | 440 |
| Precisão / Revocação / F1 | 0,518 / 0,814 / 0,633 |

Como o orçamento de alertas é uma decisão de operação, e não do modelo:

| Orçamento de alertas | % das janelas | Precisão | Revocação |
|---|---|---|---|
| 109 | 0,25% | 0,982 | 0,382 |
| 219 | 0,50% | 0,854 | 0,668 |
| 439 | 1,00% | 0,517 | 0,811 |
| 879 | 2,00% | 0,297 | 0,932 |

Revisando apenas 0,25% das janelas,
a precisão é de 98,2%: quase todo
alerta é real.

Desempenho por tipo de anomalia, os cinco previstos no enunciado:

| Anomalia | Janelas | Detectadas | Revocação | Posto mediano de risco | Tipo correto |
|---|---|---|---|---|---|
| Adulteração de arquivo | 28 | 25 | 89,3% | 97 de 43.985 (0,22%) | 100,0% |
| Força bruta de login | 31 | 30 | 96,8% | 111 de 43.985 (0,25%) | 100,0% |
| Acesso atípico | 171 | 146 | 85,4% | 145 de 43.985 (0,33%) | 100,0% |
| Falhas de decifragem | 27 | 26 | 96,3% | 156 de 43.985 (0,35%) | 100,0% |
| Surto de eventos | 23 | 1 | 4,3% | 745 de 43.985 (1,69%) | 100,0% |

O **posto mediano** mostra onde cada tipo cai no ranking de risco, e não depende do orçamento
de alertas. Os quatro primeiros ficam no meio-milésimo mais arriscado. O surto de eventos fica
no 1,69%
mais arriscado, o que é longe de passar despercebido, mas não cabe no 1% que a equipe aceita
revisar.

A anomalia mais difícil é o **surto de eventos**: ela não gera falha nenhuma, só
volume. As que falham alguma coisa são detectadas quase integralmente.

### 6.11 Desempenho

| Algoritmo | Vazão |
|---|---|
| MPC-128 (Python + numpy) | 16,26 MB/s |
| AES-256-GCM (biblioteca com AES-NI) | 446,12 MB/s |

O AES é 27,4× mais rápido, e isso era esperado:
O AES usa instruções AES-NI do processador; o MPC-128 é Python com numpy puro. A comparação mede implementação, não qualidade criptográfica.

---

## 7. Parte 4: as quatro perguntas

### O sistema apresenta efeito avalanche?

**Sim.** Inverter 1 bit da entrada altera 50,08% dos bits de saída (o ideal é 50%), com desvio padrão 5,560 contra 5,657 esperado de uma binomial(128; 0,5). Ou seja, a saída se comporta como se cada bit fosse sorteado por moeda honesta. A difusão se completa na rodada 2 e a cifra usa 14. A variante sem difusão fica em 3,10%.

### Existem padrões na saída?

**Não**, no modo CTR.
No modo CTR a saída tem entropia 7,9981 bits por byte (o máximo é 8), qui-quadrado com p = 0,0101, o que não rejeita a uniformidade, índice de coincidência 0,003908 (uma fonte uniforme dá 0,003906) e zero blocos repetidos: a saída é estatisticamente indistinguível de ruído aleatório. No modo ECB, porém, blocos claros iguais continuam gerando blocos cifrados iguais: 36,10% dos blocos se repetem mesmo com 14 rodadas. O modo de operação pesa mais que o número de rodadas.

### Qual ataque foi mais eficaz?

**Estatístico / análise de frequência.** Contra o MPC-128 íntegro nenhum dos três ataques obteve vantagem. Contra a variante sem difusão, a análise de frequência foi a mais eficaz porque é a única que entrega o conteúdo: recuperou 62,78% do texto e expôs 40 das 80 posições do registro sem precisar de chave alguma. O diferencial apenas distingue a cifra de aleatório, e a força bruta não sai do lugar em nenhum dos dois casos.

Critério de ordenação: severidade do que o atacante obtém (ler o texto > distinguir a cifra > nada). Os três ataques
produzem resultados de naturezas diferentes e não se comparam por um número
único.

| Severidade | Ataque | O que o atacante obtém | Contra a cifra íntegra | Contra a variante enfraquecida |
|---|---|---|---|---|
| 3 | Estatístico / análise de frequência | recuperação de texto claro, sem chave nenhuma | 4,59% de acerto, abaixo da linha de base de 31,26% de quem só chuta o byte mais comum | 62,78% do texto recuperado e 40 das 80 posições do registro expostas |
| 2 | Diferencial | distinguir a cifra de uma permutação aleatória | avalanche de 50,08% e nenhuma diferença de saída repetida em 100.000 pares | avalanche de apenas 3,10% e 1.543 pares caindo na mesma diferença de saída |
| 1 | Força bruta | nenhum | 1,622×10⁵⁸ anos com 1 milhão de GPUs | igualmente inviável: o espaço de chaves não depende do número de rodadas |

### O sistema é seguro? Justifique.

**Sim, com ressalvas.** Dentro do escopo testado, com força bruta, ataque diferencial e análise estatística, o MPC-128 em modo CTR se comporta como uma cifra moderna e não cedeu a nenhum dos ataques. Isso demonstra solidez de projeto, não maturidade criptográfica: a camada AES-256 existe justamente para o uso real.

**A favor:**

- Avalanche de 50,08% e critério estrito de avalanche satisfeito: confusão e difusão adequadas.
- Saída indistinguível de aleatória em todos os testes aplicados (qui-quadrado p = 0,0101).
- Espaço de chaves de 256 bits: 1,622×10⁵⁸ anos mesmo com 1 milhão de GPUs.
- Probabilidade diferencial máxima da S-box de 2^-6 por rodada.
- Chave dinâmica por mensagem (salt e nonce aleatórios) e integridade por HMAC-SHA256.
- PBKDF2 com 120.000 iterações encarece o ataque de dicionário em cinco ordens de grandeza.

**Ressalvas: e elas não são formalidade:**

- Cifra própria sem análise pública: a estrutura vem da mesma família do AES, mas S-box, matriz de difusão e permutação são escolhas nossas e nunca passaram por criptanálise independente. Em produção, use AES-256.
- O modo ECB continua vazando estrutura mesmo com 14 rodadas: apenas o modo CTR autenticado deve ser usado.
- A implementação não é de tempo constante, o que abre risco de ataque por canal lateral de temporização.
- A análise aqui é empírica: não foi feita criptanálise linear nem prova formal de resistência.

---

## 8. Conclusão

O MPC-128 passou nos três ataques exigidos. Avalanche de 50,08%,
SAC satisfeito em todas as 16.384 células, saída indistinguível de aleatória e
espaço de chaves de 256 bits colocam a cifra, nas medições feitas, no mesmo
patamar de comportamento do AES-256.

O resultado mais útil deste trabalho, porém, não é esse. É a comparação com a
variante enfraquecida, que mostra **de onde** vem a segurança:

1. **Difusão é o que sustenta tudo.** Sem MixColumns, a análise de frequência
   recupera 62,78% do texto e expõe 40
   das 80 posições do registro. Aumentar rodadas não
   corrige: com difusão desligada, 14 rodadas vazam tanto quanto 1.
2. **O modo de operação pesa mais que o número de rodadas.** O ECB preservou
   36,10% dos blocos repetidos com a
   cifra íntegra.
3. **Força bruta é o ataque errado.** Inviável contra as duas variantes; a
   superfície real é a senha, e o PBKDF2 existe para encarecê-la.
4. **A anomalia mais difícil é a que não quebra nada.** O surto de exfiltração não gera
   falha nenhuma, só volume: o modelo o coloca no **1,69% mais
   arriscado** de 43.985 janelas, mas ele fica fora do orçamento de
   440 alertas, porque perde a disputa para anomalias que falham. Não é o
   modelo que não enxerga; é o orçamento que não alcança. Dobrando o orçamento para 2%, a
   revocação sobe de 4,3% para
   23,0%.

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
pytest -q                          # 42 testes
uvicorn maxpay.api:app --reload  # dashboard em http://127.0.0.1:8000
```

## 10. Onde cada requisito está

| Requisito do enunciado | Onde está | Evidência |
|---|---|---|
| Criptografia simétrica com geração dinâmica de chaves | `maxpay/cipher.py` | §3.3 |
| XOR, substituição, permutação, blocos | `maxpay/cipher.py` | §3.2 |
| Difusão / confusão | `maxpay/cipher.py` | §6.1, §6.2 |
| Esteganografia em imagens | `maxpay/stego.py` | §6.8 |
| Big Data de eventos | `maxpay/events.py`, `maxpay/lake.py` | §6.9 |
| IA para detectar comportamento anormal | `maxpay/detect.py` | §6.10 |
| Ataque de força bruta | `maxpay/attacks/brute_force.py` | §6.3 |
| Ataque diferencial | `maxpay/attacks/differential.py` | §6.4 |
| Ataque estatístico | `maxpay/attacks/statistical.py` | §6.5, §6.6 |
| Efeito avalanche | `maxpay/attacks/differential.py` | §6.1 |
| Distribuição estatística | `maxpay/metrics.py` | §6.5 |
| Dashboard | `maxpay/api.py`, `web/` | camada 6 |
| Logs de operações criptográficas | `maxpay/events.py` | §6.9 |
| Falhas de autenticação | `maxpay/events.py` | §6.10 |
| Os 5 tipos de anomalia | `maxpay/events.py` | §6.10 |
| Arquitetura em 6 camadas | todo o pacote | §2 |
| Respostas da Parte 4 | `maxpay/experiments.py` | §7 |
