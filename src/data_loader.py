"""
Data Loader Module
Handles loading and preprocessing transaction data
"""

import pandas as pd


def load_transactions(csv_path):
    """
    Load transaction data from CSV file.

    Args:
        csv_path: Path to CSV file with columns:
            - src_wallet, dst_wallet, amount, timestamp (pipeline schema)
            - or Source_Wallet_ID, Dest_Wallet_ID, Amount, Timestamp, Token_Type

    Returns:
        pandas DataFrame with parsed timestamps and standardized columns.
    """
    df = pd.read_csv(csv_path)

    lower_cols = {col.lower(): col for col in df.columns}
    schema_options = [
        {
            "src_wallet": "src_wallet",
            "dst_wallet": "dst_wallet",
            "amount": "amount",
            "timestamp": "timestamp",
        },
        {
            "source_wallet_id": "src_wallet",
            "dest_wallet_id": "dst_wallet",
            "amount": "amount",
            "timestamp": "timestamp",
        },
        {
            "source_wallet": "src_wallet",
            "dest_wallet": "dst_wallet",
            "amount": "amount",
            "timestamp": "timestamp",
        },
    ]

    rename_map = None
    for option in schema_options:
        if all(key in lower_cols for key in option):
            rename_map = {lower_cols[key]: value for key, value in option.items()}
            break

    if rename_map is None:
        raise ValueError(
            "Unsupported transaction schema. Expected columns like "
            "src_wallet/dst_wallet/amount/timestamp or "
            "Source_Wallet_ID/Dest_Wallet_ID/Amount/Timestamp."
        )

    if "token_type" in lower_cols:
        rename_map[lower_cols["token_type"]] = "token_type"

    df = df.rename(columns=rename_map)

    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    timestamp_numeric = pd.to_numeric(df["timestamp"], errors="coerce")
    if timestamp_numeric.notna().mean() > 0.9:
        df["timestamp"] = pd.to_datetime(timestamp_numeric, unit="s", errors="coerce")
    else:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    df = df.dropna(subset=["src_wallet", "dst_wallet", "amount", "timestamp"])
    return df