---
name: FinalPay
description: Cofre criptográfico que mede a própria segurança — dashboard quase monocromático, borda de 1px, número tabular.
colors:
  branco: "#FFFFFF"
  cinza-1: "#FAFAFA"
  cinza-2: "#F5F5F6"
  linha-suave: "#EDEDEF"
  linha: "#E1E1E3"
  cinza-traco: "#C9C9CE"
  cinza-cromo: "#8F8F96"
  texto-3: "#5C5C64"
  texto-2: "#55555C"
  tinta-9: "#2A2A30"
  tinta: "#18181B"
  acento: "#15418E"
  acento-hover: "#1A4FAA"
  acento-fraco: "#EEF2FA"
  selecao: "#CFDDF5"
  ok: "#067647"
  ok-fundo: "#ECFDF3"
  ok-linha: "#ABEFC6"
  warn: "#B54708"
  warn-fundo: "#FFFAEB"
  warn-linha: "#FEDF89"
  warn-texto: "#7A3A09"
  crit: "#B42318"
  crit-fundo: "#FEF3F2"
  crit-linha: "#FECDCA"
  serie-1: "#2056C7"
  serie-2: "#C2410C"
  serie-3: "#0D9488"
  serie-1-fraca: "#DCE6F9"
  serie-2-fraca: "#FBE4D6"
  serie-3-fraca: "#D4F0EB"
typography:
  display:
    fontFamily: "Geist, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif"
    fontSize: "46px"
    fontWeight: 600
    lineHeight: 1.04
    letterSpacing: "-0.036em"
  headline:
    fontFamily: "Geist, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif"
    fontSize: "26px"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.025em"
  title:
    fontFamily: "Geist, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif"
    fontSize: "19px"
    fontWeight: 600
    lineHeight: 1.34
    letterSpacing: "-0.018em"
  subtitle:
    fontFamily: "Geist, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif"
    fontSize: "14px"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "-0.012em"
  body:
    fontFamily: "Geist, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.6
    letterSpacing: "-0.006em"
  ui:
    fontFamily: "Geist, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif"
    fontSize: "13px"
    fontWeight: 500
    lineHeight: 1.3
    letterSpacing: "-0.012em"
  meta:
    fontFamily: "Geist, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif"
    fontSize: "12.5px"
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "-0.006em"
  label:
    fontFamily: "Geist, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif"
    fontSize: "11px"
    fontWeight: 500
    lineHeight: 1.3
    letterSpacing: "0.07em"
  numero:
    fontFamily: "'Geist Mono', ui-monospace, 'SF Mono', Menlo, monospace"
    fontSize: "26px"
    fontWeight: 500
    lineHeight: 1.08
    letterSpacing: "-0.03em"
    fontFeature: "tabular-nums"
  numero-xl:
    fontFamily: "'Geist Mono', ui-monospace, 'SF Mono', Menlo, monospace"
    fontSize: "46px"
    fontWeight: 500
    lineHeight: 1
    letterSpacing: "-0.038em"
    fontFeature: "tabular-nums"
  numero-tabela:
    fontFamily: "'Geist Mono', ui-monospace, 'SF Mono', Menlo, monospace"
    fontSize: "12.5px"
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "-0.02em"
    fontFeature: "tabular-nums"
rounded:
  xs: "2px"
  sm: "4px"
  md: "6px"
  lg: "8px"
  pilula: "99px"
spacing:
  "1": "4px"
  "2": "8px"
  "3": "12px"
  "4": "16px"
  "5": "20px"
  "6": "24px"
  "7": "28px"
  "8": "32px"
