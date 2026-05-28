"""
Scoring Engine Module
Computes wallet suspicion scores with a lightweight Graph Neural Network.
"""

from gnn_model import train_gnn_wallet_scorer


def compute_wallet_scores(G, illicit_seeds):
    """
    Compute learned GNN suspicion scores for all wallets.

    Returns:
        Dictionary mapping wallet addresses to score components.
    """
    gnn_probabilities, metadata = train_gnn_wallet_scorer(G, illicit_seeds)
    wallet_scores = {}

    for wallet in G.nodes():
        probability = gnn_probabilities.get(wallet, 0.0)
        score = probability * 100
        wallet_scores[wallet] = {
            "gnn_probability": probability,
            "gnn_score": score,
            "gnn_loss": metadata.get("loss", 0.0),
            "gnn_epochs": metadata.get("epochs", 0),
            "is_seed": wallet in illicit_seeds,
            "total": score,
        }

    return wallet_scores
