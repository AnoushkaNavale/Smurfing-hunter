"""
Main execution script for Smurfing-hunter
"""

import os
import sys

import pandas as pd
sys.path.append('src')

from data_loader import load_transactions
from graph_builder import build_transaction_graph
from pattern_detectors import (
    detect_fan_out,
    detect_fan_in,
    detect_peeling_chains,
    calculate_proximity_score,
)
from scoring_engine import compute_wallet_scores
from subgraph_extractor import extract_suspicious_subgraph
from visualization import visualize_laundering_graph
from report_generator import generate_report


DEFAULT_ILLICIT_SEEDS = ["0xABC", "0xDEF"]


def load_illicit_seeds(csv_path, fallback):
    if not os.path.exists(csv_path):
        print(f"⚠️  Illicit seed file not found at {csv_path}. Using defaults.")
        return fallback

    try:
        df = pd.read_csv(csv_path)
    except Exception as exc:
        print(f"⚠️  Failed to read {csv_path} ({exc}). Using defaults.")
        return fallback

    for column in ("Wallet_ID", "wallet_id", "wallet", "address"):
        if column in df.columns:
            seeds = df[column].dropna().astype(str).unique().tolist()
            if seeds:
                print(f"✅ Loaded {len(seeds)} illicit seeds from {csv_path}")
                return seeds

    print(f"⚠️  No wallet column found in {csv_path}. Using defaults.")
    return fallback


def main():
    """
    Main execution pipeline
    """
    print("🚀 Starting Smurfing-hunter Detection System")
    print("=" * 60)
    
    csv_path = 'data/transactions.csv'
    illicit_file = 'data/illicit_wallets.csv'
    illicit_seeds = load_illicit_seeds(illicit_file, DEFAULT_ILLICIT_SEEDS)
    
    print(f"📂 Loading transactions from {csv_path}...")
    df = load_transactions(csv_path)
    print(f"✅ Loaded {len(df)} transactions")
    
    print("\n🔗 Building transaction graph...")
    G = build_transaction_graph(df)
    print(f"✅ Graph built: {G.number_of_nodes()} wallets, {G.number_of_edges()} connections")

    if illicit_seeds and all(seed not in G for seed in illicit_seeds):
        print("⚠️  None of the illicit seeds are present in the graph.")
        print("   The laundering graph may be empty or minimal.")
    
    print("\n🔍 Computing wallet suspicion scores...")
    wallet_scores = compute_wallet_scores(G, illicit_seeds)
    print(f"✅ Analyzed {len(wallet_scores)} wallets")
    
    print("\n📊 Extracting suspicious subgraph...")
    subgraph = extract_suspicious_subgraph(G, illicit_seeds, wallet_scores)
    print(f"✅ Subgraph extracted: {subgraph.number_of_nodes()} nodes, {subgraph.number_of_edges()} edges")
    
    print("\n🎨 Creating visualization...")
    visualize_laundering_graph(subgraph, wallet_scores, illicit_seeds, 'output/laundering_graph.html')
    
    print("\n📋 Generating suspicion report...")
    report = generate_report(wallet_scores, illicit_seeds)
    
    print("\n" + "=" * 60)
    print("TOP SUSPICIOUS WALLETS")
    print("=" * 60)
    print(report.to_string(index=False))
    
    output_csv = 'output/suspicion_report.csv'
    report.to_csv(output_csv, index=False)
    print(f"\n✅ Report saved to {output_csv}")
    
    print("\n" + "=" * 60)
    print("🎯 DETECTION COMPLETE")
    print("=" * 60)
    print(f"📁 Files generated:")
    print(f"  - output/laundering_graph.html (interactive visualization)")
    print(f"  - output/suspicion_report.csv (detailed scores)")


if __name__ == "__main__":
    main()