components:
  button:
    backgroundColor: "{colors.branco}"
    textColor: "{colors.tinta}"
    typography: "{typography.ui}"
    rounded: "{rounded.md}"
    padding: "0 12px"
    height: "32px"
  button-hover:
    backgroundColor: "{colors.cinza-2}"
    textColor: "{colors.tinta}"
  button-primary:
    backgroundColor: "{colors.acento}"
    textColor: "{colors.branco}"
    typography: "{typography.ui}"
    rounded: "{rounded.md}"
    padding: "0 12px"
    height: "32px"
  button-primary-hover:
    backgroundColor: "{colors.acento-hover}"
    textColor: "{colors.branco}"
  button-sm:
    backgroundColor: "{colors.branco}"
    textColor: "{colors.tinta}"
    typography: "{typography.meta}"
    rounded: "{rounded.md}"
    padding: "0 10px"
    height: "28px"
  input:
    backgroundColor: "{colors.branco}"
    textColor: "{colors.tinta}"
    typography: "{typography.ui}"
    rounded: "{rounded.md}"
    padding: "7px 10px"
    width: "100%"
  panel:
    backgroundColor: "{colors.branco}"
    textColor: "{colors.tinta}"
    rounded: "{rounded.lg}"
    padding: "16px"
  panel-head:
    backgroundColor: "{colors.branco}"
    textColor: "{colors.tinta}"
    typography: "{typography.subtitle}"
    padding: "13px 16px"
  nav-item:
    backgroundColor: "transparent"
    textColor: "{colors.texto-2}"
    typography: "{typography.ui}"
    rounded: "{rounded.md}"
    padding: "7px 12px"
    width: "100%"
  nav-item-hover:
    backgroundColor: "{colors.linha-suave}"
    textColor: "{colors.tinta}"
  nav-item-current:
    backgroundColor: "{colors.acento-fraco}"
    textColor: "{colors.acento}"
  tag:
    backgroundColor: "{colors.cinza-1}"
    textColor: "{colors.texto-2}"
    typography: "{typography.meta}"
    rounded: "{rounded.sm}"
    padding: "0 7px"
    height: "21px"
  tag-ok:
    backgroundColor: "{colors.ok-fundo}"
    textColor: "{colors.ok}"
  tag-warn:
    backgroundColor: "{colors.warn-fundo}"
    textColor: "{colors.warn}"
  tag-crit:
    backgroundColor: "{colors.crit-fundo}"
    textColor: "{colors.crit}"
  tag-info:
    backgroundColor: "{colors.acento-fraco}"
    textColor: "{colors.acento}"
  note:
    backgroundColor: "{colors.cinza-1}"
    textColor: "{colors.texto-2}"
    typography: "{typography.ui}"
    rounded: "{rounded.md}"
    padding: "11px 13px"
  note-warn:
    backgroundColor: "{colors.warn-fundo}"
    textColor: "{colors.warn-texto}"
  segmented:
    backgroundColor: "{colors.cinza-2}"
    textColor: "{colors.texto-2}"
    rounded: "{rounded.md}"
    padding: "2px"
  segmented-selected:
    backgroundColor: "{colors.branco}"
    textColor: "{colors.tinta}"
    rounded: "{rounded.sm}"
    padding: "4px 10px"
  table-header:
    backgroundColor: "{colors.cinza-1}"
    textColor: "{colors.texto-3}"
    typography: "{typography.label}"
    padding: "9px 16px"
  table-cell:
    backgroundColor: "{colors.branco}"
    textColor: "{colors.tinta}"
    typography: "{typography.meta}"
    padding: "9px 16px"
  tip:
    backgroundColor: "{colors.tinta}"
    textColor: "{colors.cinza-1}"
    rounded: "{rounded.md}"
    padding: "7px 9px"
---

# Design System: FinalPay

## Overview

**Creative North Star: "O Instrumento de Medição"**

O padrão da categoria — um dashboard de produto convencional — executado no
acabamento de Linear e Vercel/Geist, e não na sua versão genérica. A tela é um
instrumento: quase monocromática sobre fundo claro, separada por bordas de 1px,
sem nenhuma textura competindo com um número. O valor visual vem da precisão dos
cinzas, do alinhamento e da tipografia tabular, nunca de um motivo decorativo.

