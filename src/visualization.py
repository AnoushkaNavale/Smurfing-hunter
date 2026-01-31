"""
Visualization Module
Creates interactive PyVis graph visualizations
"""

from pyvis.network import Network
import numpy as np


def visualize_laundering_graph(subgraph, wallet_scores, illicit_seeds, output_file='laundering_graph.html'):
    """
    Create interactive PyVis visualization
    
    Args:
        subgraph: NetworkX DiGraph to visualize
        wallet_scores: Dictionary of wallet suspicion scores
        illicit_seeds: List of known illicit wallet addresses
        output_file: Output HTML file path
    """
    net = Network(height='800px', width='100%', directed=True, notebook=False)
    net.barnes_hut(gravity=-8000, central_gravity=0.3, spring_length=200)
    
    for node in subgraph.nodes():
        score = wallet_scores.get(node, {}).get('total', 0)
        centrality = wallet_scores.get(node, {}).get('centrality', 0)
        proximity = wallet_scores.get(node, {}).get('proximity', 0)
        
        if node in illicit_seeds:
            color = '#FF0000'
            title = f"ILLICIT SEED: {node}"
            size = 40
        elif score > 15:
            color = '#FF6600'
            title = f"HIGH RISK: {node}<br>Score: {score:.1f}"
            size = 30
        elif score > 8:
            color = '#FFA500'
            title = f"MEDIUM RISK: {node}<br>Score: {score:.1f}"
            size = 25
        else:
            color = '#90EE90'
            title = f"LOW RISK: {node}<br>Score: {score:.1f}"
            size = 20

        title += f"<br>Centrality: {centrality:.2f}"
        title += f"<br>Proximity: {proximity:.2f}"
        
        net.add_node(node, label=node[:8], title=title, color=color, size=size)
    
    for src, dst, data in subgraph.edges(data=True):
        total_amount = data['total_amount']
        count = data['count']
        
        width = min(1 + np.log10(total_amount + 1) * 2, 10)
        
        title = f"{src[:8]} → {dst[:8]}<br>Amount: {total_amount:.4f}<br>Txs: {count}"
        
        net.add_edge(src, dst, width=width, title=title, arrows='to')
    
    # Avoid pyvis .show() notebook template issues by writing HTML directly.
    net.write_html(output_file, open_browser=False, notebook=False)
    print(f"✅ Visualization saved to {output_file}")
    try:
        import webbrowser
        webbrowser.open(output_file)
    except Exception:
        # Non-fatal: if no browser is available, the file is still saved.
        pass
