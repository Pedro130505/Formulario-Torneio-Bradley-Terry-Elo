"""
Motor de Cálculo Matemático do Modelo Bradley-Terry / Elo e Algoritmo de Emparelhamento.
Suporta categorias independentes ('brinde' e 'palestra') com garantia de não repetição por usuário.
"""
import math
import random
from typing import Dict, Any, Optional, Tuple, List
from database import (
    get_all_items,
    get_item_by_id,
    get_user_voted_pairs,
    get_user_votes_count,
    record_match_vote,
    get_stats
)

# Configurações do Sistema Elo
DEFAULT_K_FACTOR = 32.0
BASE_ELO = 1000.0


def calculate_expected_score(rating_a: float, rating_b: float) -> Tuple[float, float]:
    """
    Calcula a probabilidade teórica de vitória (score esperado) usando a curva logística de Bradley-Terry/Elo.
    E_A = 1 / (1 + 10^((R_B - R_A) / 400))
    E_B = 1 - E_A
    """
    qa = 10.0 ** (rating_a / 400.0)
    qb = 10.0 ** (rating_b / 400.0)
    expected_a = qa / (qa + qb)
    expected_b = qb / (qa + qb)
    return expected_a, expected_b


def calculate_bradley_terry_metrics(rating_elo: float, jogos: int = 0, vitorias: int = 0) -> Dict[str, Any]:
    """
    Calcula métricas analíticas e Bradley-Terry para exibição em relatórios e interfaces.
    """
    # Força relativa latente (pi) centrada em 1.0 para Elo 1000
    forca_bt = round(10.0 ** ((rating_elo - BASE_ELO) / 400.0), 3)
    
    # Probabilidade de vitória contra um item médio da amostra (Elo 1000)
    prob_media = round((1.0 / (1.0 + 10.0 ** ((BASE_ELO - rating_elo) / 400.0))) * 100.0, 1)

    # Taxa de vitórias real nos duelos
    taxa_vitoria = round((vitorias / jogos * 100.0), 1) if jogos > 0 else 0.0

    # Classificação em Tiers de Desempenho
    if rating_elo >= 1080.0:
        tier = "Elite (S)"
        tier_class = "tier-s"
    elif rating_elo >= 1030.0:
        tier = "Favorito (A)"
        tier_class = "tier-a"
    elif rating_elo >= 970.0:
        tier = "Competitivo (B)"
        tier_class = "tier-b"
    elif rating_elo >= 920.0:
        tier = "Desafiante (C)"
        tier_class = "tier-c"
    else:
        tier = "Baixa Aderência (D)"
        tier_class = "tier-d"

    return {
        "forca_bt": forca_bt,
        "prob_vitoria_media": prob_media,
        "taxa_vitoria": taxa_vitoria,
        "tier": tier,
        "tier_class": tier_class
    }


def update_ratings(
    rating_a: float,
    rating_b: float,
    winner_id: str,
    id_a: str,
    id_b: str,
    k_factor: float = DEFAULT_K_FACTOR
) -> Tuple[float, float, float]:
    """
    Atualiza as pontuações Elo com base no resultado do duelo.
    Retorna (novo_elo_a, novo_elo_b, delta_elo)
    """
    exp_a, exp_b = calculate_expected_score(rating_a, rating_b)

    score_a = 1.0 if winner_id == id_a else 0.0
    score_b = 1.0 if winner_id == id_b else 0.0

    delta_a = k_factor * (score_a - exp_a)
    delta_b = k_factor * (score_b - exp_b)

    novo_elo_a = round(rating_a + delta_a, 1)
    novo_elo_b = round(rating_b + delta_b, 1)

    delta_magnitude = round(abs(delta_a), 1)
    return novo_elo_a, novo_elo_b, delta_magnitude


