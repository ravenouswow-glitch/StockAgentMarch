from datetime import datetime
import re

from interfaces.agent import AgentInput, AgentOutput, IAgent


class ChartMaster(IAgent):
    @property
    def name(self) -> str:
        return "ChartMaster"

    @property
    def model(self) -> str:
        from config import Config

        return Config.MODELS["fast"]

    def build_prompt(self, agent_input: AgentInput) -> str:
        tech = agent_input.technical_data
        if not tech:
            return f"No technical data available for {agent_input.ticker}"

        macd_signal = "Neutral"
        if tech.macd_line is not None and tech.macd_signal is not None and tech.macd_histogram is not None:
            if tech.macd_line > tech.macd_signal and tech.macd_histogram > 0:
                macd_signal = "Bullish Crossover"
            elif tech.macd_line < tech.macd_signal and tech.macd_histogram < 0:
                macd_signal = "Bearish Crossover"
            elif tech.macd_histogram > 0:
                macd_signal = "Bullish Momentum"
            else:
                macd_signal = "Bearish Momentum"

        bb_position = "Middle"
        if tech.bb_upper is not None and tech.bb_lower is not None:
            bb_range = tech.bb_upper - tech.bb_lower
            if tech.current > tech.bb_upper - (bb_range * 0.1):
                bb_position = "Near Upper Band (Overbought)"
            elif tech.current < tech.bb_lower + (bb_range * 0.1):
                bb_position = "Near Lower Band (Oversold)"
            elif bb_range < 5:
                bb_position = "Squeeze (Volatility Breakout Potential)"

        volume_signal = "Average"
        if tech.volume is not None and tech.volume_sma20 not in (None, 0):
            if tech.volume > tech.volume_sma20 * 1.5:
                volume_signal = "High Volume (Strong Conviction)"
            elif tech.volume < tech.volume_sma20 * 0.5:
                volume_signal = "Low Volume (Weak Conviction)"

        stoch_signal = "Neutral"
        if tech.stoch_rsi is not None:
            if tech.stoch_rsi > 80:
                stoch_signal = "Overbought"
            elif tech.stoch_rsi < 20:
                stoch_signal = "Oversold"

        prompt = f"""ChartMaster Technical Analysis for {agent_input.ticker}

=== PRICE ACTION ===
- Current Price: {tech.symbol}{tech.current:.2f} {tech.currency}
- Support: {tech.symbol}{tech.support:.2f}
- Resistance: {tech.symbol}{tech.resistance:.2f}
- Daily Range (ATR): {tech.symbol}{tech.atr:.2f}

=== MOVING AVERAGES ===
- SMA20: {tech.symbol}{tech.sma20:.2f} | Price vs SMA20: {"Above" if tech.current > tech.sma20 else "Below"}
- SMA50: {tech.symbol}{tech.sma50:.2f} | Price vs SMA50: {"Above" if tech.current > tech.sma50 else "Below"}
- Trend: {tech.trend}

=== MOMENTUM INDICATORS ===
- RSI (14): {tech.rsi:.1f} | {"Overbought" if tech.rsi > 70 else "Oversold" if tech.rsi < 30 else "Neutral"}
- Stochastic RSI: {tech.stoch_rsi:.1f} | {stoch_signal}
- MACD Line: {tech.macd_line:.3f} | Signal: {tech.macd_signal:.3f} | Histogram: {tech.macd_histogram:.3f}
- MACD Signal: {macd_signal}

=== VOLATILITY INDICATORS ===
- Bollinger Bands:
  - Upper: {tech.symbol}{tech.bb_upper:.2f}
  - Middle: {tech.symbol}{tech.bb_middle:.2f}
  - Lower: {tech.symbol}{tech.bb_lower:.2f}
  - Width: {tech.bb_width:.1f}% | Position: {bb_position}
- ATR (14): {tech.symbol}{tech.atr:.2f}

=== VOLUME ANALYSIS ===
- Current Volume: {tech.volume:,.0f}
- 20-Day Avg Volume: {tech.volume_sma20:,.0f}
- Volume Signal: {volume_signal}

=== QUESTION ===
{agent_input.question}

=== FORMAT EXACTLY ===
[TIMESTAMP] {datetime.now().strftime("%Y-%m-%d %H:%M UTC")}
[SUMMARY] One-line technical bias with key catalyst
[KEY_SIGNALS]
- Trend: {tech.trend}
- Momentum: {"Bullish" if tech.rsi > 50 and macd_signal.startswith("Bullish") else "Bearish" if tech.rsi < 50 and macd_signal.startswith("Bearish") else "Neutral"}
- Volatility: {"High" if tech.bb_width and tech.bb_width > 15 else "Low" if tech.bb_width and tech.bb_width < 5 else "Normal"}
- Volume: {volume_signal}
[TRADE_IDEAS]
- Entry Zone: {tech.symbol}{max(tech.support, tech.bb_lower if tech.bb_lower else tech.support):.2f} - {tech.symbol}{min(tech.resistance, tech.bb_upper if tech.bb_upper else tech.resistance):.2f}
- Stop Loss: {tech.symbol}{tech.support - tech.atr:.2f}
- Target: {tech.symbol}{tech.resistance + tech.atr:.2f}
[CONFIDENCE] 1-10"""
        return prompt

    def parse_response(self, response: str) -> AgentOutput:
        conf_match = re.search(r"\[CONFIDENCE\]\s*(\d+)", response, re.IGNORECASE)
        confidence = int(conf_match.group(1)) if conf_match else 5
        return AgentOutput(
            agent_name=self.name,
            content=response,
            confidence=confidence,
            metadata={"type": "technical", "indicators": "MACD,BB,RSI,Volume"},
            success=True,
        )
