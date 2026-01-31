"""
Report Generator Module
Generates human-readable suspicion reports
"""

import pandas as pd


def create_explanation(wallet, scores):
    """
    Generate human-readable explanation for suspicion score
    
    Args:
        wallet: Wallet address
        scores: Dictionary of score components
        
    Returns:
        Human-readable explanation string
    """
    parts = []
    
    if scores['fan_out'] > 0:
        parts.append(f"Fan-out to multiple wallets detected (score: {scores['fan_out']})")
    
    if scores['fan_in'] > 0:
        parts.append(f"Fan-in aggregation pattern (score: {scores['fan_in']})")
    
    if scores['peeling'] > 0:
        parts.append(f"Peeling chain detected (score: {scores['peeling']})")
    
    if scores['proximity'] > 7:
        parts.append("Direct connection to illicit wallet")
    elif scores['proximity'] > 3:
        parts.append(f"Close proximity to illicit wallets (score: {scores['proximity']})")
    
    if not parts:
        return "No suspicious patterns detected"
    
    return " | ".join(parts)


def generate_report(wallet_scores, illicit_seeds, top_n=20):
    """
    Generate sorted suspicion report DataFrame
    
    Args:
        wallet_scores: Dictionary of wallet suspicion scores
        illicit_seeds: List of known illicit wallet addresses
        top_n: Number of top suspicious wallets to include
        
    Returns:
        pandas DataFrame with sorted suspicion report
    """
    report_data = []
    
    for wallet, scores in wallet_scores.items():
        report_data.append({
            'Wallet': wallet,
            'Score': round(scores['total'], 2),
            'Explanation': create_explanation(wallet, scores),
            'Is_Seed': '🔴 ILLICIT' if wallet in illicit_seeds else ''
        })
    
    df_report = pd.DataFrame(report_data)
    df_report = df_report.sort_values('Score', ascending=False).reset_index(drop=True)
    
    return df_report.head(top_n)