from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
import threading
from typing import Dict, Optional

from agent.system_prompt import get_system_prompt_one, get_system_prompt
from ctf.agent.system_prompt import get_basic_prompt
from ctf.agent.utils import format_msg_history
from ctf.app_config import settings


class SessionManager:
    """Manages Google ADK sessions per user to ensure persistence across requests."""
    
    def __init__(self):
        self._session_service = InMemorySessionService()
        self._runners: Dict[str, Runner] = {}
        self._lock = threading.Lock()
    
    def get_runner(self, user_id: str, agent: Agent) -> Runner:
        """Get or create a runner for a specific user."""
        with self._lock:
            if user_id not in self._runners:
                # Create a new runner for this user
                runner = Runner(
                    agent=agent,
                    app_name="prompt_ctf",
                    session_service=self._session_service
                )
                self._runners[user_id] = runner
            return self._runners[user_id]
    
    def get_or_create_session(self, user_id: str, session_id: str) -> str:
        """Get or create a session for a user."""
        with self._lock:
            try:
                # Try to get existing session
                self._session_service.get_session(session_id)
                return session_id
            except:
                # Create new session if it doesn't exist
                try:
                    # Try different possible signatures for create_session
                    try:
                        self._session_service.create_session(session_id)
                    except TypeError:
                        # If that fails, try with user_id as keyword argument
                        self._session_service.create_session(session_id, user_id=user_id)
                    return session_id
                except Exception as e:
                    print(f"Error creating session {session_id}: {e}")
                    # If creation fails, try with a new session ID
                    import uuid
                    new_session_id = str(uuid.uuid4())
                    try:
                        self._session_service.create_session(new_session_id)
                    except TypeError:
                        self._session_service.create_session(new_session_id, user_id=user_id)
                    return new_session_id


# Global session manager instance
_session_manager = SessionManager()


def run_agent(
    agent: Agent,
    search_input: str | list,
    file_text: str | None = None,
    level: int = 0,
    system_prompt: str | None = None,
    file_type: str = "",
    max_turns: int = 10,
    user_id: str = "default_user"
):
    if not system_prompt:
        # system_prompt = get_system_prompt(level)
        system_prompt = get_basic_prompt()
    if level < 2:
        system_prompt = get_basic_prompt()
    if level > 6:
        system_prompt = get_system_prompt_one()
    if level > 8:
        system_prompt = get_system_prompt()

    prompt = f"""
       SYSTEM
       {system_prompt}
       {(file_type + " file contents: " + file_text) if file_text else ""}
       Prefer the rag_tool_func tool if unsure which tool to use.
       USER
       Level: {level}
       Query: {search_input}
       """
    from pprint import pprint

    pprint("search_input")
    pprint(search_input)
    
    # Prepare the user message
    if isinstance(search_input, list):
        # Convert list of messages to a single text
        user_text = "\n".join([msg.get("content", "") for msg in search_input if msg.get("role") == "user"])
    else:
        user_text = prompt
    
    # Try to use the agent directly - Google ADK agents should have invoke method
    response_text = ""
    try:
        # Check available methods on the agent
        print(f"Agent methods: {[m for m in dir(agent) if not m.startswith('_')]}")
        
        if hasattr(agent, 'run_live'):
            print("Using agent.run_live() as async generator of chunks")
            import asyncio
            # Collect response chunks and join into a single string
            async def _collect_run_live():
                chunks = []
                async for chunk in agent.run_live(user_text):
                    chunks.append(str(chunk))
                return ''.join(chunks)
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response_text = loop.run_until_complete(_collect_run_live())
                loop.close()
            except Exception as live_error:
                print(f"run_live collection failed: {live_error}")
                response_text = "I'm having trouble processing your request. Please try again."
        elif hasattr(agent, 'run_async'):
            print("Agent has run_async but skipping due to input compatibility issues")
            # Fallback to other methods
            response_text = ""
        elif hasattr(agent, 'invoke'):
            print("Using agent.invoke()")
            response = agent.invoke(user_text)
            response_text = str(response)
        elif hasattr(agent, 'run'):
            print("Using agent.run()")
            response = agent.run(user_text)
            response_text = str(response)
        elif hasattr(agent, 'chat'):
            print("Using agent.chat()")
            response = agent.chat(user_text)
            response_text = str(response)
        elif hasattr(agent, 'generate'):
            print("Using agent.generate()")
            response = agent.generate(user_text)
            response_text = str(response)
        else:
            print("No direct invocation method found, trying Runner with minimal setup")
            # Minimal Runner setup without session management
            try:
                session_service = InMemorySessionService()
                runner = Runner(
                    agent=agent,
                    app_name="prompt_ctf",
                    session_service=session_service
                )
                
                user_message = Content(parts=[Part(text=user_text)])
                import uuid
                session_id = str(uuid.uuid4())
                
                # Try to create session with correct signature
                try:
                    session_service.create_session(session_id)
                except Exception as create_error:
                    print(f"Session creation failed: {create_error}")
                    # Try without creating session first
                    pass
                
                for event in runner.run(
                    user_id=user_id,
                    session_id=session_id,
                    new_message=user_message
                ):
                    if event.is_final_response():
                        response_text = event.content.parts[0].text
                        break
            except Exception as runner_error:
                print(f"Runner approach failed: {runner_error}")
                response_text = "I'm having trouble processing your request. Please try again."
    except Exception as e:
        print(f"Error running agent: {e}")
        response_text = "Sorry, I encountered an error processing your request."

    return response_text, []


def setup_model():
    return LiteLlm(model="ollama_chat/qwen3:0.6b")


def search_vecs_and_prompt(
    search_input: list,
    agent: Agent,
    chat_history: list,
    max_turns: int = 10,
    user_id: str = "default_user"
):

    if chat_history:
        chat_history = format_msg_history(chat_history)
    chat_history = chat_history + search_input
    return run_agent(agent=agent, search_input=chat_history, max_turns=max_turns, user_id=user_id)
