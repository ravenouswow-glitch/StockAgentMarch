from interfaces.agent import IAgent, AgentInput, AgentOutput
from datetime import datetime
import re

class SignalPro(IAgent):
    @property
    def name(self) -> str:
        return "SignalPro"
    
    @property
    def model(self) -> str:
        from config import Config
        return Config.MODELS['smart']
    
    def build_prompt(self, agent_input: AgentInput) -> str:
        tech = agent_input.technical_data
        chart = agent_input.context.get('chart_analysis', 'N/A')
        news = agent_input.context.get('news_analysis', 'N/A')
        return f"""SignalPro Trading Analysis for {agent_input.ticker}

TECHNICAL DATA:
- Price: {tech.symbol}{tech.current:.2f} {tech.currency}
- Trend: {tech.trend}

CHART ANALYSIS:
{chart[:300] if chart else 'N/A'}

NEWS ANALYSIS:
{news[:300] if news else 'N/A'}

QUESTION: {agent_input.question}

FORMAT:
[TIMESTAMP] {datetime.now().strftime("%Y-%m-%d %H:%M UTC")}
[SUMMARY] One line trade bias
Signal: Buy/Hold/Sell
Confidence: 1-10
DONE"""
    
    def parse_response(self, response: str) -> AgentOutput:
        conf_match = re.search(r'Confidence:\s*(\d+)', response, re.IGNORECASE)
        confidence = int(conf_match.group(1)) if conf_match else 5
        signal = "Hold"
        if "BUY" in response.upper(): signal = "Buy"
        elif "SELL" in response.upper(): signal = "Sell"
        return AgentOutput(agent_name=self.name, content=response, confidence=confidence, metadata={'type': 'signal', 'signal': signal}, success=True)