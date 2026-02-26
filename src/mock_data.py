import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any

def generate_mock_option_chain(symbol: str, expiry_date: str, spot_price: float = 186.86) -> pd.DataFrame:
    """
    Generate mock option chain data for demonstration
    Based on NVDA-like data pattern from the reference image
    """
    np.random.seed(42)  # For reproducible results
    
    # Generate strike prices around spot price
    strike_range = np.arange(55, 425, 5)
    
    data = []
    
    # Create OI distribution pattern similar to reference image
    # Calls peak around spot + 10-20, Puts peak around spot - 10-20
    
    for strike in strike_range:
        # Call OI - peaks at slightly higher strikes
        call_distance = abs(strike - (spot_price + 15))
        call_oi_base = max(0, 80000 - call_distance * 1500)
        call_oi = int(call_oi_base + np.random.normal(0, 5000))
        call_oi = max(0, call_oi)
        
        # Put OI - peaks at slightly lower strikes
        put_distance = abs(strike - (spot_price - 15))
        put_oi_base = max(0, 50000 - put_distance * 1200)
        put_oi = int(put_oi_base + np.random.normal(0, 4000))
        put_oi = max(0, put_oi)
        
        # Generate option symbols
        call_symbol = f"{symbol}{expiry_date.replace('-', '')}C{strike}"
        put_symbol = f"{symbol}{expiry_date.replace('-', '')}P{strike}"
        
        # Call option
        data.append({
            'symbol': call_symbol,
            'strike': float(strike),
            'option_type': 'CALL',
            'open_interest': call_oi,
            'volume': int(call_oi * 0.1 + np.random.normal(0, 100)),
            'last_price': max(0.01, (spot_price - strike) * 0.8 + np.random.normal(0, 1)) if strike < spot_price else max(0.01, np.random.normal(2, 1)),
            'bid': max(0.01, (spot_price - strike) * 0.8 - 0.1) if strike < spot_price else max(0.01, 1.9),
            'ask': max(0.01, (spot_price - strike) * 0.8 + 0.1) if strike < spot_price else max(0.01, 2.1),
            'implied_volatility': 0.45 + np.random.normal(0, 0.05),
            'delta': 0.5 + (spot_price - strike) / 100 if strike < spot_price else max(0.01, 0.5 - (strike - spot_price) / 100),
            'gamma': 0.02 + np.random.normal(0, 0.005),
            'theta': -0.05 + np.random.normal(0, 0.01),
            'vega': 0.1 + np.random.normal(0, 0.02),
        })
        
        # Put option
        data.append({
            'symbol': put_symbol,
            'strike': float(strike),
            'option_type': 'PUT',
            'open_interest': put_oi,
            'volume': int(put_oi * 0.1 + np.random.normal(0, 100)),
            'last_price': max(0.01, (strike - spot_price) * 0.8 + np.random.normal(0, 1)) if strike > spot_price else max(0.01, np.random.normal(2, 1)),
            'bid': max(0.01, (strike - spot_price) * 0.8 - 0.1) if strike > spot_price else max(0.01, 1.9),
            'ask': max(0.01, (strike - spot_price) * 0.8 + 0.1) if strike > spot_price else max(0.01, 2.1),
            'implied_volatility': 0.45 + np.random.normal(0, 0.05),
            'delta': -0.5 - (strike - spot_price) / 100 if strike > spot_price else min(-0.01, -0.5 + (spot_price - strike) / 100),
            'gamma': 0.02 + np.random.normal(0, 0.005),
            'theta': -0.05 + np.random.normal(0, 0.01),
            'vega': 0.1 + np.random.normal(0, 0.02),
        })
    
    df = pd.DataFrame(data)
    
    # Clean up negative values
    df['volume'] = df['volume'].clip(lower=0)
    df['implied_volatility'] = df['implied_volatility'].clip(lower=0.05, upper=2.0)
    df['delta'] = df['delta'].clip(lower=-1, upper=1)
    df['gamma'] = df['gamma'].clip(lower=0)
    
    return df

def get_mock_expiry_dates() -> List[str]:
    """Generate mock expiry dates"""
    today = datetime.now()
    # Generate next 4 Fridays
    expiry_dates = []
    for i in range(1, 5):
        days_until_friday = (4 - today.weekday()) % 7 + i * 7
        expiry = today + timedelta(days=days_until_friday)
        expiry_dates.append(expiry.strftime("%Y-%m-%d"))
    return expiry_dates

def get_mock_stock_quote(symbol: str) -> Dict[str, Any]:
    """Generate mock stock quote"""
    return {
        'symbol': symbol,
        'last_price': 186.86,
        'bid': 186.80,
        'ask': 186.92,
        'volume': 45000000,
    }
