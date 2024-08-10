from typing import List, Dict
from typing_extensions import Annotated, TypedDict
from langgraph.graph.message import add_messages

# Define the AgentState TypedDict
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    task: str
    next_assistant: str
    content: List[str]
    tool_calls: List[Dict]  # Add this field to store tool calls