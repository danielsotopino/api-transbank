# Lineamientos Técnicos de Desarrollo - Python FastAPI

## 1. Estructura del Proyecto

```
ms-pago-service/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app configuration
│   ├── config.py                   # Environment configurations
│   ├── database.py                 # SQLAlchemy setup
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py                 # FastAPI dependencies
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py           # Main API router
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── pagos.py
│   │           └── clientes.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── logging_config.py       # Structured logging
│   │   ├── structured_logger.py    # Logger utility
│   │   ├── middleware.py           # Correlation middleware
│   │   ├── exceptions.py           # Domain exceptions
│   │   └── exception_handlers.py   # Global handlers
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── pago.py                 # SQLAlchemy models
│   │   └── cliente.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── pago_schemas.py         # Pydantic DTOs
│   │   ├── cliente_schemas.py
│   │   └── response_models.py      # ApiResponse models
│   │
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base_repository.py
│   │   ├── pago_repository.py
│   │   └── cliente_repository.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pago_service.py
│   │   └── cliente_service.py
│   │
│   └── utils/
│       ├── __init__.py
│       └── cache.py                # Redis cache (opcional)
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Pytest configuration
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_services/
│   │   └── test_repositories/
│   └── integration/
│       ├── __init__.py
│       └── test_api/
│           ├── test_pagos.py
│           └── test_clientes.py
│
├── alembic/                        # Database migrations
│   ├── versions/
│   ├── env.py
│   ├── script.py.mako
│   └── alembic.ini
│
├── .env                            # Environment variables
├── .env.example                    # Environment template
├── requirements.txt                # Dependencies
├── requirements-dev.txt            # Dev dependencies
├── Dockerfile
├── docker-compose.yml
└── README.md
```
### Idioma
Inglés

### Configuración de archivos principales

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.middleware import CorrelationMiddleware
from .core.exception_handlers import register_exception_handlers
from .api.v1.router import api_router
from .config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Middleware
app.add_middleware(CorrelationMiddleware)
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

# app/config.py
from pydantic import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Microservicio de Pagos"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str
    SECRET_KEY: str
    
    # Redis (opcional)
    REDIS_URL: str = None
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["*"]
    
    class Config:
        env_file = ".env"

settings = Settings()

# app/api/deps.py
from fastapi import Depends
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..services.pago_service import PagoService
from ..services.cliente_service import ClienteService

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_pago_service(db: Session = Depends(get_db)) -> PagoService:
    return PagoService(db)

def get_cliente_service(db: Session = Depends(get_db)) -> ClienteService:
    return ClienteService(db)
```

## 2. Resumen de Estándares Obligatorios

### **📝 Código**
- **Convenciones**: snake_case variables/funciones, PascalCase clases, UPPER_SNAKE_CASE constantes
- **Funciones pequeñas**: Una responsabilidad, máximo 20 líneas
- **Dependency Injection**: FastAPI dependencies con `Depends()`
- **Pydantic models**: Validación automática y serialización
- **Manejo de errores**: Excepciones personalizadas de dominio, Exception handlers

### **🔍 Logging Uniforme (CRÍTICO)**
- **Formato JSON estructurado**: Para Elastic Stack
- **Context vars obligatorio**: correlation_id en todos los logs
- **StructuredLogger**: Clase utility para consistencia organizacional
- **Niveles**: DEBUG (dev), INFO (negocio), WARNING (errores esperados), ERROR (críticos)

### **🌐 APIs REST**
- **Formato estándar**: `{success, data, errors}` en todas las respuestas
- **Exception handlers**: Convierte excepciones a formato estándar
- **Códigos de error consistentes**: Catálogo centralizado
- **HTTP Status apropiados**: 200, 400, 401, 404, 500, 503

### **🧪 Testing**
- **Unit Tests**: Mínimo 80% cobertura con pytest
- **Integration Tests**: APIs y persistencia
- **Naming descriptivo**: Tests documentan comportamiento

### **🟡 Deseables**
- **Cache distribuido**: Redis con circuit breakers
- **Circuit Breakers**: Para servicios inestables

## 2. Context Variables (Reemplazo de MDC)

Python usa `contextvars` para mantener contexto por request.

**Configuración:**
- Middleware para correlation ID en cada request
- Propagación automática en tareas async
- Limpieza automática al finalizar request

**Uso en servicios:**
- Agregar correlation_id, método, endpoint
- Contexto específico (cliente_id, pago_id, monto)
- Información de error cuando aplique

## 3. Patrón de Logs Uniforme para Elastic

### Estructura JSON Estándar

```json
{
  "@timestamp": "2025-07-04T10:30:45.123Z",
  "level": "INFO",
  "artifact": "ms-pago-service",
  "version": "1.2.3",
  "correlation_id": "abc-123-def-456",
  "endpoint": "/api/v1/pagos",
  "method": "procesar_pago",
  "message": "Pago procesado exitosamente",
  "context": {
    "cliente_id": 123,
    "pago_id": 456,
    "monto": "100.50",
    "moneda": "CLP"
  },
  "error": {
    "type": "SaldoInsuficienteException",
    "message": "Saldo insuficiente para realizar la operación",
    "traceback": "...",
    "error_code": "SALDO_INSUFICIENTE"
  },
  "traceback": "..."
}
```

### Configuración Logging

```python
# logging_config.py
import logging
import json
from datetime import datetime
from contextvars import ContextVar

