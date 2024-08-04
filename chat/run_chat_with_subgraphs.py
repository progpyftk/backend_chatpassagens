from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.tools.tavily_search import TavilySearchResults
from .tools import search_amadeus_flights, tourism_info_tool
from langchain_core.output_parsers import JsonOutputFunctionsParser
from typing import Annotated
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.graph import StateGraph

# Define tools for the agent workers

tools = [search_amadeus_flights, tourism_info_tool]

# Helper function to create agent workers
def create_agent_worker(llm, tools, system_prompt):
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])
    agent = create_openai_tools_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools)

# Define the agent workers
flight_search_agent = create_agent_worker(
    ChatOpenAI(model="gpt-4-1106-preview"),
    [search_amadeus_flights],
    "You are a flight search agent. Given a user's travel request, provide the best flight options."
)

tourism_info_agent = create_agent_worker(
    ChatOpenAI(model="gpt-4-1106-preview"),
    [tourism_info_tool],
    "You are a tourism information agent. Given a user's travel request, provide relevant information about the destination."
)

# Define the supervisor agent
system_prompt = """
You are a supervisor tasked with managing a conversation between the following workers: Flight Search Agent, Tourism Information Agent.
Given the user's request, respond with the worker to act next. Each worker will perform a task and respond with their results and status. When finished, respond with FINISH.
"""

options = ["FINISH", "Flight Search Agent", "Tourism Information Agent"]
function_def = {
    "name": "route",
    "description": "Select the next role.",
    "parameters": {
        "title": "routeSchema",
        "type": "object",
        "properties": {
            "next": {
                "title": "Next",
                "anyOf": [
                    {"enum": options},
                ],
            }
        },
        "required": ["next"],
    },
}

supervisor_prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="messages"),
    ("system", "Given the conversation above, who should act next? Or should we FINISH? Select one of: {options}")
]).partial(options=str(options))

supervisor_agent = (
    supervisor_prompt
    | ChatOpenAI(model="gpt-4-1106-preview").bind_functions(functions=[function_def], function_call="route")
    | JsonOutputFunctionsParser()
)

# Define the entry point for the graph
def entry_point(state):
    return {"messages": [HumanMessage(content=state["messages"][-1].content, name="User")]}

# Compile the graph
graph_builder = StateGraph({"messages": Annotated[list, add_messages]})
graph_builder.add_node("entry_point", entry_point)
graph_builder.add_node("flight_search_agent", flight_search_agent)
graph_builder.add_node("tourism_info_agent", tourism_info_agent)
graph_builder.add_node("supervisor_agent", supervisor_agent)
graph_builder.set_entry_point("entry_point")
graph_builder.set_finish_point("supervisor_agent")
graph = graph_builder.compile()