Densidade alta, mas calibrada para duas distâncias de leitura: a tela é vista
projetada em sala de aula, a vários metros, e também sozinha num notebook. Por
isso a interface opera a 14px enquanto o texto corrido sobe para 15px e as
evidências centrais aparecem em 26px ou 46px de Geist Mono. Cor aparece em dois
trabalhos e só neles: estado e série de dados. Todo o resto é cinza.

Recusas confirmadas no artefato: painel de segurança enfeitado (fundo escuro com
neon, cartão de sombra suave, azul de template) e mundo decorativo. A cena de uso
decide: projetor de sala com luz acesa lava fundo escuro.

**Key Characteristics:**
- Quase monocromático sobre branco, onze passos de cinza frio.
- Separação por borda de 1px; uma única sombra em todo o sistema.
- Um acento institucional (`#15418E`), reservado a estado ativo, link e foco.
- Toda grandeza medida em Geist Mono com `tabular-nums`.
- Estado sempre com rótulo em palavras ao lado da cor.
- Ícones em SVG autoral, traço único de 1,5px.

## Colors

Paleta de cinzas frios com um azul institucional; cor cromática só entra como
estado ou como série de dados.

### Primary
- **Azul Institucional** (`{colors.acento}`): item de navegação atual, link,
  botão primário, `caret-color`, anel de foco, `accent-color` de range e
  checkbox, marca da identidade e skip link. 9,64:1 sobre branco.
  **Azul Institucional Vivo** (`{colors.acento-hover}`) existe só no hover do
  botão primário. **Névoa de Acento** (`{colors.acento-fraco}`) é o fundo do
  estado atual, o halo de foco do campo e a tag informativa.
  **Azul de Seleção** (`{colors.selecao}`) pinta `::selection`.

### Secondary
As três cores de estado. Contraste medido sobre branco:
- **Verde Aprovado** (`{colors.ok}`, 5,69:1): propriedade de segurança que passou.
  Fundo `{colors.ok-fundo}`, borda `{colors.ok-linha}`.
- **Âmbar Ressalva** (`{colors.warn}`, 5,43:1): limite conhecido, resultado
  parcial. Fundo `{colors.warn-fundo}`, borda `{colors.warn-linha}`.
  Em bloco de nota o texto escurece para `{colors.warn-texto}` (8,62:1), porque o
  fundo âmbar derruba o contraste da própria cor de estado.
- **Vermelho Falha** (`{colors.crit}`, 6,57:1): variante enfraquecida que perde o
  teste. Fundo `{colors.crit-fundo}`, borda `{colors.crit-linha}`.

### Tertiary
A paleta categórica de dados, replicada em `charts.js` como `SERIES`:
- **Azul de Série** (`{colors.serie-1}`), **Laranja Queimado**
  (`{colors.serie-2}`), **Verde-Azulado** (`{colors.serie-3}`), com as variantes
  fracas para preenchimento. Verificada para deficiência de visão de cores
  (protanopia, deuteranopia e tritanopia) antes de ser adotada, em modo claro
  sobre fundo branco: pior par com **ΔE 13,7** em OKLab ×100 (alvo ≥ 8) e **22,2**
  para visão normal (piso 15), os três acima de 3:1 de contraste sobre o branco.
  Três é o teto por decisão de projeto: os três passam no teste considerando
  **todos** os pares, não só os adjacentes, e nenhum gráfico do produto precisa
  de uma quarta série. Um quarto slot exigiria refazer a verificação.

### Neutral
- **Branco** (`{colors.branco}`): fundo do documento, do painel, do campo e do
  botão secundário.
- **Papel** (`{colors.cinza-1}`): rail, cabeçalho de tabela, tag neutra, nota,
  bloco de código, hover de linha e de painel navegável.
- **Papel Fundo** (`{colors.cinza-2}`): trilha do segmented, código em linha,
  hover de botão.
- **Divisor Interno** (`{colors.linha-suave}`): divisores dentro de um bloco e
  hover de navegação; é também o cinza neutro do centro da escala divergente.
