"""Secure API client for backend communication."""

import json
import time
import asyncio
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from jose import jwt, JWTError
import logging

from .config import AgentConfig, get_agent_id


logger = logging.getLogger(__name__)


class APIClient:
    """Secure API client for communicating with the main backend service."""
    
    def __init__(self, config: AgentConfig):
        """Initialize the API client."""
        self.config = config
        self.agent_id = get_agent_id()
        self.session = self._create_session()
        self.token: Optional[str] = None
        self.token_expires_at: Optional[float] = None
        
    def _create_session(self) -> requests.Session:
        """Create a configured HTTP session with retry logic."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config.retry_attempts,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE"],
            backoff_factor=self.config.retry_backoff
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Configure SSL
        if not self.config.ssl_verify:
            session.verify = False
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        elif self.config.ssl_cert_path:
            session.verify = self.config.ssl_cert_path
            
        # Set default headers
        session.headers.update({
            "User-Agent": f"vm-agent/{self.agent_id}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        
        return session
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication token."""
        headers = {}
        
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
            
        return headers
    
    def _is_token_expired(self) -> bool:
        """Check if the current token is expired."""
        if not self.token or not self.token_expires_at:
            return True
            
        # Add 60 second buffer before expiration
        return time.time() >= (self.token_expires_at - 60)
    
    async def authenticate(self) -> bool:
        """Authenticate with the backend service."""
        try:
            auth_data = {
                "agent_id": self.agent_id,
                "agent_name": self.config.agent_name
            }
            
            if self.config.agent_token:
                auth_data["token"] = self.config.agent_token
            
            url = urljoin(self.config.backend_url, "/api/agent/auth")
            response = self.session.post(
                url,
                json=auth_data,
                timeout=self.config.api_timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                
                # Decode token to get expiration
                if self.token:
                    try:
                        decoded = jwt.get_unverified_claims(self.token)
                        self.token_expires_at = decoded.get("exp")
                    except JWTError:
                        logger.warning("Could not decode token expiration")
                        
                logger.info("Authentication successful")
                return True
            else:
                logger.error(f"Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    async def register_agent(self) -> bool:
        """Register agent with the backend service."""
        try:
            registration_data = {
                "agent_id": self.agent_id,
                "agent_name": self.config.agent_name,
                "hostname": self._get_hostname(),
                "capabilities": self._get_capabilities(),
                "version": "1.0.0"
            }
            
            url = urljoin(self.config.backend_url, "/api/agent/register")
            response = self.session.post(
                url,
                json=registration_data,
                headers=self._get_headers(),
                timeout=self.config.api_timeout
            )
            
            if response.status_code in [200, 201]:
                logger.info("Agent registration successful")
                return True
            else:
                logger.error(f"Registration failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False
    
    async def send_heartbeat(self, metrics: Optional[Dict[str, Any]] = None) -> bool:
        """Send heartbeat to the backend service."""
        try:
            if self._is_token_expired():
                if not await self.authenticate():
                    return False
            
            heartbeat_data = {
                "agent_id": self.agent_id,
                "timestamp": time.time(),
                "status": "healthy"
            }
            
            if metrics:
                heartbeat_data["metrics"] = metrics
            
            url = urljoin(self.config.backend_url, "/api/agent/heartbeat")
            response = self.session.post(
                url,
                json=heartbeat_data,
                headers=self._get_headers(),
                timeout=self.config.api_timeout
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")
            return False
    
    async def send_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Send metrics to the backend service."""
        try:
            if self._is_token_expired():
                if not await self.authenticate():
                    return False
            
            metrics_data = {
                "agent_id": self.agent_id,
                "timestamp": time.time(),
                "metrics": metrics
            }
            
            url = urljoin(self.config.backend_url, "/api/agent/metrics")
            response = self.session.post(
                url,
                json=metrics_data,
                headers=self._get_headers(),
                timeout=self.config.api_timeout
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Metrics submission error: {e}")
            return False
    
    async def get_commands(self) -> List[Dict[str, Any]]:
        """Get pending commands from the backend service."""
        try:
            if self._is_token_expired():
                if not await self.authenticate():
                    return []
            
            url = urljoin(self.config.backend_url, f"/api/agent/{self.agent_id}/commands")
            response = self.session.get(
                url,
                headers=self._get_headers(),
                timeout=self.config.api_timeout
            )
            
            if response.status_code == 200:
                return response.json().get("commands", [])
            else:
                logger.error(f"Failed to get commands: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Get commands error: {e}")
            return []
    
    async def report_command_result(self, command_id: str, result: Dict[str, Any]) -> bool:
        """Report command execution result to the backend."""
        try:
            if self._is_token_expired():
                if not await self.authenticate():
                    return False
            
            result_data = {
                "command_id": command_id,
                "agent_id": self.agent_id,
                "result": result,
                "timestamp": time.time()
            }
            
            url = urljoin(self.config.backend_url, "/api/agent/command-result")
            response = self.session.post(
                url,
                json=result_data,
                headers=self._get_headers(),
                timeout=self.config.api_timeout
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Command result reporting error: {e}")
            return False
    
    def _get_hostname(self) -> str:
        """Get system hostname."""
        import socket
        return socket.gethostname()
    
    def _get_capabilities(self) -> List[str]:
        """Get agent capabilities."""
        capabilities = ["vm_management", "metrics_collection", "libvirt"]
        
        # Check for additional capabilities
        try:
            import libvirt
            capabilities.append("libvirt_available")
        except ImportError:
            pass
            
        return capabilities
    
    def close(self):
        """Close the HTTP session."""
        if self.session:
            self.session.close()