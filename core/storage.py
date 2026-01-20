import pandas as pd
import numpy as np
import os


class Storage:
    """CSV-backed storage for canonical transactions.

    Canonical columns:
      ['tx_id', 'Date', 'Day', 'Month', 'Year', 'Amount', 'Category', 'Description', 'Source']

    Public API:
      - load_transactions()
      - save_transactions(df)
      - merge_and_save(new_df)
      - reset_file()
    """

    def __init__(self, data_dir: str = 'agent_data', filename: str = 'transactions.csv'):
        self.data_dir = data_dir
        self.filename = filename

        self.canonical_cols = ['tx_id', 'Date', 'Day', 'Month', 'Year', 'Amount', 'Category', 'Description', 'Source']

        os.makedirs(self.data_dir, exist_ok=True)
        self.tx_path = os.path.join(self.data_dir, self.filename)

    def load_transactions(self) -> pd.DataFrame:
        if os.path.exists(self.tx_path):
            df = pd.read_csv(self.tx_path)
            # Ensure all canonical columns exist, filling missing with NaN
            for c in self.canonical_cols:
                if c not in df.columns:
                    df[c] = np.nan
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
            df = df[self.canonical_cols].copy()
            return df

        return pd.DataFrame(columns=self.canonical_cols)

    def save_transactions(self, df: pd.DataFrame) -> None:
        """Persist canonical transactions."""
        df = df.copy()
        df = df[self.canonical_cols].copy()
        df['Date'] = df['Date'].astype(str)
        # leverage tmp to prevent collapsing
        tmp_path = self.tx_path + '.tmp'
        df.to_csv(tmp_path, index=False)
        os.replace(tmp_path, self.tx_path)

    def merge_and_save(self, new_df: pd.DataFrame) -> dict:
        """Merge new transactions, dedupe by tx_id, and persist."""
        existing = self.load_transactions()

        before = len(existing)
        incoming = len(new_df)

        combined = pd.concat([existing, new_df], ignore_index=True)
        combined = combined.drop_duplicates(subset=['tx_id'], keep='first')
        combined = combined.sort_values(['Date', 'Amount'], ascending=[True, False]).reset_index(drop=True)

        after = len(combined)
        inserted_est = after - before
        skipped_est = incoming - max(inserted_est, 0)

        self.save_transactions(combined)

        return {
            'existing_rows': before,
            'incoming_rows': incoming,
            'final_rows': after,
            'inserted_estimate': inserted_est,
            'skipped_estimate': skipped_est
        }
    
    def reset_file(self) -> None:
        # Create an empty canonical DataFrame
        empty_df = pd.DataFrame(columns=self.canonical_cols)

        # Persist as a brand-new transactions.csv
        tmp_path = self.tx_path + '.tmp'
        empty_df.to_csv(tmp_path, index=False)
        os.replace(tmp_path, self.tx_path)