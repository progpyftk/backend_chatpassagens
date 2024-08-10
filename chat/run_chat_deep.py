from typing import TypedDict, Annotated, List, Dict, Optional, Literal
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ChatMessage, ToolMessage
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from .tools import search_amadeus_flights
import os
from dotenv import load_dotenv
import asyncio
from langgraph.checkpoint.aiosqlite import AsyncSqliteSaver
from .prompts.flight_searcher_prompt import FLIGHT_SEARCHER_PROMPT, FLIGHT_SEARCHER_TOOL_RESPONSE_PROMPT
from .prompts.tourism_searcher_prompt import TOURISM_SEARCHER_PROMPT
from .nodes.assistant_nodes import supervisor_node, flight_searcher_node, tourism_searcher_node
from .nodes.routing_nodes import route_flight_search, main_routing_function
from .nodes.tool_nodes import execute_flight_search
from .states.agent_state import AgentState
from .utils import reset_database

# Initialize the memory
memory = SqliteSaver.from_conn_string(":memory:")

# Load environment variables
load_dotenv()

def user_input_node(state: AgentState):
    """Node function to capture user input."""
    print("----   user_input_node   ----")
    user_input = input()
    return {"messages": [HumanMessage(content=user_input)]}


async def run_chatbot():
    """Main function to run the chatbot."""
    # reseta a memoria, depois eu vou retirar isso.
    await reset_database()
    builder = StateGraph(AgentState)
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("flight_searcher", flight_searcher_node)
    builder.add_node("execute_flight_search", execute_flight_search)
    builder.add_node("tourism_searcher", tourism_searcher_node)
    builder.add_node("user_input", user_input_node)
    builder.set_entry_point("user_input")
    builder.add_conditional_edges(
        "supervisor", main_routing_function, {
                "flight_searcher": "flight_searcher",
                "tourism_searcher": "tourism_searcher",
    })
    
    builder.add_conditional_edges("flight_searcher", route_flight_search, {
        "execute_flight_search": "execute_flight_search",
        "user_input": "user_input"
    })
    builder.add_edge("execute_flight_search", "flight_searcher")
    builder.add_edge("user_input", "supervisor")
    
    # Use AsyncSqliteSaver for async operations
    async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as memory:
        graph = builder.compile(checkpointer=memory)
        thread = {"configurable": {"thread_id": "1"}}
        
        # Stream events asynchronously with version specified
        async for event in graph.astream_events({"messages": []}, thread, version='v2'):
            pass
            # print("Event received:", event)
            
            # Handle specific event types
            #if event['event'] == 'on_chain_end':
            #    print("Chain processing completed with output:", event['data'])
            #elif event['event'] == 'on_chain_start':
            #    print("Chain processing started.")
