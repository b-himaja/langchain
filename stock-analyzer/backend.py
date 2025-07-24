import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain import hub
from tools.openbb_stock_tools import (
    get_stock_summary,
    get_stock_history,
    get_stock_news,
    get_stock_price,
    get_company_name_from_ticker
)

# 1. Initialize LLM (Gemini 2.5 Flash)
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.3,
    google_api_key=os.environ["GOOGLE_API_KEY"],
    streaming=True
)

# 2. Define tools
tools = [
    get_stock_summary,
    get_stock_history,
    get_stock_news,
    get_stock_price,
    get_company_name_from_ticker
]

# 3. Load default OpenAI tools agent prompt
prompt = hub.pull("hwchase17/openai-tools-agent")

# 4. Create agent and wrap it in an executor
agent = create_openai_tools_agent(
    llm=llm,
    tools=tools,
    prompt=prompt
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    return_intermediate_steps=False
)
