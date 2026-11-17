# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Backend Python (FastAPI) servindo uma API JSON. Frontend artesanal em HTML/CSS/JS
sem framework e sem etapa de build, servido estaticamente pelo proprio FastAPI.
Escolha confirmada pelo usuario: maximo controle estetico e execucao com um unico
comando, sem `node_modules` para o avaliador instalar.

Dependencias de dados e IA: numpy, pandas, DuckDB + Parquet, scikit-learn, Pillow,
cryptography. Ambiente virtual `.venv` no proprio repositorio.

## Users

**Primario — o avaliador.** A professora Renatta Nigro (CESAR School, disciplina
Ciberseguranca Aplicada a Dados e IA). Dois momentos distintos de uso, ambos
confirmados pelo usuario:
1. assistindo a uma apresentacao projetada em sala, a varios metros da tela;
2. depois, clonando o repositorio e executando sozinha, sem acompanhamento.

**Secundario — o grupo apresentador.** Estudantes conduzindo a demonstracao ao
vivo, que precisam chegar a qualquer evidencia em poucos cliques e sem decorar
caminhos.

**Persona interna do produto — o analista de seguranca do banco.** Papel ficcional
que o sistema simula: opera o cofre, revisa alertas e decide o que investigar.

## Product Purpose

O FinalPay e um cofre criptografico para um banco digital ficticio, construido
como objeto de estudo: protege transacoes e documentos e, ao mesmo tempo, expoe
o proprio funcionamento a ataques para que se possa julgar se e seguro.

Sucesso = o avaliador percorre as seis camadas da arquitetura exigida, ve as
evidencias medidas (nao afirmadas) e consegue responder as quatro perguntas da
Parte 4 do enunciado a partir do que esta na tela.

## Positioning

A maioria dos trabalhos da disciplina implementa uma cifra OU ataca uma cifra.
O FinalPay faz as duas coisas sobre a mesma base de codigo e deixa o resultado
cair de um lado so quando os numeros mandam: a cifra propria FPC-128 convive com
uma variante deliberadamente enfraquecida, e os mesmos tres ataques rodam contra
as duas. O veredito de seguranca e derivado dos experimentos em tempo de
execucao, nunca digitado a mao.

## Operating Context

- Executado localmente em uma maquina de desenvolvimento (macOS/Linux), via
  `uvicorn finalpay.api:app`, com os dados ja gerados em `data/lake`.
- A bateria de experimentos (`python -m finalpay.experiments`) grava
  `results/experimentos.json`; dashboard, relatorio e slides leem desse arquivo.
- Sala de aula com projetor de qualidade incerta: contraste e tamanho de texto
  precisam sobreviver a isso.
- Entregaveis que acompanham o sistema: relatorio tecnico e slides, ambos em
  portugues.

## Capabilities and Constraints

Capacidades confirmadas (todas implementadas e medidas):
- cifragem simetrica propria FPC-128 (SPN, bloco 128 bits, chave 256 bits,
  14 rodadas) nos modos CTR autenticado e ECB (este ultimo so para analise);
- camada AES-256-GCM como algoritmo alternativo e linha de base de comparacao;
- chave dinamica por mensagem: PBKDF2 + HKDF sobre salt e nonce aleatorios;
- esteganografia LSB com posicoes derivadas da chave, em imagens PNG;
- geracao e armazenamento de milhoes de eventos em Parquet particionado,
  consultados com DuckDB;
- deteccao de anomalias com Isolation Forest sobre janelas de comportamento,
  cobrindo os cinco tipos de anomalia previstos no enunciado;
- tres ataques executaveis ao vivo com parametros do usuario: forca bruta,
  diferencial e estatistico/frequencia.

Restricoes:
- o FPC-128 e um exercicio academico, nao um algoritmo de producao; isso
  precisa estar dito na propria interface, nao escondido no relatorio;
- a implementacao nao e de tempo constante (canal lateral de temporizacao);
- o conjunto de eventos e sintetico, com rotulos conhecidos — e o que torna
  possivel medir precisao e revocacao do detector;
- sem autenticacao de usuario: o sistema roda local, para um avaliador.

Terminologia fixada em portugues: cofre, envelope, janela, alerta, veredito,
efeito avalanche, difusao, confusao.

## Brand Commitments

- Nome do produto: **FinalPay**. Definido pelo usuario.
- Restricao visual vinculante, nas palavras do usuario: "cores de banco",
  "sobrio e minimalista e ao mesmo tempo moderno". Registrada sem ampliacao.
- Preferencia permanente, escolhida pelo usuario na rodada de direcao: o
  **padrao da categoria**, executado em fidelidade total — sem ironia e sem
  maneirismo infiltrado. A regua de acabamento, nomeada pelo usuario, e
  **Linear e Vercel/Geist**: quase monocromatico, borda de 1px no lugar de
  sombra, cinzas precisos, cor reservada para estado. Fundo claro, decidido
  pela cena de uso (projetor de sala de aula com luz acesa lava fundo escuro).
  O usuario rejeitou explicitamente a primeira execucao desse padrao por ser
  generica ("AI slop"): aqui, convencao e um compromisso de acabamento, nao
  uma licenca para o default.
- Idioma: portugues em toda a interface e em todos os entregaveis, preservando
  os termos tecnicos consagrados em ingles (avalanche, S-box, Isolation Forest,
  Parquet).
- Autoria dos entregaveis: trabalho em grupo, confirmado pelo usuario —
  Claudio Alves, Ian Nunes, Maria Augusta, Gabriel Lima, Gabriel Rodrigues e
  Vinicius Ventura. Os seis nomes constam do relatorio, dos slides e do README.

## Evidence on Hand

Reais e no repositorio, nada fabricado:
- `results/experimentos.json` — todas as medicoes, regeneravel por comando;
- `data/lake/` — ~2.000.000 de eventos sinteticos em 30 particoes Parquet (46 MB);
- enunciado oficial: `Aula 26 - Projeto 2.pdf` (CESAR School, novembro de 2026).

Nao existem e nao devem ser inventados: clientes, depoimentos, benchmarks de
terceiros, auditoria externa da cifra, dados de usuarios reais.

## Product Principles

1. **Numero medido vence numero afirmado.** Nada aparece na tela sem ter sido
   calculado pelo codigo; se um experimento nao rodou, a interface diz isso.
2. **Mostrar os dois lados.** Toda propriedade de seguranca e apresentada junto
   da variante enfraquecida que a perde, porque e a comparacao que prova o ponto.
3. **A ressalva anda junto com o resultado.** O limite de uma cifra propria e
   parte da entrega, nao uma nota de rodape.
4. **Caber na distancia da sala.** Qualquer evidencia central precisa ser legivel
   num projetor, a varios metros.
5. **Um comando para rodar.** O avaliador nao deve precisar montar o ambiente a
   mao para ver o sistema funcionando.

## Accessibility & Inclusion

Requisito derivado do contexto de uso projetado: contraste alto o suficiente para
projetor de baixa qualidade (alvo WCAG AA para texto comum e AAA para os numeros
de destaque), nenhuma informacao transmitida apenas por cor (os estados de
seguranca precisam de rotulo textual alem da cor), e alvos de clique confortaveis
para quem opera a demonstracao de pe.