- **Borda** (`{colors.linha}`): contorno padrão de todo bloco e controle.
- **Traço** (`{colors.cinza-traco}`): borda em hover, polegar da barra de
  rolagem, aro do spinner, chave da dica sobre fundo escuro.
- **Cromo** (`{colors.cinza-cromo}`, 3,21:1): linha de referência tracejada e
  hover do polegar de rolagem. Nunca texto.
- **Texto Terciário** (`{colors.texto-3}`, 6,62:1): rótulo, meta, termo de ficha,
  texto de eixo.
- **Texto Secundário** (`{colors.texto-2}`, 7,39:1): texto corrido e de apoio.
- **Borda da Dica** (`{colors.tinta-9}`): único uso.
- **Tinta** (`{colors.tinta}`, 17,72:1): texto principal; também o fundo da dica
  de gráfico, a única superfície escura do sistema.

### Named Rules

**A Regra do Rótulo Junto.** Nenhum estado é transmitido só por cor. Toda tag
carrega palavra; o ponto de 5px é redundância, não informação. Item ativo muda
cor, peso (600) e `aria-current`. Gráfico carrega resumo em palavras.

**A Regra dos Dois Trabalhos da Cor.** Cor cromática só aparece como estado ou
como série de dados. Hierarquia, superfície e profundidade são sempre cinza.
Um painel colorido "porque é importante" está fora do sistema.

**A Regra do Cromo Tematizado.** As superfícies do navegador fazem parte da
paleta: seleção em `{colors.selecao}`, cursor e anel de foco em
`{colors.acento}`, barra de rolagem fina com polegar `{colors.cinza-traco}`
sobre trilha transparente, link com acento e sublinhado de 1px a 3px de offset.
Um azul de sistema ou uma rolagem padrão quebraria o quase-monocromático
exatamente na borda da janela.

**A Regra do Cinza de Texto.** `{colors.cinza-cromo}` fica em 3,21:1: serve a
traço, tracejado e cromo. Texto começa em `{colors.texto-3}`.

## Typography

**Interface e títulos:** Geist (400, 500, 600).
**Grandeza medida:** Geist Mono (400, 500).
Ambas **auto-hospedadas** em `web/fonts/*.woff2`, declaradas com
`font-display: swap` e `unicode-range` latino. Sem CDN, sem fonte de sistema para
display.

**Caráter:** sans neo-grotesca de aperto negativo (`-0.006em` no corpo,
`-0.021em` nos títulos, `text-wrap: balance`) ao lado de uma mono de desenho
irmão. A mono não é fantasia: é a marca visual de "isto foi medido".

### Hierarchy
- **Display** (`{typography.display}`): resposta em palavras na abertura, e o
  número único de destaque na variante mono (`{typography.numero-xl}`).
- **Headline** (`{typography.headline}`): título de página e a resposta-tese do
  Panorama; na variante mono (`{typography.numero}`), o valor da faixa de
  medidas.
- **Title** (`{typography.title}`): título de seção dentro da página.
- **Subtitle** (`{typography.subtitle}`): título de painel.
- **Body** (`{typography.body}`): texto corrido, em `{colors.texto-2}`, com
  medida de linha travada em 68ch. São 15px, um passo acima da interface, porque
  a tela é lida também projetada, a vários metros.
- **UI** (`{typography.ui}`): botão, campo, item de navegação, nota.
- **Meta** (`{typography.meta}`): legenda, carimbo, unidade, célula numérica, em
  `{colors.texto-3}`.
- **Label** (`{typography.label}`): caixa alta com `+0.07em`, em
  `{colors.texto-3}`. Rótulo de campo, cabeçalho de tabela, grupo do rail e
  rótulo de medida — e nada além disso.

### Named Rules

