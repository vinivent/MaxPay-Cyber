# Como apresentar o FinalPay

Guia de condução da defesa do Projeto 2 de Cibersegurança Aplicada a Dados e IA,
CESAR School. Grupo: Claudio Alves, Ian Nunes, Maria Augusta, Gabriel Lima, Gabriel Rodrigues, Vinicius Ventura. Professora Renatta Nigro.

Este texto explica o que é o projeto, como a apresentação está montada, quem fala
o quê, o que mostrar ao vivo e o que responder quando a pergunta vier. Os números
foram lidos da bateria de experimentos executada em
2026-11-17 09:25:25.

---

## 1. O que vocês construíram, em um parágrafo

O FinalPay é o cofre criptográfico de um banco digital fictício. Ele protege
transações com uma cifra de bloco que vocês mesmos projetaram, a FPC-128, esconde
o resultado dentro de imagens comuns, registra 1.999.952 eventos
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
60,15% do texto da variante enfraquecida, e o modo ECB vaza
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

### 1. Abertura e arquitetura (telas 1 a 3)

Abre, diz o que é o projeto e por que ele tem duas metades. Não entra em detalhe técnico: o trabalho dessa pessoa é fazer a professora entender a aposta do grupo em trinta segundos.

O que essa pessoa fala, tela a tela:

**Tela de capa.** Boa tarde, professora. O FinalPay é o cofre de um banco digital fictício, mas o problema dele é real: toda transação precisa ser cifrada, escondida e vigiada. Nós decidimos não parar na construção. Depois de montar o cofre, nós o atacamos por dentro, com ataques clássicos da criptoanálise. É isso que queremos que a senhora julgue hoje: não se o sistema funciona, mas o quanto ele resiste. O veredito vem das medições, não da nossa opinião. Vamos começar pelas camadas que uma transação atravessa antes de chegar ao painel.

**Tela de ato1.** Essa arquitetura não é enfeite. As seis camadas são as que o enunciado pede, e nós as pusemos na ordem que uma transação percorre: alguém digita, o dado é cifrado, pode ser escondido numa imagem, é guardado e lido em massa, é analisado em busca de fraude e aparece no painel de quem vigia. Essa ordem nos deixa apontar onde um ataque entraria e o que ele veria. Todas vivem no mesmo repositório, nenhuma ficou de fora. Peça por peça: o que construímos, e onde entram os ataques.

**Tela de construido.** A ideia central é que o ataque não é um projeto separado. A defesa e os três ataques moram no mesmo repositório, porque só assim conseguimos medir, em vez de apenas afirmar. Sem isso, nós estaríamos só dizendo que o sistema é seguro. E a cifra roda nas duas versões porque uma delas serve de controle. Se a enfraquecida cede e a íntegra não, a segurança está no desenho do algoritmo, e não na nossa palavra. Vamos olhar essa cifra por dentro, a FPC-128.

### 2. A cifra (telas 4 a 6)

A parte mais exposta a pergunta. Precisa saber responder o que é nosso e o que vem do AES sem hesitar, porque essa é a pergunta mais provável da banca.

O que essa pessoa fala, tela a tela:

**Tela de algoritmo.** Essas quatro operações não estão ali por enfeite. Cada uma tem um papel: o XOR entra com a chave, a substituição quebra a linearidade, a permutação e a difusão espalham a diferença de um bit pelo bloco. Os números medem se deu certo: zero pontos fixos na S-box e uniformidade diferencial 4 deixam o melhor par diferencial em 2 elevado a menos 6. Só que essa estrutura não é invenção nossa: ela vem do AES. No próximo slide mostramos, componente por componente, o que é escolha nossa.

**Tela de projeto.** Sejamos honestos: a estrutura não é nossa, é a família do AES. Escolhemos assim de propósito, porque é a rede SPN com S-box de inverso multiplicativo que garante as boas propriedades. O que é nosso são os três componentes concretos, e nenhum deles entrou por gosto: cada um passou na verificação matemática. Diferir do AES nas 256 posições da S-box é só diferença, não é prova de que a nossa é melhor. O que não se repete é a chave: as subchaves saem do HKDF, novas a cada mensagem.

