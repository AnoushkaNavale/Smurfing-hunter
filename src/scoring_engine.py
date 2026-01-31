"""
Scoring Engine Module
Computes comprehensive suspicion scores for all wallets
"""

import networkx as nx

from patterndetectors import (
    calculate_proximity_score,
    detect_fan_in,
    detect_fan_out,
    detect_peeling_chains,
)


def _normalize_scores(values, scale_max=10):
    if not values:
        return {}
    min_value = min(values.values())
    max_value = max(values.values())
    if max_value == min_value:
        return {key: 0 for key in values}
    return {
        key: ((value - min_value) / (max_value - min_value)) * scale_max
        for key, value in values.items()
    }


def _compute_weighted_degree_scores(G):
    values = {}
    for node in G.nodes():
        total = 0.0
        for _, _, data in G.in_edges(node, data=True):
            total += data.get("total_amount", 0)
        for _, _, data in G.out_edges(node, data=True):
            total += data.get("total_amount", 0)
        values[node] = total
    return _normalize_scores(values, scale_max=10)


def _compute_centrality_scores(G):
    try:
        import scipy  # noqa: F401
    except Exception:
        return _compute_weighted_degree_scores(G)

    try:
        centrality = nx.pagerank(G, weight="total_amount")
    except Exception:
        try:
            centrality = nx.pagerank(G)
        except Exception:
            return _compute_weighted_degree_scores(G)
    return _normalize_scores(centrality, scale_max=10)


def compute_wallet_scores(G, illicit_seeds):
    """
    Compute comprehensive suspicion scores for all wallets
    
    Args:
        G: NetworkX DiGraph
        illicit_seeds: List of known illicit wallet addresses
        
    Returns:
        Dictionary mapping wallet addresses to score components
        {
            wallet: {
                'fan_out': int,
                'fan_in': int,
                'peeling': int,
                'proximity': int,
                'centrality': float,
                'total': float
            }
        }
    """
    wallet_scores = {}

    all_wallets = set(G.nodes())
    centrality_scores = _compute_centrality_scores(G)

    for wallet in all_wallets:
        fan_out = detect_fan_out(G, wallet)
        fan_in = detect_fan_in(G, wallet)
        peeling = detect_peeling_chains(G, wallet)
        proximity = calculate_proximity_score(G, wallet, illicit_seeds)
        centrality = centrality_scores.get(wallet, 0)

        total_score = (
            fan_out * 2
            + fan_in * 2
            + peeling * 1.5
            + proximity * 3
            + centrality * 2
        )

        wallet_scores[wallet] = {
            'fan_out': fan_out,
            'fan_in': fan_in,
            'peeling': peeling,
            'proximity': proximity,
            'centrality': centrality,
            'total': total_score
        }
    
    return wallet_scores