import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain import hub
from tools.openbb_stock_tools import (
    get_stock_summary,
    get_stock_history,
    get_stock_news,
    get_stock_price,
    get_company_name_from_ticker,
    get_ticker_from_company_name
)
import os

# Set up the page
st.set_page_config(
    page_title="📈 LangChain Stock Advisor",
    page_icon="📈",
    layout="wide"
)

# Sidebar for settings
with st.sidebar:
    st.title("Settings")
    model_name = st.selectbox(
        "Select Model",
        ["gemini-1.5-pro", "gemini-2.5-flash"],
    )
    temperature = st.slider(
        "Model Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.3,
        step=0.1
    )
    google_api_key = st.text_input(
        "Google API Key",
        type="password",
        value=os.environ.get("GOOGLE_API_KEY", "")
    )
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    This app uses:
    - [OpenBB](https://openbb.co/) for financial data
    - [Google Gemini](https://deepmind.google/technologies/gemini/) as the LLM
    - [LangChain](https://www.langchain.com/) for agent orchestration
    """)

# Initialize the agent
@st.cache_resource
def initialize_agent(api_key, model_name, temperature):
    if not api_key:
        st.error("Please enter a valid Google API key in the sidebar.")
        st.stop()
    
    try:
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            google_api_key=api_key
        )

        tools = [
            get_stock_summary,
            get_stock_history,
            get_stock_news,
            get_stock_price,
            get_company_name_from_ticker,
            get_ticker_from_company_name
        ]

        prompt = hub.pull("hwchase17/openai-tools-agent")
        agent = create_openai_tools_agent(
            llm=llm,
            tools=tools,
            prompt=prompt
        )
        
        return AgentExecutor(agent=agent, tools=tools, verbose=True)
    except Exception as e:
        st.error(f"Failed to initialize agent: {str(e)}")
        st.stop()

# Main app
def main():
    st.title("📈 LangChain Stock Advisor (OpenBB Edition)")
    st.markdown("Ask questions about stocks and get detailed analysis powered by AI.")
    
    # Initialize session state for chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about a stock (e.g., 'What's the latest news on AAPL?')"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Display assistant response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            try:
                agent_executor = initialize_agent(google_api_key, model_name, temperature)
                result = agent_executor.invoke({"input": prompt})
                response = result["output"]
            except Exception as e:
                response = f"Error processing your request: {str(e)}"
            
            message_placeholder.markdown(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()