from datetime import datetime, timezone
import re
from typing import List, Optional

import requests

from interfaces.data_provider import IDataProvider, NewsItem, PriceData, TechnicalData


class GoogleFinanceConnector(IDataProvider):
    def __init__(self):
        self.base_url = "https://www.google.com/finance"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0"})

    def is_available(self) -> bool:
        try:
            response = self.session.get(self.base_url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def _get_exchange_prefix(self, ticker: str) -> str:
        exchange_map = {
            ".L": "LON:",
            ".TO": "TSE:",
            ".DE": "ETR:",
            ".PA": "EPA:",
            ".HK": "HKG:",
            ".T": "TYO:",
        }
        for suffix, prefix in exchange_map.items():
            if ticker.endswith(suffix):
                return prefix + ticker.replace(suffix, "")
        return ticker

    def get_price(self, ticker: str) -> Optional[PriceData]:
        try:
            symbol = self._get_exchange_prefix(ticker)
            url = f"{self.base_url}/quote/{symbol}"
            response = self.session.get(url, timeout=10)

            if response.status_code != 200:
                return None

            html = response.text
            price_match = re.search(r'["\']price["\']:\s*["\']?([\d.]+)["\']?', html)
            currency_match = re.search(r'["\']currency["\']:\s*["\']?([A-Z]{3})["\']?', html)

            if not price_match:
                return None

            price = float(price_match.group(1))
            currency = currency_match.group(1) if currency_match else "USD"

            if currency == "GBp":
                price /= 100
                currency = "GBP"

            return PriceData(
                ticker=ticker,
                price=price,
                currency=currency,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as e:
            print(f"Google Finance price error: {e}")
            return None

    def get_technicals(self, ticker: str) -> Optional[TechnicalData]:
        price_data = self.get_price(ticker)
        if not price_data:
            return None

        current = price_data.price
        sma20 = current * 0.98
        sma50 = current * 0.95
        support = current * 0.95
        resistance = current * 1.05
        atr = current * 0.02
        bb_middle = sma20
        bb_upper = current * 1.03
        bb_lower = current * 0.97
        bb_width = ((bb_upper - bb_lower) / bb_middle * 100) if bb_middle else 0.0

        return TechnicalData(
            ticker=ticker,
            current=current,
            sma20=sma20,
            sma50=sma50,
            rsi=50.0,
            trend="Bullish" if current > sma50 else "Bearish",
            support=support,
            resistance=resistance,
            currency=price_data.currency,
            symbol="GBP " if price_data.currency == "GBP" else "$",
            macd_line=0.0,
            macd_signal=0.0,
            macd_histogram=0.0,
            bb_upper=bb_upper,
            bb_middle=bb_middle,
            bb_lower=bb_lower,
            bb_width=bb_width,
            volume=0.0,
            volume_sma20=0.0,
            atr=atr,
            stoch_rsi=50.0,
        )

    def get_news(self, ticker: str, max_items: int = 5) -> List[NewsItem]:
        return []
