"""
Data Loader Module
Handles loading and preprocessing transaction data
"""

import pandas as pd


def load_transactions(csv_path):
    """
    Load transaction data from CSV file
    
    Args:
        csv_path: Path to CSV file with columns: src_wallet, dst_wallet, amount, timestamp
        
    Returns:
        pandas DataFrame with parsed timestamps
    """
    df = pd.read_csv(csv_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    return df