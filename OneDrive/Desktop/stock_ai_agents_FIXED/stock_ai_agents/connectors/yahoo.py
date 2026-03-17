import time
from datetime import datetime, timezone
from typing import List, Optional

import pandas as pd
import yfinance as yf

from interfaces.data_provider import IDataProvider, NewsItem, PriceData, TechnicalData


class YahooConnector(IDataProvider):
    def __init__(self):
        self._cache = {}
        self._last_check = None

    def is_available(self) -> bool:
        try:
            stock = yf.Ticker("AAPL")
            info = stock.info
            self._last_check = datetime.now()
            return bool(info)
        except Exception as e:
            print(f"Yahoo availability check failed: {e}")
            return False

    def get_price(self, ticker: str) -> Optional[PriceData]:
        try:
            time.sleep(1)
            stock = yf.Ticker(ticker)
            info = stock.info
            df = stock.history(period="1d")

            if df.empty:
                print(f"Yahoo: No data for {ticker}")
                return None

            price = float(df["Close"].iloc[-1])
            currency = info.get("currency", "USD")
            if currency == "GBp":
                price /= 100
                currency = "GBP"

            return PriceData(
                ticker=ticker,
                price=price,
                currency=currency,
                timestamp=datetime.now(timezone.utc).isoformat(),
                change_pct=float(info.get("regularMarketChangePercent", 0)),
            )
        except Exception as e:
            print(f"Yahoo price error for {ticker}: {e}")
            return None

    def get_technicals(self, ticker: str) -> Optional[TechnicalData]:
        try:
            time.sleep(2)
            stock = yf.Ticker(ticker)
            df = stock.history(period="6mo")
            info = stock.info

            if df.empty or len(df) < 50:
                print(f"Yahoo: Insufficient data for {ticker} (got {len(df)} days)")
                return None

            currency = info.get("currency", "USD")

            def convert(value: float) -> float:
                return value / 100 if currency == "GBp" else value

            df["SMA20"] = df["Close"].rolling(20).mean()
            df["SMA50"] = df["Close"].rolling(50).mean()

            delta = df["Close"].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = -delta.where(delta < 0, 0).rolling(14).mean()
            rs = gain / loss
            df["RSI"] = 100 - (100 / (1 + rs))

            exp1 = df["Close"].ewm(span=12, adjust=False).mean()
            exp2 = df["Close"].ewm(span=26, adjust=False).mean()
            df["MACD"] = exp1 - exp2
            df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
            df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]

            df["BB_Middle"] = df["SMA20"]
            bb_std = df["Close"].rolling(20).std()
            df["BB_Upper"] = df["BB_Middle"] + (bb_std * 2)
            df["BB_Lower"] = df["BB_Middle"] - (bb_std * 2)
            df["BB_Width"] = (df["BB_Upper"] - df["BB_Lower"]) / df["BB_Middle"] * 100

            df["Volume_SMA20"] = df["Volume"].rolling(20).mean()

            high_low = df["High"] - df["Low"]
            high_close = (df["High"] - df["Close"].shift()).abs()
            low_close = (df["Low"] - df["Close"].shift()).abs()
            ranges = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            df["ATR"] = ranges.rolling(14).mean()

            rsi_min = df["RSI"].rolling(14).min()
            rsi_max = df["RSI"].rolling(14).max()
            df["Stoch_RSI"] = 100 * (df["RSI"] - rsi_min) / (rsi_max - rsi_min)

            current = convert(float(df["Close"].iloc[-1]))
            sma20 = convert(float(df["SMA20"].iloc[-1]))
            sma50 = convert(float(df["SMA50"].iloc[-1]))
            rsi = float(df["RSI"].iloc[-1])

            macd_line = float(df["MACD"].iloc[-1])
            macd_signal = float(df["MACD_Signal"].iloc[-1])
            macd_hist = float(df["MACD_Hist"].iloc[-1])

            bb_upper = convert(float(df["BB_Upper"].iloc[-1]))
            bb_middle = convert(float(df["BB_Middle"].iloc[-1]))
            bb_lower = convert(float(df["BB_Lower"].iloc[-1]))
            bb_width = float(df["BB_Width"].iloc[-1])

            volume = float(df["Volume"].iloc[-1])
            volume_sma20 = float(df["Volume_SMA20"].iloc[-1])
            atr = convert(float(df["ATR"].iloc[-1]))
            stoch_rsi = float(df["Stoch_RSI"].iloc[-1])

            support = convert(float(df["Low"].tail(20).min()))
            resistance = convert(float(df["High"].tail(20).max()))

            trend_signals = 0
            if current > sma50:
                trend_signals += 1
            if current > sma20:
                trend_signals += 1
            if macd_hist > 0:
                trend_signals += 1
            if rsi > 50:
                trend_signals += 1

            trend = "Bullish" if trend_signals >= 3 else "Bearish" if trend_signals <= 1 else "Neutral"
            display_currency = "GBP" if currency == "GBp" else currency
            symbol = "GBP " if display_currency == "GBP" else "$"

            return TechnicalData(
                ticker=ticker,
                current=current,
                sma20=sma20,
                sma50=sma50,
                rsi=rsi,
                trend=trend,
                support=support,
                resistance=resistance,
                currency=display_currency,
                symbol=symbol,
                macd_line=macd_line,
                macd_signal=macd_signal,
                macd_histogram=macd_hist,
                bb_upper=bb_upper,
                bb_middle=bb_middle,
                bb_lower=bb_lower,
                bb_width=bb_width,
                volume=volume,
                volume_sma20=volume_sma20,
                atr=atr,
                stoch_rsi=stoch_rsi,
            )
        except Exception as e:
            print(f"Yahoo technicals error for {ticker}: {e}")
            import traceback

            traceback.print_exc()
            return None

    def get_news(self, ticker: str, max_items: int = 5) -> List[NewsItem]:
        return []