correlation_id_var: ContextVar[str] = ContextVar('correlation_id')
endpoint_var: ContextVar[str] = ContextVar('endpoint')
method_var: ContextVar[str] = ContextVar('method')

class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "@timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "artifact": os.getenv("SERVICE_NAME", "unknown"),
            "version": os.getenv("SERVICE_VERSION", "unknown"),
            "correlation_id": correlation_id_var.get(None),
            "endpoint": endpoint_var.get(None),
            "method": method_var.get(None),
            "message": record.getMessage(),
        }
        
        if hasattr(record, 'context'):
            log_entry["context"] = record.context
            
        if hasattr(record, 'error'):
            log_entry["error"] = record.error
            
        if record.exc_info:
            log_entry["traceback"] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry)
```

### Utility StructuredLogger

```python
# structured_logger.py
import logging
from typing import Dict, Any, Optional
from contextvars import ContextVar

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        
    def _log(self, level: int, message: str, context: Optional[Dict[str, Any]] = None, 
             error: Optional[Dict[str, Any]] = None):
        extra = {}
        if context:
            extra['context'] = context
        if error:
            extra['error'] = error
            
        self.logger.log(level, message, extra=extra)
    
    def info(self, message: str, context: Optional[Dict[str, Any]] = None):
        self._log(logging.INFO, message, context)
    
    def warning(self, message: str, context: Optional[Dict[str, Any]] = None):
        self._log(logging.WARNING, message, context)
    
    def error(self, message: str, context: Optional[Dict[str, Any]] = None, 
              error: Optional[Dict[str, Any]] = None):
        self._log(logging.ERROR, message, context, error)
    
    def debug(self, message: str, context: Optional[Dict[str, Any]] = None):
        self._log(logging.DEBUG, message, context)
    
    # Helper methods
    def with_cliente(self, cliente_id: int):
        return ContextBuilder(self).with_cliente(cliente_id)
    
    def with_pago(self, pago_id: int):
        return ContextBuilder(self).with_pago(pago_id)

class ContextBuilder:
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        self.context = {}
    
    def with_cliente(self, cliente_id: int):
        self.context['cliente_id'] = cliente_id
        return self
    
    def with_pago(self, pago_id: int):
        self.context['pago_id'] = pago_id
        return self
    
    def with_monto(self, monto: str):
        self.context['monto'] = monto
        return self
    
    def info(self, message: str):
        self.logger.info(message, self.context)
    
    def warning(self, message: str):
        self.logger.warning(message, self.context)
    
    def error(self, message: str, error: Optional[Dict[str, Any]] = None):
        self.logger.error(message, self.context, error)
