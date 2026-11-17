---
version: 1
slug: "web-index-html"
primary_target: "web/index.html"
related_targets: []
---

## Scope

Superficie unica: o dashboard do MaxPay (`web/index.html`), modo Operate.
Oito destinos numa navegacao lateral: Panorama, as seis camadas da arquitetura
do enunciado (Cofre, Cifragem, Esteganografia, Big Data, IA, Veredito) e o
Laboratorio de ataques. Publico: a professora avaliadora, primeiro numa
projecao de sala de aula a varios metros, depois sozinha num notebook.

## Direction contract

THESIS: O padrao da categoria, levado ao acabamento de Linear e Vercel, e nao a
sua versao generica. Esta tela recusa o painel de seguranca enfeitado — fundo
escuro com neon, cartoes de sombra suave, azul de template — e tambem recusa o
mundo decorativo: aqui nenhuma textura compete com um numero. A tela vale pela
precisao dos cinzas, pelo alinhamento e pela tipografia tabular, nao por um
motivo visual. Cada afirmacao de seguranca aparece colada a medida que a
sustenta e, quando existe, a variante enfraquecida que a perde.

OWN-WORLD: Quase monocromatico sobre fundo claro. Uma escala de dez cinzas
frios (#FFFFFF a #18181B), separacao por borda de 1px (#E1E1E3), zero sombra
decorativa. Um unico azul institucional #15418E para estado ativo, selecao e
link; estados em vermelho #B42318, ambar #B54708 e verde #067647, sempre com
rotulo textual ao lado, nunca cor sozinha. Geist para interface, Geist Mono com
`tabular-nums` para toda grandeza medida, serial e hash. Raio 6px, escala de
espaco de 4px, densidade alta. Icones desenhados em SVG com traco unico de
1,5px. As superficies do navegador (selecao, cursor, barra de rolagem, anel de
foco) sao tematizadas a partir da mesma paleta.

STORY: A avaliadora entende em dez segundos que o sistema mede a si mesmo; passa
a acreditar porque cada numero vem acompanhado da variante enfraquecida que
falha no mesmo teste; e age abrindo o Laboratorio de ataques para rodar com os
proprios parametros e ver o resultado mudar.

FIRST VIEWPORT: Barra superior de 56px com a marca MaxPay, o estado da bateria
e o botao de executar. Rail esquerdo de 248px com a navegacao: Panorama, as seis
camadas numeradas de 1 a 6 (a numeracao carrega informacao — e a ordem da
arquitetura exigida) e, apos um divisor rotulado ANALISE, o Laboratorio de
ataques. A area principal abre no Panorama: a pergunta "O sistema e seguro?"
respondida em display, com a ressalva na mesma altura; abaixo, a faixa de quatro
medidas de topo em Geist Mono; abaixo, as quatro respostas da Parte 4, cada uma
com seu numero e seu contraponto enfraquecido. A acao primaria (Executar
bateria) fica na barra superior, a direita.

FORM: Padrao da categoria (a porta permanente), escolhido pelo usuario sobre a
mao rolada; posicao fora da lista ordenada, por ser a saida padrao e nao um
candidato. seed:717fcbc4d177b883

FINISH: unreviewed and undocumented is unfinished; this build ends with the
finish review, the verdict, DESIGN.md, and every shipping raster carrying its
provenance

## Unresolved

Nenhuma decisao visual em aberto. Pendente apenas de produto: os nomes do grupo
ja foram confirmados e entram no relatorio e nos slides, nao na interface.
