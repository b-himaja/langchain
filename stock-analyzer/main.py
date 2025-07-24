# # # # stock_bot_gemini.py

# # import os
# # from dotenv import load_dotenv
# # load_dotenv()
# # # from langchain.agents import initialize_agent, AgentType
# # # from langchain_community.utilities.polygon import PolygonAPIWrapper
# # # from langchain_community.tools.polygon.aggregates import PolygonAggregates
# # # from langchain_community.tools.polygon.last_quote import PolygonLastQuote
# # # from langchain_community.tools.polygon.ticker_news import PolygonTickerNews
# # # from langchain_google_genai import ChatGoogleGenerativeAI
# # # from langchain_ollama import ChatOllama
# # # from langchain.memory import ConversationBufferMemory
# # # from langchain.prompts import PromptTemplate

# # # # Load your API keys
# # # polygon_key = os.environ["POLYGON_API_KEY"]
# # # google_key = os.environ["GOOGLE_API_KEY"]

# # # # Create a shared Polygon API wrapper
# # # api = PolygonAPIWrapper(polygon_api_key=polygon_key)

# # # # Initialize tools
# # # agg_tool = PolygonAggregates(api_wrapper=api)
# # # quote_tool = PolygonLastQuote(api_wrapper=api)
# # # news_tool = PolygonTickerNews(api_wrapper=api)

# # # tools = [quote_tool, agg_tool, news_tool]

# # # # Setup Gemini LLM
# # # llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
# # # llm1 = ChatOllama(model="llama2", temperature=0)
# # # # Add conversation memory
# # # extraction_prompt = PromptTemplate.from_template("""
# # # You are an AI assistant. From the following user question, extract:
# # # - The stock ticker symbol (if mentioned)
# # # - Whether they want latest price (yes/no)
# # # - Whether they want historical prices (yes/no)
# # # - Whether they want news (yes/no)
# # # - If historical prices, extract start and end date in YYYY-MM-DD format.

# # # Always return the answer in exactly this format:

# # # TICKER=XYZ
# # # PRICE=yes|no
# # # HISTORICAL=yes|no
# # # FROM=YYYY-MM-DD
# # # TO=YYYY-MM-DD
# # # NEWS=yes|no

# # # User Question:
# # # {query}
# # # """)

# # # extract_chain = extraction_prompt | llm

# # import os
# # import re
# # import json
# # from datetime import datetime, timezone
# # from langchain_google_genai import ChatGoogleGenerativeAI
# # from langchain.prompts import PromptTemplate
# # from langchain.chains import LLMChain

# # # ------------------------------------------------
# # # Utility: Clean triple-backtick JSON from LLM
# # # ------------------------------------------------

# # def clean_json_string(s: str) -> str:
# #     """
# #     Removes triple backticks and extra markdown formatting from LLM output.
# #     """
# #     # Remove ```json ... ```
# #     s = re.sub(r"^```json\s*", "", s, flags=re.IGNORECASE | re.MULTILINE)
# #     s = re.sub(r"^```", "", s, flags=re.MULTILINE)
# #     s = re.sub(r"```$", "", s, flags=re.MULTILINE)
# #     return s.strip()


# # # ------------------------------------------------
# # # Polygon Aggregates Wrapper
# # # ------------------------------------------------

# # def polygon_agg_wrapper(input_str: str) -> str:
# #     """
# #     Expects input like:
# #         AAPL,2024-01-01,2024-01-10
# #     """
# #     ticker, from_date, to_date = input_str.split(",")

# #     from langchain_community.utilities.polygon import PolygonAPIWrapper
# #     from langchain_community.tools.polygon.aggregates import PolygonAggregates

# #     polygon_api = PolygonAPIWrapper(
# #         polygon_api_key=os.environ["POLYGON_API_KEY"]
# #     )

# #     agg_tool = PolygonAggregates(api_wrapper=polygon_api)

# #     result = agg_tool.run({
# #         "ticker": ticker,
# #         "from_date": from_date,
# #         "to_date": to_date,
# #         "timespan_multiplier": 1,
# #         "timespan": "day",
# #         "limit": 50,
# #     })

# #     # Parse result if JSON string
# #     if isinstance(result, str):
# #         try:
# #             result = json.loads(result)
# #         except json.JSONDecodeError:
# #             return result

# #     if isinstance(result, dict) and "results" in result:
# #         bars = result["results"]
# #     elif isinstance(result, list):
# #         bars = result
# #     else:
# #         return str(result)

