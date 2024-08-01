# chat/run_chat.py

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_openai import ChatOpenAI
from datetime import datetime
from .tools import search_amadeus_flights
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph, START
from .utils import create_tool_node_with_fallback, _print_event
from langgraph.prebuilt import tools_condition
from IPython.display import Image, display
from dotenv import load_dotenv
import os

load_dotenv()  # Carrega as variáveis de ambiente do arquivo .env

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
        result = None
        while True:
            configuration = config.get("configurable", {})
            result = self.runnable.invoke(state, configuration)
            if result:
                break
        return {"messages": result}

def run_chatbot():
    llm = ChatOpenAI(api_key=os.getenv('OPENAI_API_KEY'), model="gpt-4o-mini-2024-07-18")
    primary_assistant_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                " You are an assistant specializing in travel inquiries, particularly flight bookings. "
                " Your task is to interpret the user's question and select the most appropriate tool to provide accurate and helpful information. "
                " Focus on delivering the best results related to flight options, booking details, and other travel-related services."
                " Ensure comprehensive searches and do not hesitate to use multiple tools if necessary."
                "\nCurrent time: {time}.",
            ),
            ("placeholder", "{messages}"),
        ]
    ).partial(time=datetime.now())
    
    tools = [search_amadeus_flights]
    assistant_runnable = primary_assistant_prompt | llm.bind_tools(tools)
    
    builder = StateGraph(State)
    builder.add_node("assistant", Assistant(assistant_runnable))
    builder.add_node("tools", create_tool_node_with_fallback(tools))
    builder.add_edge(START, "assistant")
    builder.add_conditional_edges("assistant", tools_condition)
    builder.add_edge("tools", "assistant")
    
    memory = SqliteSaver.from_conn_string(":memory:")
    graph = builder.compile(checkpointer=memory)

    config = {
        "configurable": {
            "thread_id": 1,
        }
    }
    question = "Quais são as melhores opções de passagens aéreas saindo de VIX para São Paulo em 05/08/2024, eu posso chegar em qualquer aeroporto de São Paulo"
    
    _printed = set()
    events = graph.stream(
        {"messages": ("user", question)}, config, stream_mode="values"
    )
    for event in events:
        _print_event(event, _printed)
    
    try:
        display(Image(graph.get_graph(xray=True).draw_mermaid_png()))
    except Exception:
        pass

