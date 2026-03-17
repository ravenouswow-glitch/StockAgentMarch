import asyncio
import os
import sys

import streamlit as st

# Add project root to path so imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="4-Agent Stock AI", page_icon="chart_with_upwards_trend", layout="wide")

st.markdown(
    '<p style="font-size: 2.5rem; color: #1a73e8; font-weight: bold;">4-Agent Stock AI</p>',
    unsafe_allow_html=True,
)

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

with st.sidebar:
    st.title("Settings")
    data_source = st.selectbox(
        "Data Source",
        ["Yahoo Finance", "Google Finance", "Both (Auto-Fallback)"],
        index=1,
    )
    use_chart = st.checkbox("ChartMaster", value=True)
    use_news = st.checkbox("NewsHound", value=True)
    use_signal = st.checkbox("SignalPro", value=True)
    use_director = st.checkbox("Director", value=True)

col1, col2 = st.columns([3, 1])
with col1:
    ticker = st.text_input("Stock Ticker", value="AAPL")
    question = st.text_input("Your Question", value="Technical outlook")
with col2:
    analyze_btn = st.button("Analyze", type="primary", use_container_width=True)

st.markdown("### Quick Select")
cols = st.columns(6)
quick_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "LLOY.L"]
for i, col in enumerate(cols):
    with col:
        if st.button(quick_tickers[i], use_container_width=True):
            ticker = quick_tickers[i]


async def run_analysis_async(ticker, question, data_source, use_chart, use_news, use_signal, use_director):
    from agents.chart_master import ChartMaster
    from agents.director import Director
    from agents.news_hound import NewsHound
    from agents.signal_pro import SignalPro
    from connectors.google_finance import GoogleFinanceConnector
    from connectors.news import NewsConnector
    from connectors.yahoo import YahooConnector
    from pipelines.full_analysis import FullAnalysisPipeline

    if data_source == "Yahoo Finance":
        data_providers = [YahooConnector(), NewsConnector()]
    elif data_source == "Google Finance":
        data_providers = [GoogleFinanceConnector(), NewsConnector()]
    else:
        data_providers = [GoogleFinanceConnector(), YahooConnector(), NewsConnector()]

    agents = []
    if use_chart:
        agents.append(ChartMaster())
    if use_news:
        agents.append(NewsHound())
    if use_signal:
        agents.append(SignalPro())
    if use_director:
        agents.append(Director())

    pipeline = FullAnalysisPipeline(data_providers, agents, None)
    return await pipeline.run(ticker, question)


def run_analysis(ticker, question, data_source, use_chart, use_news, use_signal, use_director):
    coro = run_analysis_async(ticker, question, data_source, use_chart, use_news, use_signal, use_director)
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


if analyze_btn:
    if not any([use_chart, use_news, use_signal, use_director]):
        st.error("Select at least one agent before running an analysis.")
    else:
        with st.spinner("Running analysis. This may take 30-60 seconds."):
            try:
                result = run_analysis(ticker, question, data_source, use_chart, use_news, use_signal, use_director)
                st.session_state.analysis_result = result
            except Exception as e:
                st.error(f"Error: {str(e)}")
                import traceback

                st.code(traceback.format_exc())

if st.session_state.analysis_result:
    result = st.session_state.analysis_result
    if result.success:
        st.success("Analysis complete.")

        if "Director" in result.outputs:
            st.markdown("### Director Recommendation")
            st.info(result.outputs["Director"].content.replace("\n", "\n\n"))

        cols = st.columns(4)
        with cols[0]:
            st.metric("Agents Used", len(result.outputs))
        with cols[1]:
            if "Director" in result.outputs:
                st.metric("Confidence", f"{result.outputs['Director'].confidence}/10")
        with cols[2]:
            st.metric("Data Source", data_source)
        with cols[3]:
            st.metric("Ticker", ticker)

        for agent_name, output in result.outputs.items():
            with st.expander(f"{agent_name} Analysis", expanded=False):
                st.write(output.content)
                st.caption(f"Confidence: {output.confidence}/10")
    else:
        st.error(f"Analysis failed: {result.error}")
        st.info(
            "Try a different data source, switch ticker, or rerun after a short wait if a provider is rate-limiting."
        )

st.divider()
st.markdown(
    "<div style='text-align: center; color: #666;'>Not financial advice | Data may be delayed</div>",
    unsafe_allow_html=True,
)
