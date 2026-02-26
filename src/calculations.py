import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class WeightedAverageResult:
    """Weighted average calculation result"""
    call_wgt_avg: float
    put_wgt_avg: float
    all_wgt_avg: float
    spot_price: float
    call_total_oi: int
    put_total_oi: int
    all_total_oi: int

class OICalculator:
    """Open Interest weighted average calculator"""
    
    @staticmethod
    def _to_float(value):
        """Convert Decimal or other numeric types to float"""
        if isinstance(value, Decimal):
            return float(value)
        return float(value) if value is not None else 0.0
    
    @staticmethod
    def _convert_dataframe_types(df: pd.DataFrame) -> pd.DataFrame:
        """Convert Decimal columns to float for calculations"""
        df = df.copy()
        numeric_columns = ['strike', 'open_interest', 'last_price', 'bid', 'ask', 
                          'implied_volatility', 'delta', 'gamma', 'theta', 'vega']
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: OICalculator._to_float(x))
        
        return df
    
    @staticmethod
    def calculate_weighted_averages(
        df: pd.DataFrame, 
        spot_price: float
    ) -> WeightedAverageResult:
        """
        Calculate weighted average strike prices based on Open Interest
        
        Formulas:
        1. Call WgtAvg = Σ(Ki × CallOIi) / Σ(CallOIi)
        2. Put WgtAvg = Σ(Ki × PutOIi) / Σ(PutOIi)
        3. All WgtAvg = Σ(Ki × (CallOIi + PutOIi)) / Σ(CallOIi + PutOIi)
        
        Args:
            df: DataFrame with columns ['strike', 'option_type', 'open_interest']
            spot_price: Current stock price
            
        Returns:
            WeightedAverageResult with all calculations
        """
        # Convert data types first
        df = OICalculator._convert_dataframe_types(df)
        
        # Filter out rows with OI = 0
        df = df[df['open_interest'] > 0].copy()
        
        if df.empty:
            return WeightedAverageResult(
                call_wgt_avg=0,
                put_wgt_avg=0,
                all_wgt_avg=0,
                spot_price=float(spot_price),
                call_total_oi=0,
                put_total_oi=0,
                all_total_oi=0
            )
        
        # Separate calls and puts
        calls = df[df['option_type'] == 'CALL']
        puts = df[df['option_type'] == 'PUT']
        
        # Calculate Call weighted average
        if not calls.empty and calls['open_interest'].sum() > 0:
            call_wgt_avg = float((calls['strike'] * calls['open_interest']).sum() / calls['open_interest'].sum())
            call_total_oi = int(calls['open_interest'].sum())
        else:
            call_wgt_avg = 0.0
            call_total_oi = 0
        
        # Calculate Put weighted average
        if not puts.empty and puts['open_interest'].sum() > 0:
            put_wgt_avg = float((puts['strike'] * puts['open_interest']).sum() / puts['open_interest'].sum())
            put_total_oi = int(puts['open_interest'].sum())
        else:
            put_wgt_avg = 0.0
            put_total_oi = 0
        
        # Calculate All weighted average
        all_total_oi = call_total_oi + put_total_oi
        if all_total_oi > 0:
            # Merge calls and puts to get combined OI per strike
            call_oi = calls.groupby('strike')['open_interest'].sum().reset_index()
            call_oi.columns = ['strike', 'call_oi']
            
            put_oi = puts.groupby('strike')['open_interest'].sum().reset_index()
            put_oi.columns = ['strike', 'put_oi']
            
            # Merge on strike
            combined = pd.merge(call_oi, put_oi, on='strike', how='outer').fillna(0)
            combined['total_oi'] = combined['call_oi'] + combined['put_oi']
            
            all_wgt_avg = float((combined['strike'] * combined['total_oi']).sum() / combined['total_oi'].sum())
        else:
            all_wgt_avg = 0.0
        
        return WeightedAverageResult(
            call_wgt_avg=round(call_wgt_avg, 2),
            put_wgt_avg=round(put_wgt_avg, 2),
            all_wgt_avg=round(all_wgt_avg, 2),
            spot_price=round(float(spot_price), 2),
            call_total_oi=call_total_oi,
            put_total_oi=put_total_oi,
            all_total_oi=all_total_oi
        )
    
    @staticmethod
    def prepare_oi_distribution_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare data for OI distribution chart
        
        Returns DataFrame with columns:
        - strike: Strike price
        - call_oi: Call open interest
        - put_oi: Put open interest
        """
        # Convert data types first
        df = OICalculator._convert_dataframe_types(df)
        
        # Group by strike and option type
        grouped = df.groupby(['strike', 'option_type'])['open_interest'].sum().reset_index()
        
        # Pivot to get calls and puts as separate columns
        pivoted = grouped.pivot(index='strike', columns='option_type', values='open_interest').fillna(0)
        
        # Ensure both CALL and PUT columns exist
        if 'CALL' not in pivoted.columns:
            pivoted['CALL'] = 0
        if 'PUT' not in pivoted.columns:
            pivoted['PUT'] = 0
        
        # Reset index to make strike a column
        result = pivoted.reset_index()
        result.columns = ['strike', 'call_oi', 'put_oi']
        
        # Convert to float to avoid Decimal issues in charts
        result['strike'] = result['strike'].astype(float)
        result['call_oi'] = result['call_oi'].astype(float)
        result['put_oi'] = result['put_oi'].astype(float)
        
        # Sort by strike
        result = result.sort_values('strike')
        
        return result
    
    @staticmethod
    def get_max_pain_strike(df: pd.DataFrame) -> float:
        """
        Calculate Max Pain strike price
        Max Pain is the strike where the total OI of calls and puts is maximized
        """
        distribution = OICalculator.prepare_oi_distribution_data(df)
        distribution['total_oi'] = distribution['call_oi'] + distribution['put_oi']
        max_pain_idx = distribution['total_oi'].idxmax()
        return float(distribution.loc[max_pain_idx, 'strike'])
