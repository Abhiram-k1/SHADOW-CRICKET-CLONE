import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("security_middleware")

class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Prevent stack trace leakage and log safe diagnostics
        start_time = time.time()
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"Internal Error processing {request.method} {request.url.path}: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "internal_server_error",
                        "message": "An unexpected error occurred. No stack trace is leaked."
                    }
                }
            )
