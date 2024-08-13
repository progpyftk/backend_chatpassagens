from langchain_core.messages import SystemMessage, HumanMessage
from ..prompts.supervisor_prompt import SUPERVISOR_PROMPT, extract_json
from ..states.agent_state import AgentState
from services.llm_service import LLMService
import pprint
from langchain_core.messages import SystemMessage, ToolMessage
from ..prompts.flight_searcher_prompt import FLIGHT_SEARCHER_PROMPT, FLIGHT_SEARCHER_TOOL_RESPONSE_PROMPT
from ..tools import search_amadeus_flights, flight_price_analisys
from ..states.agent_state import AgentState
from services.llm_service import LLMService

llm = LLMService().get_llm()

def supervisor_node(state: AgentState):
    """Node function for the supervisor agent."""
    print(len(state['messages']))
    for message in state['messages']:
        print(message)
    print("----   supervisor_node   ----")
    response = llm.invoke([SystemMessage(content=SUPERVISOR_PROMPT)] + state['messages'])
    print("\n----   Resposta criada pela LLM SUPERVISOR   ----")
    pprint.pprint(response)
    parsed_response = extract_json(response)
    print("\n----   Resposta do SUPERVISOR após o extract_json   ----")
    pprint.pprint(parsed_response)
    next_assistant = parsed_response['route']

    # Ensure the response is either "flight_searcher" or "tourism_searcher"
    if next_assistant not in ["flight_searcher", "tourism_searcher"]:
       raise ValueError(f"Unexpected assistant type: {next_assistant}")
    
    print(f"Next assistant: {next_assistant}")
    return {"messages": response, "next_assistant": next_assistant}

def flight_searcher_node(state: AgentState):
    """Node function for the flight searcher agent."""
    print("----   flight_searcher_node   ----")
    tools = [search_amadeus_flights, flight_price_analisys]
    if state['messages'] and isinstance(state['messages'][-1], ToolMessage):
        state['messages'].extend([SystemMessage(content=FLIGHT_SEARCHER_TOOL_RESPONSE_PROMPT.format(content=state['messages']))])
        response = llm.bind_tools(tools, parallel_tool_calls=True).invoke(state['messages'])
        print("\n----   Resposta criada pela LLM apóis a chamada das Tools dentro do if   ----")
        print(response)
        return {"messages": response}
    
    response = llm.bind_tools(tools, parallel_tool_calls=True).invoke(
        [SystemMessage(content=FLIGHT_SEARCHER_PROMPT)] + state['messages'])
    print("\n----   Resposta da LLM para realizar a chamada da Tool OU responder o usuário   ----")
    print(response)

    return {"messages": response}

def tourism_searcher_node(state: AgentState):
    """Node function for the tourism searcher agent."""
    tools = [search_amadeus_flights]
    response = llm.bind_tools(tools, parallel_tool_calls=True).invoke(
        [SystemMessage(content="prompt do tourist searcher")] + state['messages'])
    return {"messages": response}

def user_input_node(state: AgentState):
    """Node function to capture user input."""
    print("----   user_input_node   ----")
    user_input = input()
    return {"messages": [HumanMessage(content=user_input)]}
