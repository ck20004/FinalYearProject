from typing import Dict, Any
import json
import asyncio
from .base_agent import BaseAgent, AgentInput, AgentOutput, AgentState
from services.ollama_service import ollama_service
from services.vector_db_service import vector_db_service

class InfraDesignerAgent(BaseAgent):
    """Enhanced Agent responsible for designing AWS infrastructure"""
    
    def __init__(self):
        super().__init__(
            name="InfraDesignerAgent",
            description="Designs AWS infrastructure based on user requirements and best practices"
        )
        self.system_prompt = """You are an expert AWS Solutions Architect with 10+ years of hands-on experience designing secure, scalable, and cost-effective cloud infrastructure.

IMPORTANT: RESPOND WITH VALID JSON ONLY:

{
  "analysis": {
    "app_type": "web app/api/data pipeline",
    "scale": "small/medium/large",
    "expected_users": 1000,
    "concurrent_users": 100,
    "key_requirements": ["requirement1", "requirement2"],
    "region": "ap-south-1"/"us-east-1"/ etc.,
  },
  "services": [
    {
      "name": "web-tier",
      "aws_service": "EC2/Lambda/ECS",
      "instance_type": "t3.medium",
      "configuration": {"vcpus": 2, "memory_gb": 4},
      "purpose": "handles requests",
      "estimated_monthly_cost_usd": 50
    }
  ],
  "architecture_type": "3-tier/serverless/microservices",
  "networking": {
    "vpc_cidr": "10.0.0.0/16",
    "public_subnets": 2,
    "private_subnets": 2,
    "load_balancer": "ALB"
  },
  "cost_estimate": {
    "currency": "INR",
    "estimated_total_monthly_cost": 4150,
    "cost_breakdown": {"compute": 2500, "database": 1250, "networking": 400}
  },
  "rationale": "Brief explanation of design decisions"
}

COST GUIDELINES (USD to INR * 83):
- t3.micro: $8/month, t3.small: $17/month, t3.medium: $34/month
- RDS t3.micro: $15/month, ALB: $23/month

NAT Gateway: $45/month

S3 storage: $0.024/GB-month

DESIGN RULES:
1. Use provided user metrics (expected_users, concurrent_users, daily_requests, latency_requirements, storage) to size resources appropriately
2. Default region = ap-south-1 (Mumbai), default currency = INR
3. Be specific with instance types, database engines, storage classes, and exact services
4. Consider usage patterns for scaling and cost optimization
5. Design for the specified latency requirements
6. Plan storage based on provided storage requirements
7. Scale compute resources based on concurrent users and daily requests
8. Include constraints in design decisions"""

# CRITICAL: You MUST include a "connections" array to define the data flow.
# Each object in the array must have a "from" and a "to" key, matching the "name" of the services you defined.
# You can also include an optional "label" for the connection (e.g., "HTTPS", "Read/Write", "API Call").

