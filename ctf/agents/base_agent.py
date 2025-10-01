"""
Base agent class for CTF challenges using Google ADK with Sequential Workflow and Guardrails
"""

from typing import Any, Dict, List, Optional
from google.adk import LlmAgent, SequentialAgent, Tool
from google.adk.models import OllamaModel
from google.adk.runners import Runner
from google.adk.sessions import Session, SessionService, InMemorySessionService
from ctf.agent.tools import submit_answer_func, hints_func, rag_tool_func


class BaseCTFAgent:
    """Base class for CTF challenge agents with workflow protection"""
    
    def __init__(self, level: int, system_prompt: str):
        self.level = level
        self.system_prompt = system_prompt
        self.model = OllamaModel(
            model_name="qwen2.5:0.5b",
            base_url="http://localhost:11434"
        )
        
        # Define tools available to all agents
        self.tools = [
            Tool.from_function(submit_answer_func),
            Tool.from_function(hints_func),
            Tool.from_function(rag_tool_func),
        ]
        
        # Create the main LLM agent
        self.main_agent = LlmAgent(
            model=self.model,
            system_prompt=self.system_prompt,
            tools=self.tools,
        )
        
        # Create session service for state management
        self.session_service = InMemorySessionService()
        
        # Create runner with callbacks for protection
        self.runner = Runner(
            session_service=self.session_service,
            before_model_callback=self._before_model_callback,
            after_model_callback=self._after_model_callback,
            before_tool_callback=self._before_tool_callback,
        )
        
        # Create sequential workflow agent
        self.workflow_agent = SequentialAgent(
            agents=[self.main_agent],
            runner=self.runner,
        )
    
    async def _before_model_callback(self, session: Session, user_input: str) -> Optional[str]:
        """Guardrail: Check input before sending to model"""
        # Log the input for monitoring
        print(f"[Level {self.level}] Input received: {user_input[:100]}...")
        
        # Check for obvious prompt injection patterns
        injection_patterns = [
            "ignore previous instructions",
            "forget everything",
            "you are now",
            "pretend to be",
            "act as if",
            "system prompt",
            "jailbreak",
            "override",
        ]
        
        user_input_lower = user_input.lower()
        for pattern in injection_patterns:
            if pattern in user_input_lower:
                print(f"[Level {self.level}] BLOCKED: Detected injection pattern '{pattern}'")
                return f"I cannot process requests that contain '{pattern}'. Please rephrase your question."
        
        # Level-specific protection
        if self.level >= 3:
            # Enhanced protection for higher levels
            advanced_patterns = [
                "roleplay",
                "simulation",
                "hypothetical",
                "what if",
                "imagine",
            ]
            for pattern in advanced_patterns:
                if pattern in user_input_lower:
                    print(f"[Level {self.level}] BLOCKED: Detected advanced injection pattern '{pattern}'")
                    return f"Advanced injection attempts are not allowed. Please ask direct questions."
        
        # Store input in session state for analysis
        session.state["last_input"] = user_input
        session.state["input_count"] = session.state.get("input_count", 0) + 1
        
        return None  # Allow the request to proceed
    
    async def _after_model_callback(self, session: Session, response: str) -> Optional[str]:
        """Guardrail: Check output after model generates response"""
        # Log the response for monitoring
        print(f"[Level {self.level}] Response generated: {response[:100]}...")
        
        # Check for sensitive information leakage
        sensitive_patterns = [
            "password",
            "secret",
            "key",
            "token",
            "credential",
        ]
        
        response_lower = response.lower()
        for pattern in sensitive_patterns:
            if pattern in response_lower and self.level >= 1:
                print(f"[Level {self.level}] FILTERED: Detected sensitive pattern '{pattern}' in response")
                # Replace with generic message
                return "I cannot provide sensitive information. Please ask for hints if you need help."
        
        # Store response in session state
        session.state["last_response"] = response
        session.state["response_count"] = session.state.get("response_count", 0) + 1
        
        return None  # Allow the response to proceed
    
    async def _before_tool_callback(self, session: Session, tool_name: str, tool_args: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Guardrail: Check tool usage before execution"""
        print(f"[Level {self.level}] Tool requested: {tool_name} with args: {tool_args}")
        
        # Check for SQL injection in sql_query tool
        if tool_name == "sql_query" and "user_id" in tool_args:
            user_id = str(tool_args["user_id"])
            sql_injection_patterns = [
                "' OR '1'='1",
                "'; DROP TABLE",
                "UNION SELECT",
                "INSERT INTO",
                "DELETE FROM",
            ]
            
            for pattern in sql_injection_patterns:
                if pattern.upper() in user_id.upper():
                    print(f"[Level {self.level}] BLOCKED: SQL injection detected in user_id")
                    return {
                        "status": "error",
                        "error_message": "Invalid user ID format detected. Please provide a valid user ID."
                    }
        
        # Check for file path traversal in file operations
        if "path" in tool_args or "file" in tool_args:
            path_value = str(tool_args.get("path", tool_args.get("file", "")))
            if ".." in path_value or "/etc/" in path_value or "C:\\" in path_value:
                print(f"[Level {self.level}] BLOCKED: Path traversal detected")
                return {
                    "status": "error", 
                    "error_message": "Invalid file path detected. Access denied."
                }
        
        # Store tool usage in session state
        session.state["last_tool"] = tool_name
        session.state["tool_count"] = session.state.get("tool_count", 0) + 1
        
        return None  # Allow the tool to proceed
    
    async def run(self, user_input: str) -> str:
        """Run the agent with user input through sequential workflow"""
        try:
            # Create a new session for this interaction
            session = Session()
            
            # Run through the sequential workflow
            response = await self.workflow_agent.run(user_input, session=session)
            
            return response.content if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            print(f"[Level {self.level}] Error in agent execution: {str(e)}")
            return f"I encountered an error processing your request. Please try again."
    
    def get_agent(self) -> SequentialAgent:
        """Get the underlying workflow agent"""
        return self.workflow_agent
    
    def get_session_service(self) -> SessionService:
        """Get the session service for state management"""
        return self.session_service
