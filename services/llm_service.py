# llm_service.py
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

class LLMService:
    def __init__(self):
        # self.llm = ChatOpenAI(api_key=os.getenv('OPENAI_API_KEY'), model="gpt-4o-mini-2024-07-18", temperature=0)
        self.llm = ChatOpenAI(api_key=os.getenv('OPENAI_API_KEY'), model="gpt-4o", temperature=0)

    def get_llm(self):
        return self.llm