# Example "connections" array:
# "connections": [
#   { "from": "Internet_Gateway", "to": "Application_Load_Balancer", "label": "HTTPS Traffic" },
#   { "from": "Application_Load_Balancer", "to": "Web_Server_ASG" },
#   { "from": "Web_Server_ASG", "to": "User_Database", "label": "SQL" },
#   { "from": "Web_Server_ASG", "to": "Product_Images_S3", "label": "S3 API" }
# ]
    
    async def execute(self, input_data: AgentInput, state: AgentState) -> AgentOutput:
        """Execute enhanced infrastructure design"""
        try:
            # Validate input
            if not self.validate_input(input_data):
                return self._create_error_output(
                    input_data.session_id,
                    "Invalid input: Prompt must be at least 10 characters"
                )
            
            # Check Ollama availability
            if not ollama_service.is_available():
                return self._create_error_output(
                    input_data.session_id,
                    "Ollama service not available. Please start Ollama with: ollama serve"
                )
            
            print("🔎 Searching for relevant architecture patterns...")
            try:
                similar_patterns = vector_db_service.search_similar_patterns(input_data.prompt, limit=6)
                if similar_patterns:
                    print(f"✅ Found {len(similar_patterns)} relevant patterns.")
                else:
                    print("⚠️ No relevant patterns found. Proceeding with base knowledge.")
            except Exception as e:
                print(f"⚠️ Vector DB search failed: {e}. Proceeding without examples.")
                similar_patterns = []
            
            examples_prompt_section = ""
            if similar_patterns:
                examples_json = json.dumps([p['architecture'] for p in similar_patterns], indent=2)
                examples_prompt_section = f"""
                ---
                REFERENCE ARCHITECTURES:
                Here are some reference architectures that are similar to the user's request.
                Use these as inspiration for your design.

                {examples_json}
                ---
                """

            user_prompt = f"""{examples_prompt_section}
            
            Design AWS infrastructure for:
            
            Prompt: {input_data.prompt}
            Users: {input_data.context.get('expected_total_users', 1000)}
            Concurrent: {input_data.context.get('concurrent_users', 100)}
            Region: {input_data.context.get('region', 'ap-south-1')}
            Budget: ${input_data.context.get('max_cost', 'flexible')}/month
            
            Design optimized AWS architecture in JSON format."""
            
            # SINGLE ATTEMPT WITH TIMEOUT
            try:
                # Set a timeout for the generation
                architecture_design = await asyncio.wait_for(
                    ollama_service.generate_structured_response(
                        system_prompt=self.system_prompt,
                        user_prompt=user_prompt,
                        context=input_data.context
                    ),
                    timeout=1200  # 60 second timeout
                )
                
                # Quick validation and fallback
                if architecture_design.get("raw_response"):
                    architecture_design = self._create_quick_fallback(input_data.context)
                
            except asyncio.TimeoutError:
                print("⏰ Ollama generation timeout, using fallback")
                architecture_design = self._create_quick_fallback(input_data.context)
            
            # Update state
            self.update_state(state, {
                "current_step": "infrastructure_design_complete",
                "architecture": architecture_design,
                "status": "processing"
            })
            
            return AgentOutput(
                agent_name=self.name,
                session_id=input_data.session_id,
                result={
                    "architecture": architecture_design,
                    "model_used": ollama_service.default_model,
                    # "requirements_analysis": requirements
                },
                status="complete",
                next_agent=None,
            )
            
        except Exception as e:
            return self._create_error_output(input_data.session_id, f"Execution error: {str(e)}")
        
    def _create_quick_fallback(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Quick fallback design - minimal but complete"""
        users = context.get("expected_total_users", 1000)
        concurrent = context.get("concurrent_users", 100)
        
        # Quick sizing logic
        if concurrent > 500:
            instance_type = "t3.medium"
            instance_cost = 34
        elif concurrent > 100:
            instance_type = "t3.small"
            instance_cost = 17
        else:
            instance_type = "t3.micro"
            instance_cost = 8
        
        total_cost_usd = instance_cost + 15 + 23  # Instance + RDS + ALB
        total_cost_inr = total_cost_usd * 83
        
        return {
            "analysis": {
                "app_type": "web application",
                "scale": "medium" if users > 5000 else "small",
                "expected_users": users,
                "concurrent_users": concurrent,
                "key_requirements": ["web hosting", "database"]
            },
            "services": [
                {
                    "name": "web-tier",
                    "aws_service": "EC2",
                    "instance_type": instance_type,
                    "configuration": {"vcpus": 2, "memory_gb": 4},
                    "purpose": "Host web application",
                    "estimated_monthly_cost_usd": instance_cost
                },
                {
                    "name": "database",
                    "aws_service": "RDS MySQL",
                    "instance_type": "db.t3.micro",
                    "configuration": {"engine": "MySQL 8.0", "multi_az": True},
                    "purpose": "Application database",
                    "estimated_monthly_cost_usd": 15
                }
            ],
            "architecture_type": "3-tier web application",
            "networking": {
                "vpc_cidr": "10.0.0.0/16",
                "public_subnets": 2,
                "private_subnets": 2,
                "load_balancer": "ALB"
            },
            "cost_estimate": {
                "currency": "INR",
                "estimated_total_monthly_cost": total_cost_inr,
                "cost_breakdown": {
                    "compute": instance_cost * 83,
                    "database": 15 * 83,
                    "networking": 23 * 83
                }
            },
            "rationale": f"Optimized for {users:,} users with {concurrent:,} concurrent capacity using {instance_type} instances."
        }
    
    def _create_error_output(self, session_id: str, error_message: str) -> AgentOutput:
        """Create standardized error output"""
        return AgentOutput(
            agent_name=self.name,
            session_id=session_id,
            result={},
            status="error",
            metadata={"error": error_message}
        )
    
    def validate_input(self, input_data: AgentInput) -> bool:
        """Enhanced input validation"""
        if not input_data.prompt or len(input_data.prompt.strip()) < 10:
            return False
        
        # # Check for basic architecture keywords
        # prompt_lower = input_data.prompt.lower()
        # architecture_keywords = [
        #     "app", "application", "website", "system", "service", 
        #     "platform", "infrastructure", "deploy", "host"
        # ]
        
        # if not any(keyword in prompt_lower for keyword in architecture_keywords):
        #     return False
        
        return True