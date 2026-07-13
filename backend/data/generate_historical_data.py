import os
import csv
import math
import random
from datetime import datetime, timedelta

def generate_asset_data(filename, start_value, base_drift, base_vol, shocks, start_year=1990, end_year=2026):
    data = []
    current_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 1, 1)
    
    current_val = start_value
    
    while current_date < end_date:
        # Determine current regime/shock
        drift = base_drift
        vol = base_vol
        
        for shock in shocks:
            if shock['start'] <= current_date <= shock['end']:
                drift = shock.get('drift', base_drift)
                vol = shock.get('vol', base_vol)
                break
                
        # Daily return using GBM
        dt = 1/252
        daily_drift = (drift - 0.5 * vol**2) * dt
        daily_vol = vol * math.sqrt(dt) * random.gauss(0, 1)
        
        current_val *= math.exp(daily_drift + daily_vol)
        
        # Only save end of month to keep file small but useful
        if current_date.day == 28:
            data.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "close": round(current_val, 2)
            })
            
        current_date += timedelta(days=1)
        
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['date', 'close'])
        writer.writeheader()
        writer.writerows(data)

def generate_macro_data(filename, base_rate, shocks, start_year=1990, end_year=2026):
    data = []
    current_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 1, 1)
    
    current_rate = base_rate
    
    while current_date < end_date:
        target_rate = base_rate
        for shock in shocks:
            if shock['start'] <= current_date <= shock['end']:
                target_rate = shock['rate']
                break
                
        # Mean reversion towards target rate
        current_rate += 0.05 * (target_rate - current_rate) + random.gauss(0, 0.001)
        
        if current_date.day == 28:
            data.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "value": round(current_rate, 4)
            })
            
        current_date += timedelta(days=1)
        
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['date', 'value'])
        writer.writeheader()
        writer.writerows(data)

if __name__ == "__main__":
    random.seed(42)
    os.makedirs('backend/data/market', exist_ok=True)
    os.makedirs('backend/data/macro', exist_ok=True)
    
    # Common shocks
    dotcom = {'start': datetime(2000, 3, 1), 'end': datetime(2002, 10, 1), 'drift': -0.20, 'vol': 0.35}
    gfc = {'start': datetime(2008, 1, 1), 'end': datetime(2009, 3, 1), 'drift': -0.40, 'vol': 0.45}
    covid = {'start': datetime(2020, 2, 1), 'end': datetime(2020, 4, 1), 'drift': -0.60, 'vol': 0.60}
    inflation_crisis = {'start': datetime(2022, 1, 1), 'end': datetime(2023, 1, 1), 'drift': -0.15, 'vol': 0.25}
    
    print("Generating Nifty 50...")
    generate_asset_data(
        'backend/data/market/nifty50.csv', 
        start_value=1000, 
        base_drift=0.14, 
        base_vol=0.22, 
        shocks=[dotcom, gfc, covid, inflation_crisis]
    )
    
    print("Generating S&P 500...")
    generate_asset_data(
        'backend/data/market/sp500.csv', 
        start_value=350, 
        base_drift=0.10, 
        base_vol=0.16, 
        shocks=[dotcom, gfc, covid, inflation_crisis]
    )
    
    print("Generating Gold...")
    gold_gfc = {'start': datetime(2008, 1, 1), 'end': datetime(2009, 3, 1), 'drift': 0.15, 'vol': 0.20} # Gold up in GFC
    gold_covid = {'start': datetime(2020, 2, 1), 'end': datetime(2020, 8, 1), 'drift': 0.25, 'vol': 0.25}
    generate_asset_data(
        'backend/data/market/gold.csv', 
        start_value=400, 
        base_drift=0.07, 
        base_vol=0.15, 
        shocks=[gold_gfc, gold_covid]
    )
    
    print("Generating India CPI...")
    # Inflation shocks
    high_inf_90s = {'start': datetime(1990, 1, 1), 'end': datetime(1998, 1, 1), 'rate': 0.10}
    high_inf_10s = {'start': datetime(2010, 1, 1), 'end': datetime(2014, 1, 1), 'rate': 0.11}
    covid_inf = {'start': datetime(2021, 1, 1), 'end': datetime(2023, 1, 1), 'rate': 0.07}
    generate_macro_data('backend/data/macro/india_cpi.csv', base_rate=0.05, shocks=[high_inf_90s, high_inf_10s, covid_inf])
    
    print("Generating RBI Repo Rate...")
    repo_90s = {'start': datetime(1990, 1, 1), 'end': datetime(1998, 1, 1), 'rate': 0.12}
    repo_gfc = {'start': datetime(2008, 10, 1), 'end': datetime(2010, 1, 1), 'rate': 0.04}
    repo_covid = {'start': datetime(2020, 3, 1), 'end': datetime(2022, 1, 1), 'rate': 0.04}
    generate_macro_data('backend/data/macro/rbi_repo.csv', base_rate=0.065, shocks=[repo_90s, repo_gfc, repo_covid])
    
    print("Data generation complete.")
