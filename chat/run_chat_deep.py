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


memory = SqliteSaver.from_conn_string(":memory:")

# Load environment variables
load_dotenv()

# Initialize the LLM
llm = ChatOpenAI(api_key=os.getenv('OPENAI_API_KEY'), model="gpt-4o-mini-2024-07-18", temperature=0)

# Define the AgentState TypedDict
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    task: str
    next_assistant: str
    content: List[str]
    tool_calls: List[Dict]  # Add this field to store tool calls
    
class Supervisor(BaseModel):
    """Analyse conversation then you can awnser the user or route the message for a specialized assistant including your thoughts"""

    though: Optional[str] = Field(description="Any thoughts you have about the user's question that may help the next assistant")
    awnser: Optional[str] = Field(description="The awnser to the user, based on the last agent awsers, or asking for more information")
    route_to: Optional[Literal['flight_searcher', 'tourism_searcher']] = Field(description="The specialized assistant to route the user's question to")
    action_justification: str = Field(description="Justify why you are routing the user's question to the specialized assistant or direclty awnsering the user")

# Initialize tools
tools = [search_amadeus_flights]
tool_node = ToolNode(tools)

# Define prompts for the LLM
SUPERVISOR_PROMPT = """
You are a supervisor tasked with analyzing the user's question and then routing the question to a specialized assistant. 
You must respond with only one of the following options based on the question: 
- "flight_searcher" for questions related to flight searches.
- "tourism_searcher" for questions related SOCCER.

Do not include any other text in your response.
"""

FLIGHT_SEARCHER_PROMPT = """ 
Você é um especialista em passagens aéreas e está encarregado de responder a pergunta do usuário sobre passagens aéreas.
Você tem acesso a algumas ferramentas para ajudá-lo com essa tarefa para diferentes aeroportos você pode chamar a ferramenta em paralelo./n
Você também deve utilzar o contexto da conversa para responder o usuário. 
Você pode conversar livremente com ele./n
Caso pense que as informações fornecidas pelo usuário não são suficientes, ou não fazem sentido, você pode pedir mais informações./n
Caso precise de mais informações, responda com as informações que você precisa.
------
{content}"""

TOURISM_SEARCHER_PROMPT = """
You are a tourism specialist and you are tasked with answering the users question about tourism. You have some tools at your disposal to help you with this task.
/n
{content}
"""






def supervisor_node(state: AgentState):
    """Node function for the supervisor agent."""
    
    structured_llm = llm.with_structured_output(Supervisor, include_raw=True)
    
    print("----   supervisor_node   ----")
    state['messages'].extend([SystemMessage(content=SUPERVISOR_PROMPT)])

    response = structured_llm.invoke([SystemMessage(content=SUPERVISOR_PROMPT)] + state['messages'])
    print("\n----   Resposta criada pela LLM SUPERVISOR   ----")
    print(response)
  
    next_assistant = response['parsed'].route_to

    # Ensure the response is either "flight_searcher" or "tourism_searcher"
    if next_assistant not in ["flight_searcher", "tourism_searcher"]:
       raise ValueError(f"Unexpected assistant type: {next_assistant}")
    
    print(f"Next assistant: {next_assistant}")
    return {"messages": response, "next_assistant": next_assistant}

def flight_searcher_node(state: AgentState):
    """Node function for the flight searcher agent."""
    print("----   flight_searcher_node   ----")
    tools = [search_amadeus_flights]

    for message in state["messages"]:
        pass
    
    if state['messages'] and isinstance(state['messages'][-1], ToolMessage):
        state['messages'].extend([SystemMessage(content="Você é o especilista em passagens aéreas, tendo em vista a conversa abaixo e o resultado das tools, crie uma resposta estruturada para o usuário.")])
        response = llm.bind_tools(tools, parallel_tool_calls=True).invoke(state['messages'])
        print("\n----   Resposta criada pela LLM apóis a chamada das Tools dentro do if   ----")
        print(response)
        return {"messages": response}
    
    response = llm.bind_tools(tools, parallel_tool_calls=True).invoke(
        [SystemMessage(content=FLIGHT_SEARCHER_PROMPT)] + state['messages'])
    print("\n----   Resposta da LLM para realizar a chamada da Tool OU responder o usuário   ----")
    print(response)

    return {"messages": response}

def execute_flight_search(state: AgentState):
    """Node function to execute the flight search tool."""
    print('\n----   execute_flight_search   ----')
    result = tool_node.invoke({"messages": state["messages"]})
    return {"messages": result['messages']}

def route_flight_search(state: AgentState):
    """Routing function to decide if the tool should be executed."""
    print('\n----   route_flight_search   ----')
    if state["messages"][-1].tool_calls:    
        print("router verificou que a última mensagem foi uma necessidade chamada de tool")
        return "execute_flight_search"
    else:
        print("router verificou que a última mensagem NÃO FOI uma necessidade chamada de tool")
        return "user_input"

def tourism_searcher_node(state: AgentState):
    """Node function for the tourism searcher agent."""
    result = llm.bind_tools(tools).invoke([
        SystemMessage(content=TOURISM_SEARCHER_PROMPT),
        HumanMessage(content=state['task'])
    ])
    return {"content": result['output']}

def main_routing_function(state: AgentState):
    """Main routing function to determine the next assistant."""
    if state["next_assistant"] == "flight_searcher":
        return "flight_searcher"
    
    if state["next_assistant"] == "tourism_searcher":
        return "tourism_searcher"
    
    return "supervisor"

def user_input_node(state: AgentState):
    """Node function to capture user input."""
    print("----   user_input_node   ----")
    user_input = input()
    return {"messages": [HumanMessage(content=user_input)]}

def format_supervisor_message(raw_message):
    """Extract and format the supervisor message."""
    # Extract the relevant information from the raw message
    if 'raw' in raw_message:
        ai_message = raw_message['raw']
        # Ensure the AIMessage has the necessary fields
        if 'content' in ai_message and 'tool_calls' in ai_message['additional_kwargs']:
            # Create a formatted message
            return {
                "role": "assistant",  # Set the role appropriately
                "content": {
                    "thought": None,  # You can set this if needed
                    "answer": ai_message['content'],  # Use the content from AIMessage
                    "route_to": raw_message['parsed'].route_to,
                    "action_justification": raw_message['parsed'].action_justification
                }
            }
    return None  # Return None if the message is not valid

async def run_chatbot():
    """Main function to run the chatbot."""
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
            print("Event received:", event)
            
            # Handle specific event types
            #if event['event'] == 'on_chain_end':
            #    print("Chain processing completed with output:", event['data'])
            #elif event['event'] == 'on_chain_start':
            #    print("Chain processing started.")