# #     if not bars:
# #         return "No data found."

# #     rows = []
# #     rows.append("Date        Open     High     Low      Close    Volume")
# #     rows.append("--------------------------------------------------------------")
# #     for r in bars:
# #         dt = datetime.fromtimestamp(r["t"] / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
# #         row = f"{dt:<11} {r['o']:<8.2f} {r['h']:<8.2f} {r['l']:<8.2f} {r['c']:<8.2f} {int(r['v']):,}"
# #         rows.append(row)

# #     return "\n".join(rows)


# # # ------------------------------------------------
# # # Polygon Ticker News Wrapper
# # # ------------------------------------------------
# # from datetime import datetime

# # def polygon_ticker_news_wrapper(input_str: str) -> str:
# #     """
# #     Calls the Polygon Ticker News tool and returns a human-friendly formatted string.
# #     """
# #     ticker = input_str.strip()

# #     from langchain_community.utilities.polygon import PolygonAPIWrapper
# #     from langchain_community.tools.polygon.ticker_news import PolygonTickerNews

# #     polygon_api = PolygonAPIWrapper(
# #         polygon_api_key=os.environ["POLYGON_API_KEY"]
# #     )

# #     news_tool = PolygonTickerNews(api_wrapper=polygon_api)

# #     result = news_tool.run(ticker)

# #     # If result is already a plain string (e.g. "No news found.")
# #     if isinstance(result, str):
# #         # Try to parse JSON if it's a JSON string
# #         try:
# #             result_data = json.loads(result)
# #         except json.JSONDecodeError:
# #             return result.strip()  # it's plain text

# #     else:
# #         # It's likely a dict or list already
# #         result_data = result

# #     # If it's a dict with "results"
# #     if isinstance(result_data, dict) and "results" in result_data:
# #         articles = result_data["results"]
# #     elif isinstance(result_data, list):
# #         articles = result_data
# #     else:
# #         return f"Unexpected result type: {type(result_data)}"

# #     if not articles:
# #         return f"No news found for {ticker}."

# #     formatted_articles = []
# #     for article in articles:
# #         headline = article.get("headline", "")
# #         url = article.get("article_url", "")
# #         author = article.get("author", "Unknown Author")
# #         pub_date = article.get("published_utc", "")
# #         description = article.get("description", "")
# #         tickers = ", ".join(article.get("tickers", []))
# #         keywords = ", ".join(article.get("keywords", []))
        
# #         if pub_date:
# #             dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
# #             date_str = dt.strftime("%Y-%m-%d %H:%M")
# #         else:
# #             date_str = "N/A"

# #         insights = ""
# #         for insight in article.get("insights", []):
# #             insights += (
# #                 f"  - {insight.get('ticker', '')}: {insight.get('sentiment', '')}\n"
# #                 f"    Reason: {insight.get('sentiment_reasoning', '')}\n"
# #             )

# #         text = (
# #             f"📰 **{headline}**\n"
# #             f"Author: {author}\n"
# #             f"Published: {date_str}\n"
# #             f"URL: {url}\n"
# #             f"Tickers: {tickers}\n"
# #             f"Keywords: {keywords}\n"
# #             f"Description: {description}\n"
# #         )
# #         if insights:
# #             text += f"Insights:\n{insights}"

# #         formatted_articles.append(text)

# #     return "\n\n".join(formatted_articles)




# # # ------------------------------------------------
# # # Gemini LLM
# # # ------------------------------------------------

# # llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

# # # ------------------------------------------------
# # # Tool Extraction Prompt
# # # ------------------------------------------------

# # prompt = PromptTemplate.from_template("""
# # You are an AI agent deciding which Polygon tools to call.

# # Available tools:
# # - PolygonAggregates → for daily price history, can be used to get latest prices of stock by looking at the previous day price. Needs INPUT_STRING formatted like: "TICKER,FROM_DATE,TO_DATE"
# # - PolygonTickerNews → for recent news about a ticker. Needs INPUT_STRING like: "TICKER"

# # From the user's question below, extract all tools that should be called.

# # Return a JSON array like:
# # [
# #   {{"TOOL_NAME": "...", "INPUT_STRING": "..."}},
# #   ...
# # ]

# # User question:
# # {query}
# # """)

# # extract_chain = prompt | llm

