import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass

import pandas as pd
import streamlit as st

from src.calculations import OICalculator


@dataclass
class FetchResult:
    """Data fetch result"""
    success: bool
    data: Optional[Dict[str, Any]]
    error_message: Optional[str] = None
    status: str = "成功"


class DataFetcher:
    """Unified data fetching service with error handling and rate limiting"""

    def __init__(self, client):
        self.client = client

    def fetch_oi_data_for_symbol(
        self,
        symbol: str,
        expiry_date: str
    ) -> FetchResult:
        """Fetch OI data for a single symbol"""
        symbol = symbol.strip().upper()
        if not symbol:
            return FetchResult(False, None, "股票代码为空", "错误")

        try:
            # Get stock quote
            stock_quote = self.client.get_stock_quote(symbol)
            spot_price = float(stock_quote.get('last_price', 0))

            # Get option chain
            option_df = self.client.get_option_chain_by_date(symbol, expiry_date)

            if not option_df.empty:
                # Calculate weighted averages
                result = OICalculator.calculate_weighted_averages(option_df, spot_price)

                # Calculate Gap
                gap = 0
                if result.all_wgt_avg != 0:
                    gap = ((spot_price - result.all_wgt_avg) / result.all_wgt_avg) * 100

                return FetchResult(
                    success=True,
                    data={
                        '股票代码': symbol,
                        '行权日': expiry_date,
                        'Spot': round(spot_price, 2),
                        'All WgtAvg': result.all_wgt_avg,
                        'Call WgtAvg': result.call_wgt_avg,
                        'Put WgtAvg': result.put_wgt_avg,
                        'Gap': round(gap, 2),
                    },
                    status="成功"
                )
            else:
                return FetchResult(
                    success=False,
                    data={'股票代码': symbol, '行权日': expiry_date, 'Spot': round(spot_price, 2)},
                    status="无期权数据"
                )
        except Exception as e:
            error_msg = str(e)
            if "Too many" in error_msg:
                return FetchResult(False, None, error_msg, "API限流")
            else:
                return FetchResult(False, None, error_msg, "错误")

    def fetch_oi_data_for_symbols(
        self,
        symbols: List[str],
        expiry_date: str,
        delay: float = 2,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> pd.DataFrame:
        """Fetch OI data for multiple symbols with rate limiting"""
        results = []
        error_messages = []

        for i, symbol in enumerate(symbols):
            if progress_callback:
                progress_callback(i, len(symbols))

            result = self.fetch_oi_data_for_symbol(symbol, expiry_date)

            if result.data:
                result.data['状态'] = result.status
                results.append(result.data)

            if not result.success and result.error_message:
                error_messages.append(f"{symbol}: {result.error_message}")

            # Add delay to avoid rate limiting
            if i < len(symbols) - 1:
                time.sleep(delay)

        if progress_callback:
            progress_callback(len(symbols), len(symbols))

        # Show error messages if any
        if error_messages:
            with st.expander("⚠️ 部分股票获取失败"):
                for msg in error_messages:
                    st.warning(msg)

        return pd.DataFrame(results)

    def fetch_trend_data(
        self,
        symbol: str,
        expiry_dates: List[str],
        delay: float = 2,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict[str, Any]]:
        """Fetch trend data for multiple expiry dates"""
        trend_data = []

        for i, expiry_date in enumerate(expiry_dates):
            if progress_callback:
                progress_callback(i, len(expiry_dates))

            try:
                # Get stock quote
                stock_quote = self.client.get_stock_quote(symbol)
                spot_price = float(stock_quote.get('last_price', 0))

                # Add delay to avoid rate limiting
                if i > 0:
                    time.sleep(delay)

                # Get option chain
                option_df = self.client.get_option_chain_by_date(symbol, expiry_date)

                if not option_df.empty:
                    # Calculate weighted averages
                    result = OICalculator.calculate_weighted_averages(option_df, spot_price)

                    trend_data.append({
                        'expiry_date': expiry_date,
                        'call_wgt_avg': result.call_wgt_avg,
                        'put_wgt_avg': result.put_wgt_avg,
                        'all_wgt_avg': result.all_wgt_avg,
                        'spot_price': spot_price
                    })
            except Exception as e:
                error_msg = str(e)
                if "Too many" in error_msg:
                    st.warning(f"{expiry_date}: API请求过于频繁，请稍后再试")
                else:
                    st.warning(f"{expiry_date}: 获取数据失败 - {error_msg}")

        if progress_callback:
            progress_callback(len(expiry_dates), len(expiry_dates))

        return trend_data
