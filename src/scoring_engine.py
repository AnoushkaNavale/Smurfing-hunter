"""
Scoring Engine Module
Computes comprehensive suspicion scores for all wallets
"""

from patterndetectors import detect_fan_out, detect_fan_in, detect_peeling_chains, calculate_proximity_score


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
                'total': float
            }
        }
    """
    wallet_scores = {}
    
    all_wallets = set(G.nodes())
    
    for wallet in all_wallets:
        fan_out = detect_fan_out(G, wallet)
        fan_in = detect_fan_in(G, wallet)
        peeling = detect_peeling_chains(G, wallet)
        proximity = calculate_proximity_score(G, wallet, illicit_seeds)
        
        wallet_scores[wallet] = {
            'fan_out': fan_out,
            'fan_in': fan_in,
            'peeling': peeling,
            'proximity': proximity,
            'total': fan_out * 2 + fan_in * 2 + peeling * 1.5 + proximity * 3
        }
    
    return wallet_scores