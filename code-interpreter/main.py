import os
from dotenv import load_dotenv
from langchain import hub
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain.agents import create_react_agent, AgentExecutor
from langchain_experimental.tools import PythonREPLTool
from langchain_experimental.agents import create_csv_agent
from langchain_core.tools import Tool
from typing import Any


load_dotenv()

def main():
    instructions = """You are an agent designed to write and execute python code to answer questions.
    You have access to a python REPL, which you can use to execute python code.
    If you get an error, debug your code and try again.
    Only use the output of your code to answer the question. 
    You might know the answer without running any code, but you should still run the code to get the answer.
    If it does not seem like you can write code to answer the question, just return "I don't know" as the answer.
    """
    base_prompt = hub.pull("langchain-ai/react-agent-template")
    prompt = base_prompt.partial(instructions=instructions)

    tools = [PythonREPLTool()]

    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
    llm1 = ChatOllama(model="llama2", temperature=0)

    agent = create_react_agent(
        prompt=prompt,
        llm=llm,
        tools=tools
    )

    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


    csv_agent = create_csv_agent(
        llm = llm,
        path = "episode_info.csv",
        verbose=True,
        allow_dangerous_code=True

    )

    def python_agent_executor_wrapper(original_prompt: str) -> dict[str, Any]:
        return agent_executor.invoke({"input": original_prompt})

    tools = [
        Tool(
            name="Python Agent",
            func=python_agent_executor_wrapper,
            description="""useful when you need to transform natural language to python and execute the python code,
                          returning the results of the code execution
                          DOES NOT ACCEPT CODE AS INPUT""",
        ),
        Tool(
            name="CSV Agent",
            func=csv_agent.invoke,
            description="""useful when you need to answer question over episode_info.csv file,
                         takes an input the entire question and returns the answer after running pandas calculations""",
        ),
    ]

    instructions = """
    You are an agent designed to answer user questions ONLY by using one of the tools provided to you.
    Do NOT answer from your own knowledge.
    You must always choose a tool to get the answer.

    If the question is about calculations on the CSV file, use the CSV Agent tool.
    If the question requires running custom Python code, use the Python Agent tool.
    Do not produce a Final Answer unless it comes from the output of a tool.
    """

    prompt = base_prompt.partial(instructions=instructions)
    grand_agent = create_react_agent(
        prompt=prompt,
        llm = llm,
        tools=tools
    )

    grand_agent_executor = AgentExecutor(
        agent=grand_agent, 
        tools=tools, verbose=True, 
        handle_parsing_errors=True
        )

    print(
        grand_agent_executor.invoke(
            {
                "input" : "which season has the most episodes?"
            }
        )
    )




if __name__ == "__main__":
    main()


