import ollama
import asyncio
from typing import Dict, Any, Optional, List
from agents.config import agent_config
import json

class OllamaService:
    """Service for interacting with local Ollama models"""
    
    def __init__(self):
        self.base_url = agent_config.ollama_base_url
        self.default_model = agent_config.default_model
        self.fallback_model = agent_config.fallback_model
        self.temperature = agent_config.temperature
        self.client = ollama.Client(host=self.base_url)
        self.available_models = []
        self._check_ollama_connection()
    
    def _check_ollama_connection(self):
        """Check if Ollama is running and get available models"""
        try:
            # Create client
            client = ollama.Client(host=self.base_url)
            
            # Get list of available models
            models = client.list()
            self.available_models = [model['name'] for model in models['models']]
            print(f"✅ Connected to Ollama. Available models: {self.available_models}")
            
            # Check if default model is available
            if self.default_model not in self.available_models:
                print(f"⚠️  Default model {self.default_model} not found. Available: {self.available_models}")
                if self.fallback_model in self.available_models:
                    self.default_model = self.fallback_model
                    print(f"📝 Using fallback model: {self.default_model}")
                elif self.available_models:
                    self.default_model = self.available_models[0]
                    print(f"📝 Using first available model: {self.default_model}")
        
        except Exception as e:
            print(f"❌ Failed to connect to Ollama: {e}")
            print("Make sure Ollama is running with: ollama serve")
            self.available_models = []
    
    async def generate_response(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        context: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        stream: bool = False
    ) -> str:
        """Generate response using Ollama model"""
        
        model = model or self.default_model
        
        if model not in self.available_models:
            raise ValueError(f"Model {model} not available. Available models: {self.available_models}")
        
        # Construct the full prompt
        full_prompt = f"""System: {system_prompt}\n\nUser: {user_prompt}"""
        
        # Add context if provided
        if context:
            context_text = f"\nContext: {json.dumps(context, indent=2)}"
            full_prompt += context_text
        
        full_prompt += "\n\nAssistant:"
        
        try:
            # Create client for this request
            client = ollama.Client(host=self.base_url)
            
            # Use asyncio to run the synchronous ollama call
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.generate(
                    model=model,
                    prompt=full_prompt,
                    options={
                        'temperature': self.temperature,
                        'num_ctx': 4096,  # Context window
                        'top_p': agent_config.top_p,
                        'repeat_penalty': agent_config.repeat_penalty
                    }
                )
            )
            
            return response['response'].strip()
        
        except Exception as e:
            # Try fallback model if available
            if model != self.fallback_model and self.fallback_model in self.available_models:
                print(f"⚠️  Model {model} failed, trying fallback {self.fallback_model}")
                return await self.generate_response(
                    system_prompt, 
                    user_prompt, 
                    context, 
                    self.fallback_model
                )
            else:
                raise Exception(f"Ollama generation failed: {str(e)}")
    
    async def generate_structured_response(
        self,
        system_prompt: str,
        user_prompt: str,
        context: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate structured JSON response"""
        
        # Enhanced system prompt for JSON output
        json_system_prompt = f"""{system_prompt}

IMPORTANT: Your response MUST be valid JSON format. Do not include any text before or after the JSON object.
Start your response with {{ and end with }}.
"""
        
        response_text = await self.generate_response(
            json_system_prompt,
            user_prompt,
            context,
            model
        )
        
        try:
            # Try to parse JSON from response
            import re
            
            # Extract JSON from response (in case there's extra text)
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group()
                return json.loads(json_text)
            else:
                # If no JSON found, create a structured response
                return {
                    "status": "success",
                    "content": response_text,
                    "raw_response": True
                }
        
        except json.JSONDecodeError as e:
            print(f"⚠️  Failed to parse JSON from response: {e}")
            return {
                "status": "partial_success",
                "content": response_text,
                "parse_error": str(e),
                "raw_response": True
            }
    
    def is_available(self) -> bool:
        """Check if Ollama service is available"""
        return len(self.available_models) > 0
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        return self.available_models
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get information about a specific model"""
        try:
            client = ollama.Client(host=self.base_url)
            info = client.show(model_name)
            return info
        except Exception as e:
            return {"error": str(e)}

# Global Ollama service instance
ollama_service = OllamaService()