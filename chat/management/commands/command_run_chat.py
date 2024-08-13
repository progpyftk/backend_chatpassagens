# chat/management/commands/command_run_chat.py
import asyncio

from django.core.management.base import BaseCommand
# from chat.run_chat import run_chatbot
from chat.run_chat import run_chatbot

class Command(BaseCommand):
    help = 'Run the chatbot'

    def handle(self, *args, **kwargs):
        print('Entrando no command_run_chat')
        asyncio.run(run_chatbot())
