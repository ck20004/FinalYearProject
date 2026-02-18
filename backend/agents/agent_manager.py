from typing import Dict, Any, Optional, List
from .base_agent import BaseAgent, AgentInput, AgentOutput, AgentState
from .infra_designer_agent import InfraDesignerAgent
from .aws_fetch_agent import AwsFetchAgent
from .optimization_agent import OptimizationAgent
import asyncio

class AgentManager:
    """Manages the orchestration of multiple agents"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.workflows: Dict[str, List[str]] = {}
        self._initialize_agents()
        self._setup_workflows()
    
    def _initialize_agents(self):
        
        # Register agents
        self.agents = {
            "infra_designer": InfraDesignerAgent(),
            "aws_fetch": AwsFetchAgent(),
            "optimization_agent": OptimizationAgent(),
        }
    
    def _setup_workflows(self):
        """Define agent execution workflows"""
        self.workflows = {
            "architecture_generation": [
                "infra_designer",
            ],
            "optimize_existing_architecture": [
                "aws_fetch",
                "optimization_agent",
            ]
        }
    
    async def execute_workflow(
        self, 
        workflow_name: str, 
        initial_input: AgentInput, 
        initial_state: AgentState
    ) -> AgentState:
        """
        Executes a predefined workflow of agents.
        """
        if workflow_name not in self.workflows:
            raise ValueError(f"Workflow '{workflow_name}' not found.")
        
        workflow = self.workflows[workflow_name]
        current_state = initial_state
        current_input = initial_input
        last_output: Optional[AgentOutput] = None

        for agent_name in workflow:
            if agent_name not in self.agents:
                raise ValueError(f"Agent '{agent_name}' not found in agent manager.")
            
            agent = self.agents[agent_name]
            print(f"Executing agent: {agent.name}")
            
            # Update state before execution
            current_state.current_step = f"executing_{agent_name}"
            
            output = await agent.execute(current_input, current_state)
            last_output = output  # Store the most recent output

            if output.status == "error":
                print(f"Agent {agent.name} failed with error: {output.metadata.get('error')}")
                current_state.status = "error"
                current_state.error = output.metadata.get('error', 'Unknown agent error')
                return current_state
            
            # Pass results to the next agent in the chain
            current_input.previous_results[agent_name] = output.result
        
        # After the loop, set the final state's result from the last agent's output
        if last_output and current_state.status != "error":
            current_state.result = last_output.result
            current_state.status = "complete"
            current_state.current_step = "workflow_complete"
        
        return current_state
    
    async def execute_single_agent(
        self, 
        agent_name: str, 
        input_data: AgentInput, 
        state: AgentState
    ) -> AgentOutput:
        """Execute a single agent"""
        if agent_name not in self.agents:
            raise ValueError(f"Agent {agent_name} not found")
        
        agent = self.agents[agent_name]
        return await agent.execute(input_data, state)
    
    def get_available_agents(self) -> List[str]:
        """Get list of available agents"""
        return list(self.agents.keys())
    
    def get_available_workflows(self) -> List[str]:
        """Get list of available workflows"""
        return list(self.workflows.keys())

# Global agent manager instance
agent_manager = AgentManager()