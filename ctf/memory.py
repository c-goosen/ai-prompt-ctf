from typing import List, Dict, Any
from dataclasses import dataclass
from pydantic import BaseModel

@dataclass
class Message:
    role: str
    content: str

class SimpleChatMemory:
    def __init__(self, token_limit: int = 3000, chat_store: Dict[str, List[Message]] = None, chat_store_key: str = None):
        self.token_limit = token_limit
        self.chat_store = chat_store or {}
        self.chat_store_key = chat_store_key
        self.messages: List[Message] = []
        
        if chat_store_key and chat_store_key in chat_store:
            self.messages = chat_store[chat_store_key]
    
    def add_message(self, role: str, content: str) -> None:
        self.messages.append(Message(role=role, content=content))
        if self.chat_store_key:
            self.chat_store[self.chat_store_key] = self.messages
    
    def get_messages(self, key: str = None) -> List[Dict[str, str]]:
        if key:
            messages = self.chat_store.get(key, [])
            return [{"role": msg.role, "content": msg.content} for msg in messages]
        return [{"role": msg.role, "content": msg.content} for msg in self.messages]
    
    def clear(self) -> None:
        self.messages = []
        if self.chat_store_key and self.chat_store_key in self.chat_store:
            del self.chat_store[self.chat_store_key]
    
    @classmethod
    def from_defaults(cls, token_limit: int = 3000, chat_store: Dict[str, List[Message]] = None, chat_store_key: str = None):
        return cls(token_limit=token_limit, chat_store=chat_store, chat_store_key=chat_store_key) 