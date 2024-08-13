
from langchain_core.messages import SystemMessage
from ..prompts.supervisor_prompt import SUPERVISOR_PROMPT, extract_json
from ..states.agent_state import AgentState
from services.llm_service import LLMService
import pprint
from langchain_core.messages import SystemMessage, ToolMessage
from ..prompts.flight_searcher_prompt import FLIGHT_SEARCHER_PROMPT, FLIGHT_SEARCHER_TOOL_RESPONSE_PROMPT
from ..tools import search_amadeus_flights, flight_price_analisys
from ..states.agent_state import AgentState
from services.llm_service import LLMService
from langgraph.prebuilt import ToolNode


# Initialize tools
tools = [search_amadeus_flights, flight_price_analisys]
tool_node = ToolNode(tools)

def execute_flight_search(state: AgentState):
    """Node function to execute the flight search tool."""
    print('\n----   execute_flight_search   ----')
    result = tool_node.invoke({"messages": state["messages"]})
    return {"messages": result['messages']}