**A Regra Tabular.** Toda grandeza medida — número, serial, hash, base64, rótulo
de eixo, célula numérica, valor de ficha, valor de dica — é Geist Mono com
`font-variant-numeric: tabular-nums`. A largura não pode dançar entre
redesenhos. Número alinha à direita em tabela e em ficha técnica; o cabeçalho
dessas colunas volta para a sans.

**A Regra da Resposta em Palavras.** Mono fica reservado para número. Resposta em
palavras é sans, mesmo a 46px. Mono como figurino de "tela técnica" está fora.

**A Regra do Rótulo Não-Kicker.** O estilo de rótulo em caixa alta pertence a
campo, cabeçalho de tabela e grupo de navegação. Nenhuma página abre com uma
linha em caixa alta acima do título.

## Layout

Casca fixa em duas colunas: barra superior de 56px (`position: fixed`,
translúcida — branco a 86% com `backdrop-filter: saturate(180%) blur(12px)` — e
borda inferior de 1px) e rail esquerdo de 248px (`position: fixed`, fundo
`{colors.cinza-1}`, borda direita de 1px). O conteúdo ocupa a segunda coluna com
`padding: calc(56px + 28px) 32px 96px` e `max-width: 1120px`.

O padding esquerdo da barra superior (24px) alinha ao texto do rail (12+12) e o
direito (32px) ao conteúdo principal.

**Ritmo de espaço:** base 4px, com passos ópticos ímpares onde a altura de linha
pede (5, 7, 9, 11, 13, 18). O ritmo dominante é **16px** (corpo de painel, gap de
grade, pilha padrão) e **28px** (pilha larga, cabeçalho de página). Grades são
`repeat(n, minmax(0, 1fr))` com `align-items: start` — 2, 3 ou 4 colunas.

**Reserva de altura:** todo host de dado assíncrono declara `min-height` no CSS
(painel do Panorama 248/304/212px, veredito 640px, gráficos 230–250px, faixa de
medidas vazia 113px). Sem isso a página salta quando os dados chegam.

**Marcos e ordem de leitura:** `header` da barra superior, `nav` do rail com
rótulo acessível, `main#conteudo`. Cada destino é uma `section` com
`aria-labelledby` apontando para o próprio título; um `h1` por destino, seções em
`h2`, títulos de painel em `h2` com o tamanho de subtítulo — a tag dá o nível, a
classe dá o tamanho. O primeiro elemento focável do documento é um skip link para
`#conteudo`, escondido por `translateY(-200%)` e visível em `:focus`.

### Named Rules

**A Regra dos Dois Pontos de Quebra.** Em **≤1080px** as grades de 3 e 4 colunas
caem para 2 e a faixa de medidas vira 2×2, reconstruindo as bordas (o terceiro
item perde a borda esquerda, terceiro e quarto ganham borda superior). Em
**≤860px** a casca se desmonta: rail a 0px, coluna única, o rail passa a estático
e vira uma faixa horizontal rolável com borda inferior, a barra superior reduz a
16px e esconde a tag da marca e o estado da bateria, todas as grades viram uma
coluna, display e headline caem para 22px e os destaques de 46px para 32px.

**A Regra do `min-width: 0`.** Item de grade tem `min-width: auto` por padrão:
sem zerar, a linha rolável do rail estica a coluna e a página inteira vaza de
lado no celular. Vale para a casca, para as colunas e para a barra superior.

## Elevation & Depth

Sistema plano. Profundidade é dada por **borda de 1px** e por camada tonal entre
`{colors.branco}`, `{colors.cinza-1}` e `{colors.cinza-2}` — nunca por sombra.
Hover não levanta nada: escurece a borda para `{colors.cinza-traco}` ou troca o
fundo um passo. A barra superior se separa por translucidez e borda, não por
sombra.

### Shadow Vocabulary
- **Dica flutuante** (`box-shadow: 0 4px 12px rgb(24 24 27 / 18%)`): a única
  sombra decorativa do sistema, e só porque a dica flutua sobre o gráfico e
  precisa se descolar dele.
