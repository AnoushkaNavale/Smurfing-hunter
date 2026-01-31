"""
Subgraph Extractor Module
Extracts relevant subgraph containing illicit seeds and suspicious neighbors
"""

from collections import deque


def extract_suspicious_subgraph(G, illicit_seeds, wallet_scores, depth=3, max_nodes=200):
    """
    Extract subgraph containing illicit seeds and suspicious neighbors
    
    Args:
        G: NetworkX DiGraph
        illicit_seeds: List of known illicit wallet addresses
        wallet_scores: Dictionary of wallet suspicion scores
        depth: BFS depth for neighborhood exploration
        max_nodes: Maximum nodes to include in subgraph
        
    Returns:
        NetworkX DiGraph subgraph
    """
    subgraph_nodes = set(illicit_seeds)
    
    for seed in illicit_seeds:
        if seed not in G:
            continue
        
        visited = {seed}
        queue = deque([(seed, 0)])
        
        while queue:
            node, d = queue.popleft()
            
            if d >= depth:
                continue
            
            for neighbor in list(G.successors(node)) + list(G.predecessors(node)):
                if neighbor in visited:
                    continue
                
                visited.add(neighbor)
                
                if wallet_scores.get(neighbor, {}).get('total', 0) > 5:
                    subgraph_nodes.add(neighbor)
                    queue.append((neighbor, d + 1))
                elif d < depth - 1:
                    queue.append((neighbor, d + 1))
    
    if len(subgraph_nodes) > max_nodes:
        sorted_nodes = sorted(
            subgraph_nodes,
            key=lambda n: wallet_scores.get(n, {}).get('total', 0),
            reverse=True
        )
        subgraph_nodes = set(sorted_nodes[:max_nodes])
    
    return G.subgraph(subgraph_nodes).copy()