"""
Report Generator Module
Generates human-readable GNN suspicion reports.
"""

import pandas as pd


def create_explanation(wallet, scores):
    """
    Generate a human-readable explanation for the learned GNN score.
    """
    probability = scores.get("gnn_probability", 0)

    if scores.get("is_seed"):
        return "Known illicit seed wallet used as a positive GNN training label"

    if probability >= 0.75:
        return "High GNN risk probability based on learned neighborhood and transaction features"
    if probability >= 0.5:
        return "Elevated GNN risk probability based on graph message passing"
    if probability >= 0.25:
        return "Moderate GNN risk probability; review if connected to high-risk clusters"

    return "Low GNN risk probability"


def generate_report(wallet_scores, illicit_seeds, top_n=None):
    """
    Generate sorted suspicion report DataFrame.

    Args:
        wallet_scores: Dictionary of wallet suspicion scores
        illicit_seeds: List of known illicit wallet addresses
        top_n: Number of top suspicious wallets to include. Use None for all wallets.

    Returns:
        pandas DataFrame with sorted suspicion report
    """
    report_data = []

    for wallet, scores in wallet_scores.items():
        report_data.append(
            {
                "Wallet": wallet,
                "Score": round(scores["total"], 2),
                "GNN_Probability": round(scores.get("gnn_probability", 0), 4),
                "GNN_Epochs": scores.get("gnn_epochs", 0),
                "GNN_Loss": scores.get("gnn_loss", 0),
                "Explanation": create_explanation(wallet, scores),
                "Is_Seed": "ILLICIT" if wallet in illicit_seeds else "",
            }
        )

    df_report = pd.DataFrame(report_data)
    df_report = df_report.sort_values("Score", ascending=False).reset_index(drop=True)

    if top_n is not None:
        return df_report.head(top_n)

    return df_report