- **Halo de foco** (`box-shadow: 0 0 0 3px {colors.acento-fraco}`): anel de foco
  de campo, não sombra. Acompanha borda de acento e `outline` de 2px.

### Named Rules

**A Regra da Borda em Vez da Sombra.** Um bloco novo se separa com
`1px solid {colors.linha}` e raio de 8px. Se a tentação for uma sombra suave, a
resposta é borda mais troca de fundo. A exceção é nominal e única: a dica de
gráfico.

**A Regra do Painel Sem Cartão Dentro.** Painel não aninha painel. Quatro números
se separam por divisores de 1px dentro de um único contorno, não por quatro
caixas; tabela e gráfico entram com o corpo do painel sem padding, encostando na
borda.

## Shapes

Quatro raios com papel fixo: **2px** só para marca de dado com 12px ou menos
(quadrado de legenda, quadrado de série dentro da dica), onde 4px já leria como
círculo; **4px** para peça pequena (tag, quadrado numerado da navegação, marca da
identidade, botão interno do segmented, código em linha, anel de foco),
**6px** como padrão (botão, campo, nota, item de navegação, dica, skip link) e
**8px** para contêiner (painel, faixa de medidas). Pílula (`99px`) só em forma
redonda: ponto de estado, spinner, polegar da barra de rolagem. Anel de foco
global arredonda a 3px.

Borda é sempre 1px: `{colors.linha}` no contorno externo de qualquer bloco ou
controle, `{colors.linha-suave}` em divisor interno. Nenhuma borda de 2px,
nenhuma borda tracejada fora da linha de referência do gráfico.

Ícones: `<symbol>` SVG em sprite único no documento, `viewBox 0 0 24 24`, traço
único de **1,5px** em `currentColor`, `fill: none`, pontas e junções
arredondadas, renderizados a 14px (botão), 15px (nota) ou 16px (navegação).

## Components

### Buttons
- **Forma:** retângulo suave (raio 6px), borda de 1px, altura de 32px
  (`{components.button}`), 28px na variante pequena (`{components.button-sm}`).
  Ícone SVG de 14px com 7px de gap.
- **Secundário (padrão):** branco com borda; hover escurece fundo e borda
  (`{components.button-hover}`), `:active` desce um passo para
  `{colors.linha-suave}`, `[disabled]` fica em opacidade .5 com cursor proibido.
- **Primário:** acento sólido sem borda visível (`{components.button-primary}`),
  hover em `{components.button-primary-hover}`, `:active` volta ao acento base.
  Um primário por tela — a ação de executar a bateria, na barra superior.
- **Foco:** anel global de 2px com 2px de offset.

### Chips
- **Tag de estado** (`{components.tag}`): 21px de altura, ponto de 5px em
  `currentColor` + rótulo em palavras. Variantes `{components.tag-ok}`,
  `{components.tag-warn}`, `{components.tag-crit}`, `{components.tag-info}` e a
  neutra padrão; a variante lisa suprime o ponto para rótulo que não é estado.
  A borda sempre acompanha a família da cor.

### Cards / Containers
- **Painel** (`{components.panel}`): raio 8px, borda de 1px, `overflow: hidden`.
  Cabeçalho (`{components.panel-head}`) alinhado por `baseline` com divisor
  interno; corpo com 16px, ou sem padding para tabela e gráfico.
  Sem sombra. Na variante navegável, hover escurece a borda e vira fundo papel.
- **Faixa de medidas:** grade de 4 colunas num contorno único, dividida por
  bordas de 1px; cada célula é rótulo + valor mono + nota.

### Inputs / Fields
- **Campo** (`{components.input}`): borda de 1px, raio 6px, largura total,
  rótulo em bloco com 6px de respiro. Área de texto é mono 12,5px, altura mínima
  de 92px, redimensionável só na vertical.
- **Foco:** borda de acento + halo de 3px em `{colors.acento-fraco}`; por teclado
  soma `outline` de 2px. Foco por clique recebe borda e halo, sem o `outline`.
