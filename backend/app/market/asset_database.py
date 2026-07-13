import os
import pandas as pd
from typing import Dict, Optional, Tuple
from datetime import datetime

class AssetDatabase:
    """
    Market Intelligence Layer: Asset Database
    Loads and provides access to historical asset and macroeconomic data.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AssetDatabase, cls).__new__(cls)
            cls._instance._load_data()
        return cls._instance
        
    def _load_data(self):
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
        self.assets: Dict[str, pd.DataFrame] = {}
        self.macro: Dict[str, pd.DataFrame] = {}
        
        # Load Market Assets
        market_dir = os.path.join(self.data_dir, 'market')
        if os.path.exists(market_dir):
            for file in os.listdir(market_dir):
                if file.endswith('.csv'):
                    asset_name = file.split('.')[0]
                    df = pd.read_csv(os.path.join(market_dir, file), parse_dates=['date'])
                    df.set_index('date', inplace=True)
                    df.sort_index(inplace=True)
                    # Calculate monthly returns
                    df['return'] = df['close'].pct_change()
                    self.assets[asset_name] = df
                    
        # Load Macro Data
        macro_dir = os.path.join(self.data_dir, 'macro')
        if os.path.exists(macro_dir):
            for file in os.listdir(macro_dir):
                if file.endswith('.csv'):
                    macro_name = file.split('.')[0]
                    df = pd.read_csv(os.path.join(macro_dir, file), parse_dates=['date'])
                    df.set_index('date', inplace=True)
                    df.sort_index(inplace=True)
                    self.macro[macro_name] = df
                    
    def get_asset_return_series(self, asset: str, start_date: str = None, end_date: str = None) -> pd.Series:
        """Returns the monthly return series for an asset."""
        if asset not in self.assets:
            raise ValueError(f"Asset {asset} not found.")
            
        df = self.assets[asset]
        if start_date:
            df = df.loc[start_date:]
        if end_date:
            df = df.loc[:end_date]
            
        return df['return'].dropna()
        
    def get_historical_event_drawdown(self, asset: str, start_date: str, end_date: str) -> float:
        """Calculates the maximum drawdown of an asset during a specific historical period."""
        if asset not in self.assets:
            return 0.0
            
        df = self.assets[asset].loc[start_date:end_date]
        if df.empty:
            return 0.0
            
        peak = df['close'].expanding(min_periods=1).max()
        drawdown = (df['close'] / peak) - 1
        return drawdown.min()
        
    def get_macro_average(self, indicator: str, start_date: str = None, end_date: str = None) -> float:
        """Returns the average value of a macro indicator over a period."""
        if indicator not in self.macro:
            raise ValueError(f"Macro indicator {indicator} not found.")
            
        df = self.macro[indicator]
        if start_date:
            df = df.loc[start_date:]
        if end_date:
            df = df.loc[:end_date]
            
        return df['value'].mean()
