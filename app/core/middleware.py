import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from .logging_config import correlation_id_var, endpoint_var, method_var
from fastapi.responses import JSONResponse
from app.config import settings


class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        endpoint = str(request.url.path)
        method = request.method
        
        correlation_id_var.set(correlation_id)
        endpoint_var.set(endpoint)
        method_var.set(method)
        
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response

class TransbankHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Excluir health, docs y openapi
        if request.url.path.startswith("/health") or \
           request.url.path.startswith("/openapi") or \
           request.url.path.startswith("/docs"):
            return await call_next(request)

        api_key_id = request.headers.get("Tbk-Api-Key-Id") or settings.TRANSBANK_COMMERCE_CODE
        api_key_secret = request.headers.get("Tbk-Api-Key-Secret") or settings.TRANSBANK_API_KEY
        if not api_key_id or not api_key_secret:
            return JSONResponse(
                status_code=401,
                content={"detail": "Faltan credenciales de Transbank (header o settings)"}
            )
        # Puedes adjuntar a request.state si necesitas en endpoints
        request.state.tbk_api_key_id = api_key_id
        request.state.tbk_api_key_secret = api_key_secret
        return await call_next(request)