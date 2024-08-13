
# Próximos passos:
# `1. Depois de receber o resultado da chamada da tool o agente de flight search tem que poder chamar mais ferramentas se necessario.`


from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph
from langgraph.checkpoint.aiosqlite import AsyncSqliteSaver
from .nodes.assistant_nodes import supervisor_node, flight_searcher_node, tourism_searcher_node, user_input_node
from .nodes.routing_nodes import route_flight_search, main_routing_function
from .nodes.tool_nodes import execute_flight_search
from .states.agent_state import AgentState
from .utils import reset_database
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the memory
memory = SqliteSaver.from_conn_string(":memory:")

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