def get_next_matchup(
    uid: str,
    canal: str = "geral",
    categoria: str = "brinde",
    curso: Optional[str] = None
) -> Dict[str, Any]:
    """
    Algoritmo Inteligente de Emparelhamento (Active Learning):
    1. Filtra itens ativos da categoria selecionada ('brinde' ou 'palestra').
    2. Se for palestra, filtra os tópicos de acordo com o curso do aluno.
    3. Garante que NÃO repete combinações já votadas por este usuário (UID).
    4. Prioriza itens com menor número de duelos para cobertura balanceada.
    5. Busca oponentes de Elo próximo para maximizar o ganho de informação.
    6. Alterna a posição visual (esquerda/direita) para anular viés de tela.
    """
    itens = get_all_items(active_only=True, categoria=categoria, curso=curso)
    if len(itens) < 2:
        return {
            "status": "erro",
            "mensagem": f"É necessário ter pelo menos 2 opções ativas para duelos na categoria '{categoria}'."
        }

    # Conjunto de pares já respondidos por este UID nesta categoria
    pares_votados = get_user_voted_pairs(uid, categoria=categoria)
    total_usuario = get_user_votes_count(uid, categoria=categoria)

    # Identifica todos os pares possíveis ainda não votados por este usuário
    todos_itens_ids = [i["id"] for i in itens]
    itens_map = {i["id"]: i for i in itens}

    pares_disponiveis = []
    for i in range(len(todos_itens_ids)):
        for j in range(i + 1, len(todos_itens_ids)):
            p = frozenset([todos_itens_ids[i], todos_itens_ids[j]])
            if p not in pares_votados:
                pares_disponiveis.append((todos_itens_ids[i], todos_itens_ids[j]))

    # Se já votou em todos os pares possíveis
    if not pares_disponiveis:
        return {
            "status": "concluido",
            "mensagem": "Você já avaliou todas as opções disponíveis nesta categoria! Excelente participação!",
            "totalRespondidosUsuario": total_usuario,
            "totalItensAtivos": len(itens)
        }

    # Algoritmo de seleção: Priorizar itens com menos jogos e menor distância de Elo
    # Atribui uma pontuação de prioridade para cada par disponível
    melhor_par = None
    menor_score = float("inf")

    # Amostra até 40 pares para cálculo rápido e balanceado
    amostra_pares = random.sample(pares_disponiveis, min(40, len(pares_disponiveis)))

    for id_a, id_b in amostra_pares:
        item_a = itens_map[id_a]
        item_b = itens_map[id_b]

        soma_jogos = item_a["jogos"] + item_b["jogos"]
        dif_elo = abs(item_a["rating_elo"] - item_b["rating_elo"])
        ruido = random.uniform(0, 15)

        # Queremos minimizar jogos totais e diferença de Elo
        score = (soma_jogos * 10.0) + dif_elo + ruido
        if score < menor_score:
            menor_score = score
            melhor_par = (item_a, item_b)

    item1, item2 = melhor_par

    # Alterna aleatoriamente ordem visual para eliminar viés de lado (Left-side bias)
    if random.choice([True, False]):
        item_esq, item_dir = item1, item2
    else:
        item_esq, item_dir = item2, item1

    # Sanitização: Retorna apenas dados necessários para visualização limpa
    def sanitize(item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": item["id"],
            "nome": item["nome"],
            "categoria": item.get("categoria", "brinde"),
            "imagem_url": item.get("imagem_url") or "https://images.unsplash.com/photo-1549465220-1a8b9238cd48?w=800&auto=format&fit=crop&q=80"
        }

    return {
        "status": "ok",
        "categoria": categoria,
        "itemA": sanitize(item_esq),
        "itemB": sanitize(item_dir),
        "totalRespondidosUsuario": total_usuario,
        "totalItensAtivos": len(itens)
    }


def process_vote(
    uid: str,
    item_a_id: str,
    item_b_id: str,
    vencedor_id: str,
    canal: str = "geral",
    categoria: str = "brinde"
) -> Dict[str, Any]:
    """
    Processa a escolha do usuário, atualiza a pontuação Elo de ambos os itens e registra na auditoria.
    """
    item_a = get_item_by_id(item_a_id)
    item_b = get_item_by_id(item_b_id)

    if not item_a or not item_b:
        raise ValueError("Um ou ambos os itens do duelo não foram encontrados.")

    if vencedor_id not in (item_a_id, item_b_id):
        raise ValueError("O ID do vencedor deve ser correspondente ao item A ou item B.")

    perdedor_id = item_b_id if vencedor_id == item_a_id else item_a_id

    elo_a_antes = item_a["rating_elo"]
    elo_b_antes = item_b["rating_elo"]

    novo_elo_a, novo_elo_b, delta = update_ratings(
        rating_a=elo_a_antes,
        rating_b=elo_b_antes,
        winner_id=vencedor_id,
        id_a=item_a_id,
        id_b=item_b_id,
        k_factor=DEFAULT_K_FACTOR
    )

    # Determina categoria a partir do item A
    cat_final = item_a.get("categoria") or categoria

    record_match_vote(
        uid=uid,
        canal=canal,
        item_a_id=item_a_id,
        item_b_id=item_b_id,
        vencedor_id=vencedor_id,
        perdedor_id=perdedor_id,
        elo_a_antes=elo_a_antes,
        elo_b_antes=elo_b_antes,
        elo_a_depois=novo_elo_a,
        elo_b_depois=novo_elo_b,
        delta_elo=delta,
        categoria=cat_final
    )

    novo_elo_venc = novo_elo_a if vencedor_id == item_a_id else novo_elo_b
    novo_elo_perd = novo_elo_b if vencedor_id == item_a_id else novo_elo_a
    total_usuario = get_user_votes_count(uid, categoria=cat_final)

    return {
        "status": "ok",
        "mensagem": "Voto registrado com sucesso!",
        "delta_elo": delta,
        "novo_elo_vencedor": novo_elo_venc,
        "novo_elo_perdedor": novo_elo_perd,
        "total_usuario": total_usuario
    }


def get_enriched_leaderboard(
    categoria: Optional[str] = None,
    curso: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retorna o leaderboard com enriquecimento de métricas estatísticas e Bradley-Terry para o painel Admin.
    """
    itens = get_all_items(active_only=False, order_by="rating_elo DESC", categoria=categoria, curso=curso)
    resultado = []

    for idx, item in enumerate(itens, start=1):
        metrics = calculate_bradley_terry_metrics(
            rating_elo=item["rating_elo"],
            jogos=item["jogos"],
            vitorias=item["vitorias"]
        )

        item_enriquecido = dict(item)
        item_enriquecido.update(metrics)
        item_enriquecido["posicao"] = idx
        resultado.append(item_enriquecido)

    return resultado
