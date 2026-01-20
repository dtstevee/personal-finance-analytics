import pandas as pd
from core.storage import Storage
from core.ingestion import Ingestion
from core.report import FinanceReport
from core.predict import BudgetPredictor

# Execution Layer
class Agent:
    def __init__(self, data_dir: str = 'agent_data', filename: str = 'transactions.csv'):
        self.storage = Storage(data_dir, filename)
        self.ingestion = Ingestion(self.storage)
        self.report = FinanceReport(self.storage)

    # Data Modifying Layer
    def add_data(self, path: str, firm: str) -> dict:
        print("Data is added into the storage")
        return self.ingestion.add_data(path,firm)
    
    def load_transactions(self) -> pd.DataFrame:
        return self.storage.load_transactions()
    
    # Reporting Layer
    def flex_spend_report(self, start, end, fill_missing_days: bool = True):
        df = self.load_transactions()
        return self.report.spend_summary(df, start, end, fill_missing_days=fill_missing_days)
    
    # Prediction Layer
    def run_next_month_prediction(self):
        
        df = self.load_transactions()

        p = BudgetPredictor()
        panel = p.build_monthly_panel(df)
        panel_with_feature = p.make_features(panel)
        
        p.fit_ridge(panel_with_feature, feature = ['lag_1', 'roll3_mean'], alpha = 1.0, val_months = 3)

        pred = p.predict_next_month(panel_with_feature)

        return pred