from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import uuid

class AgentState(BaseModel):
    """Base state for agent communication"""
    session_id: str
    messages: List[Dict[str, Any]] = []
    context: Dict[str, Any] = {}
    current_step: str = ""
    status: str = "pending"  # pending, processing, complete, error
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class AgentInput(BaseModel):
    """Input structure for agents"""
    prompt: str
    context: Dict[str, Any] = {}
    session_id: str
    previous_results: Dict[str, Any] = {}

class AgentOutput(BaseModel):
    """Output structure for agents"""
    agent_name: str
    session_id: str
    result: Dict[str, Any]
    status: str
    next_agent: Optional[str] = None
    metadata: Dict[str, Any] = {}

class BaseAgent(ABC):
    """Base class for all ArchiMind agents"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.agent_id = str(uuid.uuid4())
    
    @abstractmethod
    async def execute(self, input_data: AgentInput, state: AgentState) -> AgentOutput:
        """Execute the agent's main functionality"""
        pass
    
    @abstractmethod
    def validate_input(self, input_data: AgentInput) -> bool:
        """Validate input data for this agent"""
        pass
    
    def update_state(self, state: AgentState, updates: Dict[str, Any]) -> AgentState:
        """Update agent state with new information"""
        for key, value in updates.items():
            if hasattr(state, key):
                setattr(state, key, value)
            else:
                state.context[key] = value
        return state
    
    def log_execution(self, input_data: AgentInput, output: AgentOutput):
        """Log agent execution for debugging"""
        print(f"[{self.name}] Executed for session {input_data.session_id}")
        print(f"[{self.name}] Status: {output.status}")