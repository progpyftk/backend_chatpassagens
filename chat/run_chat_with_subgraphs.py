# chat/run_chat.py

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

load_dotenv()  # Carrega as variáveis de ambiente do arquivo .env

llm = ChatOpenAI(api_key=os.getenv('OPENAI_API_KEY'), model="gpt-4o-mini-2024-07-18")

def update_dialog_stack(left: list[str], right: Optional[str]) -> list[str]:
    """Push or pop the state."""
    if right is None:
        return left
    if right == "pop":
        return left[:-1]
    return left + [right]

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_info: str
    dialog_state: Annotated[
        list[
            Literal[
                "assistant",
                "flight_search_assistant",
                "inspiration_tourism",
            ]
        ],
        update_dialog_stack,
    ]
   
# Vamos criar um assistente para cada tipo de interesse do usuário
# 1. Assistente de voos 
# 2. Assistente de inspiração de voo
# 3. Assistente de turismo
# 4. a "primary assistant" to route between these

# Definição dos runnables de cada assistente especializado
# Cada um desses runnables possui seu próprio prompt, LLM, e schema para tools
# Cada um deles pode chamar a tool "CompleteOrScalate" para indicar se o fluxo de controle deve voltar ao assistente principal ou se deve continuar com a ferramenta atual


class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
        while True:
            result = self.runnable.invoke(state)
            #  se o assistente não tiver ferramentas ou informações para responder à pergunta específica, 
            #  ele pode não conseguir fornecer uma resposta útil. O design do método garante que o assistente 
            # tente várias vezes até obter uma resposta válida ou até que o sistema determine que não pode ajudar com a consulta específica.
            if not result.tool_calls and (                                                 # se não houver chamadas de ferramenta
                not result.content                                                         # ou se não houver conteúdo
                or isinstance(result.content, list) and not result.content[0].get("text")  # ou se o conteúdo for uma lista e se for una lista se o primeiro item não tiver texto 
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")] # cria uma nova mensagem do usuário com o texto "Respond with a real output."
                state = {**state, "messages": messages}                                  # atualiza o estado com a nova mensagem, adicionando-a à lista de mensagens do state   
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

flight_search_assistant_tools = [search_amadeus_flights, CompleteOrEscalate]
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
class ToFlightSearchAssistant(BaseModel):
    """Transfers work to a specialized assistant to handle flight search."""

    request: str = Field(
        description="Any necessary followup questions the update flight assistant should clarify before proceeding."
    )

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
            "by invoking the corresponding tool. Only the specialized assistants are given permission to do this for the user. "
            "The user is not aware of the different specialized assistants, so do not mention them; just quietly delegate through function calls. "
            "Provide detailed information to the customer"
            " When searching, be persistent. Expand your query bounds if the first search returns no results. "
            " If a search comes up empty, expand your search before giving up."
            "\nCurrent time: {time}.",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now())

primary_assistant_tools = [ToFlightSearchAssistant, ToTourismAssistant]

assistant_runnable = primary_assistant_prompt | llm.bind_tools(primary_assistant_tools)

# A função entry_node retorna um dicionário contendo uma mensagem ToolMessage que informa ao usuário q
# ue o assistente especializado está no comando e que ele deve refletir sobre a conversa anterior entre o assistente principal e o usuário. 
# Create a function to make an "entry" node for each workflow, stating "the current assistant ix assistant_name".
# O parâmetro state é passado para a função interna entry_node quando o grafo de estado está sendo executado. Vamos detalhar como isso acontece.
# A função create_entry_node retorna a função entry_node. Esta função é adicionada ao grafo de estado como um nó. Quando o grafo de estado é executado, 
# ele invoca a função entry_node, passando o estado atual do grafo como argumento.
# builder.add_node(enter_flight_search_assistant", create_entry_node("Flight Search Assistant", "flight_search_assistant"))
# A ToolMessage irá dizer qual assistente está no comando.
def create_entry_node(assistant_name: str, new_dialog_state: str) -> Callable:
    def entry_node(state: State) -> dict:
        print(f"--- entry_node() interna----")
        print(f"---Entering {assistant_name} ----")
        print(f"---\n state: {state} \n----")

        # Verifique se há tool_calls antes de tentar acessá-lo
        if not state["messages"] or not hasattr(state["messages"][-1], 'tool_calls') or not state["messages"][-1].tool_calls:
            return state  # Se não houver chamadas de ferramentas, retorne o estado atual.

        tool_call_id = state["messages"][-1].tool_calls[0]["id"]
        print("Estou aqui !!!")
        print(f"---\n state['messages'][-1]: {state['messages'][-1]} \n----")
        print(f"---\n tool_call_id: {tool_call_id} \n----")
        result = {"messages": [
                ToolMessage(
                    content=f"The assistant is now the {assistant_name}. Reflect on the above conversation between the host assistant and the user."
                    f" The user's intent is unsatisfied. Use the provided tools to assist the user. Remember, you are {assistant_name},"
                    " and the booking, update, or other action is not complete until after you have successfully invoked the appropriate tool."
                    " If the user changes their mind or needs help for other tasks, call the CompleteOrEscalate function to let the primary host assistant take control."
                    " Do not mention who you are - just act as the proxy for the assistant.",
                    tool_call_id=tool_call_id,
                )
            ],
            "dialog_state": new_dialog_state,}
        print("Vou printar o resultado")
        print(result)
        return result
            
        

    return entry_node

