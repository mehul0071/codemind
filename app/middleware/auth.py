from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.config import settings

EXEMPT_PATHS = {"/", "/health", "/docs", "/openapi.json", "/redoc"}

class APIKeyMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next) -> Response:
        if not settings.API_KEY:
            return await call_next(request)

        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        api_key = request.headers.get("X-API-Key", "")
        if api_key != settings.API_KEY:
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "Forbidden: invalid or missing X-API-Key header."
                },
            )

        return await call_next(request)
