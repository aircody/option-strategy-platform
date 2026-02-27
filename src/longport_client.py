from longport.openapi import QuoteContext, Config
from typing import Optional, List, Dict, Any
import pandas as pd
from datetime import datetime, date

class LongportClient:
    _instance: Optional['LongportClient'] = None
    _ctx: Optional[QuoteContext] = None
    _has_option_permission: bool = True
    _last_error: Optional[str] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def connect(self, app_key: str, app_secret: str, access_token: str):
        """Connect to LongPort API"""
        config = Config(
            app_key=app_key,
            app_secret=app_secret,
            access_token=access_token
        )
        self._ctx = QuoteContext(config)
        self._last_error = None
        return self._ctx
    
    @property
    def ctx(self) -> QuoteContext:
        if self._ctx is None:
            raise RuntimeError("LongPort client not connected. Call connect() first.")
        return self._ctx
    
    @property
    def has_option_permission(self) -> bool:
        return self._has_option_permission
    
    @property
    def last_error(self) -> Optional[str]:
        return self._last_error
    
    def _format_symbol(self, symbol: str) -> str:
        """Format symbol with market suffix"""
        symbol = symbol.upper().strip()
        if '.' not in symbol:
            # Default to US market for common US stocks
            symbol = f"{symbol}.US"
        return symbol
    
    def _parse_date(self, date_str: str) -> date:
        """Parse date string to date object"""
        if isinstance(date_str, date) and not isinstance(date_str, datetime):
            return date_str
        if isinstance(date_str, datetime):
            return date_str.date()
        # Parse string format "YYYY-MM-DD"
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    
    def get_expiry_dates(self, symbol: str) -> List[str]:
        """Get all available expiry dates for a symbol (today and future only)"""
        symbol = self._format_symbol(symbol)
        try:
            expiry_dates = self.ctx.option_chain_expiry_date_list(symbol)
            self._has_option_permission = True
            self._last_error = None
            
            # Get today's date
            today = date.today()
            
            # Filter dates: only keep today and future dates
            future_dates = []
            for d in expiry_dates:
                # Convert to date object if it's a string
                if isinstance(d, str):
                    d = datetime.strptime(d, "%Y-%m-%d").date()
                
                # Only include today and future dates
                if d >= today:
                    future_dates.append(str(d))
            
            return future_dates
        except Exception as e:
            error_msg = str(e)
            self._last_error = error_msg
            print(f"Error getting expiry dates: {error_msg}")
            
            # Check if it's a permission issue
            if "do not have access" in error_msg.lower() or "purchase" in error_msg.lower():
                self._has_option_permission = False
            
            return []
    
    def get_option_chain(self, symbol: str, expiry_date: Optional[str] = None) -> pd.DataFrame:
        """
        Get option chain data for a symbol
        
        Args:
            symbol: Stock symbol (e.g., "NVDA" or "NVDA.US")
            expiry_date: Option expiry date in format "YYYY-MM-DD"
        
        Returns:
            DataFrame with option chain data
        """
        symbol = self._format_symbol(symbol)
        
        # Get expiry dates if not provided
        if expiry_date is None:
            expiry_dates = self.get_expiry_dates(symbol)
            if not expiry_dates:
                return pd.DataFrame()
            expiry_date = expiry_dates[0]
        
        # Convert expiry_date string to date object
        try:
            expiry_date_obj = self._parse_date(expiry_date)
        except Exception as e:
            self._last_error = f"Invalid date format: {e}"
            print(f"Error parsing date: {e}")
            return pd.DataFrame()
        
        # Get option chain info for the expiry date
        try:
            chain_info = self.ctx.option_chain_info_by_date(symbol, expiry_date_obj)
            self._has_option_permission = True
            self._last_error = None
            print(f"[DEBUG] {symbol} chain_info: {len(chain_info) if chain_info else 0} items")
        except Exception as e:
            error_msg = str(e)
            self._last_error = error_msg
            print(f"[DEBUG] Error getting option chain info for {symbol}: {error_msg}")
            
            if "do not have access" in error_msg.lower() or "purchase" in error_msg.lower():
                self._has_option_permission = False
            
            return pd.DataFrame()
        
        if not chain_info:
            print(f"[DEBUG] {symbol}: chain_info is empty")
            return pd.DataFrame()
        
        # Extract option symbols from chain_info
        # StrikePriceInfo has call_symbol and put_symbol attributes
        option_symbols = []
        for info in chain_info:
            if hasattr(info, 'call_symbol') and info.call_symbol:
                option_symbols.append(info.call_symbol)
            if hasattr(info, 'put_symbol') and info.put_symbol:
                option_symbols.append(info.put_symbol)
            # Also extract strike price if available
        
        if not option_symbols:
            print(f"[DEBUG] {symbol}: No option symbols found in chain info")
            return pd.DataFrame()
        
        print(f"[DEBUG] {symbol}: Found {len(option_symbols)} option symbols")
        
        # Get quotes for all options
        try:
            quotes = self.ctx.option_quote(option_symbols)
        except Exception as e:
            error_msg = str(e)
            self._last_error = error_msg
            print(f"Error getting option quotes: {error_msg}")
            return pd.DataFrame()
        
        # Build DataFrame
        data = []
        for quote in quotes:
            # Determine option type from direction field (enum type)
            # OptionDirection.Call or OptionDirection.Put
            direction = getattr(quote, 'direction', None)
            if direction:
                # Convert enum to string
                direction_str = str(direction)
                if 'Call' in direction_str:
                    option_type = 'CALL'
                elif 'Put' in direction_str:
                    option_type = 'PUT'
                else:
                    # Fallback to symbol parsing
                    option_type = self._get_option_type_from_symbol(quote.symbol)
            else:
                # Fallback to symbol parsing
                option_type = self._get_option_type_from_symbol(quote.symbol)
            
            # Extract strike price if available
            strike = 0
            if hasattr(quote, 'strike_price'):
                strike = quote.strike_price
            
            data.append({
                'symbol': quote.symbol,
                'strike': strike,
                'option_type': option_type,
                'open_interest': getattr(quote, 'open_interest', 0) or 0,
                'volume': getattr(quote, 'volume', 0) or 0,
                'last_price': getattr(quote, 'last_done', 0) or 0,
                'bid': getattr(quote, 'bid', 0) or 0,
                'ask': getattr(quote, 'ask', 0) or 0,
                'implied_volatility': getattr(quote, 'implied_volatility', 0) or 0,
                'delta': getattr(quote, 'delta', 0) or 0,
                'gamma': getattr(quote, 'gamma', 0) or 0,
                'theta': getattr(quote, 'theta', 0) or 0,
                'vega': getattr(quote, 'vega', 0) or 0,
            })
        
        return pd.DataFrame(data)
    
    def _get_option_type_from_symbol(self, symbol: str) -> str:
        """
        Determine option type from symbol.
        Option symbols typically have format: SYMBOL[DATE][C/P][STRIKE]
        e.g., NVDA260307C190000.US or CRCL260306C30000.US
        """
        # Remove the .US suffix if present
        if '.US' in symbol:
            symbol = symbol.replace('.US', '')
        
        # Find the C or P before the strike price
        # Pattern: after 6 digits (date), look for C or P
        import re
        match = re.search(r'\d{6}([CP])', symbol)
        if match:
            return 'CALL' if match.group(1) == 'C' else 'PUT'
        
        # Fallback: check if 'C' appears before any digits at the end
        # This is less reliable but works for most cases
        parts = symbol.split('C')
        if len(parts) > 1:
            # Check if the part after C starts with digits (strike price)
            after_c = parts[-1]
            if after_c and after_c[0].isdigit():
                return 'CALL'
        
        return 'PUT'  # Default to PUT if can't determine
    
    def get_option_chain_by_date(self, symbol: str, expiry_date: str) -> pd.DataFrame:
        """Get option chain for a specific expiry date"""
        return self.get_option_chain(symbol, expiry_date)
    
    def get_stock_quote(self, symbol: str) -> Dict[str, Any]:
        """Get stock quote"""
        symbol = self._format_symbol(symbol)
        
        try:
            quotes = self.ctx.quote([symbol])
            if quotes:
                quote = quotes[0]
                return {
                    'symbol': quote.symbol,
                    'last_price': getattr(quote, 'last_done', 0) or 0,
                    'bid': getattr(quote, 'bid', 0) or 0,
                    'ask': getattr(quote, 'ask', 0) or 0,
                    'volume': getattr(quote, 'volume', 0) or 0,
                }
        except Exception as e:
            error_msg = str(e)
            self._last_error = error_msg
            print(f"Error getting stock quote: {error_msg}")
        
        return {'symbol': symbol, 'last_price': 0, 'bid': 0, 'ask': 0, 'volume': 0}
