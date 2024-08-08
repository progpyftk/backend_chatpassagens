# chat/run_chat.py
import pprint
from typing import Annotated, Optional, Literal
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
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import Callable
from langchain_core.messages import ToolMessage
from typing import Literal
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph
from langgraph.prebuilt import tools_condition
import shutil
import uuid
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults


load_dotenv()  # Carrega as variáveis de ambiente do arquivo .env

llm = ChatOpenAI(api_key=os.getenv('OPENAI_API_KEY'),model="gpt-3.5-turbo-0125", temperature=0)

def update_dialog_stack(left: list[str], right: Optional[str]) -> list[str]:
    """Push or pop the state."""
    if right is None:
        return left
    if right == "pop":
        return left[:-1]
    return left + [right]

class ToFlightSearchAssistant(BaseModel):
    """Transfers work to a specialized assistant to look up at the internet about nature and other stuff."""
    
    request: str = Field(
        description="Any necessary followup questions to help to find more info."
    )
    

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_info: str
    dialog_state: Annotated[
        list[
            Literal[
                "primary_assistant",
                "flight_search_assistant",
                "inspiration_tourism",
            ]
        ],
        update_dialog_stack,
    ]


class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
        while True:
            result = self.runnable.invoke(state)
            print("Printanto o resultado da chamada do assistente")
            print(state)
            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}
    
    
class CompleteOrEscalate(BaseModel): # https://python.langchain.com/v0.2/docs/how_to/tool_calling/#pydantic-class
    """A tool to mark the current task as completed and/or to escalate control of the dialog to the main assistant,
    who can re-route the dialog based on the user's needs."""

    cancel: bool = True
    reason: str
    #  é uma ferramenta utilizada para marcar uma tarefa como concluída e/ou para escalar o controle do diálogo 
    # de volta ao assistente principal, que pode redirecionar o diálogo com base nas necessidades do usuário.
    # se cancel é True, a tarefa atual é marcada como concluída e o controle do diálogo é escalado de volta ao assistente principal.
    # se cancel é False, significa que a tarefa não foi cancelada. Nesse cenário, o assistente especializado indica que
    # precisa de mais informações ou precisa realizar ações adicionais antes de concluir a tarefa ou escalá-la de volta ao assistente
    class Config:
        schema_extra = {
            "example": {
                "cancel": True,
                "reason": "User changed their mind about the current task.",
            },
            "example 2": {
                "cancel": True,
                "reason": "I have fully completed the task.",
            },
            "example 3": {
                "cancel": False,
                "reason": "I need to search the user's emails or calendar for more information.",
            },
        }
        
# Definição dos assistentes especializados

# Flight Search Assistent
flight_search_assistant_prompt = ChatPromptTemplate.from_messages(
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

tavily_tool = TavilySearchResults(max_results=5)

flight_search_assistant_tools = [tavily_tool, CompleteOrEscalate]
flight_search_assistant_runnable = flight_search_assistant_prompt | llm.bind_tools(flight_search_assistant_tools)

# Tourism Assistent
tourism_assistant_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                " Utilize sua capacidade para responder às perguntas sobre locais turisticos ao usuário. "
                "\nCurrent time: {time}.",
            ),
            ("placeholder", "{messages}"),
        ]
    ).partial(time=datetime.now())

tourism_assistant_tools = [CompleteOrEscalate]
tourism_assistant_runnable = tourism_assistant_prompt | llm.bind_tools(tourism_assistant_tools)

# Definição do assistente principal	e suas tools
# As classes Pydantic são usadas para definir ferramentas que a LLM pode invocar durante suas operações. Elas funcionam da seguinte forma:
# a LLM pode gerar instâncias desta classe com base nas entradas do usuário e invocá-la para realizar a ação especificada.
# Cada ferramenta é definida como uma classe que herda de `BaseModel` do Pydantic. Os atributos da classe representam os parâmetros que a ferramenta aceita.
# Cada atributo é tipado, garantindo que a entrada do usuário corresponda ao tipo esperado.
# `Field` pode ser usado para fornecer descrições adicionais dos parâmetros, que ajudam a LLM a entender o propósito de cada um.

# Primary Assistant
# Adicione a ToolMessage dentro da classe ToFlightSearchAssistant


class ToTourismAssistant(BaseModel):
    """Transfers work to a specialized assistant to handle tourism hints and information."""

    request: str = Field(
        description="Any necessary followup questions the tourism assistant should clarify before proceeding."
    )

