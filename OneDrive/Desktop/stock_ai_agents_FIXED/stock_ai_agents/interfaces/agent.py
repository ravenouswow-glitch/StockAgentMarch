from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class AgentInput:
    ticker: str
    question: str
    price_data: Any
    technical_data: Any
    news_data: Any
    context: Dict[str, Any]


@dataclass
class AgentOutput:
    agent_name: str
    content: str
    confidence: int
    metadata: Dict[str, Any]
    success: bool


class IAgent(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def model(self) -> str:
        pass

    @abstractmethod
    def build_prompt(self, input: AgentInput) -> str:
        pass

    @abstractmethod
    def parse_response(self, response: str) -> AgentOutput:
        pass

    async def execute(self, input: AgentInput) -> AgentOutput:
        try:
            from config import Config

            prompt = self.build_prompt(input)
            if Config.has_groq_key():
                response = await self._call_groq(prompt)
            else:
                response = self._build_fallback_response(input)
            return self.parse_response(response)
        except Exception as e:
            return AgentOutput(
                agent_name=self.name,
                content=f"Error: {str(e)}",
                confidence=0,
                metadata={},
                success=False,
            )

    async def _call_groq(self, prompt: str) -> str:
        from groq import AsyncGroq
        from config import Config

        client = AsyncGroq(api_key=Config.GROQ_API_KEY)
        response = await client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1000,
        )
        return response.choices[0].message.content

    def _build_fallback_response(self, input: AgentInput) -> str:
        tech = input.technical_data
        news_items = input.news_data or []
        bullish_news = sum(1 for item in news_items if getattr(item, "sentiment", "").lower() == "bullish")
        bearish_news = sum(1 for item in news_items if getattr(item, "sentiment", "").lower() == "bearish")

        if self.name == "ChartMaster":
            trend = getattr(tech, "trend", "Neutral")
            rsi = getattr(tech, "rsi", 50.0)
            momentum = "Bullish" if rsi > 55 else "Bearish" if rsi < 45 else "Neutral"
            confidence = 7 if trend in {"Bullish", "Bearish"} else 5
            return (
                "[TIMESTAMP] Local fallback\n"
                f"[SUMMARY] {trend} technical bias with {momentum.lower()} momentum\n"
                "[KEY_SIGNALS]\n"
                f"- Trend: {trend}\n"
                f"- Momentum: {momentum}\n"
                f"- RSI: {rsi:.1f}\n"
                "[TRADE_IDEAS]\n"
                f"- Entry Zone: {getattr(tech, 'support', 0):.2f} - {getattr(tech, 'resistance', 0):.2f}\n"
                f"- Stop Loss: {max(getattr(tech, 'support', 0) - getattr(tech, 'atr', 0), 0):.2f}\n"
                f"- Target: {getattr(tech, 'resistance', 0) + getattr(tech, 'atr', 0):.2f}\n"
                f"[CONFIDENCE] {confidence}"
            )

        if self.name == "NewsHound":
            overall = "Bullish" if bullish_news > bearish_news else "Bearish" if bearish_news > bullish_news else "Neutral"
            confidence = 6 if news_items else 3
            rows = "\n".join(
                f"{getattr(item, 'date', 'N/A')}|{getattr(item, 'source', 'Unknown')}|{getattr(item, 'title', 'No headline')}|{getattr(item, 'sentiment', 'Neutral')}"
                for item in news_items[:3]
            ) or "N/A|N/A|No recent headlines found|Neutral"
            return (
                "[TIMESTAMP] Local fallback\n"
                f"[SOURCES] {len(news_items)} articles\n"
                f"[SUMMARY] {overall} news tone based on the latest available headlines\n"
                "[TABLE]\n"
                "Date|Source|Headline|Sentiment\n"
                f"{rows}\n"
                f"[CONFIDENCE] {confidence}"
            )

        if self.name == "SignalPro":
            trend = getattr(tech, "trend", "Neutral")
            signal = "Buy" if trend == "Bullish" and bullish_news >= bearish_news else "Sell" if trend == "Bearish" and bearish_news > bullish_news else "Hold"
            confidence = 7 if signal != "Hold" else 5
            return (
                "[TIMESTAMP] Local fallback\n"
                f"[SUMMARY] {signal} bias from combined technical and news signals\n"
                f"Signal: {signal}\n"
                f"Confidence: {confidence}\n"
                "DONE"
            )

        signal_text = input.context.get("signalpro_analysis", "")
        if "sell" in signal_text.lower():
            answer = "Sell"
        elif "buy" in signal_text.lower():
            answer = "Buy"
        else:
            answer = "Hold"
        confidence = 6 if answer != "Hold" else 5
        return (
            "=== DIRECTOR ANSWER ===\n"
            f"Question: {input.question}\n"
            f"Answer: {answer} based on the current technical trend and recent headline balance\n"
            "Why: This fallback combines price trend, RSI posture, and headline sentiment without external LLM inference.\n"
            f"Confidence: {confidence}/10\n"
            "Data Sources: Yahoo Finance / Google Finance fallback + news connectors\n"
            "Top Risk: No Groq API key configured; recommendation is based on local heuristics.\n"
            "Data Timestamp: Local fallback"
        )
