# Smurfing & Layering Detection System

A rule-based graph analytics system for detecting money laundering patterns in cryptocurrency transactions.

## Overview

This system analyzes blockchain transaction data to identify suspicious patterns associated with money laundering, including:
- **Fan-Out**: One wallet rapidly distributing funds to multiple wallets
- **Fan-In**: Multiple wallets aggregating funds into one wallet (mule accounts)
- **Peeling Chains**: Sequential transactions with decreasing amounts to obfuscate trails
- **Proximity Analysis**: Distance to known illicit wallets

## Project Structure

```
├── main.py                 # Main execution script
├── data_loader.py          # Transaction data loading
├── graph_builder.py        # Graph construction
├── pattern_detectors.py    # Pattern detection algorithms
├── scoring_engine.py       # Suspicion scoring logic
├── subgraph_extractor.py   # Relevant subgraph extraction
├── visualization.py        # Interactive graph visualization
└── report_generator.py     # Suspicion report generation
```

## Requirements

```
pandas
networkx
pyvis
numpy
```

## Input Data Format

Create a CSV file named `transactions.csv` with the following columns:
- `src_wallet`: Source wallet address
- `dst_wallet`: Destination wallet address
- `amount`: Transaction amount (float)
- `timestamp`: UNIX timestamp (seconds)

Example:
```csv
src_wallet,dst_wallet,amount,timestamp
0xABC,0x123,100.5,1640000000
0x123,0x456,95.2,1640000100
```

## Configuration

Edit `main.py` to configure:
```python
csv_path = 'transactions.csv'
illicit_seeds = ["0xABC", "0xDEF"]  # Known illicit wallet addresses
```

## Usage

Run the system:
```bash
python main.py
```

## Outputs

1. **laundering_graph.html**: Interactive visualization
   - 🔴 Red nodes: Known illicit wallets
   - 🟠 Orange nodes: High-risk wallets
   - 🟢 Green nodes: Low-risk wallets
   - Node size = suspicion score
   - Edge width = transaction amount

2. **suspicion_report.csv**: Detailed suspicion scores
   - Sorted by total suspicion score
   - Human-readable explanations
   - Top 20 suspicious wallets

## Detection Algorithms

### Fan-Out Detection
- Identifies wallets sending to ≥5 addresses within 1 hour
- Checks for similar transaction amounts (±15%)
- Score: 0-10 based on pattern frequency

### Fan-In Detection
- Identifies wallets receiving from ≥5 addresses
- Checks if senders share common ancestors (depth 2)
- Score: 0-10 based on common ancestor pairs

### Peeling Chain Detection
- Identifies transaction chains of length ≥4
- Detects monotonically decreasing amounts
- Simulates gas fee obfuscation
- Score: 0-10 based on chain count

### Proximity Score
- Measures distance to known illicit wallets
- 1 hop = score 8
- 2 hops = score 5
- 3 hops = score 3
- Known illicit = score 10

## Scoring Formula

```
Total Score = (fan_out × 2) + (fan_in × 2) + (peeling × 1.5) + (proximity × 3)
```

## Thresholds

- Fan-out: ≥5 recipients, ≤1 hour window, ±15% amount similarity
- Fan-in: ≥5 senders, common ancestors within depth 2
- Peeling: ≥4 hops, 50-95% decay rate
- Proximity: BFS depth = 3

## Limitations

- No GNN or deep learning (rule-based only)
- Single-chain analysis (no cross-chain)
- Static dataset (no real-time)
- Hardcoded thresholds (not adaptive)

