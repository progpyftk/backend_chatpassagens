# services/llm_service.py
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()  # Carrega as variáveis de ambiente do arquivo .env

# Exemplo de uso
if __name__ == "__main__":
    chat = ChatOpenAI(model="gpt-4o-mini-2024-07-18")
    prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant. Answer all questions to the best of your ability.",
        ),
        ("placeholder", "{messages}"),
    ]
    )
    chain = prompt | chat
    
    ai_msg = chain.invoke(
    {
        "messages": [
            (
                "human",
                "Translate this sentence from English to French: I love programming.",
            ),
            ("ai", "J'adore la programmation."),
            ("human", "What did you just say?"),
        ],
    }
    )
    print(ai_msg.content)

