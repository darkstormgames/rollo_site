"""Rate limiting middleware for FastAPI."""

import time
from collections import defaultdict, deque
from typing import Dict, Tuple

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from core.config import settings
from core.logging import get_logger

logger = get_logger("rate_limit")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""
    
    def __init__(self, app, calls_per_minute: int = 60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.window_size = 60  # 1 minute
        # Store for each IP: deque of timestamps
        self.ip_requests: Dict[str, deque] = defaultdict(lambda: deque())
        
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        if "x-forwarded-for" in request.headers:
            return request.headers["x-forwarded-for"].split(",")[0].strip()
        elif "x-real-ip" in request.headers:
            return request.headers["x-real-ip"]
        else:
            return request.client.host if request.client else "unknown"
    
    def _is_rate_limited(self, ip: str) -> bool:
        """Check if IP is rate limited."""
        now = time.time()
        requests = self.ip_requests[ip]
        
        # Remove old requests outside the window
        while requests and requests[0] <= now - self.window_size:
            requests.popleft()
        
        # Check if we're over the limit
        if len(requests) >= self.calls_per_minute:
            return True
        
        # Add current request
        requests.append(now)
        return False
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with rate limiting."""
        client_ip = self._get_client_ip(request)
        
        # Apply stricter rate limiting to auth endpoints
        auth_rate_limit = settings.auth_rate_limit_per_minute
        if request.url.path.startswith("/api/auth/"):
            if self._is_auth_rate_limited(client_ip, auth_rate_limit):
                logger.warning(f"Auth rate limit exceeded for IP: {client_ip}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many authentication requests. Please try again later."
                )
        elif self._is_rate_limited(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later."
            )
        
        response = await call_next(request)
        return response
    
    def _is_auth_rate_limited(self, ip: str, limit: int) -> bool:
        """Check auth-specific rate limiting."""
        auth_key = f"auth_{ip}"
        now = time.time()
        requests = self.ip_requests[auth_key]
        
        # Remove old requests outside the window
        while requests and requests[0] <= now - self.window_size:
            requests.popleft()
        
        # Check if we're over the limit
        if len(requests) >= limit:
            return True
        
        # Add current request
        requests.append(now)
        return False