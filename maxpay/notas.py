"""Notas do apresentador, uma por tela do deck.

Texto para ser LIDO EM VOZ ALTA durante a defesa. A tecla `N` mostra e esconde
o painel na apresentacao; ele tambem sai na impressao quando esta visivel.

Registro seco e curto de proposito: a nota comeca pelo fato e nao comenta a
propria apresentacao.

Todo numero sai de `results/experimentos.json`, o mesmo arquivo que alimenta o
deck e o relatorio. Isso nao e zelo decorativo: na primeira versao os numeros
estavam digitados a mao, e quando a bateria rodou de novo a fala passou a
contradizer o slide projetado atras de quem estava falando.

Chave = id da tela em `slides.py`.
"""

from __future__ import annotations

from maxpay.experiments import carregar
from maxpay.report import i, n


def construir(res: dict) -> dict[str, str]:
    """Monta as 19 notas a partir de uma bateria ja executada."""
    c = res["cifra"]
    pj = c["projeto"]
    dif = res["diferencial"]
    integro, aes = dif["mpc_integro"], dif["aes256"]
    sem_dif, fraco = dif["mpc_sem_difusao_14_rodadas"], dif["mpc_fraco"]
    chave_av = dif["avalanche_chave"]
    dist_integro, dist_fraco = dif["distinguidor_integro"], dif["distinguidor_fraco"]
    freq_f, freq_c = res["frequencia"]["sem_difusao"], res["frequencia"]["com_difusao"]
    seg = res["estego"]["esteganalise"]["segmentos_suspeitos"]
    ia = res["bigdata"]["ia"]["metricas"]
    surto = next(t for t in ia["por_tipo"] if t["tipo"] == "surto_de_eventos")
    dic = res["dicionario"]
    # Ha duas linhas com bits=256, uma por cenario. A fala cita a de GPU, que e
    # a que o slide mostra; pegar a primeira traria a de 1 nucleo, 10^6 maior.
    gpu256 = next(
        p for p in res["forca_bruta"]["projecao"]
        if p["bits"] == 256 and "GPU" in p["cenario"]
    )
    perfis = {p["rotulo"]: p for p in res["estatistico"]["perfis"]}
    ctr, ecb = perfis["mpc_ctr_14_rodadas"], perfis["mpc_ecb_14_rodadas"]

    def pct(x: float) -> str:
        return f"{n(x)}%"

    return {
        "capa": (
            "O MaxPay é o cofre de transações de um banco digital fictício. A cifra é nossa, "
            "escrita do zero. Os ataques contra ela também são nossos, e é o resultado desses "
            "ataques que a gente vem mostrar."
        ),
        "ato1": (
            "Uma transação entra pelo formulário, é cifrada, pode ser escondida dentro de uma "
            "imagem, vira evento no lago de dados e aparece no painel de quem vigia. São seis "
            "camadas, nessa ordem."
        ),
        "construido": (
            "Cada camada tem uma aba onde dá para ver funcionando: Cofre, Ocultar, Antifraude e "
            "Resistência. Nenhuma tela é maquete. Tudo roda na hora, com os dados e os parâmetros "
            "que a senhora escolher."
        ),
        "algoritmo": (
            f"Cada rodada faz quatro coisas: a subchave entra por XOR, a S-box troca byte por "
            f"byte, o ShiftRows muda as posições e o MixColumns mistura as colunas. São "
            f"{c['rodadas']} rodadas, bloco de {c['bloco_bits']} bits e chave de "
            f"{c['chave_bits']}."
        ),
        "projeto": (
            f"A estrutura é da mesma família do AES, e isso é escolha nossa. Nossos também são "
            f"três componentes: a constante {pj['sbox_constante']} da S-box, a permutação "
            f"{tuple(pj['deslocamentos'])} e a matriz de difusão {tuple(pj['matriz_difusao'])}. "
            f"Cada um passou por verificação matemática."
        ),
        "chave": (
            f"A senha vira chave no PBKDF2, com {i(dic['iteracoes_pbkdf2'])} iterações, só para "
            f"encarecer o chute de quem tentar adivinhar. Nada fica guardado em disco. Trocar um "
            f"bit da chave muda {pct(chave_av['media_pct'])} dos bits de saída."
        ),
        "estego": (
            f"Os bits da mensagem vão para posições que só a chave sabe. No teste de Westfeld, o "
            f"LSB sequencial acende {seg['lsb_sequencial_sem_chave']} de 20 segmentos e o nosso "
            f"acende {seg['lsb_chaveado_maxpay']}, igual à imagem limpa. Foi o único detector que "
            f"rodamos."
        ),
        "antifraude": (
            f"O modelo treinou sem rótulo nenhum e mesmo assim separa quase tudo: ROC AUC "
            f"{n(ia['roc_auc'], 4)}. O surto de eventos é a exceção, com "
            f"{n(surto['revocacao_pct'], 1)}% de revocação. Ele não passa batido, fica no "
            f"{pct(surto['percentil_mediano'])} mais arriscado, mas não cabe no orçamento de "
            f"alertas."
        ),
        "ato2": (
            "Atacamos a cifra em duas versões: a íntegra e uma com a difusão desligada. A fraca é "
            "o grupo de controle. Quando o ataque derruba só ela, a diferença está no desenho e "
            "não no teste."
        ),
        "avalanche": (
            f"Um bit na entrada muda {pct(integro['media_pct'])} da saída, o mesmo que o AES-256 "
            f"deu aqui, {pct(aes['media_pct'])}. Sem o MixColumns cai para "
            f"{pct(sem_dif['media_pct'])}, e com uma rodada só dá {pct(fraco['media_pct'])}. "
            f"Rodada a mais não substitui difusão."
        ),
        "padroes": (
            f"Em CTR a saída não tem bloco repetido e a entropia chega a "
            f"{n(ctr['entropia_bits_por_byte'], 4)} de 8. Em ECB, bloco igual na entrada sai "
            f"igual: {pct(ecb['repeticao_blocos']['pct_repetidos'])} repetidos, mesmo com "
            f"{c['rodadas']} rodadas. O modo pesa mais que as rodadas."
        ),
        "bruta": (
            f"{gpu256['anos_fmt']} com um milhão de GPUs. Mas esse número vale para qualquer "
            f"cifra de {c['chave_bits']} bits. O resultado útil é o de baixo: o PBKDF2 limita o "
            f"atacante a {n(dic['tentativas_por_segundo'], 1)} tentativas por segundo, e a senha "
            f"{dic['senha_quebrada']} caiu em {n(dic['segundos'])} s."
        ),
        "diferencial": (
            f"Na cifra íntegra nenhuma diferença de saída repetiu: "
            f"{pct(dist_integro['pct_saidas_distintas'])} distintas. Na versão sem difusão, a mais "
            f"frequente apareceu {i(dist_fraco['ocorrencias'])} vezes. Esse viés é exatamente o "
            f"que um ataque diferencial procura."
        ),
        "estatistico": (
            f"Esse ataque não usa chave, só conta bytes. Sem difusão ele devolve "
            f"{pct(freq_f['acuracia_pct'])} do texto e abre {freq_f['posicoes_expostas']} das "
            f"{freq_f['posicoes_registro']} posições do registro. Com difusão cai para "
            f"{pct(freq_c['acuracia_pct'])}, abaixo da linha de base de "
            f"{pct(freq_c['linha_base_unigrama_pct'])}."
        ),
        "ato3": (
            "Agora as quatro perguntas do enunciado, cada uma com o número que sustenta a "
            "resposta. Depois vem o que esses números não autorizam a gente a afirmar, porque "
            "quem atacou a cifra fomos nós mesmos."
        ),
        "perguntas": (
            f"Avalanche sim, {pct(integro['media_pct'])} dos bits. Padrões não, entropia "
            f"{n(ctr['entropia_bits_por_byte'], 4)} de 8. O ataque mais eficaz foi o estatístico, "
            f"que recuperou {pct(freq_f['acuracia_pct'])} do texto da variante fraca. Seguro sim, "
            f"com ressalvas."
        ),
        "conclusao": (
            f"Difusão é o que sustenta tudo: sem ela a frequência devolve "
            f"{pct(freq_f['acuracia_pct'])} do texto. O modo de operação pesa mais que o número de "
            f"rodadas. Força bruta é o ataque errado, porque a superfície real é a senha. E a "
            f"anomalia mais difícil é a que não quebra nada."
        ),
        "limites": (
            "A S-box, a matriz de difusão e a permutação são escolhas nossas e nunca passaram por "
            "criptanálise de gente de fora. A implementação também não é de tempo constante. Em "
            "produção, quem protege o dinheiro é o AES-256."
        ),
        "obrigado": (
            "O trabalho foi dividido entre os nomes da tela, e cada um responde pela parte que "
            "fez. As perguntas que mais ajudam a gente são as que apontam o que ficou fraco, "
            "então pode vir."
        ),
    }


_res = carregar()
NOTAS: dict[str, str] = construir(_res) if _res else {}