- **Hover:** borda para `{colors.cinza-traco}`.
- **Desabilitado:** não há estilo autoral; herda o do navegador.
- **Segmented** (`{components.segmented}`): alternador de duas a três opções,
  trilha cinza com borda; a opção escolhida fica branca com borda
  (`{components.segmented-selected}`), e o padding compensa o 1px para o texto
  não deslocar. O estado vem de `aria-pressed`, não de uma classe.
- **Caixa de seleção e range:** `accent-color` em `{colors.acento}`, caixa de 15px.

### Navigation
- **Item** (`{components.nav-item}`): 13px/500, raio 6px, largura total, ícone de
  16px ou quadrado numerado de 19px em mono — a numeração carrega informação, é a
  ordem da arquitetura. Hover em `{components.nav-item-hover}`; o destino atual
  (`{components.nav-item-current}`) soma peso 600 e inverte o quadrado numerado
  para acento sólido.
- **Grupos** separados por 20px, cada um com seu rótulo em caixa alta.
- **Mobile (≤860px):** o rail vira faixa horizontal rolável no topo, itens em
  largura automática e sem quebra, rótulos de grupo escondidos.

### Tables
- **Tabela:** cabeçalho fixo (`position: sticky`) com estilo de rótulo sobre
  fundo papel (`{components.table-header}`); linhas separadas por divisor
  interno, última sem borda, hover de linha em papel. Célula numérica
  (`{components.table-cell}`) alinha à direita em mono tabular.
- **Ficha técnica:** duas colunas (`max-content 1fr`), termo em texto terciário à
  esquerda, valor em mono tabular à direita, divisor por linha, último par sem
  borda.
- **Nota** (`{components.note}`): bloco com ícone de 15px e texto de 13px;
  variante âmbar (`{components.note-warn}`) com texto escurecido.

### Gráficos (componente de assinatura)

SVG escrito à mão em `charts.js`, três primitivas: linha, barras e matriz.
Regras que a camada impõe:

- **Um único eixo rotulado por gráfico:** ticks de Y mais a linha de base em X.
  Sem eixo duplo.
- **Marcas finas:** a barra nunca passa de 44px de largura, por mais espaço que
  sobre; o modo denso zera gap e raio para histograma.
- **Extremidade arredondada de até 4px só no topo**, ancorada na linha de base
  (`r = min(raio, altura)`), desenhada à mão em `path`. A base nunca arredonda.
- **Grade recessiva:** linhas de grade em `{colors.linha-suave}` com
  `shape-rendering: crispEdges`, eixo em `{colors.linha}`, linha de referência
  tracejada `3 3` em `{colors.cinza-cromo}`. Textos de eixo em mono 11px, nomes
  de categoria em sans 10,5px, título de eixo em caixa alta `+0.06em`.
- **Passo de tick inteiro quando a grandeza é inteira:** um eixo de rodadas não
  pode rotular 2,8 como "3". Formatação `pt-BR`, vírgula decimal.
- **Legenda só a partir de duas séries**, acima do gráfico, quadradinho de 9px +
  nome; a legenda anterior é removida a cada redesenho para não empilhar.
- **Camada de hover em todas as formas:** em linha, retângulo de captura com mira
  vertical e um ponto de leitura por posição de X; em barras, hover por barra a
  0,78 de opacidade; em matriz, captura por célula. A dica
  (`{components.tip}`) é sempre chave + valor em mono tabular, sobre a única
  superfície escura do sistema.
- **Escala divergente para a matriz SAC:** dois polos (`{colors.serie-1}` ↔
  `{colors.serie-2}`) com `{colors.linha-suave}` neutro no centro, porque o SAC
  gira em torno de 0,5; legendada com três marcas numéricas. A matriz é
  rasterizada em canvas de 1px por célula e pintada com
  `image-rendering: pixelated`.
