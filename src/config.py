import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    LONGPORT_APP_KEY = os.getenv("LONGPORT_APP_KEY")
    LONGPORT_APP_SECRET = os.getenv("LONGPORT_APP_SECRET")
    LONGPORT_ACCESS_TOKEN = os.getenv("LONGPORT_ACCESS_TOKEN")
    LONGPORT_HTTP_URL = os.getenv("LONGPORT_HTTP_URL", "https://openapi.longportapp.com")
    LONGPORT_QUOTE_WS_URL = os.getenv("LONGPORT_QUOTE_WS_URL", "wss://openapi-quote.longportapp.com/v2")
    LONGPORT_TRADE_WS_URL = os.getenv("LONGPORT_TRADE_WS_URL", "wss://openapi-trade.longportapp.com/v2")
