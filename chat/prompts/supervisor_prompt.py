# supervisor_prompt.py
from typing import Literal, Optional
from pydantic import BaseModel, Field
import re, json
from langchain_core.messages import AIMessage

# Esquema para a resposta do supervisor
class SupervisorResponse(BaseModel):
    """O esquema para a resposta do supervisor. Deve ser seguido de forma rigorosa."""

    route_to: Literal["flight_searcher", "tourism_searcher"] = Field(..., description="The chosen assistant based on the query")
    thought: Optional[str] = Field(None, description="The thought process behind the decision")
    assistant_hint: Optional[str] = Field(None, description="Hint or additional context for the next assistant")


# prompt para o supervisor
SUPERVISOR_PROMPT = """
Você é um supervisor responsável por analisar a pergunta do usuário e, em seguida, direcioná-la para um assistente especializado.
Você deve responder com apenas uma das seguintes opções com base na pergunta:
- "route":"flight_searcher" para perguntas relacionadas a buscas de voos.
- "route":"tourism_searcher" para perguntas relacionadas ao turismo.

Além de sua decisão, forneça o seguinte:
- "thought": Explique o raciocínio por trás de sua decisão.
- "assistant_hint": Forneça qualquer contexto ou dica útil que o próximo assistente possa precisar.

Apresente sua resposta em JSON que corresponda ao seguinte esquema: ```json\n{schema}\n```.
"""


# função para extrair JSON de uma mensagem AIMessage
def extract_json(message: AIMessage) -> dict:
    """Extracts JSON content from a string where JSON is embedded between 
json and
 tags.

    Parameters:
        text (str): The text containing the JSON content.

    Returns:
        dict: The extracted JSON object.
    """
    text = message.content
    pattern = r"```json(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)

    if matches:
        try:
            return json.loads(matches[0].strip())
        except Exception:
            raise ValueError(f"Failed to parse JSON from the message: {message.content}")
    else:
        raise ValueError(f"No JSON found in the message: {message.content}")