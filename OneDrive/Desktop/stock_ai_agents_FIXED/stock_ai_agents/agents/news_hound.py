from interfaces.agent import IAgent, AgentInput, AgentOutput
from datetime import datetime
import re

class NewsHound(IAgent):
    @property
    def name(self) -> str:
        return "NewsHound"
    
    @property
    def model(self) -> str:
        from config import Config
        return Config.MODELS['fast']
    
    def build_prompt(self, agent_input: AgentInput) -> str:
        news = agent_input.news_data
        if not news:
            return f"No news available for {agent_input.ticker}"
        news_text = "\n".join([f"- {n.title} ({n.sentiment})" for n in news[:5]])
        return f"""NewsHound Analysis for {agent_input.ticker}

RECENT NEWS:
{news_text}

QUESTION: {agent_input.question}

FORMAT EXACTLY:
[TIMESTAMP] {datetime.now().strftime("%Y-%m-%d %H:%M UTC")}
[SOURCES] {len(news)} articles
[SUMMARY] One line: overall sentiment + key catalyst
[TABLE]
Date|Source|Headline|Sentiment
{chr(10).join([f"{n.date}|{n.source}|{n.title}|{n.sentiment}" for n in news[:3]])}
[CONFIDENCE] 1-10"""
    
    def parse_response(self, response: str) -> AgentOutput:
        conf_match = re.search(r'\[CONFIDENCE\]\s*(\d+)', response, re.IGNORECASE)
        confidence = int(conf_match.group(1)) if conf_match else 5
        return AgentOutput(
            agent_name=self.name,
            content=response,
            confidence=confidence,
            metadata={'type': 'news'},
            success=True
        )
