from .base_agent import BaseAgent, AgentInput, AgentOutput, AgentState
from services.aws_service import aws_service
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

class AwsFetchAgent(BaseAgent):
    """
    Agent responsible for fetching existing AWS infrastructure using the AWSService.
    """
    
    def __init__(self):
        super().__init__(
            name="AwsFetchAgent",
            description="Fetches current AWS infrastructure to provide context for new designs."
        )
    
    def validate_input(self, input_data: AgentInput) -> bool:
        """
        Validates the input for the AwsFetchAgent.
        For this agent, no specific input is required, so it always returns True.
        This method is required by the BaseAgent abstract class.
        """
        return True

    async def execute(self, input_data: AgentInput, state: AgentState) -> AgentOutput:
        """
        Executes the AWS resource discovery process.
        """
        print("Executing AwsFetchAgent...")
        try:
            discovered_resources = await aws_service.discover_resources()
            
            if not discovered_resources:
                return AgentOutput(
                    agent_name=self.name,
                    session_id=input_data.session_id,
                    result={"message": "No existing AWS resources found or AWS Config is not enabled."},
                    status="complete_with_warning",
                    next_agent="optimization_agent" # Or another appropriate agent
                )

            # Update the shared state with the discovered infrastructure
            self.update_state(state, {
                "existing_infrastructure": discovered_resources,
                "aws_scan_complete": True
            })

            return AgentOutput(
                agent_name=self.name,
                session_id=input_data.session_id,
                result={
                    "summary": f"Discovered {sum(len(v) for v in discovered_resources.values())} resources across {len(discovered_resources)} service types.",
                    "discovered_resources": discovered_resources
                },
                status="complete",
                next_agent="optimization_agent" # Or another appropriate agent
            )

        except (NoCredentialsError, PartialCredentialsError):
            error_msg = "AWS credentials not found. Please configure them as environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)."
            print(f"ERROR: {error_msg}")
            return self._create_error_output(input_data.session_id, error_msg)
        except Exception as e:
            error_msg = f"An unexpected error occurred during AWS discovery: {str(e)}"
            print(f"ERROR: {error_msg}")
            return self._create_error_output(input_data.session_id, error_msg)

    def _create_error_output(self, session_id: str, error_message: str) -> AgentOutput:
        """Creates a standardized error output."""
        return AgentOutput(
            agent_name=self.name,
            session_id=session_id,
            result={},
            status="error",
            metadata={"error": error_message}
        )