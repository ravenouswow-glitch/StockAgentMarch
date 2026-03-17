from interfaces.agent import IAgent, AgentInput, AgentOutput
from datetime import datetime
import re

class Director(IAgent):
    @property
    def name(self) -> str:
        return "Director"
    
    @property
    def model(self) -> str:
        from config import Config
        return Config.MODELS['smart']
    
    def build_prompt(self, agent_input: AgentInput) -> str:
        chart = agent_input.context.get('chart_analysis', 'N/A')
        news = agent_input.context.get('news_analysis', 'N/A')
        signal = agent_input.context.get('signal_analysis', 'N/A')
        return f"""Director Final Recommendation for {agent_input.ticker}

CHARTMASTER: {chart[:400] if chart else 'N/A'}
NEWSHOUND: {news[:400] if news else 'N/A'}
SIGNALPRO: {signal[:400] if signal else 'N/A'}

QUESTION: {agent_input.question}

FORMAT EXACTLY:
=== DIRECTOR ANSWER ===
Question: {agent_input.question}
Answer: [Buy/Hold/Sell/Wait + one line reason]
Why: [Brief explanation]
Confidence: [1-10]/10
Data Sources: Yahoo Finance + DuckDuckGo News + Groq AI
Top Risk: [Single biggest risk]
Data Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}"""
    
    def parse_response(self, response: str) -> AgentOutput:
        conf_match = re.search(r'Confidence:\s*(\d+)', response, re.IGNORECASE)
        confidence = int(conf_match.group(1)) if conf_match else 5
        return AgentOutput(agent_name=self.name, content=response, confidence=confidence, metadata={'type': 'final'}, success=True)