```

### Middleware para Correlation ID

```python
# middleware.py
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from .logging_config import correlation_id_var, endpoint_var, method_var

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
```

### Estándares de Logging

#### 🟢 **INFO Level - Eventos de Negocio**
- Inicio y fin de operaciones importantes
- Cambios de estado relevantes
- Resultados de procesos críticos

#### 🟡 **WARNING Level - Errores Esperados**
- Errores de negocio recuperables
- Servicios externos no disponibles
- Validaciones fallidas

#### 🔴 **ERROR Level - Errores Críticos**
- Errores inesperados del sistema
- Fallas de integración críticas
- Excepciones no controladas

### Qué NO Logear

- Información sensible (passwords, tokens, números de tarjeta)
- Logs en loops intensivos
- Objetos completos con datos personales

## 4. Cache en Alta Disponibilidad (Deseable)

> **Nota**: El cache es una optimización deseable pero NO obligatoria. Implementar solo cuando el performance lo requiera.

### Configuración Redis

```python
# cache.py
import redis
import json
from typing import Optional, Any
from contextlib import asynccontextmanager

class CacheService:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url, decode_responses=True)
    
    async def get(self, key: str) -> Optional[Any]:
        try:
            value = self.redis.get(key)
            return json.loads(value) if value else None
        except Exception:
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        try:
            self.redis.setex(key, ttl, json.dumps(value))
        except Exception:
            pass
    
    async def delete(self, key: str):
        try:
            self.redis.delete(key)
        except Exception:
            pass
```

### Cache con Resilencia

```python
# cache_decorator.py
import functools
from typing import Callable, Any
from .cache import CacheService

def cached(ttl: int = 3600, key_prefix: str = ""):
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try cache first
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache_service.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator
```

## 5. Formato Estándar de Respuestas API REST

### Estructura Obligatoria

```json
{
  "success": true,
  "data": { /* objeto o lista de resultados */ },
  "errors": [{ "code": "ERROR_CODE", "message": "Descripción del error" }]
}
```

### Modelos Pydantic

```python
# response_models.py
from pydantic import BaseModel
from typing import Optional, List, Any, Generic, TypeVar

T = TypeVar('T')

class ApiError(BaseModel):
    code: str
    message: str

class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    errors: List[ApiError] = []
    
    @classmethod
    def success_response(cls, data: T) -> 'ApiResponse[T]':
        return cls(success=True, data=data, errors=[])
    
    @classmethod
    def error_response(cls, errors: List[ApiError]) -> 'ApiResponse[None]':
        return cls(success=False, data=None, errors=errors)
    
    @classmethod
    def single_error(cls, code: str, message: str) -> 'ApiResponse[None]':
        return cls.error_response([ApiError(code=code, message=message)])
```

### Excepciones Personalizadas

```python
# exceptions.py
class DomainException(Exception):
    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class ClienteNoEncontradoException(DomainException):
    def __init__(self, cliente_id: int):
        super().__init__(
            f"Cliente con ID {cliente_id} no encontrado",
            "CLIENTE_NO_ENCONTRADO"
        )

class SaldoInsuficienteException(DomainException):
    def __init__(self, saldo_actual: str, monto_requerido: str):
        super().__init__(
            f"Saldo insuficiente. Actual: {saldo_actual}, Requerido: {monto_requerido}",
            "SALDO_INSUFICIENTE"
        )
```

### Exception Handlers

```python
# exception_handlers.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from .exceptions import DomainException
from .response_models import ApiResponse, ApiError
from .structured_logger import StructuredLogger

logger = StructuredLogger(__name__)

async def domain_exception_handler(request: Request, exc: DomainException):
    logger.warning(
        f"Error de dominio: {exc.message}",
        context={
            "error_code": exc.error_code,
            "endpoint": str(request.url.path),
            "method": request.method
        }
    )
    
    response = ApiResponse.single_error(exc.error_code, exc.message)
    return JSONResponse(
        status_code=400,
        content=response.dict()
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(
        f"HTTP Exception: {exc.detail}",
        context={
            "status_code": exc.status_code,
            "endpoint": str(request.url.path),
            "method": request.method
        }
    )
    
    response = ApiResponse.single_error("HTTP_ERROR", str(exc.detail))
    return JSONResponse(
        status_code=exc.status_code,
        content=response.dict()
    )

async def general_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Error inesperado: {str(exc)}",
        context={
            "endpoint": str(request.url.path),
            "method": request.method
        },
        error={
            "type": type(exc).__name__,
            "message": str(exc)
        }
    )
    
    response = ApiResponse.single_error("INTERNAL_ERROR", "Error interno del servidor")
    return JSONResponse(
        status_code=500,
        content=response.dict()
    )
