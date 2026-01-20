from core.storage import Storage
import pandas as pd


class FinanceReport:

    def __init__(self, storage: Storage):
        self.storage = storage
    
    def monthly_spend_by_category(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        if df.empty:
            return pd.DataFrame(columns=['month', 'Category', 'spend'])

        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        df = df.dropna(subset=['Date', 'Amount'])

        if df.empty:
            return pd.DataFrame(columns=['month', 'Category', 'spend'])

        df['month'] = df['Date'].dt.to_period('M').astype(str)
        df['spend'] = df['Amount']

        monthly = (
            df.groupby(['month', 'Category'], as_index=False)['spend']
            .sum()
            .sort_values(['month', 'spend'], ascending=[True, False])
        )

        return monthly
    
    def spend_summary(
        self,
        df: pd.DataFrame,
        start,
        end,
        fill_missing_days: bool = True
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Return (spend_by_category, spend_per_day) within [start, end] inclusive.

        Global Amount contract:
          - spend  = positive Amount
          - refund = negative Amount
        """
        df = df.copy()


        # Inclusive date range (normalize to day boundaries)
        start_ts = pd.to_datetime(start).floor('D')
        end_ts = pd.to_datetime(end).floor('D') + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)

        df = df[(df['Date'] >= start_ts) & (df['Date'] <= end_ts)]

        # Spend only (exclude refunds/credits)
        df = df[df['Amount'] > 0].copy()

        # Category
        df['Category'] = df['Category'].fillna('Uncategorized').astype(str)

        # ---- spend by category ----
        by_category = (
            df.groupby('Category', as_index=False)['Amount']
              .sum()
              .rename(columns={'Amount': 'spend'})
              .reset_index(drop=True)
        )

        # ---- spend per day ----
        df['day'] = df['Date'].dt.floor('D')
        by_day = (
            df.groupby('day', as_index=False)['Amount']
              .sum()
              .rename(columns={'Amount': 'spend'})
              .sort_values('day')
              .reset_index(drop=True)
        )

        if fill_missing_days:
            all_days = pd.date_range(start=start_ts.floor('D'), end=end_ts.floor('D'), freq='D')
            by_day = (
                by_day.set_index('day')
                      .reindex(all_days, fill_value=0)
                      .rename_axis('day')
                      .reset_index()
            )

        return by_category, by_day
        