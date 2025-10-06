import os

from kotaemon.chatbot import ChatConversation, SimpleRespondentChatbot
from kotaemon.llms.chats.openai import ChatOpenAI


class ConsoleChat(ChatConversation):
    system_message: str = "You are a helpful assistant."
    bot = SimpleRespondentChatbot(
        llm=ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "dummy-key"),
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0,
        )
    )


if __name__ == "__main__":
    ConsoleChat().terminal_session()

