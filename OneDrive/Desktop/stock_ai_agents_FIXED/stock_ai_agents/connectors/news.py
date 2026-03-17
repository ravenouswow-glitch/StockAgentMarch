from datetime import datetime
import re
from typing import List, Optional

import requests

from interfaces.data_provider import IDataProvider, NewsItem


class NewsConnector(IDataProvider):
    def __init__(self, max_results: int = 10):
        self.max_results = max_results

    def is_available(self) -> bool:
        return True

    def get_price(self, ticker: str) -> Optional[any]:
        return None

    def get_technicals(self, ticker: str) -> Optional[any]:
        return None

    def get_news(self, ticker: str, max_items: int = 5) -> List[NewsItem]:
        if ticker.endswith(".L"):
            try:
                news = self._fetch_rns_news(ticker, max_items)
                if news:
                    print(f"[OK] Found {len(news)} RNS announcements for {ticker}")
                    return news
            except Exception as e:
                print(f"RNS failed for {ticker}: {e}")

        try:
            news = self._fetch_ddgs_news(ticker, max_items)
            if news:
                print(f"[OK] Found {len(news)} news items via DDGS for {ticker}")
                return news
        except Exception as e:
            print(f"DDGS failed for {ticker}: {e}")

        try:
            news = self._fetch_google_news(ticker, max_items)
            if news:
                print(f"[OK] Found {len(news)} news items via Google News for {ticker}")
                return news
        except Exception as e:
            print(f"Google News failed for {ticker}: {e}")

        print(f"[WARN] No news found for {ticker}")
        return []

    def _fetch_rns_news(self, ticker: str, max_items: int) -> List[NewsItem]:
        try:
            clean_ticker = ticker.replace(".L", "")
            rns_query = f"{clean_ticker} RNS site:rns-pdf.londonstockexchange.com"
            rss_url = f"https://news.google.com/rss/search?q={rns_query}&hl=en-GB&gl=GB&ceid=GB:en"
            response = requests.get(rss_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            if response.status_code != 200:
                return self._fetch_rns_alternative(ticker, max_items)

            items = re.findall(r"<item>(.*?)</item>", response.text, re.DOTALL)
            if not items:
                return self._fetch_rns_alternative(ticker, max_items)

            news_items = []
            for item in items[:max_items]:
                title_match = re.search(r"<title>(.*?)</title>", item)
                link_match = re.search(r"<link>(.*?)</link>", item)
                date_match = re.search(r"<pubDate>(.*?)</pubDate>", item)
                if not title_match:
                    continue

                title = re.sub(r"\s*-\s*RNS.*$", "", title_match.group(1).strip(), flags=re.IGNORECASE)
                link = link_match.group(1).strip() if link_match else ""
                date = date_match.group(1).strip() if date_match else datetime.now().strftime("%Y-%m-%d")
                ann_type = self._classify_rns_announcement(title)
                news_items.append(
                    NewsItem(
                        title=f"[{ann_type}] {title[:80]}",
                        source="RNS/LSE",
                        date=date,
                        url=link,
                        sentiment=self._analyze_rns_sentiment(title),
                    )
                )
            return news_items
        except Exception:
            return []

    def _fetch_rns_alternative(self, ticker: str, max_items: int) -> List[NewsItem]:
        try:
            clean_ticker = ticker.replace(".L", "")
            company_names = {"LLOY": "Lloyds Banking Group", "BARC": "Barclays", "HSBA": "HSBC Holdings"}
            company_name = company_names.get(clean_ticker, clean_ticker)
            query = f"{company_name} RNS announcement regulatory news"
            rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-GB&gl=GB&ceid=GB:en"
            response = requests.get(rss_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            if response.status_code != 200:
                return []

            items = re.findall(r"<item>(.*?)</item>", response.text, re.DOTALL)
            news_items = []
            for item in items[:max_items]:
                title_match = re.search(r"<title>(.*?)</title>", item)
                link_match = re.search(r"<link>(.*?)</link>", item)
                date_match = re.search(r"<pubDate>(.*?)</pubDate>", item)
                if not title_match:
                    continue

                title = title_match.group(1).strip()[:100]
                link = link_match.group(1).strip() if link_match else ""
                date = date_match.group(1).strip() if date_match else datetime.now().strftime("%Y-%m-%d")
                news_items.append(
                    NewsItem(
                        title=f"[RNS] {title}",
                        source="RNS/LSE",
                        date=date,
                        url=link,
                        sentiment=self._analyze_rns_sentiment(title),
                    )
                )
            return news_items
        except Exception:
            return []

    def _classify_rns_announcement(self, title: str) -> str:
        title_lower = title.lower()
        if any(w in title_lower for w in ["result", "earnings", "trading update", "financial"]):
            return "FINANCIAL"
        if any(w in title_lower for w in ["dividend", "distribution"]):
            return "DIVIDEND"
        if any(w in title_lower for w in ["director", "dealings", "insider"]):
            return "DIRECTOR DEALINGS"
        if any(w in title_lower for w in ["acquisition", "merger", "takeover"]):
            return "M&A"
        if any(w in title_lower for w in ["buyback", "own shares", "purchase"]):
            return "SHARE BUYBACK"
        return "REGULATORY"

    def _analyze_rns_sentiment(self, title: str) -> str:
        title_lower = title.lower()
        positive = ["beat", "growth", "increase", "rise", "profit", "gain", "upgrade", "strong", "dividend increase", "buyback"]
        negative = ["miss", "loss", "decline", "drop", "fall", "warning", "downgrade", "weak", "crisis", "lawsuit"]
        pos_count = sum(1 for w in positive if w in title_lower)
        neg_count = sum(1 for w in negative if w in title_lower)
        if pos_count > neg_count:
            return "Bullish"
        if neg_count > pos_count:
            return "Bearish"
        return "Neutral"

    def _fetch_ddgs_news(self, ticker: str, max_items: int) -> List[NewsItem]:
        try:
            try:
                from ddgs import DDGS
            except ImportError:
                try:
                    from duckduckgo_search import DDGS
                except ImportError:
                    return []

            with DDGS() as ddgs:
                query = self._build_search_query(ticker)
                results = list(ddgs.text(query, max_results=self.max_results))
                if not results:
                    return []

                news_items = []
                for item in results[:max_items]:
                    title = item.get("title", "")[:100]
                    href = item.get("href", "")
                    body = item.get("body", "")
                    source = self._extract_source(href)
                    sentiment = self._analyze_sentiment(body)
                    news_items.append(
                        NewsItem(
                            title=title,
                            source=source,
                            date=datetime.now().strftime("%Y-%m-%d"),
                            url=href,
                            sentiment=sentiment,
                        )
                    )
                return news_items
        except Exception:
            return []

    def _fetch_google_news(self, ticker: str, max_items: int) -> List[NewsItem]:
        try:
            query = self._build_search_query(ticker)
            rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
            response = requests.get(rss_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            if response.status_code != 200:
                return []

            items = re.findall(r"<item>(.*?)</item>", response.text, re.DOTALL)
            if not items:
                return []

            exclude_keywords = self._get_exclude_keywords(ticker)
            include_keywords = self._get_include_keywords(ticker)
            news_items = []
            for item in items[: max_items * 3]:
                title_match = re.search(r"<title>(.*?)</title>", item)
                link_match = re.search(r"<link>(.*?)</link>", item)
                date_match = re.search(r"<pubDate>(.*?)</pubDate>", item)
                if not title_match:
                    continue

                title = title_match.group(1).strip()
                title_lower = title.lower()
                if any(kw in title_lower for kw in exclude_keywords):
                    continue
                if include_keywords and not any(kw in title_lower for kw in include_keywords):
                    continue

                link = link_match.group(1).strip() if link_match else ""
                date = date_match.group(1).strip() if date_match else datetime.now().strftime("%Y-%m-%d")
                source = self._extract_source(link)
                news_items.append(
                    NewsItem(
                        title=title[:100],
                        source=source,
                        date=date,
                        url=link,
                        sentiment=self._analyze_sentiment(title),
                    )
                )
                if len(news_items) >= max_items:
                    break
            return news_items
        except Exception:
            return []

    def _build_search_query(self, ticker: str) -> str:
        ticker_queries = {
            "LLOY.L": "Lloyds Banking Group stock",
            "BARC.L": "Barclays bank stock",
            "HSBA.L": "HSBC Holdings stock",
        }
        if ticker in ticker_queries:
            return ticker_queries[ticker]
        if ticker.endswith(".L"):
            return f"{ticker.replace('.L', '')} London Stock Exchange stock"
        return f"{ticker} stock news"

    def _get_exclude_keywords(self, ticker: str) -> List[str]:
        exclude_map = {"LLOY.L": ["hapag-lloyd", "jamie lloyd", "lloyd webber", "shipping", "theater"]}
        return exclude_map.get(ticker, [])

    def _get_include_keywords(self, ticker: str) -> List[str]:
        financial_tickers = ["LLOY.L", "BARC.L", "HSBA.L"]
        if ticker in financial_tickers:
            return ["bank", "banking", "shares", "stock", "earnings", "profit", "dividend"]
        return []

    def _extract_source(self, url: str) -> str:
        if not url or "/" not in url:
            return "Unknown"
        try:
            domain = url.split("/")[2].lower().replace("www.", "")
            return domain.replace(".com", "").replace(".co.uk", "").title()
        except Exception:
            return "News"

    def _analyze_sentiment(self, text: str) -> str:
        if not text:
            return "Neutral"
        text = text.lower()
        bullish = sum(1 for w in ["beat", "upgrade", "growth", "gain", "profit", "strong"] if w in text)
        bearish = sum(1 for w in ["miss", "downgrade", "loss", "warning", "decline", "weak"] if w in text)
        if bullish > bearish:
            return "Bullish"
        if bearish > bullish:
            return "Bearish"
        return "Neutral"