def run_chatbot():
    # Construção dos subgrafos - cada um assisntente especializado terá seu próprio subgrafo, serão todos muito parecidos.
    # node 1: enter_*: utilizamos a função create_entry_node para adicionar uma tool message sinalizando que um agente especializado está no comando
    # node 2: assistant: um prompt + llm que recebe o state atual que poderá utilizar uma tool, perguntar uma questão do usuário ou finalizar o workflow (retornal ao assistente principal)
    # node 3: tools - aqui apenas estamos definindo os nodes, não necessariamente serão utilizados
    
    # Função que decide qual nó será executado a seguir com base no estado atual.
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
    
    
    # A função pop_dialog_state é usada para gerenciar a transição do controle do fluxo de diálogo de volta para o assistente principal, retirando o estado atual da pilha de diálogo. Isso é útil para garantir que, após a execução de um assistente especializado, o controle seja retornado ao assistente principal, que pode então continuar a gerenciar a interação com o usuário.
    def pop_dialog_state(state: State) -> dict:
        """Pop the dialog stack and return to the main assistant.

        This lets the full graph explicitly track the dialog flow and delegate control
        to specific sub-graphs.
        """
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
    
    
    # O grafo de estado transita para o nó retornado pela função de roteamento.
    def route_primary_assistant(
        state: State,
    ) -> Literal[
        "primary_assistant_tools",
        "enter_flight_search_assistant",
        "__end__",
    ]:
        route = tools_condition(state)
        if route == END:
            return END
        # A função verifica quais ferramentas foram chamadas na última mensagem (state["messages"][-1].tool_calls).
        tool_calls = state["messages"][-1].tool_calls
        if tool_calls: # Baseado no nome da ferramenta chamada, a função retorna um valor literal que corresponde a um dos nós de destino.
            if tool_calls[0]["name"] == ToFlightSearchAssistant.__name__:
                return "enter_flight_search_assistant"
            elif tool_calls[0]["name"] == ToTourismAssistant.__name__:
                return "enter_tourism_assistant"
            return "primary_assistant_tools"
        raise ValueError("Invalid route")
    
    
    # Each delegated workflow can directly respond to the user
    # When the user responds, we want to return to the currently active workflow
    def route_to_workflow(
            state: State,
        ) -> Literal[
            "primary_assistant",
            "flight_search_assistant"
        ]:
            """If we are in a delegated state, route directly to the appropriate assistant."""
            dialog_state = state.get("dialog_state")
            if not dialog_state:
                return "primary_assistant"
            return dialog_state[-1]
        
    
    builder = StateGraph(State)
    
    builder.add_node("primary_assistant", Assistant(assistant_runnable))
    builder.add_node("primary_assistant_tools", create_tool_node_with_fallback(primary_assistant_tools))
    builder.add_node("enter_flight_search_assistant", create_entry_node("Flight Search Assistant", "flight_search_assistant"))
    builder.add_node("flight_search_assistant", Assistant(flight_search_assistant_runnable))
    builder.add_node("flight_search_tools", create_tool_node_with_fallback(flight_search_assistant_tools))
    builder.add_node("leave_skill", pop_dialog_state)
    
    
    builder.add_edge(START, "primary_assistant")
    builder.add_conditional_edges("primary_assistant", route_to_workflow)
    builder.add_edge("enter_flight_search_assistant", "flight_search_assistant")
    builder.add_edge("flight_search_tools", "flight_search_assistant")
    builder.add_conditional_edges("flight_search_tools", route_search_flight)
    builder.add_edge("leave_skill", "primary_assistant")
    builder.add_conditional_edges(
        "primary_assistant",
        route_primary_assistant,
        {
            "enter_flight_search_assistant": "enter_flight_search_assistant", # se route_primary_assistant retornar "enter_flight_search_assistant", o grafo transita para "enter_flight_search_assistant". 
            "primary_assistant_tools": "primary_assistant_tools", # Se retornar "primary_assistant_tools", transita para "primary_assistant_tools". Se retornar END, o grafo termina a execução.
            END: END,
        },
    )
    builder.add_edge("primary_assistant_tools", "primary_assistant")

    # Compile graph
    memory = SqliteSaver.from_conn_string(":memory:")
    graph = builder.compile(
    checkpointer=memory,)
    
    
    # ---- INICIANDO A CONVERSAÇÃO -----
    
    # Update with the backup file so we can restart from the original place in each section
    thread_id = str(uuid.uuid4())
    
    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }
    
    _printed = set()
    
    question = "Quais são as melhores opções de passagens aéreas saindo de VIX para São Paulo em 05/08/2024, eu posso chegar em qualquer aeroporto de São Paulo"
    events = graph.stream(
        {"messages": ("user", question)}, config, stream_mode="values"
    )
    for event in events:
        _print_event(event, _printed)
        print(f"-------\n State: {graph.get_state(config)}\n--------")
    snapshot = graph.get_state(config)
    while snapshot.next:
        # We have an interrupt! The agent is trying to use a tool, and the user can approve or deny it
        # Note: This code is all outside of your graph. Typically, you would stream the output to a UI.
        # Then, you would have the frontend trigger a new run via an API call when the user has provided input.
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