from langgraph.graph import StateGraph, START, END
from agents.state import HedgeFundState
from agents.data_fetcher import fetch_market_data
from agents.analysts import technical_analyst, fundamental_analyst, sentiment_analyst
from agents.portfolio_mgr import portfolio_manager

workflow = StateGraph(HedgeFundState)
workflow.add_node("data_fetcher", fetch_market_data)
workflow.add_node("tech_analyst", technical_analyst)
workflow.add_node("fundamental_analyst", fundamental_analyst)
workflow.add_node("sentiment_analyst", sentiment_analyst)
workflow.add_node("portfolio_boss", portfolio_manager)

workflow.add_edge(START, "data_fetcher")
workflow.add_edge("data_fetcher", "tech_analyst")
workflow.add_edge("data_fetcher", "fundamental_analyst")
workflow.add_edge("data_fetcher", "sentiment_analyst")
workflow.add_edge("tech_analyst", "portfolio_boss")
workflow.add_edge("fundamental_analyst", "portfolio_boss")
workflow.add_edge("sentiment_analyst", "portfolio_boss")
workflow.add_edge("portfolio_boss", END)

app = workflow.compile()