"""
Visualization Module
Creates interactive PyVis graph visualizations
"""

from pyvis.network import Network
import numpy as np


def visualize_laundering_graph(
    subgraph,
    wallet_scores,
    illicit_seeds,
    output_file='laundering_graph.html',
    open_browser=True,
):
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
        fan_out = wallet_scores.get(node, {}).get('fan_out', 0)
        fan_in = wallet_scores.get(node, {}).get('fan_in', 0)
        gather_scatter = wallet_scores.get(node, {}).get('gather_scatter', 0)
        cyclic = wallet_scores.get(node, {}).get('cyclic', 0)
        peeling = wallet_scores.get(node, {}).get('peeling', 0)
        
        if node in illicit_seeds:
            color = '#FF0000'
            title = f"ILLICIT SEED: {node}"
            size = 40
        elif score > 15:
            color = '#FF6600'
            title = f"HIGH RISK: {node}"
            size = 30
        elif score > 8:
            color = '#FFA500'
            title = f"MEDIUM RISK: {node}"
            size = 25
        else:
            color = '#90EE90'
            title = f"LOW RISK: {node}"
            size = 20

        title_parts = [
            title,
            f"Score: {score:.1f}",
            f"Centrality: {centrality:.2f}",
            f"Proximity: {proximity:.2f}",
        ]
        if any([fan_out, fan_in, gather_scatter, cyclic, peeling]):
            title_parts.append(
                "Patterns: "
                f"FO={fan_out}, FI={fan_in}, GS={gather_scatter}, "
                f"CY={cyclic}, PE={peeling}"
            )
        title = " | ".join(title_parts)
        
        net.add_node(node, label=node[:8], title=title, color=color, size=size)
    
    for src, dst, data in subgraph.edges(data=True):
        total_amount = data['total_amount']
        count = data['count']
        
        width = min(1 + np.log10(total_amount + 1) * 2, 10)
        
        title = f"{src[:8]} → {dst[:8]} | Amount: {total_amount:.4f} | Txs: {count}"
        
        net.add_edge(src, dst, width=width, title=title, arrows='to')
    
    # Avoid pyvis .show() notebook template issues by writing HTML directly.
    net.write_html(output_file, open_browser=False, notebook=False)
    print(f"✅ Visualization saved to {output_file}")
    if open_browser:
        try:
            import webbrowser
            webbrowser.open(output_file)
        except Exception:
            # Non-fatal: if no browser is available, the file is still saved.
            pass
