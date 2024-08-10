
from langchain_core.messages import SystemMessage
from ..prompts.supervisor_prompt import SUPERVISOR_PROMPT, extract_json
from ..states.agent_state import AgentState
from services.llm_service import LLMService
import pprint
from langchain_core.messages import SystemMessage, ToolMessage
from ..prompts.flight_searcher_prompt import FLIGHT_SEARCHER_PROMPT, FLIGHT_SEARCHER_TOOL_RESPONSE_PROMPT
from ..tools import search_amadeus_flights
from ..states.agent_state import AgentState
from services.llm_service import LLMService


def route_flight_search(state: AgentState):
    """Routing function to decide if the tool should be executed."""
    print('\n----   route_flight_search   ----')
    if state["messages"][-1].tool_calls:    
        print("router verificou que a última mensagem foi uma necessidade chamada de tool")
        return "execute_flight_search"
    else:
        print("router verificou que a última mensagem NÃO FOI uma necessidade chamada de tool")
        return "user_input"
    
def main_routing_function(state: AgentState):
    """Main routing function to determine the next assistant."""
    if state["next_assistant"] == "flight_searcher":
        return "flight_searcher"
    
    if state["next_assistant"] == "tourism_searcher":
        return "tourism_searcher"
    
    return "supervisor"