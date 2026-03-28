"""
Proxy management for Prollama
"""

from typing import Dict, Any, Optional, List
import httpx
from pydantic import BaseModel, Field
from rich.console import Console

console = Console()


class ProxyConfig(BaseModel):
    """Proxy configuration model"""
    host: str = Field(default="localhost", description="Proxy host")
    port: int = Field(default=8080, description="Proxy port")
    enabled: bool = Field(default=False, description="Whether proxy is enabled")
    auth: Optional[Dict[str, str]] = Field(default=None, description="Proxy authentication")


class ProxyRequest(BaseModel):
    """Proxy request model"""
    method: str = Field(..., description="HTTP method")
    url: str = Field(..., description="Target URL")
    headers: Dict[str, str] = Field(default_factory=dict, description="Request headers")
    body: Optional[str] = Field(default=None, description="Request body")


class ProxyResponse(BaseModel):
    """Proxy response model"""
    status_code: int = Field(..., description="HTTP status code")
    headers: Dict[str, str] = Field(default_factory=dict, description="Response headers")
    body: str = Field(..., description="Response body")


class ProxyManager:
    """Manager for HTTP proxy operations"""
    
    def __init__(self, config: Optional[ProxyConfig] = None):
        self.config = config or ProxyConfig()
        self.client = httpx.Client()
    
    def forward_request(self, request: ProxyRequest) -> ProxyResponse:
        """Forward request through proxy"""
        if not self.config.enabled:
            console.print("[yellow]⚠[/yellow] Proxy is disabled, making direct request")
        
        try:
            # Prepare proxy settings if enabled
            proxy_url = None
            if self.config.enabled:
                proxy_url = f"http://{self.config.host}:{self.config.port}"
            
            # Make request
            response = self.client.request(
                method=request.method,
                url=request.url,
                headers=request.headers,
                content=request.body,
                proxy=proxy_url if self.config.enabled else None,
                timeout=30.0
            )
            
            return ProxyResponse(
                status_code=response.status_code,
                headers=dict(response.headers),
                body=response.text
            )
        except Exception as e:
            console.print(f"[red]✗[/red] Proxy request failed: {e}")
            raise
    
    def test_proxy(self) -> bool:
        """Test proxy connectivity"""
        if not self.config.enabled:
            console.print("[yellow]⚠[/yellow] Proxy is disabled")
            return True
        
        try:
            test_request = ProxyRequest(
                method="GET",
                url="https://httpbin.org/ip",
                headers={"User-Agent": "prollama/0.1.1"}
            )
            
            response = self.forward_request(test_request)
            success = response.status_code == 200
            
            if success:
                console.print(f"[green]✓[/green] Proxy test successful: {self.config.host}:{self.config.port}")
            else:
                console.print(f"[red]✗[/red] Proxy test failed: {response.status_code}")
            
            return success
        except Exception as e:
            console.print(f"[red]✗[/red] Proxy test failed: {e}")
            return False
    
    def log_request(self, request: ProxyRequest, response: ProxyResponse) -> None:
        """Log proxy request and response"""
        console.print(f"[blue]→[/blue] {request.method} {request.url}")
        console.print(f"[blue]←[/blue] {response.status_code} ({len(response.body)} bytes)")
    
    def close(self):
        """Close HTTP client"""
        self.client.close()