# # # ------------------------------------------------
# # # Tool Dispatch Function
# # # ------------------------------------------------

# # def run_tools_from_query(user_query: str) -> str:
# #     """
# #     Runs all required tools based on a user's question.
# #     """

# #     # Run Gemini extraction
# #     extraction_text = extract_chain.invoke({"query": user_query})
# #     print(f"🔎 Gemini extraction:\n{extraction_text}\n")

# #     # Clean JSON string if wrapped in markdown
# #     cleaned = clean_json_string(extraction_text.content)

# #     # Parse JSON safely
# #     try:
# #         tool_calls = json.loads(cleaned)
# #     except Exception as e:
# #         return f"❌ Failed to parse Gemini response: {e}\nRaw output:\n{extraction_text}"

# #     all_outputs = []

# #     for call in tool_calls:
# #         tool_name = call.get("TOOL_NAME")
# #         input_str = call.get("INPUT_STRING")

# #         if tool_name == "PolygonAggregates":
# #             result = polygon_agg_wrapper(input_str)
# #         elif tool_name == "PolygonTickerNews":
# #             result = polygon_ticker_news_wrapper(input_str)
# #         else:
# #             result = f"Unknown tool: {tool_name}"

# #         all_outputs.append(f"→ **{tool_name}**\n{result}")

# #     return "\n\n".join(all_outputs)


# # # ------------------------------------------------
# # # Chatbot Loop
# # # ------------------------------------------------

# # def chat_loop():
# #     print("🔮 Gemini Polygon Stock Bot")
# #     print("Type 'exit' to quit.\n")

# #     while True:
# #         user_input = input("You: ")

# #         if user_input.lower() in ["exit", "quit"]:
# #             print("Goodbye!")
# #             break

# #         try:
# #             result = run_tools_from_query(user_input)
# #             print(f"Bot:\n{result}\n")
# #         except Exception as e:
# #             print(f"Error: {e}\n")


# # # ------------------------------------------------
# # # Run if main
# # # ------------------------------------------------

# # if __name__ == "__main__":
# #     chat_loop()


# # stock_advisor_openbb.py

# import os
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_community.llms import Ollama
# from langchain.agents import AgentExecutor, create_openai_tools_agent
# from langchain import hub

# # Import tools from OpenBB wrapper
# from tools.openbb import (
#     get_stock_summary,
#     get_stock_history,
#     get_technical_indicators
# )

# # Pick your LLM
# llm = ChatGoogleGenerativeAI(
#     model="gemini-2.5-flash",
#     temperature=0.3,
#     google_api_key=os.environ.get("GOOGLE_API_KEY")
# )

# # Or Ollama:
# # llm = Ollama(model="llama3")

# tools = [
#     get_stock_summary,
#     get_stock_history,
#     get_technical_indicators
# ]

# prompt = hub.pull("hwchase17/openai-tools-agent")

# agent = create_openai_tools_agent(
#     llm=llm,
#     tools=tools,
#     prompt=prompt
# )

# agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# if __name__ == "__main__":
#     print("📈 LangChain Stock Advisor (OpenBB Edition)")
#     while True:
#         user_input = input("Ask about a stock (or 'exit'): ")
#         if user_input.lower() == "exit":
#             break
#         result = agent_executor.invoke({"input": user_input})
#         print(result["output"])


# stock_advisor_openbb.py

import os
from openbb import obb


from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_community.llms import Ollama
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain import hub

# Import tools from OpenBB wrapper
from tools.openbb_stock_tools import (
    get_stock_summary,
    get_stock_history,
    get_stock_news,
    get_stock_price,
    get_company_name_from_ticker
)

# Pick your LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.3,
    google_api_key=os.environ.get("GOOGLE_API_KEY")
)

# Or Ollama:
# llm = Ollama(model="llama3")

tools = [
    get_stock_summary,
    get_stock_history,
    get_stock_news,
    get_stock_price,
    get_company_name_from_ticker

]

prompt = hub.pull("hwchase17/openai-tools-agent")

agent = create_openai_tools_agent(
    llm=llm,
    tools=tools,
    prompt=prompt
)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

if __name__ == "__main__":
    print("📈 LangChain Stock Advisor (OpenBB Edition)")
    while True:
        user_input = input("Ask about a stock (or 'exit'): ")
        if user_input.lower() == "exit":
            break
        result = agent_executor.invoke({"input": user_input})
        print(result["output"])
