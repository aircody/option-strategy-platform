from typing import Optional
import streamlit as st

from src.longport_client import LongportClient
from src.mock_data import generate_mock_option_chain, get_mock_expiry_dates, get_mock_stock_quote
from src.config import Config


class ClientFactory:
    """Factory for creating API clients"""

    @staticmethod
    def create_longport_client() -> Optional[LongportClient]:
        """Create and connect LongPort client"""
        try:
            client = LongportClient()
            client.connect(
                app_key=Config.LONGPORT_APP_KEY,
                app_secret=Config.LONGPORT_APP_SECRET,
                access_token=Config.LONGPORT_ACCESS_TOKEN
            )
            return client
        except Exception as e:
            st.error(f"连接 LongPort API 失败: {str(e)}")
            return None

    @staticmethod
    def create_mock_client():
        """Create mock client for demonstration"""
        class MockClient:
            def get_expiry_dates(self, symbol):
                return get_mock_expiry_dates()

            def get_option_chain_by_date(self, symbol, expiry_date):
                return generate_mock_option_chain(symbol, expiry_date)

            def get_stock_quote(self, symbol):
                return get_mock_stock_quote(symbol)

        return MockClient()
