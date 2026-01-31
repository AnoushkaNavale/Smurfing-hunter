"""
Pattern Detectors Module
Implements rule-based detection for fan-out, fan-in, peeling chains, and proximity scoring
"""

import networkx as nx
import numpy as np


def detect_fan_out(G, wallet, time_window_hours=1, min_degree=5, amount_similarity=0.15):
    """
    Detect fan-out pattern: one wallet sends to many within short time
    
    Args:
        G: NetworkX DiGraph
        wallet: Wallet address to analyze
        time_window_hours: Time window for concurrent transactions
        min_degree: Minimum number of recipients to flag
        amount_similarity: Maximum relative difference for similar amounts
        
    Returns:
        Count of suspicious fan-out events (capped at 10)
    """
    if wallet not in G:
        return 0
    
    out_edges = list(G.out_edges(wallet, data=True))
    if len(out_edges) < min_degree:
        return 0
    
    fan_out_count = 0
    
    for edge_data in out_edges:
        src, dst, data = edge_data
        timestamps = data['timestamps']
        amounts = data['amounts']
        
        for i, ts in enumerate(timestamps):
            concurrent_txs = []
            
            for other_edge in out_edges:
                _, other_dst, other_data = other_edge
                if other_dst == dst:
                    continue
                
                for j, other_ts in enumerate(other_data['timestamps']):
                    time_diff = abs((other_ts - ts).total_seconds() / 3600)
                    if time_diff <= time_window_hours:
                        concurrent_txs.append({
                            'dst': other_dst,
                            'amount': other_data['amounts'][j],
                            'timestamp': other_ts
                        })
            
            if len(concurrent_txs) >= min_degree - 1:
                all_amounts = [amounts[i]] + [tx['amount'] for tx in concurrent_txs]
                avg_amount = np.mean(all_amounts)
                
                similar_amounts = sum(
                    1 for amt in all_amounts 
                    if abs(amt - avg_amount) / avg_amount <= amount_similarity
                )
                
                if similar_amounts >= min_degree * 0.7:
                    fan_out_count += 1
                    break
    
    return min(fan_out_count, 10)


def detect_fan_in(G, wallet, min_degree=5, ancestor_depth=2):
    """
    Detect fan-in pattern: many wallets send to one (aggregation)
    Check if senders share common ancestors
    
    Args:
        G: NetworkX DiGraph
        wallet: Wallet address to analyze
        min_degree: Minimum number of senders to flag
        ancestor_depth: How far back to look for common ancestors
        
    Returns:
        Fan-in suspicion score (capped at 10)
    """
    if wallet not in G:
        return 0
    
    in_edges = list(G.in_edges(wallet, data=True))
    if len(in_edges) < min_degree:
        return 0
    
    senders = [src for src, dst, _ in in_edges]
    
    common_ancestor_pairs = 0
    
    for i, sender1 in enumerate(senders):
        ancestors1 = set()
        try:
            for depth in range(1, ancestor_depth + 1):
                for node in nx.single_source_shortest_path_length(
                    G.reverse(), sender1, cutoff=depth
                ).keys():
                    if node != sender1:
                        ancestors1.add(node)
        except:
            pass
        
        for sender2 in senders[i+1:]:
            ancestors2 = set()
            try:
                for depth in range(1, ancestor_depth + 1):
                    for node in nx.single_source_shortest_path_length(
                        G.reverse(), sender2, cutoff=depth
                    ).keys():
                        if node != sender2:
                            ancestors2.add(node)
            except:
                pass
            
            if len(ancestors1 & ancestors2) > 0:
                common_ancestor_pairs += 1
    
    expected_random = len(senders) * (len(senders) - 1) / 4 / G.number_of_nodes()
    
    if common_ancestor_pairs > expected_random * 2:
        return min(int(common_ancestor_pairs / 2), 10)
    
    return 0


def detect_peeling_chains(G, wallet, min_length=4):
    """
    Detect peeling chain: long path with decreasing amounts (gas fee obfuscation)
    
    Args:
        G: NetworkX DiGraph
        wallet: Starting wallet address
        min_length: Minimum chain length to consider
        
    Returns:
        Count of peeling chains detected (capped at 10)
    """
    if wallet not in G:
        return 0
    
    peeling_chains = 0
    
    def explore_path(current, path, amounts):
        nonlocal peeling_chains
        
        if len(path) >= min_length:
            is_decreasing = all(
                amounts[i] > amounts[i+1] 
                for i in range(len(amounts)-1)
            )
            
            decay_rate = amounts[-1] / amounts[0] if amounts[0] > 0 else 0
            if is_decreasing and 0.5 <= decay_rate <= 0.95:
                peeling_chains += 1
                return
        
        if len(path) >= min_length + 2:
            return
        
        if current not in G:
            return
        
        for neighbor in G.successors(current):
            if neighbor in path:
                continue
            
            edge_data = G[current][neighbor]
            avg_amount = edge_data['total_amount'] / edge_data['count']
            
            if not amounts or avg_amount < amounts[-1]:
                explore_path(
                    neighbor, 
                    path + [neighbor], 
                    amounts + [avg_amount]
                )
    
    explore_path(wallet, [wallet], [])
    
    return min(peeling_chains, 10)


def calculate_proximity_score(G, wallet, illicit_seeds, max_depth=3):
    """
    Calculate proximity to known illicit wallets
    Closer = higher score
    
    Args:
        G: NetworkX DiGraph
        wallet: Wallet address to analyze
        illicit_seeds: List of known illicit wallet addresses
        max_depth: Maximum hops to consider
        
    Returns:
        Proximity score (0-10, higher = closer to illicit wallets)
    """
    if wallet in illicit_seeds:
        return 10
    
    min_distance = float('inf')
    
    for seed in illicit_seeds:
        if seed not in G or wallet not in G:
            continue
        
        try:
            distance = nx.shortest_path_length(G, seed, wallet)
            min_distance = min(min_distance, distance)
        except nx.NetworkXNoPath:
            pass
        
        try:
            distance = nx.shortest_path_length(G, wallet, seed)
            min_distance = min(min_distance, distance)
        except nx.NetworkXNoPath:
            pass
    
    if min_distance == float('inf'):
        return 0
    
    if min_distance == 1:
        return 8
    elif min_distance == 2:
        return 5
    elif min_distance == 3:
        return 3
    else:
        return max(0, 10 - min_distance)