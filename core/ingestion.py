from core.storage import Storage
import re
import os
import pandas as pd
import hashlib


class Ingestion:
    def __init__(self, storage: Storage):
        self.storage = storage
        self.canonical_cols = self.storage.canonical_cols

    # ------------------------------
    # tx_id assignment
    # ------------------------------
    def assign_tx_id(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        def make_base_key(row) -> str:
            dt = pd.to_datetime(row['Date'], errors = 'coerce')
            date_s = dt.strftime('%Y-%m-%d') if pd.notna(dt) else ''

            amt = pd.to_numeric(row['Amount'], errors = 'coerce')
            amt_s = f'{float(amt):.2f}' if pd.notna(amt) else ''

            desc_val = row.get('Description', '')
            if pd.isna(desc_val):
                desc_val = ''
            desc = str(desc_val).strip().lower()
            desc = re.sub(r"\s+", " ", desc)

            source_val = row.get('Source', '')
            if pd.isna(source_val):
                source_val = ''
            source = str(source_val).strip().upper()

            key = f"{source}|{date_s}|{amt_s}|{desc}"
            return key
        
        def assign_dup_rank(df: pd.DataFrame) -> pd.DataFrame:
            df = df.copy()
            df['_base_key'] = df.apply(make_base_key, axis=1)
            df = df.sort_values(['_base_key'], kind='mergesort').reset_index(drop=True)
            df['_dup_rank'] = df.groupby('_base_key').cumcount()
            return df
        
        def encode_tx_id(df: pd.DataFrame) -> pd.DataFrame:
            df = df.copy()
            df['tx_id'] = (df['_base_key'] + '|' +df['_dup_rank'].astype(str)
                        ).apply(lambda s: hashlib.sha1(s.encode('utf-8')).hexdigest())
            df = df.drop(columns = ['_base_key', '_dup_rank'])
            return df
        
        df = assign_dup_rank(df)
        df = encode_tx_id(df)
        
        return df
    
    def ingest_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Derive Day/Month/Year from Date as part of the canonical schema.
        """
        df = df.copy()
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Day'] = df['Date'].dt.day
        df['Month'] = df['Date'].dt.month
        df['Year'] = df['Date'].dt.year
        return df


    def ingest(self, path: str, firm: str) -> pd.DataFrame:
        firm = firm.strip().upper()

        # AMEX loader
        def load_amex_xlsx(xlsx_path: str) -> pd.DataFrame:
            # Data Loading
            raw = pd.read_excel(xlsx_path, header=None)

            # --- Detect header row (first column == 'date') ---
            header_candidates = raw.index[
                raw.iloc[:, 0].astype(str).str.strip().str.lower().eq('date')
            ].tolist()

            if not header_candidates:
                raise ValueError(
                    "Could not find AMEX header row."
                )

            header_id = header_candidates[0]
            col = raw.loc[header_id, :].tolist()
            df = raw.loc[header_id + 1:, :].copy()
            df.columns = col

            # Make sure date and amount are in correct types
            df['Date'] = pd.to_datetime(df['Date'], format='mixed', errors='coerce')
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')

            # --- Remove non-spend rows (payments/autopay) ---
            # We keep statement credits/refunds as negative Amounts, but we drop *payments*
            # because they are not spending and will inflate credits/net metrics.
            payment_pat = r"\b(autopay|payment|mobile\s+payment|online\s+payment|directpay|bill\s+pay|thank\s+you)\b"
            df = df[
                ~df['Description'].astype(str).str.contains(payment_pat, case=False, na=False, regex=True)
            ].copy().reset_index(drop=True)

            # --- Split hierarchical AMEX category (Main-Sub) ---
            df[['category_main', 'category_sub']] = (
                df['Category'].astype(str)
                .str.split('-', n=1, expand=True)
            )

            # --- Map AMEX categories to Discover-style flat categories ---
            def amex_to_discover(main, sub):
                main = str(main).strip().lower()
                sub = str(sub).strip().lower()

                # --- Non-spend / bookkeeping rows ---
                # Some AMEX exports may include payments/credits buckets. Drop them here.
                # NOTE: We still allow "awards/rebate" credits to be labeled explicitly.
                if 'award' in main or 'rebate' in main:
                    return 'Awards and Rebate Credits'

                if 'payment' in main or 'payments' in main:
                    return None

                if 'credit' in main or 'credits' in main:
                    return None

                if 'fees & adjustments' in main:
                    return None  # drop later

                # --- Spend category mapping (Discover-style) ---
                # Restaurants
                if 'restaurant' in main or 'dining' in main:
                    return 'Restaurants'

                # Supermarkets (Discover calls this "Supermarkets")
                if 'merchandise & supplies' in main and ('grocer' in sub or 'supermarket' in sub or 'grocery' in sub):
                    return 'Supermarkets'
                if 'supermarket' in main or 'grocery' in main:
                    return 'Supermarkets'

                # Gasoline
                if ('transportation' in main and 'fuel' in sub) or 'gas' in main or 'gasoline' in main:
                    return 'Gasoline'

                # Travel / Entertainment
                if 'travel' in main or 'entertainment' in main or 'lodging' in sub or 'air' in sub or 'hotel' in sub:
                    return 'Travel/ Entertainment'

                # Education
                if 'education' in main or 'school' in sub or 'tuition' in sub:
                    return 'Education'

                # Government Services
                if 'government' in main or 'tax' in sub or 'dmv' in sub:
                    return 'Government Services'

                # Interest
                if 'interest' in main:
                    return 'Interest'

                # Department Stores
                if 'department' in main or 'department store' in sub:
                    return 'Department Stores'

                # Warehouse Clubs
                if 'warehouse' in main or 'warehouse club' in sub:
                    return 'Warehouse Clubs'

                # Merchandise (general retail)
                if 'merchandise & supplies' in main:
                    return 'Merchandise'

                # Default
                return 'Unknown Source'  # fallback

            df['Category'] = df.apply(
                lambda r: amex_to_discover(r['category_main'], r['category_sub']),
                axis=1
            )
            df = df[df['Category'].notna()].copy()

            # --- Canonicalize: add Source and tx_id ---
            df['Source'] = 'AMEX'
            df = df.reset_index(drop=True)
            df = df[['Date', 'Description', 'Amount', 'Category', 'Source']].copy()

            return df

        # DISCOVER loader
        def load_discover_csv(csv_path: str) -> pd.DataFrame:
            """Load Discover statement from CSV (new format)."""

            # Data Loading (read raw rows first to allow header detection)
            raw = pd.read_csv(csv_path, header=None, dtype=str)

            # --- Detect header row (first column contains something like 'Trans. Date') ---
            first_col_norm = (
                raw.iloc[:, 0]
                .astype(str)
                .str.strip()
                .str.lower()
                .str.replace(r"[^a-z0-9]+", "", regex=True)
            )

            header_candidates = raw.index[
                first_col_norm.isin(['transdate', 'transactiondate', 'transactdate'])
            ].tolist()

            if not header_candidates:
                raise ValueError(
                    "Could not find Discover header row. Expected first column header like 'Trans. Date'."
                )

            header_id = header_candidates[0]
            col = raw.loc[header_id, :].tolist()
            df = raw.loc[header_id + 1:, :].copy()
            df.columns = col

            # Normalize column names (strip) and build a normalized lookup
            df.columns = [str(c).strip() for c in df.columns]
            col_norm_map = {
                str(c).strip(): re.sub(r"[^a-z0-9]+", "", str(c).strip().lower())
                for c in df.columns
            }

            def _pick(norm_targets):
                for orig, norm in col_norm_map.items():
                    if norm in norm_targets:
                        return orig
                return None

            # Discover exports commonly include: Trans. Date, Post Date, Description, Amount, Category
            date_col = _pick({'transdate', 'transactiondate', 'transactdate'})
            desc_col = _pick({'description'})
            amt_col = _pick({'amount'})
            cat_col = _pick({'category'})

            missing = [name for name, col in [("Date", date_col), ("Description", desc_col), ("Amount", amt_col), ("Category", cat_col)] if col is None]
            if missing:
                raise ValueError(
                    f"Discover CSV missing required columns: {missing}. Available columns: {list(df.columns)}"
                )

            # --- Select and rename columns to canonical names ---
            df = df[[date_col, desc_col, amt_col, cat_col]].copy()
            df.columns = ['Date', 'Description', 'Amount', 'Category']

            # --- Type normalization ---
            df['Date'] = pd.to_datetime(df['Date'], format='mixed', errors='coerce')
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')

            # --- Remove non-spend rows (Payments and Credits) ---
            df = df[
                ~df['Category'].astype(str).str.contains('Payments and Credits', case=False, na=False)
            ].copy()

            # --- Remove payment rows that are sometimes categorized differently ---
            payment_pat = r"\b(autopay|payment|online\s+payment|directpay|bill\s+pay|thank\s+you)\b"
            df = df[
                ~df['Description'].astype(str).str.contains(payment_pat, case=False, na=False, regex=True)
            ].copy()

            # --- Remove promo statement credits (data-layer cleanup) ---
            # Examples: "$100 STATEMENT CREDIT ...", "$100 REFER A FRIEND CREDIT"
            # These are not payments, but promotional credits that can distort credit metrics.
            promo_credit_pat = r"\b(statement\s+credit|refer\s+a\s+friend\s+credit)\b"
            df = df[
                ~df['Description'].astype(str).str.contains(promo_credit_pat, case=False, na=False, regex=True)
            ].copy()

            # --- Canonicalize: add Source and tx_id ---
            df['Source'] = 'DISCOVER'
            df = df.reset_index(drop=True)

            return df

        # Dispatch
        if firm == 'AMEX':
            df = load_amex_xlsx(path)
        elif firm == 'DISCOVER':
            df = load_discover_csv(path)
        else:
            raise ValueError(f"Unsupported firm: {firm}")
        
        df = self.ingest_dates(df)
        df = self.assign_tx_id(df)
        df = df[self.canonical_cols].copy()
        return df

    # ------------------------------
    # orchestration
    # ------------------------------
    def add_data(self, path: str, firm: str) -> dict:
        new_tx = self.ingest(path, firm)
        stats = self.storage.merge_and_save(new_tx)
        print('New data has been processed')
        return stats