**Tela de chave.** Essa é a parte que mais nos deu trabalho. Queríamos um cofre que não guardasse chave em disco, então tudo nasce da senha, na hora. As 120.000 iterações do PBKDF2 existem para encarecer o chute de senha de quem levar o banco de dados embora. E os 50,06% são o teste de espalhamento que fizemos: 1 bit trocado na chave e a saída já não lembra a anterior. Chave boa não resolve onde o envelope fica guardado. É aí que escondemos o envelope dentro de uma imagem.

### 3. Esteganografia e antifraude (telas 7 e 8)

Duas camadas em duas telas. Segura a explicação do surto de eventos, que é o número fraco da tabela e precisa do contexto do posto de risco para não parecer falha de projeto.

O que essa pessoa fala, tela a tela:

**Tela de estego.** O ponto aqui não é esconder melhor, é esconder sem deixar assinatura estatística. O LSB sequencial clássico acende 3 de 20 segmentos no qui-quadrado: ele denuncia a presença da mensagem antes de qualquer tentativa de quebra. Na versão chaveada medimos 0, o mesmo resultado da imagem limpa. Mas o qui-quadrado é um detector só, e não testamos todos. A portadora comporta 55.286 bytes, então isso não é canal para volume grande. Volume grande é o próximo problema, e ele aparece do lado dos dados.

**Tela de antifraude.** O modelo aprendeu sem rótulos, e mesmo assim separa quase tudo: ROC AUC 0,9965 e um ganho de 126,2 vezes sobre o acaso. O surto de eventos merece explicação. A revocação é de 4,3%, o pior número da tabela, mas o posto de risco conta outra história: o modelo o coloca no 1,69% mais arriscado de 43.985 janelas. Ele não passa despercebido, ele perde a disputa pelo orçamento de alertas para as anomalias que geram falha. É por isso que medimos as duas coisas. Detectar bem não prova que a cifra resiste, então fomos atacar a nossa.

### 4. Avalanche e padrões (telas 9 a 11)

Carrega a virada do argumento: a comparação entre a cifra íntegra e a enfraquecida. É aqui que o trabalho deixa de afirmar e passa a demonstrar.

O que essa pessoa fala, tela a tela:

**Tela de ato2.** Não confiamos numa cifra só porque ela é nossa. Então atacamos a nossa. A versão enfraquecida é o nosso grupo de controle. Quando um ataque derruba a fraca e não a íntegra, a resistência é da cifra, não um defeito do teste. A força bruta é a exceção: não quebra nenhuma das duas, porque o tamanho da chave não depende das rodadas. Esses ataques dizem se a cifra aguenta, não por que ela aguenta. Para isso medimos como um único bit de entrada se espalha pela saída.

**Tela de avalanche.** O contraste é o ponto. Sem difusão, a cifra não melhora com mais rodadas: 14 rodadas dão 3,13%, e uma rodada só dá 3,09%. Repetir operação ruim não conserta nada. Quem espalha o bit é o MixColumns, e a difusão fecha na rodada 2; o resto é margem. Com difusão, medimos 50,11%, colado nos 50,01% do AES-256. O desvio padrão de 5,698 contra 5,657 mostra que a dispersão também bate, não só a média. Mas um bit bem espalhado não garante saída sem padrão. É isso que medimos agora.

**Tela de padroes.** Nós colocamos a cifra contra o AES e contra o /dev/urandom do sistema. No modo CTR, a saída da FPC-128 passa nos mesmos testes que esse ruído, então não achamos atalho estatístico. No modo ECB a história muda, e nós assumimos: 36,10% dos blocos se repetem com as mesmas 14 rodadas. O motivo é o modo, não a cifra: bloco igual na entrada vira bloco igual na saída, e rodada nenhuma conserta isso. Em CTR esse vazamento não aparece, e sobra tentar todas as chaves. Nós medimos o custo.

### 5. Os três ataques (telas 12 a 14)

O núcleo da Parte 3 do enunciado. Fecha com a análise de frequência, que é o ataque que funcionou, e entrega para o veredito.

O que essa pessoa fala, tela a tela:

