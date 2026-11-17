"""Notas do apresentador, uma por tela do deck.

Texto para ser LIDO EM VOZ ALTA durante a defesa. A tecla `N` mostra e esconde
o painel na apresentacao; ele tambem sai na impressao quando esta visivel.

Cada nota foi escrita contra o texto que de fato aparece na tela e depois
revisada por um passo adversarial, que procurou numero inventado, afirmacao sem
lastro na projecao e exagero de resultado.

Chave = id da tela em `slides.py`.
"""

NOTAS: dict[str, str] = {
    "capa": """Boa tarde, professora. O FinalPay é o cofre de um banco digital fictício, mas o problema dele é real: toda transação precisa ser cifrada, escondida e vigiada. Nós decidimos não parar na construção. Depois de montar o cofre, nós o atacamos por dentro, com ataques clássicos da criptoanálise.

É isso que queremos que a senhora julgue hoje: não se o sistema funciona, mas o quanto ele resiste. O veredito vem das medições, não da nossa opinião. Vamos começar pelas camadas que uma transação atravessa antes de chegar ao painel.""",

    "ato1": """Essa arquitetura não é enfeite. As seis camadas são as que o enunciado pede, e nós as pusemos na ordem que uma transação percorre: alguém digita, o dado é cifrado, pode ser escondido numa imagem, é guardado e lido em massa, é analisado em busca de fraude e aparece no painel de quem vigia. Essa ordem nos deixa apontar onde um ataque entraria e o que ele veria. Todas vivem no mesmo repositório, nenhuma ficou de fora. Peça por peça: o que construímos, e onde entram os ataques.""",

    "construido": """A ideia central é que o ataque não é um projeto separado. A defesa e os três ataques moram no mesmo repositório, porque só assim conseguimos medir, em vez de apenas afirmar. Sem isso, nós estaríamos só dizendo que o sistema é seguro.

E a cifra roda nas duas versões porque uma delas serve de controle. Se a enfraquecida cede e a íntegra não, a segurança está no desenho do algoritmo, e não na nossa palavra. Vamos olhar essa cifra por dentro, a FPC-128.""",

    "algoritmo": """Essas quatro operações não estão ali por enfeite. Cada uma tem um papel: o XOR entra com a chave, a substituição quebra a linearidade, a permutação e a difusão espalham a diferença de um bit pelo bloco. Os números medem se deu certo: zero pontos fixos na S-box e uniformidade diferencial 4 deixam o melhor par diferencial em 2 elevado a menos 6.

Só que essa estrutura não é invenção nossa: ela vem do AES. No próximo slide mostramos, componente por componente, o que é escolha nossa.""",

    "projeto": """Sejamos honestos: a estrutura não é nossa, é a família do AES. Escolhemos assim de propósito, porque é a rede SPN com S-box de inverso multiplicativo que garante as boas propriedades. O que é nosso são os três componentes concretos, e nenhum deles entrou por gosto: cada um passou na verificação matemática.

Diferir do AES nas 256 posições da S-box é só diferença, não é prova de que a nossa é melhor. O que não se repete é a chave: as subchaves saem do HKDF, novas a cada mensagem.""",

    "chave": """Essa é a parte que mais nos deu trabalho. Queríamos um cofre que não guardasse chave em disco, então tudo nasce da senha, na hora. As 120.000 iterações do PBKDF2 existem para encarecer o chute de senha de quem levar o banco de dados embora. E os 50,06% são o teste de espalhamento que fizemos: 1 bit trocado na chave e a saída já não lembra a anterior.

Chave boa não resolve onde o envelope fica guardado. É aí que escondemos o envelope dentro de uma imagem.""",

    "estego": """O ponto aqui não é esconder melhor, é esconder sem deixar assinatura estatística. O LSB sequencial clássico acende 3 de 20 segmentos no qui-quadrado: ele denuncia a presença da mensagem antes de qualquer tentativa de quebra. Na versão chaveada medimos 0, o mesmo resultado da imagem limpa.

Mas o qui-quadrado é um detector só, e não testamos todos. A portadora comporta 55.286 bytes, então isso não é canal para volume grande. Volume grande é o próximo problema, e ele aparece do lado dos dados.""",

    "antifraude": """O modelo aprendeu sem rótulos, e mesmo assim separa quase tudo: ROC AUC 0,9965 e um ganho de 126,2 vezes sobre o acaso.

O surto de eventos merece explicação. A revocação é de 4,3%, o pior número da tabela, mas o posto de risco conta outra história: o modelo o coloca no 1,69% mais arriscado de 43.985 janelas. Ele não passa despercebido, ele perde a disputa pelo orçamento de alertas para as anomalias que geram falha. É por isso que medimos as duas coisas. Detectar bem não prova que a cifra resiste, então fomos atacar a nossa.""",

    "ato2": """Não confiamos numa cifra só porque ela é nossa. Então atacamos a nossa. A versão enfraquecida é o nosso grupo de controle. Quando um ataque derruba a fraca e não a íntegra, a resistência é da cifra, não um defeito do teste. A força bruta é a exceção: não quebra nenhuma das duas, porque o tamanho da chave não depende das rodadas.

Esses ataques dizem se a cifra aguenta, não por que ela aguenta. Para isso medimos como um único bit de entrada se espalha pela saída.""",

    "avalanche": """O contraste é o ponto. Sem difusão, a cifra não melhora com mais rodadas: 14 rodadas dão 3,13%, e uma rodada só dá 3,09%. Repetir operação ruim não conserta nada. Quem espalha o bit é o MixColumns, e a difusão fecha na rodada 2; o resto é margem. Com difusão, medimos 50,11%, colado nos 50,01% do AES-256. O desvio padrão de 5,698 contra 5,657 mostra que a dispersão também bate, não só a média. Mas um bit bem espalhado não garante saída sem padrão. É isso que medimos agora.""",

    "padroes": """Nós colocamos a cifra contra o AES e contra o /dev/urandom do sistema. No modo CTR, a saída da FPC-128 passa nos mesmos testes que esse ruído, então não achamos atalho estatístico.

No modo ECB a história muda, e nós assumimos: 36,10% dos blocos se repetem com as mesmas 14 rodadas. O motivo é o modo, não a cifra: bloco igual na entrada vira bloco igual na saída, e rodada nenhuma conserta isso. Em CTR esse vazamento não aparece, e sobra tentar todas as chaves. Nós medimos o custo.""",

    "bruta": """Esse número astronômico prova menos do que parece. Ele mede o tamanho do espaço de chaves, não a qualidade do nosso desenho interno. Uma cifra fraca com a mesma chave daria a mesma conta, então não cantamos vitória aqui.

O resultado útil é o de baixo. Com 114,6 tentativas por segundo, banco123 caiu em 0,06 segundos. O atacante não vai lutar com a matemática, vai atrás do usuário. Falta então olhar a estrutura interna da cifra, e é isso que atacamos agora.""",

    "diferencial": """Esse ataque não tenta adivinhar a chave. Nós procuramos uma diferença de saída que se repita, porque repetição é estrutura vazando. Para mostrar que o método funciona, atacamos a nossa própria versão enfraquecida, de 1 rodada e sem difusão, e ela ficou distinguível. A versão íntegra não ficou.

O porquê está na tela: a uniformidade diferencial 4 limita cada rodada, e 14 rodadas empilham esse limite até não sobrar nada explorável. Isso não é prova de segurança: é um ataque conhecido que não passou.""",

    "estatistico": """Esse é o ataque que mais nos incomodou, porque não usamos chave nenhuma: só contamos bytes. Na variante sem difusão, como o registro bancário tem largura fixa, cada posição do bloco virou uma substituição simples. E com isso recuperamos 60,15% do texto e abrimos 38 de 80 posições.

Com difusão, cai para 4,29%, abaixo da linha de base de 31,26%. E olhem o texto recuperado: ele sai sujo. A frequência entrega o formato do registro, não a transação inteira. É com essa ressalva que fechamos o veredito.""",

    "ato3": """Até aqui nós mostramos medições. Agora vem a parte difícil: decidir o que elas provam. E tem um limite que precisamos assumir. A cifra é nossa, e os ataques que rodamos contra ela também. Ninguém de fora tentou quebrá-la ainda. Então ela resistiu ao que nós sabemos tentar, e isso não é o mesmo que ser segura. Agora vamos responder às perguntas do enunciado, cada uma com o número que sustenta a resposta, e depois mostrar onde esse veredito deixa de valer.""",

    "perguntas": """Respondemos as quatro com número, não com opinião. As duas primeiras são boas notícias: 50,11% de bits virados contra os 50% ideais, e uma entropia quase no teto.

A terceira é a que incomoda. O ataque mais eficaz não quebrou a chave: ele explorou a falta de difusão de uma variante e recuperou 60,15% do texto. Então o sim da última linha é condicional: 1,716 vezes 10 elevado a 58 anos protege a chave, não protege um projeto malfeito. É dessa diferença que tiramos as lições.""",

    "conclusao": """Nós entramos achando que segurança era número de rodadas. Os dados disseram outra coisa. Sem difusão, a frequência devolve 60,15% do texto, e rodada extra nenhuma conserta isso. Com a cifra intacta, o ECB preservou 36,10% dos blocos repetidos: bloco igual entra, bloco igual sai. Em ambos, o erro é de projeto, não de força.

Sobre a anomalia que escapou, nós não vamos maquiar: o orçamento de 1% foi escolha nossa, e ela custou essa detecção. Passar nos ataques que fizemos não é o mesmo que estar seguro.""",

    "limites": """Esse slide é o que mais nos custou escrever. Passar nos três ataques que nós mesmos montamos não prova que o FPC-128 é seguro: nós escolhemos os ataques, então testamos só o que imaginamos. Prova que o projeto está coerente. Quem valida uma cifra é a comunidade, ao longo de anos, tentando quebrar. Por isso o AES-256 fica na camada que protegeria dinheiro de verdade. As ressalvas são reais: em ECB a estrutura ainda vaza. Preferimos assumir isso a maquiar o resultado. Queremos ouvir vocês.""",

    "obrigado": """Fechamos onde começamos: o FinalPay foi construído para ser atacado pelo próprio grupo. O que levamos daqui não é a cifra, é o método. Medir, tentar quebrar, e dizer com clareza o que o resultado não prova.

O trabalho foi dividido entre os nomes que estão na tela, do cofre à detecção de anomalias, e cada um responde pela parte que fez. Estamos aqui para as perguntas, inclusive as que apontam o que ainda está fraco. São essas que fazem o projeto andar.""",
}
