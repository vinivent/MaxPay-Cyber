"""Notas do apresentador, uma por tela do deck.

Texto para ser LIDO EM VOZ ALTA durante a defesa. A tecla `N` mostra e esconde
o painel na apresentacao; ele tambem sai na impressao quando esta visivel.

Registro deliberadamente seco: a nota comeca pelo fato, nao por comentario
sobre a propria apresentacao. Todo numero citado existe no texto da tela.

Chave = id da tela em `slides.py`.
"""

NOTAS: dict[str, str] = {
    "capa": """O FinalPay é o cofre de transações de um banco digital fictício. A cifra é nossa, escrita do zero. O resultado fica escondido dentro de uma imagem, e o evento vai para um lago de dados vigiado por um modelo. Os ataques rodam contra a cifra íntegra e contra uma variante enfraquecida de propósito.""",

    "ato1": """As seis camadas estão na ordem em que uma transação as percorre: alguém digita e o dado é cifrado. Depois pode ser escondido numa imagem, é guardado e lido em massa, é analisado em busca de fraude e aparece no painel. Um ataque em cada ponto só alcança o que a camada anterior entregou.""",

    "construido": """A versão enfraquecida é a mesma cifra, com a difusão desligada e as rodadas reduzidas. Ela serve de grupo de controle. Se um ataque derruba a fraca e a íntegra aguenta, a resistência vem do desenho, não de um teste mal feito. Os três ataques cifram ali mesmo, com chave sorteada na hora.""",

    "algoritmo": """O XOR mistura a subchave, a S-box quebra a linearidade, ShiftRows e MixColumns espalham a diferença. Uniformidade diferencial 4 limita cada byte ativo a 2 elevado a menos 6. A difusão obriga vários bytes ativos por rodada, e 14 rodadas deixam margem contra ataque diferencial. Pontos fixos 0: nenhum byte sai igual da S-box.""",

    "projeto": """A afim com 0x0D, a permutação, a difusão e o escalonamento HKDF/HMAC-SHA256 diferem do AES, e a S-box muda nas 256 posições. Cada escolha passou por verificação: a S-box é bijetiva, com zero ponto fixo e uniformidade 4, e a difusão é MDS por todos os menores.""",

    "chave": """As 120.000 iterações do PBKDF2 encarecem o chute de senha, caso alguém leve os envelopes guardados. Em troca, senha perdida é cofre perdido: não existe cópia da chave em disco. Os 50,06% saíram do nosso teste de espalhamento, e metade é o alvo: passar disso não seria melhor.""",

    "estego": """O qui-quadrado de Westfeld procura o padrão regular que o LSB sequencial deixa na imagem. Com as posições derivadas da chave, esse padrão não aparece, e o teste não acusa nada. Foi o único detector que rodamos. Contra outros ataques, não temos medida.""",

    "antifraude": """ROC AUC 0,9965 significa que uma janela de ataque quase sempre aparece acima de uma janela normal no ranking. Surto de eventos tem revocação 4,3% com posto de risco 1,69%: metade dessas 23 janelas está ainda mais perto do topo das 43.985, e mesmo assim fora do orçamento de alertas.""",

    "ato2": """A versão enfraquecida é o grupo de controle. Se um ataque derruba a fraca e não a íntegra, a resistência vem do desenho da cifra, e não de um defeito do teste. A força bruta contra a chave é exceção: não quebra nenhuma das duas, porque o tamanho da chave não depende das rodadas.""",

    "avalanche": """A FPC-128 íntegra vira 50,11% dos bits, contra 50,01% do AES-256. O MixColumns é quem espalha o bit: sem ele, 14 rodadas param em 3,13% e uma rodada dá 3,09%. A difusão fecha na rodada 2, e o resto das 14 é margem. O desvio medido, 5,698, casa com o 5,657 esperado.""",

    "padroes": """Em CTR o p do qui-quadrado é 0,6823. O AES-256-GCM deu 0,4132 e o /dev/urandom de controle deu 0,3133; nenhum dos três rejeita uniformidade. O teste mede distribuição, não resistência a ataque. Em ECB bloco igual na entrada vira bloco igual na saída, e 14 rodadas ainda deixam 36,10% de blocos repetidos.""",

    "bruta": """Um espaço de 2 elevado a 256 é igual em qualquer cifra de 256 bits, então esse número não avalia o nosso desenho. O PBKDF2 limita o atacante a 114,6 tentativas por segundo. Com isso a defesa real é a senha: banco123 cai em 0,06 s, uma de 12 caracteres resiste.""",

    "diferencial": """Repetição máxima 1 significa que nenhuma diferença de saída apareceu duas vezes. Sem difusão, a diferença mais frequente aparece 1.536 vezes, e esse viés já separa a cifra de uma função aleatória. Com uniformidade diferencial 4, as 14 rodadas levam a probabilidade para fora do alcance prático. Isso cobre apenas o ataque diferencial.""",

    "estatistico": """A contagem de bytes dispensa chave: trabalha só sobre o texto cifrado. Sem difusão, cada posição do bloco guarda um alfabeto próprio, e caem 38 das 80 posições, 60,15% do texto. Com difusão a recuperação desce para 4,29%, abaixo da linha de base de 31,26%. Sobra o formato, não o valor nem a conta.""",

    "ato3": """Quem atacou a cifra foi a nossa própria equipe. Ninguém de fora tentou quebrá-la. Ela resistiu aos ataques que nós conseguimos imaginar, e isso não é o mesmo que resistir aos ataques que existem. Fora dessa lista, não temos resultado nenhum para mostrar.""",

    "perguntas": """A análise de frequência devolveu 60,15% do texto claro sem precisar de chave nenhuma, e só contra a variante sem difusão. Na cifra íntegra, nenhum ataque teve vantagem. Os 1,716 vezes 10 elevado a 58 anos de força bruta protegem a chave, não as escolhas de projeto.""",

    "conclusao": """Sem MixColumns, nenhuma rodada extra devolve a difusão que falta. No ECB a cifra estava íntegra, e o que faltou foi o modo de operação. O limite de 1% de alertas foi nossa escolha; com ele, o surto fica no 1,69% mais arriscado e passa sem alerta.""",

    "limites": """A S-box, a matriz de difusão e a permutação nunca foram avaliadas por gente de fora. Os três ataques foram os nossos, e teste de quem projeta não vale como criptanálise. O tempo de execução varia, o que entrega informação sobre a chave. No produto, quem protege o dado é o AES-256.""",

    "obrigado": """O FinalPay cifra a transação, esconde o envelope numa imagem e detecta anomalias. Depois o próprio grupo o atacou. Nós escolhemos esses ataques, então eles não medem o que um atacante de fora tentaria. Cada integrante responde pela parte que fez, e preferimos as perguntas que apontam o que ficou fraco.""",
}
