from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.middleware import CorrelationMiddleware, TransbankHeaderMiddleware
from .core.exception_handlers import register_exception_handlers
from .core.logging_config import setup_logging
from .api.v1.router import api_router
from .config import settings
from app.schemas.response_models import ApiResponse

# Setup logging
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    debug=settings.DEBUG
)

# Middleware
app.add_middleware(CorrelationMiddleware)
app.add_middleware(TransbankHeaderMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
register_exception_handlers(app)

# Routers
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {
        "message": "Transbank Oneclick API",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


@app.get("/health", response_model=ApiResponse[dict])
async def health_check():
    data = {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "environment": settings.ENVIRONMENT
    }
    return ApiResponse.success_response(data)