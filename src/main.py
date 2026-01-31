"""
Main execution script for Smurfing & Layering Detection System
"""

from data_loader import load_transactions
from graph_builder import build_transaction_graph
from pattern_detectors import detect_fan_out, detect_fan_in, detect_peeling_chains, calculate_proximity_score
from scoring_engine import compute_wallet_scores
from subgraph_extractor import extract_suspicious_subgraph
from visualization import visualize_laundering_graph
from report_generator import generate_report


def main():
    """
    Main execution pipeline
    """
    print("🚀 Starting Smurfing & Layering Detection System")
    print("=" * 60)
    
    csv_path = 'transactions.csv'
    illicit_seeds = ["0xABC", "0xDEF"]
    
    print(f"📂 Loading transactions from {csv_path}...")
    df = load_transactions(csv_path)
    print(f"✅ Loaded {len(df)} transactions")
    
    print("\n🔗 Building transaction graph...")
    G = build_transaction_graph(df)
    print(f"✅ Graph built: {G.number_of_nodes()} wallets, {G.number_of_edges()} connections")
    
    print("\n🔍 Computing wallet suspicion scores...")
    wallet_scores = compute_wallet_scores(G, illicit_seeds)
    print(f"✅ Analyzed {len(wallet_scores)} wallets")
    
    print("\n📊 Extracting suspicious subgraph...")
    subgraph = extract_suspicious_subgraph(G, illicit_seeds, wallet_scores)
    print(f"✅ Subgraph extracted: {subgraph.number_of_nodes()} nodes, {subgraph.number_of_edges()} edges")
    
    print("\n🎨 Creating visualization...")
    visualize_laundering_graph(subgraph, wallet_scores, illicit_seeds)
    
    print("\n📋 Generating suspicion report...")
    report = generate_report(wallet_scores, illicit_seeds)
    
    print("\n" + "=" * 60)
    print("TOP SUSPICIOUS WALLETS")
    print("=" * 60)
    print(report.to_string(index=False))
    
    output_csv = 'suspicion_report.csv'
    report.to_csv(output_csv, index=False)
    print(f"\n✅ Report saved to {output_csv}")
    
    print("\n" + "=" * 60)
    print("🎯 DETECTION COMPLETE")
    print("=" * 60)
    print(f"📁 Files generated:")
    print(f"  - laundering_graph.html (interactive visualization)")
    print(f"  - suspicion_report.csv (detailed scores)")


if __name__ == "__main__":
    main()