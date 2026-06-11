"""
Auth middleware stub (no-op for MVP).
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class AuthMiddleware(BaseHTTPMiddleware):
    """Placeholder auth middleware — passes all requests through."""

    async def dispatch(self, request: Request, call_next):
        # TODO: Implement JWT auth
        return await call_next(request)