# The top-level assistant performs general Q&A and delegates specialized tasks to other assistants.
# The task delegation is a simple form of semantic routing / does simple intent detection
primary_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful customer support assistant for Swiss Airlines. "
            "Your primary role is to undestand what the user is looking for.. "
            "If a customer requests to searcg a flight or get trip recommendations, delegate the task to the appropriate specialized assistant"
            "by invoking the corresponding tool. "
            "Descreve em detalhes o que o usuário está buscando e dê ideias para o próximo assistente especializado"
            "The user is not aware of the different specialized assistants, so do not mention them; just quietly delegate through function calls. "
            "\nCurrent time: {time}.",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now())

primary_assistant_tools = [ToFlightSearchAssistant]

assistant_runnable = primary_assistant_prompt | llm.bind_tools(primary_assistant_tools)

def create_entry_node(assistant_name: str, new_dialog_state: str) -> Callable:
    def entry_node(state: State) -> dict:
                  
        tool_call_id = state["messages"][-1].tool_calls[0]["id"]
        print("\n --- create_entry_node --- \n")  
        print(f"state: {state} \n")   
        print(f"state['messages']: {state['messages']} \n") 
        print(f"\n tool_call_id: {tool_call_id}")
        state['messages'].append(ToolMessage(content="DEU CERTO", name='ToFlightSearchAssistant', id=tool_call_id, tool_call_id=tool_call_id))
        print(state['messages'])
        
        
        return {
            "messages": [
                ToolMessage(
                    content=f"The assistant is now the {assistant_name}. Reflect on the above conversation between the host assistant and the user."
                    f" The user's intent is unsatisfied. Use the provided tools to assist the user. Remember, you are {assistant_name},"
                    " and the booking, update, other other action is not complete until after you have successfully invoked the appropriate tool."
                    " If the user changes their mind or needs help for other tasks, call the CompleteOrEscalate function to let the primary host assistant take control."
                    " Do not mention who you are - just act as the proxy for the assistant.",
                    tool_call_id=tool_call_id,id=tool_call_id
                )
            ],
            "dialog_state": new_dialog_state,
        }
    return entry_node


