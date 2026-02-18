from .base_agent import BaseAgent, AgentInput, AgentOutput, AgentState
from services.ollama_service import ollama_service
import json

class OptimizationAgent(BaseAgent):
    """
    Agent responsible for analyzing existing infrastructure and suggesting optimizations.
    """
    def __init__(self):
        super().__init__(
            name="OptimizationAgent",
            description="Analyzes AWS resources and suggests cost, performance, and security optimizations."
        )
        self.system_prompt = """You are an expert AWS Architecture optimization specialist.
Given a JSON list of existing AWS resources, analyze it and provide actionable optimization suggestions based strictly on user prompt.
Only Provide optimizations which are relevant to the user prompt, do not provide any optimizations which are not related to user prompt

Provide your analysis in a VALID JSON format
In the JSON key-value pairs, the key is the type of optimization that you are suggesting and the value field will have multiple values like the resource id, resource type, optimization suggestion and estimated improvement.
the response should follow the given structure:
"OptimizationSuggestions": [
{
    "type": "EC2 Instance Optimization",
    "resourceId": "i-0f589186239f36ee4",
    "resourceType": "AWS::EC2::Instance",
    "optimizationSuggestion": "Increase instance type to 't3.2xlarge' for better performance and cost efficienc",
    "estimatedImprovement": "10% increase in throughput and 15% reduction in costs"
},
{
    "type": "IAM Role Optimization",
    "resourceId": "AROARYEUCLW6B5OGZG6QZ",
    "resourceType": "AWS::IAM::Role",
    "optimizationSuggestion": "Limit access to necessary resources and remove unnecessary permissions.",
    "estimatedImprovement": "25% reduction in security risks and 10% decrease in costs"
}
]
"""
# Focus on these key areas:
# 1.  **Cost Savings**: Identify unused or underutilized resources (e.g., old snapshots, unattached EBS volumes, idle load balancers). Suggest rightsizing EC2 instances. Recommend Savings Plans or Reserved Instances.
# 2.  **Performance**: Suggest upgrading to newer generation instance types (e.g., t3 to t4g). Recommend using a CDN like CloudFront for S3 buckets.
# 3.  **Security**: Point out security groups open to the world (0.0.0.0/0) on sensitive ports. Check for public S3 buckets. Recommend using IAM Roles over static credentials.
# 4.  **High Availability**: Suggest moving single-instance deployments into an Auto Scaling Group across multiple AZs.

# like this:
# {
#   "Optimization Type": [
#     {
#       "resource_id": "vol-012345abc",
#       "resource_type": "AWS::EC2::Volume",
#       "suggestion": "This EBS volume is 'available' and not attached to any instance. Consider deleting it to save costs.",
#       "estimated_improvement": ""
#     }
#   ]

    def validate_input(self, input_data: AgentInput) -> bool:
        """
        For this agent, validation simply means checking if the required data
        exists in the state from the previous agent. It doesn't use the prompt directly.
        """
        # This method is required by the BaseAgent, but for this agent,
        # the primary validation happens inside the execute method by checking the state.
        return True

    async def execute(self, input_data: AgentInput, state: AgentState) -> AgentOutput:
        print("Executing OptimizationAgent...")
        
        # 1. Get the discovered resources from the state
        existing_infrastructure = state.context.get("existing_infrastructure")
        if not existing_infrastructure:
            return self._create_error_output(input_data.session_id, "No existing infrastructure found in the state to analyze.")

        # 2. Prepare the data for the LLM
        # To avoid making the prompt too large, we'll just send a summary for now.
        # A more advanced version could send details chunk by chunk.
        resource_summary = {
            rtype: [
                {
                    "resourceId": res.get("resourceId"),
                    "awsRegion": res.get("awsRegion"),
                    "tags": res.get("tags")
                } for res in rlist
            ]
            for rtype, rlist in existing_infrastructure.items() if rlist
        }
        
        user_prompt = f"""User Request: "{input_data.prompt}"
        Analyze the following AWS resource summary based on the user's request and provide optimization suggestions.Resource Summary: {json.dumps(resource_summary, indent=2)}"""

        # 3. Call the LLM to get optimization suggestions
        try:
            optimization_suggestions = await ollama_service.generate_structured_response(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt
            )
        except Exception as e:
            return self._create_error_output(input_data.session_id, f"LLM generation failed: {e}")

        # 4. Update the state with the results
        self.update_state(state, {
            "optimization_summary": optimization_suggestions,
            "optimization_complete": True
        })

        return AgentOutput(
            agent_name=self.name,
            session_id=input_data.session_id,
            result=optimization_suggestions,
            status="complete",
            next_agent=None # This is the last agent in this workflow for now
        )

    def _create_error_output(self, session_id: str, error_message: str) -> AgentOutput:
        """Creates a standardized error output."""
        return AgentOutput(
            agent_name=self.name,
            session_id=session_id,
            result={},
            status="error",
            metadata={"error": error_message}
        )