**Tela de bruta.** Esse número astronômico prova menos do que parece. Ele mede o tamanho do espaço de chaves, não a qualidade do nosso desenho interno. Uma cifra fraca com a mesma chave daria a mesma conta, então não cantamos vitória aqui. O resultado útil é o de baixo. Com 114,6 tentativas por segundo, banco123 caiu em 0,06 segundos. O atacante não vai lutar com a matemática, vai atrás do usuário. Falta então olhar a estrutura interna da cifra, e é isso que atacamos agora.

**Tela de diferencial.** Esse ataque não tenta adivinhar a chave. Nós procuramos uma diferença de saída que se repita, porque repetição é estrutura vazando. Para mostrar que o método funciona, atacamos a nossa própria versão enfraquecida, de 1 rodada e sem difusão, e ela ficou distinguível. A versão íntegra não ficou. O porquê está na tela: a uniformidade diferencial 4 limita cada rodada, e 14 rodadas empilham esse limite até não sobrar nada explorável. Isso não é prova de segurança: é um ataque conhecido que não passou.

**Tela de estatistico.** Esse é o ataque que mais nos incomodou, porque não usamos chave nenhuma: só contamos bytes. Na variante sem difusão, como o registro bancário tem largura fixa, cada posição do bloco virou uma substituição simples. E com isso recuperamos 60,15% do texto e abrimos 38 de 80 posições. Com difusão, cai para 4,29%, abaixo da linha de base de 31,26%. E olhem o texto recuperado: ele sai sujo. A frequência entrega o formato do registro, não a transação inteira. É com essa ressalva que fechamos o veredito.

### 6. Veredito e fechamento (telas 15 a 19)

Responde as quatro perguntas da Parte 4 e assume os limites. A honestidade dessa parte vale mais que o resultado positivo das anteriores.

O que essa pessoa fala, tela a tela:

**Tela de ato3.** Até aqui nós mostramos medições. Agora vem a parte difícil: decidir o que elas provam. E tem um limite que precisamos assumir. A cifra é nossa, e os ataques que rodamos contra ela também. Ninguém de fora tentou quebrá-la ainda. Então ela resistiu ao que nós sabemos tentar, e isso não é o mesmo que ser segura. Agora vamos responder às perguntas do enunciado, cada uma com o número que sustenta a resposta, e depois mostrar onde esse veredito deixa de valer.

**Tela de perguntas.** Respondemos as quatro com número, não com opinião. As duas primeiras são boas notícias: 50,11% de bits virados contra os 50% ideais, e uma entropia quase no teto. A terceira é a que incomoda. O ataque mais eficaz não quebrou a chave: ele explorou a falta de difusão de uma variante e recuperou 60,15% do texto. Então o sim da última linha é condicional: 1,716 vezes 10 elevado a 58 anos protege a chave, não protege um projeto malfeito. É dessa diferença que tiramos as lições.

**Tela de conclusao.** Nós entramos achando que segurança era número de rodadas. Os dados disseram outra coisa. Sem difusão, a frequência devolve 60,15% do texto, e rodada extra nenhuma conserta isso. Com a cifra intacta, o ECB preservou 36,10% dos blocos repetidos: bloco igual entra, bloco igual sai. Em ambos, o erro é de projeto, não de força. Sobre a anomalia que escapou, nós não vamos maquiar: o orçamento de 1% foi escolha nossa, e ela custou essa detecção. Passar nos ataques que fizemos não é o mesmo que estar seguro.

**Tela de limites.** Esse slide é o que mais nos custou escrever. Passar nos três ataques que nós mesmos montamos não prova que o FPC-128 é seguro: nós escolhemos os ataques, então testamos só o que imaginamos. Prova que o projeto está coerente. Quem valida uma cifra é a comunidade, ao longo de anos, tentando quebrar. Por isso o AES-256 fica na camada que protegeria dinheiro de verdade. As ressalvas são reais: em ECB a estrutura ainda vaza. Preferimos assumir isso a maquiar o resultado. Queremos ouvir vocês.