def run_chatbot():

    def route_search_flight(
        state: State,
    ) -> Literal[
        "flight_search_tools", # se a rota for para utilizar alguma tool
        "leave_skill",         # retorna para o assistente principal
        "__end__",             # se a rota for para finalizar o workflow
    ]:
        route = tools_condition(state) # verifica se a rota é para utilizar alguma tool - a função tools_condition é uma função predefinida que verifica se a rota é para utilizar alguma tool
        if route == END:
            return END
        tool_calls = state["messages"][-1].tool_calls # state["messages"][-1].tool_calls está verificando as chamadas de ferramentas feitas no nó flight_search_assistant (ou qualquer nó que esteja atualmente sendo executado)
        did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls) # verifica se alguma das chamadas de ferramentas (tool_calls) realizadas pelo assistente foi uma chamada à ferramenta CompleteOrEscalate. A função any verifica se alguma das chamadas de ferramentas em tool_calls possui o nome "CompleteOrEscalate". Se ao menos uma chamada de ferramenta for CompleteOrEscalate, any retorna True; caso contrário, retorna False.
        if did_cancel: # did_cancel será True se alguma das chamadas de ferramentas for CompleteOrEscalate e cancel estiver configurado como True. 
            return "leave_skill" # Isso indica que o assistente deve interromper seu trabalho atual e retornar o controle ao assistente principal.
        return "flight_search_tools"
    
    
    def pop_dialog_state(state: State) -> dict:
        """Pop the dialog stack and return to the main assistant.

        This lets the full graph explicitly track the dialog flow and delegate control
        to specific sub-graphs.
        """
        print("---- \n estou na pop_dialog_state \n -----")
        messages = []
        if state["messages"][-1].tool_calls:
            # Note: Doesn't currently handle the edge case where the llm performs parallel tool calls
            messages.append(
                ToolMessage(
                    content="Resuming dialog with the host assistant. Please reflect on the past conversation and assist the user as needed.",
                    tool_call_id=state["messages"][-1].tool_calls[0]["id"],
                )
            )
        return {
            "dialog_state": "pop",
            "messages": messages,
        }
    
    
    def route_primary_assistant(
        state: State,
    ) -> Literal[
        "enter_flight_search_assistant",
        "__end__",
    ]:
        route = tools_condition(state)
        if route == END:
            return END
        tool_calls = state["messages"][-1].tool_calls
        if tool_calls:
            if tool_calls[0]["name"] == ToFlightSearchAssistant.__name__:
                print(f"---- \n estou na route_primary_assistant, e a ferramenta chamada foi {ToFlightSearchAssistant.__name__} \n -----")
                return "enter_flight_search_assistant"
            elif tool_calls[0]["name"] == ToTourismAssistant.__name__:
                return "enter_tourism_assistant"
            return "primary_assistant_tools"
        raise ValueError("Invalid route")


    def route_to_workflow(
            state: State,
        ) -> Literal[
            "primary_assistant",
            "flight_search_assistant"
        ]:
            """If we are in a delegated state, route directly to the appropriate assistant."""
            dialog_state = state.get("dialog_state")
            if not dialog_state:
                print("---- \n dialog_state é None, roteando de volta para o primary_assistant \n -----")
                return "primary_assistant"
            return dialog_state[-1]
        
    @tool
    def fetch_user_flight_information() -> list[dict]:
        """Fetch all tickets for the user along with corresponding flight information and seat assignments.

        Returns:
            A list of dictionaries where each dictionary contains the ticket details,
            associated flight details, and the seat assignments for each ticket belonging to the user.
        """
        return [{"ticket_no": "7240005432906569", "book_ref": "C46E9F", "flight_id": 19250, "flight_no": "LX0112", "departure_airport": "CDG", "arrival_airport": "BSL", "scheduled_departure": "2024-04-30 12:09:03.561731-04:00", "scheduled_arrival": "2024-04-30 13:39:03.561731-04:00", "seat_no": "18E", "fare_conditions": "Economy"}]    
        
    def check_tool_messages(state: State) -> dict:
        print("---- \n estou na check_tool_messages \n -----")
        print("---- \n estou na check_tool_messages \n -----")
        print(state)
        
        
        
        return { 'dialog_state': 'primary_assistant' }  
        
    def user_info(state: State):
        return {"user_info": fetch_user_flight_information.invoke({})}
    
    builder = StateGraph(State)
    
    
    builder.add_node("primary_assistant", Assistant(assistant_runnable))
    builder.add_node("primary_assistant_tools", create_tool_node_with_fallback(primary_assistant_tools))
    
    # adicionando os nodes relacionados ao flight_search_assistant
    builder.add_node("enter_flight_search_assistant", create_entry_node("Flight Search Assistant", "flight_search_assistant"))
    builder.add_node("flight_search_assistant", Assistant(flight_search_assistant_runnable))
    builder.add_node("flight_search_tools", create_tool_node_with_fallback(flight_search_assistant_tools))
    builder.add_node("leave_skill", pop_dialog_state)
    
    builder.add_node("check_tool_messages", check_tool_messages)
    # aducionando arestas e condicionais
    
    builder.add_node("fetch_user_info", user_info)
    builder.add_edge(START, "fetch_user_info")
    builder.add_conditional_edges("fetch_user_info", route_to_workflow)

    builder.add_conditional_edges("primary_assistant", route_to_workflow)
    builder.add_conditional_edges(
        "primary_assistant",
        route_primary_assistant,
        {
            "enter_flight_search_assistant": "enter_flight_search_assistant", # se route_primary_assistant retornar "enter_flight_search_assistant", o grafo transita para "enter_flight_search_assistant". 
            "primary_assistant_tools": "primary_assistant_tools", # Se retornar "primary_assistant_tools", transita para "primary_assistant_tools". Se retornar END, o grafo termina a execução.
            END: END,
        },
    )
    
    # builder.add_edge("enter_flight_search_assistant", "flight_search_assistant")
    builder.add_edge("enter_flight_search_assistant", "check_tool_messages")
    builder.add_edge("flight_search_tools", "flight_search_assistant")
    builder.add_conditional_edges("flight_search_tools", route_search_flight)
    builder.add_edge("leave_skill", "primary_assistant")
    builder.add_edge("primary_assistant_tools", "primary_assistant")

    # Compile graph
    memory = SqliteSaver.from_conn_string(":memory:")
    graph = builder.compile(
    checkpointer=memory,)
    
    

    thread_id = str(uuid.uuid4())
    
    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }
    
    _printed = set()
    
    question = "Qual a relação entre os pinguins africanos e as correntes maritimas?"
    events = graph.stream(
        {"messages": ("user", question)}, config, stream_mode="values"
    )
    for event in events:
        _print_event(event, _printed)
    snapshot = graph.get_state(config)
    while snapshot.next:
        user_input = input(
            "Do you approve of the above actions? Type 'y' to continue;"
            " otherwise, explain your requested changed.\n\n"
        )
        if user_input.strip() == "y":
            # Just continue
            result = graph.invoke(
                None,
                config,
            )
        else:
            print("User denied the action.")
            # Satisfy the tool invocation by
            # providing instructions on the requested changes / change of mind
            result = graph.invoke(
                {
                    "messages": [
                        ToolMessage(
                            tool_call_id=event["messages"][-1].tool_calls[0]["id"],
                            content=f"API call denied by user. Reasoning: '{user_input}'. Continue assisting, accounting for the user's input.",
                        )
                    ]
                },
                config,
            )
        snapshot = graph.get_state(config)