- **Resumo acessível obrigatório:** todo host declara `data-resumo`, e a
  moldura o copia para o `<title>` e para o `aria-label` do SVG. É a leitura do
  gráfico em palavras para quem não vê a forma.
- **Redesenho estável:** só redesenha com variação de largura ≥24px, sobre a
  altura já reservada no CSS.

### Spinner
Aro de 13px em `{colors.cinza-traco}` com topo em acento, 620ms linear infinito.
Em movimento reduzido, para de girar e fica estático em acento.

### Named Rules

**A Regra do Único Movimento Autorado.** Existe um só momento de animação no
sistema: a curva de avalanche se desenha uma vez
(`stroke-dashoffset`, 900ms, `cubic-bezier(.16,1,.3,1)`, `forwards`). Fora dele
só há transições funcionais de 90–120ms e o spinner de trabalho. Com
`prefers-reduced-motion: reduce`, animações e transições caem para 1ms, a curva
aparece inteira e o spinner congela.

## Do's and Don'ts

### Do:
- **Do** separar com `1px solid {colors.linha}` e raio de 8px, e dar
  profundidade trocando o fundo entre branco, `{colors.cinza-1}` e
  `{colors.cinza-2}`.
- **Do** colocar toda grandeza medida em Geist Mono com `tabular-nums`, alinhada
  à direita quando vive em coluna.
- **Do** acompanhar toda cor de estado de um rótulo em palavras — a cor é
  redundância.
- **Do** manter o texto corrido a 15px e travado em 68ch: a tela é lida também
  projetada, a vários metros.
- **Do** declarar `min-height` em qualquer host que recebe dado assíncrono, antes
  de preencher.
- **Do** declarar `data-resumo` em todo gráfico novo, com a leitura do dado em
  palavras.
- **Do** desenhar ícone novo como `<symbol>` no sprite, `viewBox 0 0 24 24`,
  traço de 1,5px em `currentColor`.
- **Do** manter contraste em AA para texto comum e AAA para número de destaque,
  pelo projetor de sala com luz acesa; texto começa em `{colors.texto-3}`
  (6,62:1).
- **Do** manter um `h1` por destino, seção em `h2` e o skip link como primeiro
  focável; nenhuma regra remove `outline` sem pôr outro anel no lugar.

### Don't:
- **Don't** usar sombra decorativa. Nenhum cartão flutua; a única sombra
  não-foco do sistema é a da dica de gráfico.
- **Don't** aninhar cartão dentro de cartão: divisor de 1px dentro de um contorno
  único resolve.
- **Don't** abrir uma página com linha em caixa alta acima do título. O estilo de
  rótulo é de campo, de cabeçalho de tabela e de grupo de navegação.
- **Don't** usar mono como figurino: resposta em palavras é sans, mesmo a 46px.
- **Don't** transmitir estado só por cor — um ponto verde sem a palavra ao lado
  está fora.
- **Don't** usar emoji ou ícone de fonte no lugar de SVG.
- **Don't** introduzir fundo escuro com neon ou azul de template: a cena de uso
  (projetor com luz acesa) lava fundo escuro.
- **Don't** carregar fonte por CDN nem cair em fonte de sistema para display: as
  duas famílias são auto-hospedadas em woff2.
- **Don't** pôr texto sobre `{colors.cinza-cromo}` (3,21:1); ele serve a traço e
  cromo.
- **Don't** abrir um quarto slot de série de dados: a validação cobre três.
- **Don't** escrever valor de espaço solto em atributo `style`; use a escala.

<!-- Divergências registradas entre o contrato de direção e o artefato: o
contrato fala em "raio 6px", o build usa três raios com papéis fixos (4/6/8); o
contrato fala em "escala de espaço de 4px", o build é base 4 com passos ópticos
ímpares (5, 7, 9, 11, 13, 18); a escala de cinzas tem onze tokens, com
texto-3 e texto-2 como vizinhos próximos dividindo o papel de texto secundário.
Em ambos os casos vale o artefato. -->