**Tela de obrigado.** Fechamos onde começamos: o FinalPay foi construído para ser atacado pelo próprio grupo. O que levamos daqui não é a cifra, é o método. Medir, tentar quebrar, e dizer com clareza o que o resultado não prova. O trabalho foi dividido entre os nomes que estão na tela, do cofre à detecção de anomalias, e cada um responde pela parte que fez. Estamos aqui para as perguntas, inclusive as que apontam o que ainda está fraco. São essas que fazem o projeto andar.

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
setas. A imagem não muda aos olhos, e o PSNR de 61,71 dB
explica por quê. Depois use o botão de exemplo do painel da direita e revele.
Troque a senha e tente revelar de novo: a extração é recusada.

**Terceira parada, aba Resistência.** Esta é a demonstração que justifica o
trabalho. Rode o ataque de análise de frequência com a difusão **desligada**: ele
recupera 60,15% do texto e expõe
38 das 80 posições do registro
bancário, sem usar chave nenhuma. Deixe a professora ler o texto recuperado na
tela. Depois marque "Difusão ligada" e rode outra vez: cai para
4,29%, abaixo da linha de base de
31,26% de quem simplesmente chuta o byte mais
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
usa rotações (0, 1, 2, 3, 5) com constante 0x0D
contra (0, 1, 2, 3, 4) e 0x63 do AES; a
permutação é (0, 2, 3, 1) contra (0, 1, 2, 3);
a matriz de difusão é (1, 1, 3, 2) contra
(2, 3, 1, 1). A S-box resultante difere da do AES nas 256
posições. Nenhum desses valores foi escolhido por gosto: cada um saiu de uma busca
que só aceitou o que passou na verificação matemática, e existe um teste automatizado
que falha se alguém reintroduzir a construção do AES sem perceber.

**"Vocês provaram que a cifra é segura?"**
Não, e a tela 18 diz isso com todas as letras. O que foi provado é que ela resistiu
aos três ataques que o grupo sabe executar. Uma cifra se torna confiável por anos de
tentativa pública de quebra, não por uma bateria de testes dos próprios autores. É
por isso que a camada AES-256 existe no sistema.

**"Por que a detecção do surto de eventos é de só 4,3%?"**
Porque a revocação depende do orçamento de alertas, e o posto de risco não. O modelo
coloca o surto no 1,69% mais arriscado de
43.985 janelas, ou seja, ele enxerga a anomalia. O que acontece é que ela
perde a disputa pelo 1% de janelas que a equipe aceita revisar, porque compete com
anomalias que geram falha de autenticação ou de integridade. Dobrando o orçamento
para 2%, a detecção sobe. É um problema de política de operação, não de modelo cego.

**"Os dados são reais?"**
Não, e isso é proposital. Os eventos são sintéticos e **rotulados**, e é justamente
por isso que dá para medir precisão e revocação. Com dados reais sem rótulo, não
haveria como dizer se o modelo acertou.

**"Por que 14 rodadas, se a difusão fecha na rodada 2?"**
Margem de segurança. A difusão se completa cedo, e o resto das rodadas existe para
que um ataque que avance algumas rodadas ainda esbarre em muitas pela frente. É a
mesma lógica do AES, que usa 14 rodadas na versão de 256 bits.

**"Qual foi o ataque mais eficaz?"**
Estatístico / análise de frequência, e vale explicar o critério: os três ataques
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
| Efeito avalanche, cifra íntegra | 50,11% |
| Efeito avalanche, 14 rodadas sem difusão | 3,13% |
| Efeito avalanche, 1 rodada sem difusão | 3,09% |
| Entropia da saída em modo CTR | 7,9985 bits por byte |
| Blocos repetidos em modo ECB | 36,10% |
| Força bruta, 256 bits, 1 milhão de GPUs | 1,716×10⁵⁸ anos |
| Senha fraca pelo dicionário | caiu em 0,06 s |
| Análise de frequência, sem difusão | 60,15% do texto |
| Análise de frequência, com difusão | 4,29% |
| PSNR da esteganografia | 61,71 dB |
| Segmentos suspeitos, LSB chaveado | 0 de 20 |
| Eventos processados | 1.999.952 |
| ROC AUC do detector | 0,9965 |
