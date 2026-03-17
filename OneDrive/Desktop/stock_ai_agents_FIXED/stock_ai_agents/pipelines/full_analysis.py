from dataclasses import dataclass
from typing import Dict, List, Optional

from interfaces.agent import AgentInput, AgentOutput, IAgent
from interfaces.data_provider import IDataProvider
from interfaces.output_handler import IOutputHandler


@dataclass
class AnalysisResult:
    ticker: str
    success: bool
    outputs: Dict[str, AgentOutput]
    error: Optional[str] = None


class FullAnalysisPipeline:
    def __init__(
        self,
        data_providers: List[IDataProvider],
        agents: List[IAgent],
        output_handler: Optional[IOutputHandler],
    ):
        self.data_providers = data_providers
        self.agents = agents
        self.output_handler = output_handler

    async def run(self, ticker: str, question: str = "Technical outlook") -> AnalysisResult:
        try:
            price_data = None
            technical_data = None
            news_data = []

            for provider in self.data_providers:
                provider_name = provider.__class__.__name__
                print(f"Trying {provider_name}...")

                if price_data is None:
                    try:
                        price_data = provider.get_price(ticker)
                        if price_data:
                            print(f"[OK] Got price from {provider_name}")
                    except Exception as e:
                        print(f"[WARN] Price failed from {provider_name}: {e}")

                if technical_data is None:
                    try:
                        technical_data = provider.get_technicals(ticker)
                        if technical_data:
                            print(f"[OK] Got technicals from {provider_name}")
                    except Exception as e:
                        print(f"[WARN] Technicals failed from {provider_name}: {e}")

                try:
                    provider_news = provider.get_news(ticker, max_items=5)
                    if provider_news:
                        news_data.extend(provider_news)
                        print(f"[OK] Got {len(provider_news)} news items from {provider_name}")
                except Exception as e:
                    print(f"[WARN] News failed from {provider_name}: {e}")

            if not technical_data:
                error_msg = "Could not fetch technical data from any source"
                print(f"ERROR: {error_msg}")
                return AnalysisResult(ticker=ticker, success=False, outputs={}, error=error_msg)

            if not self.agents:
                error_msg = "No agents selected for analysis"
                print(f"ERROR: {error_msg}")
                return AnalysisResult(ticker=ticker, success=False, outputs={}, error=error_msg)

            agent_input = AgentInput(
                ticker=ticker,
                question=question,
                price_data=price_data,
                technical_data=technical_data,
                news_data=news_data,
                context={},
            )

            outputs: Dict[str, AgentOutput] = {}
            for agent in self.agents:
                print(f"[{agent.name}] Processing...")
                try:
                    output = await agent.execute(agent_input)
                    outputs[agent.name] = output
                    agent_input.context[f"{agent.name.lower()}_analysis"] = output.content
                    status = "[OK]" if output.success else "[WARN]"
                    print(f"{status} {agent.name} complete")
                except Exception as e:
                    print(f"[WARN] {agent.name} failed: {e}")
                    outputs[agent.name] = AgentOutput(
                        agent_name=agent.name,
                        content=f"Error: {str(e)}",
                        confidence=0,
                        metadata={},
                        success=False,
                    )

            success = any(output.success for output in outputs.values())
            error = None if success else "All agents failed to produce an analysis"
            return AnalysisResult(ticker=ticker, success=success, outputs=outputs, error=error)

        except Exception as e:
            error_msg = f"Pipeline error: {str(e)}"
            print(f"ERROR: {error_msg}")
            import traceback

            traceback.print_exc()
            return AnalysisResult(ticker=ticker, success=False, outputs={}, error=error_msg)
