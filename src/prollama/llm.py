"""
LLM interface for Prollama
"""

from typing import Dict, Any, Optional, List
import httpx
from pydantic import BaseModel, Field
from rich.console import Console

console = Console()


class Message(BaseModel):
    """Message model for LLM interactions"""
    role: str = Field(..., description="Message role: system, user, or assistant")
    content: str = Field(..., description="Message content")


class LLMResponse(BaseModel):
    """Response model for LLM"""
    content: str = Field(..., description="Response content")
    usage: Dict[str, int] = Field(default_factory=dict, description="Token usage info")
    model: str = Field(..., description="Model used")


class LLMInterface:
    """Interface for interacting with LLM providers"""
    
    def __init__(self, provider: str = "openai", api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.client = httpx.Client()
    
    def chat(self, messages: List[Message], **kwargs) -> LLMResponse:
        """Send chat completion request"""
        if self.provider == "openai":
            return self._openai_chat(messages, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _openai_chat(self, messages: List[Message], **kwargs) -> LLMResponse:
        """OpenAI chat completion"""
        if not self.api_key:
            raise ValueError("API key is required for OpenAI")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [msg.model_dump() for msg in messages],
            **kwargs
        }
        
        try:
            response = self.client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30.0
            )
            response.raise_for_status()
            
            result = response.json()
            choice = result["choices"][0]
            
            return LLMResponse(
                content=choice["message"]["content"],
                usage=result.get("usage", {}),
                model=result["model"]
            )
        except Exception as e:
            console.print(f"[red]✗[/red] LLM request failed: {e}")
            raise
    
    def simple_chat(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Simple chat interface"""
        messages = []
        if system_prompt:
            messages.append(Message(role="system", content=system_prompt))
        messages.append(Message(role="user", content=prompt))
        
        response = self.chat(messages)
        return response.content
    
    def close(self):
        """Close HTTP client"""
        self.client.close()
