from abc import ABC, abstractmethod
from typing import Optional, List
from dataclasses import dataclass

@dataclass
class PriceData:
    ticker: str
    price: float
    currency: str
    timestamp: str
    change_pct: Optional[float] = None

@dataclass
class TechnicalData:
    ticker: str
    current: float
    sma20: float
    sma50: float
    rsi: float
    trend: str
    support: float
    resistance: float
    currency: str
    symbol: str
    # Advanced Indicators
    macd_line: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_width: Optional[float] = None
    volume: Optional[float] = None
    volume_sma20: Optional[float] = None
    atr: Optional[float] = None
    stoch_rsi: Optional[float] = None

@dataclass
class NewsItem:
    title: str
    source: str
    date: str
    url: str
    sentiment: str

class IDataProvider(ABC):
    @abstractmethod
    def get_price(self, ticker: str) -> Optional[PriceData]:
        pass
    
    @abstractmethod
    def get_technicals(self, ticker: str) -> Optional[TechnicalData]:
        pass
    
    @abstractmethod
    def get_news(self, ticker: str, max_items: int = 5) -> List[NewsItem]:
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        pass