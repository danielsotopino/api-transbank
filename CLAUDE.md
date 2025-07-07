# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Transbank Oneclick API service built with Python FastAPI, implementing secure payment processing using the official Transbank SDK. The service allows users to register credit/debit cards and process one-click payments.

## Key Architecture Components

### FastAPI Structure
- **main.py**: FastAPI application configuration with middleware and exception handlers
- **config.py**: Environment configurations using Pydantic BaseSettings
- **database.py**: SQLAlchemy setup with connection pooling
- **api/**: REST API endpoints organized by version (v1)
- **core/**: Core utilities (logging, middleware, exceptions)
- **models/**: SQLAlchemy ORM models
- **schemas/**: Pydantic DTOs for request/response validation
- **repositories/**: Data access layer with repository pattern
- **services/**: Business logic layer
- **utils/**: Utility functions and cache implementation

### Transbank Integration
- Uses official transbank-sdk Python package
- Implements Oneclick Mall pattern for multi-store transactions
- Supports both integration and production environments
- Handles card inscription, transaction authorization, and operation management

## Development Standards

### Code Conventions
- **Variables/Functions**: snake_case
- **Classes**: PascalCase  
- **Constants**: UPPER_SNAKE_CASE
- **Function size**: Maximum 20 lines, single responsibility
- **Dependency Injection**: Use FastAPI's `Depends()` system
- **Error Handling**: Custom domain exceptions with global handlers

### Required Structured Logging
- **Format**: JSON structured logs for Elastic Stack
- **Context Variables**: All logs must include correlation_id
- **Logger**: Use StructuredLogger utility class
- **Levels**: DEBUG (dev), INFO (business), WARNING (expected errors), ERROR (critical)

### API Response Format
All endpoints must return standardized responses:
```json
{
  "success": true,
  "data": { /* results */ },
  "errors": [{ "code": "ERROR_CODE", "message": "Description" }]
}
```

### Database
- **ORM**: SQLAlchemy with declarative base
- **Migrations**: Alembic for database schema changes
- **Repository Pattern**: Base repository with generic CRUD operations
- **Transactions**: Service layer handles database transactions

## Development Commands

### Testing
- **Unit Tests**: `pytest tests/unit/`
- **Integration Tests**: `pytest tests/integration/`
- **Coverage**: `pytest --cov=app tests/`

### Database
- **Create Migration**: `alembic revision --autogenerate -m "description"`
- **Run Migrations**: `alembic upgrade head`
- **Downgrade**: `alembic downgrade -1`

### Development Server
- **Run Server**: `uvicorn app.main:app --reload`
- **Environment**: Set `ENVIRONMENT=development` for local development

## Security Requirements

### Transbank Configuration
- **Headers**: `Tbk-Api-Key-Id` and `Tbk-Api-Key-Secret` for authentication
- **Environments**: 
  - Integration: Use `configure_for_testing()`
  - Production: Use `configure_for_production(commerce_code, api_key)`
- **Encryption**: Sensitive data (tbk_user, card info) must be encrypted in database

### Rate Limiting
- **Inscription**: 10 requests/minute per user
- **Transactions**: 100 requests/minute per commerce
- **Queries**: 1000 requests/minute per commerce

## Testing Strategy

### Unit Tests
- Minimum 80% code coverage
- Mock external dependencies (Transbank SDK)
- Test business logic validation
- Use pytest fixtures for common test data

### Integration Tests
- Test complete API flows
- Use test database with transactions
- Test with Transbank integration environment
- Verify error handling and edge cases

## Environment Configuration

### Integration Environment
```python
from transbank.webpay.oneclick.mall_inscription import MallInscription
from transbank.webpay.oneclick.mall_transaction import MallTransaction

MallInscription.build_for_integration(
    commerce_code="YOUR_COMMERCE_CODE",
    api_key="YOUR_API_KEY"
)
MallTransaction.build_for_integration(
    commerce_code="YOUR_COMMERCE_CODE",
    api_key="YOUR_API_KEY"
)
```

### Production Environment
```python
from transbank.webpay.oneclick.mall_inscription import MallInscription
from transbank.webpay.oneclick.mall_transaction import MallTransaction

MallInscription.build_for_production(
    commerce_code="YOUR_COMMERCE_CODE",
    api_key="YOUR_API_KEY"
)
MallTransaction.build_for_production(
    commerce_code="YOUR_COMMERCE_CODE",
    api_key="YOUR_API_KEY"
)
```

## Key Files and Patterns

### Exception Handling
- **Custom Exceptions**: Inherit from `DomainException` with error codes
- **Global Handlers**: Convert exceptions to standard API response format
- **Validation**: Use Pydantic models for automatic request validation

### Logging Pattern
```python
from core.structured_logger import StructuredLogger

logger = StructuredLogger(__name__)
# Contexto flexible recomendado:
logger.with_context("key", "value").info("Message")
logger.with_contexts(key1="value1", key2="value2").info("Message")

# También puedes encadenar más contexto:
logger.with_contexts(username=username, transaction_id=tid).info("Transaction authorized successfully")

# El contexto se agrega automáticamente, no es necesario pasar 'context' como argumento.
```

### Service Pattern
```python
class SomeService:
    def __init__(self, repository: SomeRepository):
        self.repository = repository
    
    async def business_operation(self, data):
        # Business logic with transaction management
        pass
```

## Transbank Specific Considerations

### SDK Usage
- Always handle `response_code` in transaction responses (0 = success)
- Implement proper timeout handling (60s for inscription, 30s for transactions)
- Use official test cards for integration testing
- Follow Transbank certification process before production

### Data Models
- **OneclickInscription**: Stores user card registrations
- **OneclickTransaction**: Stores transaction records
- **OneclickTransactionDetail**: Stores individual transaction details per commerce

## Error Handling Patterns

### Standard Error Response
```json
{
  "error": {
    "code": "DOMAIN_ERROR_CODE",
    "message": "User-friendly description",
    "tbk_error_code": "TBK_CODE",
    "timestamp": "2025-01-01T00:00:00Z"
  },
  "status": 400
}
```

### Common Error Codes
- `CLIENTE_NO_ENCONTRADO`: User not found
- `SALDO_INSUFICIENTE`: Insufficient balance
- `TARJETA_NO_VALIDA`: Invalid card
- `TRANSACCION_RECHAZADA`: Transaction rejected by Transbank