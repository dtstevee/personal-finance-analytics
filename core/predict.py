import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

class BudgetPredictor:

    def __init__(self):
        pass
    
    def build_monthly_panel(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df[df['Amount'] >= 0].copy()

        panel = (
            df.groupby(['Month', 'Year', 'Category'], as_index = False)['Amount']
                    .sum()
                    .rename(columns  = {'Amount': 'spend'})
                    .sort_values(['Year', 'Month', 'Category'],
                                 ascending = [False, True, True])
        )
        # time indexing
        panel['t'] = panel['Year'].astype(int) * 12 + panel['Month'].astype(int)

        return panel
    
    def identify_rare_categories(self, 
                                 threshold: float, 
                                 df: pd.DataFrame) -> pd.DataFrame:

        df = df.copy()

        # Find how many months in the dataset
        total_month = int(df['t'].nunique())
        if total_month == 0:
            return df

        # Only active months are used to estimate appearance probability and conditional mean
        df_active = df[df['spend'] > 0].copy()

        panel = df_active.groupby('Category').agg(
            active_m=('t', 'nunique'),
            total_spend=('spend', 'sum'),
            mu=('spend', 'mean')
        )

        panel['p'] = panel['active_m'] / total_month
        panel['ratio'] = panel['p']
        panel['scarcity'] = (panel['ratio'] < threshold).astype(int)

        # set of rare categories R
        scare_item = set(panel.index[panel['scarcity'] == 1].tolist())
        unknown_source_E = float((panel.loc[list(scare_item), 'p'] 
                                  * panel.loc[list(scare_item), 'mu'])
                                  .sum()) if scare_item else 0.0

        # Keep only common categories
        df = df[~df['Category'].isin(scare_item)].copy()

        # Add pooled category for every month in the panel
        month_index = df[['Year', 'Month']].drop_duplicates().copy()
        pooled = month_index.copy()
        pooled['Category'] = 'Unknown Source'
        pooled['spend'] = unknown_source_E
        pooled['t'] = pooled['Year'].astype(int) * 12 + pooled['Month'].astype(int)

        df = pd.concat([df, pooled], ignore_index=True)

        df = (
            df.groupby(['Month', 'Year', 'Category'], as_index=False)['spend']
              .sum()
              .sort_values(['Year', 'Month', 'Category'],
                           ascending=[False, True, True])
        )

        df['t'] = df['Year'].astype(int) * 12 + df['Month'].astype(int)

        # store for debugging / downstream use
        self.scare_item = scare_item
        self.unknown_source_E = unknown_source_E

        return df
    



'''
    def make_features(self, df: pd.DataFrame) -> pd.DataFrame:
        
        df = (df.sort_values(['Category', 'Year', 'Month'], 
                            ascending = [True, True, True])
                            .reset_index(drop = True)).copy()
        
        df['y'] = df['spend']
        
        df['lag_1'] = df.groupby('Category')['spend'].shift(1)

        df['roll3_mean'] = (
            df.groupby('Category')['spend']
            .apply(lambda s: s.shift(1).rolling(3).mean())
            .reset_index(level = 0, drop = True)
        )
        
        df = df.dropna(subset = ['lag_1']).reset_index(drop = True)
        df['roll3_mean'] = df['roll3_mean'].fillna(df['lag_1'])

        return df

    # fit ridge function
    def fit_ridge(self,
                    df: pd.DataFrame,
                    feature: list[str],
                    alpha: float = 1.0,
                    val_months: int = 3) -> None:
        
        df = df.copy()

        # time indexing
        df = df.sort_values(['t', 'Category']).reset_index(drop = True)

        # training/validation
        unique_t = sorted(df['t'].unique())
        
        if len(unique_t) <= val_months:
            cutoff_t = unique_t[-1]
            train_df = df
            valid_df = df.iloc[0:0] # just another way to write a zero degree dataframe
        else:
            cutoff_t = unique_t[-(val_months + 1)]
            train_df = df[df['t'] <= cutoff_t]
            valid_df = df[df['t'] > cutoff_t]
        
        X_train = train_df[feature].values
        y_train = train_df["y"].values

        # Scaling
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)

        # 3) Fit Ridge
        model = Ridge(alpha=alpha)
        model.fit(X_train_scaled, y_train)

        # 4) Save to self for later prediction
        self.model = model
        self.scaler = scaler
        self.feature = feature
        self.cutoff_t = int(cutoff_t)
        
        # future debugging purpose
        print(len(train_df), len(valid_df))
    
    def predict_next_month(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        latest = (df.sort_values(['Category', 't'])
              .groupby('Category', as_index = False)
              .tail(1)
              .reset_index(drop = True)
                )
        
        latest['t_next'] = latest['t'] + 1
        X_next = latest[self.feature].values
        X_next_scaled = self.scaler.transform(X_next)

        y_pred = self.model.predict(X_next_scaled)

        out = pd.DataFrame(
            {"Category": latest['Category'],
             't_next': latest['t_next'],
             'y_pred': y_pred}
        )

        return out
'''
