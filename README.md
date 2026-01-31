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

Create a CSV file named `transactions.csv` with one of the following schemas:

**Pipeline schema**
- `src_wallet`: Source wallet address
- `dst_wallet`: Destination wallet address
- `amount`: Transaction amount (float)
- `timestamp`: UNIX timestamp (seconds)

**Problem-statement schema**
- `Source_Wallet_ID`
- `Dest_Wallet_ID`
- `Timestamp` (seconds or ISO datetime string)
- `Amount`
- `Token_Type` (optional)

Example:
```csv
src_wallet,dst_wallet,amount,timestamp
0xABC,0x123,100.5,1640000000
0x123,0x456,95.2,1640000100
```

## Configuration

Edit `main.py` to configure:
```python
csv_path = 'data/transactions.csv'
illicit_file = 'data/illicit_wallets.csv'  # Optional seed list
```

## Usage

Run the system:
```bash
python main.py
```

Generate a synthetic dataset (optional):
```bash
python data_generator.py
```

## Web App (Frontend + Backend)

Install dependencies:
```bash
pip install -r requirements.txt
```

Start the backend API (serves the frontend too):
```bash
uvicorn backend.app:app --reload
```

Open the UI:
```
http://localhost:8000
```

Upload a transactions CSV (required) and an illicit wallets CSV (optional).

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

### Gather-Scatter Detection
- Identifies fan-out then fan-in topologies (A → B,C,D → ... → Z)
- Score: 0-10 based on recombination count

### Cyclic Detection
- Identifies directed cycles returning to the same wallet
- Score: 0-10 based on cycle participation

### Peeling Chain Detection
- Identifies transaction chains of length ≥4
- Requires a small "peel" transfer at each hop (gas-fee pattern)
- Detects monotonically decreasing main-transfer amounts
- Checks time delays between hops to hide the trail
- Score: 0-10 based on chain count

### Proximity Score
- Measures distance to known illicit wallets
- 1 hop = score 8
- 2 hops = score 5
- 3 hops = score 3
- Known illicit = score 10

## Scoring Formula

```
Total Score = (centrality × 2) + (proximity × 3)
```

## Thresholds

- Fan-out: ≥5 recipients, ≤1 hour window, ±15% amount similarity
- Fan-in: ≥5 senders, common ancestors within depth 2
- Gather-scatter: ≥3 fan-out, ≥2 recombinations
- Cyclic: directed cycle length ≤6
- Peeling: ≥4 hops, 50-98% decay rate
- Peeling peel ratio: 0.3-5% of main transfer
- Peeling delay window: 10 minutes to 72 hours between hops
- Proximity: BFS depth = 3

## Limitations

- No GNN or deep learning (rule-based only)
- Single-chain analysis (no cross-chain)
- Static dataset (no real-time)
- Hardcoded thresholds (not adaptive)