```

### Configuración de la App

```python
# main.py
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from .middleware import CorrelationMiddleware
from .exception_handlers import (
    domain_exception_handler,
    http_exception_handler,
    general_exception_handler
)
from .exceptions import DomainException

app = FastAPI(
    title="Microservicio de Pagos",
    version="1.0.0"
)

# Middleware
app.add_middleware(CorrelationMiddleware)

# Exception handlers
app.add_exception_handler(DomainException, domain_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        errors.append(ApiError(
            code="VALIDATION_ERROR",
            message=f"{error['loc'][-1]}: {error['msg']}"
        ))
    
    response = ApiResponse.error_response(errors)
    return JSONResponse(
        status_code=422,
        content=response.dict()
    )
```

### Ejemplo de Endpoint

```python
# endpoints/pagos.py
from fastapi import APIRouter, Depends, HTTPException
from ..response_models import ApiResponse
from ..structured_logger import StructuredLogger
from ..exceptions import ClienteNoEncontradoException, SaldoInsuficienteException

router = APIRouter()
logger = StructuredLogger(__name__)

@router.post("/pagos", response_model=ApiResponse[dict])
async def procesar_pago(
    pago_request: PagoRequest,
    pago_service: PagoService = Depends(get_pago_service)
):
    logger.info(
        "Iniciando procesamiento de pago",
        context={
            "cliente_id": pago_request.cliente_id,
            "monto": str(pago_request.monto),
            "moneda": pago_request.moneda
        }
    )
    
    try:
        resultado = await pago_service.procesar_pago(pago_request)
        
        logger.info(
            "Pago procesado exitosamente",
            context={
                "cliente_id": pago_request.cliente_id,
                "pago_id": resultado.pago_id,
                "monto": str(pago_request.monto)
            }
        )
        
        return ApiResponse.success_response(resultado.dict())
        
    except ClienteNoEncontradoException as e:
        raise e
    except SaldoInsuficienteException as e:
        raise e
    except Exception as e:
        logger.error(
            f"Error inesperado procesando pago: {str(e)}",
            context={
                "cliente_id": pago_request.cliente_id,
                "monto": str(pago_request.monto)
            }
        )
        raise
```

## 6. Base de Datos - SQLAlchemy + Alembic

### Configuración SQLAlchemy ORM

```python
# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/dbname")

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

### Models

```python
# models/pago.py
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class Pago(Base):
    __tablename__ = "pagos"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    monto = Column(Numeric(10, 2), nullable=False)
    moneda = Column(String(3), nullable=False, default="CLP")
    estado = Column(String(20), nullable=False, default="PENDIENTE")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    cliente = relationship("Cliente", back_populates="pagos")

# models/cliente.py
class Cliente(Base):
    __tablename__ = "clientes"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    saldo = Column(Numeric(10, 2), nullable=False, default=0)
    created_at = Column(DateTime, server_default=func.now())
    
    pagos = relationship("Pago", back_populates="cliente")
```

### Configuración Alembic

```bash
# Inicializar Alembic
alembic init alembic

# Crear migración
alembic revision --autogenerate -m "create pagos and clientes tables"

# Aplicar migración
alembic upgrade head
```

```python
# alembic/env.py
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from app.database import Base
from app.models import pago, cliente  # Import all models

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()
```

### Repository Pattern

```python
# repositories/base_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional, Generic, TypeVar
from sqlalchemy.orm import Session

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    def __init__(self, db: Session, model_class):
        self.db = db
        self.model_class = model_class
    
    def get_by_id(self, id: int) -> Optional[T]:
        return self.db.query(self.model_class).filter(self.model_class.id == id).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        return self.db.query(self.model_class).offset(skip).limit(limit).all()
    
    def create(self, obj: T) -> T:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj
    
    def update(self, obj: T) -> T:
        self.db.commit()
        self.db.refresh(obj)
        return obj
    
    def delete(self, id: int) -> bool:
        obj = self.get_by_id(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return True
        return False

# repositories/pago_repository.py
from .base_repository import BaseRepository
from ..models.pago import Pago

class PagoRepository(BaseRepository[Pago]):
    def __init__(self, db: Session):
        super().__init__(db, Pago)
    
    def get_by_cliente_id(self, cliente_id: int) -> List[Pago]:
        return self.db.query(Pago).filter(Pago.cliente_id == cliente_id).all()
    
    def get_by_estado(self, estado: str) -> List[Pago]:
        return self.db.query(Pago).filter(Pago.estado == estado).all()

# repositories/cliente_repository.py
from .base_repository import BaseRepository
from ..models.cliente import Cliente

class ClienteRepository(BaseRepository[Cliente]):
    def __init__(self, db: Session):
        super().__init__(db, Cliente)
    
    def get_by_email(self, email: str) -> Optional[Cliente]:
        return self.db.query(Cliente).filter(Cliente.email == email).first()
    
    def update_saldo(self, cliente_id: int, nuevo_saldo: Decimal) -> Optional[Cliente]:
        cliente = self.get_by_id(cliente_id)
        if cliente:
            cliente.saldo = nuevo_saldo
            return self.update(cliente)
        return None
```

### Services con Transacciones

```python
# services/pago_service.py
from decimal import Decimal
from sqlalchemy.orm import Session
from ..repositories.pago_repository import PagoRepository
from ..repositories.cliente_repository import ClienteRepository
from ..models.pago import Pago
from ..exceptions import ClienteNoEncontradoException, SaldoInsuficienteException
from ..structured_logger import StructuredLogger

logger = StructuredLogger(__name__)

class PagoService:
    def __init__(self, db: Session):
        self.db = db
        self.pago_repo = PagoRepository(db)
        self.cliente_repo = ClienteRepository(db)
    
    async def procesar_pago(self, cliente_id: int, monto: Decimal, moneda: str = "CLP") -> Pago:
        logger.info(
            "Iniciando procesamiento de pago",
            context={"cliente_id": cliente_id, "monto": str(monto), "moneda": moneda}
        )
        
        try:
            # Begin transaction
            cliente = self.cliente_repo.get_by_id(cliente_id)
            if not cliente:
                raise ClienteNoEncontradoException(cliente_id)
            
            if cliente.saldo < monto:
                raise SaldoInsuficienteException(str(cliente.saldo), str(monto))
            
            # Crear pago
            pago = Pago(
                cliente_id=cliente_id,
                monto=monto,
                moneda=moneda,
                estado="PROCESADO"
            )
            pago = self.pago_repo.create(pago)
            
            # Actualizar saldo
            nuevo_saldo = cliente.saldo - monto
            self.cliente_repo.update_saldo(cliente_id, nuevo_saldo)
            
            logger.info(
                "Pago procesado exitosamente",
                context={
                    "cliente_id": cliente_id,
                    "pago_id": pago.id,
                    "monto": str(monto),
                    "nuevo_saldo": str(nuevo_saldo)
                }
            )
            
            return pago
            
        except Exception as e:
            self.db.rollback()
            logger.error(
                f"Error procesando pago: {str(e)}",
                context={"cliente_id": cliente_id, "monto": str(monto)}
            )
            raise
```

### DTOs/Schemas Pydantic

```python
# schemas/pago_schemas.py
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from typing import Optional

class PagoCreate(BaseModel):
    cliente_id: int = Field(..., gt=0)
    monto: Decimal = Field(..., gt=0, decimal_places=2)
    moneda: str = Field(default="CLP", regex="^[A-Z]{3}$")

class PagoResponse(BaseModel):
    id: int
    cliente_id: int
    monto: Decimal
    moneda: str
    estado: str
    created_at: datetime
    
    class Config:
        orm_mode = True

# schemas/cliente_schemas.py
class ClienteCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., regex="^[^@]+@[^@]+\.[^@]+$")
    saldo: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)

class ClienteResponse(BaseModel):
    id: int
    nombre: str
    email: str
    saldo: Decimal
    created_at: datetime
    
    class Config:
        orm_mode = True
```

### Database Testing

```python
# conftest.py (actualizado)
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .main import app
from .database import Base, get_db

# Test database
SQLALCHEMY_DATABASE_URL = "postgresql://test_user:test_pass@localhost/test_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def db_setup():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(db_setup):
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
```

## 7. Dependency Injection

### Configuración de Dependencias

```python
# dependencies.py
from fastapi import Depends
from sqlalchemy.orm import Session
from .database import SessionLocal
from .services import PagoService, ClienteService
from .repositories import PagoRepository, ClienteRepository

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_pago_repository(db: Session = Depends(get_db)) -> PagoRepository:
    return PagoRepository(db)

def get_cliente_repository(db: Session = Depends(get_db)) -> ClienteRepository:
    return ClienteRepository(db)

def get_pago_service(
    pago_repo: PagoRepository = Depends(get_pago_repository),
    cliente_repo: ClienteRepository = Depends(get_cliente_repository)
) -> PagoService:
    return PagoService(pago_repo, cliente_repo)
```

## 7. Testing

### Configuración de Tests

```python
# conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .main import app
from .database import Base
from .dependencies import get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
```

### Ejemplo de Test

```python
# test_pagos.py
import pytest
from .conftest import client, db

def test_procesar_pago_exitoso(client, db):
    # Arrange
    pago_data = {
        "cliente_id": 1,
        "monto": "100.50",
        "moneda": "CLP"
    }
    
    # Act
    response = client.post("/api/v1/pagos", json=pago_data)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["monto"] == "100.50"
    assert data["errors"] == []

def test_cliente_no_encontrado(client, db):
    # Arrange
    pago_data = {
        "cliente_id": 999,
        "monto": "100.50",
        "moneda": "CLP"
    }
    
    # Act
    response = client.post("/api/v1/pagos", json=pago_data)
    
    # Assert
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["errors"][0]["code"] == "CLIENTE_NO_ENCONTRADO"
```

---

## Resumen de Lineamientos Obligatorios vs Deseables

### 🔴 **OBLIGATORIOS**

**📝 Código:**
- Convenciones de nomenclatura Python
- Funciones pequeñas y cohesivas
- Dependency injection con FastAPI
- Pydantic models para validación
- Manejo de errores estructurado

**🔍 Logging UNIFORME:**
- Context vars con correlation_id
- Formato JSON estructurado para Elastic
- StructuredLogger para consistencia
- Niveles de log apropiados

**🌐 APIs:**
- Formato de respuesta estándar
- Exception handlers globales
- Códigos de error centralizados

**🧪 Testing:**
- Unit tests con pytest
- Integration tests para endpoints críticos

### 🟡 **DESEABLES**

- Cache distribuido con Redis
- Circuit breakers para resilencia
- Métricas avanzadas de negocio

### 📋 **Checklist de Implementación**

#### Para cada nuevo servicio:
- [ ] Separación de responsabilidades en capas
- [ ] Context vars configurado con correlation_id
- [ ] StructuredLogger implementado
- [ ] Logging configurado para JSON en producción
- [ ] Exception handlers globales
- [ ] Formato ApiResponse en todos los endpoints
- [ ] Pydantic models con validaciones
- [ ] Unit tests con cobertura mínima
- [ ] Integration tests para endpoints críticos
- [ ] Configuración por ambiente

#### Para logging específicamente:
- [ ] Todos los logs contienen correlation_id
- [ ] Operaciones de negocio loggeadas en INFO
- [ ] Errores esperados en WARNING con contexto
- [ ] Errores críticos en ERROR con traceback
- [ ] No se loggea información sensible
- [ ] Logs estructurados siguen formato JSON estándar

