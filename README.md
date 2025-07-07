# Transbank Oneclick API

API REST para integración con Transbank Oneclick Mall, permitiendo pagos en un solo clic mediante tarjetas previamente inscritas.

## Características

- **FastAPI**: Framework moderno de alta performance
- **Transbank SDK**: Integración oficial con SDK de Python
- **Structured Logging**: Logs estructurados en JSON para Elastic Stack
- **Arquitectura Limpia**: Separación en capas (API, Core, Models, Services)
- **Base de Datos**: SQLAlchemy ORM con migraciones Alembic
- **Testing**: Tests unitarios e integración con pytest
- **Docker**: Containerización completa con docker-compose

## Requisitos

- Python 3.11+
- PostgreSQL 13+
- Redis (opcional, para cache)

## Instalación

### Desarrollo Local

1. **Clonar repositorio**
```bash
git clone <repository-url>
cd api-transbank
```

2. **Crear entorno virtual**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate     # Windows
```

3. **Instalar dependencias**
```bash
pip install -r requirements-dev.txt
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

5. **Ejecutar migraciones**
```bash
alembic upgrade head
```

6. **Ejecutar servidor de desarrollo**
```bash
uvicorn app.main:app --reload
```

### Con Docker

```bash
# Ejecutar toda la stack
docker-compose up -d

# Solo la base de datos para desarrollo
docker-compose up -d db redis
```

## Configuración

### Variables de Entorno

Ver `.env.example` para todas las variables disponibles.

**Principales:**
- `DATABASE_URL`: URL de conexión a PostgreSQL
- `TRANSBANK_ENVIRONMENT`: `integration` o `production`
- `TRANSBANK_COMMERCE_CODE`: Código de comercio de Transbank
- `TRANSBANK_API_KEY`: API Key de Transbank

### Ambientes Transbank

**Integración (Testing):**
- Configuración automática con códigos de prueba
- Tarjetas de prueba disponibles en documentación Transbank

**Producción:**
- Requiere certificación con Transbank
- Configurar `TRANSBANK_COMMERCE_CODE` y `TRANSBANK_API_KEY` reales

## API Endpoints

### Inscripciones

- `POST /api/v1/oneclick/mall/inscription/start` - Iniciar inscripción
- `PUT /api/v1/oneclick/mall/inscription/finish` - Finalizar inscripción  
- `DELETE /api/v1/oneclick/mall/inscription/delete` - Eliminar inscripción
- `GET /api/v1/oneclick/mall/inscription/{username}` - Listar inscripciones

### Transacciones

- `POST /api/v1/oneclick/mall/transaction/authorize` - Autorizar transacción
- `GET /api/v1/oneclick/mall/transaction/status/{child_buy_order}` - Estado transacción
- `PUT /api/v1/oneclick/mall/transaction/capture` - Captura diferida
- `POST /api/v1/oneclick/mall/transaction/refund` - Reversar transacción
- `GET /api/v1/oneclick/mall/transaction/history/{username}` - Historial

### Utilidades

- `GET /` - Información de la API
- `GET /health` - Health check

## Desarrollo

### Comandos Útiles

```bash
# Tests
pytest                          # Ejecutar todos los tests
pytest tests/unit/             # Solo tests unitarios
pytest tests/integration/      # Solo tests de integración
pytest --cov=app               # Con coverage

# Base de datos
alembic revision --autogenerate -m "descripcion"  # Crear migración
alembic upgrade head                               # Aplicar migraciones
alembic downgrade -1                              # Revertir última migración

# Linting
black app/ tests/              # Formatear código
flake8 app/ tests/             # Linter
mypy app/                      # Type checking
```

### Estructura del Proyecto

```
app/
├── api/                    # Endpoints REST
│   └── v1/
├── core/                   # Infraestructura (logging, middleware, exceptions)
├── models/                 # Modelos SQLAlchemy
├── schemas/                # Modelos Pydantic (DTOs)
├── services/               # Lógica de negocio
├── utils/                  # Utilidades
├── config.py               # Configuración
├── database.py             # Setup base de datos
└── main.py                 # Aplicación FastAPI

tests/
├── unit/                   # Tests unitarios
├── integration/            # Tests de integración
└── conftest.py             # Fixtures de pytest
```

## Logging

### Formato Estructurado

Todos los logs siguen formato JSON estructurado:

```json
{
  "@timestamp": "2025-07-06T10:30:45.123Z",
  "level": "INFO",
  "artifact": "api-transbank",
  "version": "1.0.0",
  "correlation_id": "abc-123-def-456",
  "endpoint": "/api/v1/oneclick/mall/transaction/authorize",
  "method": "POST",
  "message": "Transacción autorizada exitosamente",
  "context": {
    "username": "user123",
    "parent_buy_order": "order_456",
    "total_amount": 50000
  }
}
```

### Uso en Código

```python
from app.core.structured_logger import StructuredLogger

logger = StructuredLogger(__name__)

# Log simple
logger.info("Operación completada")

# Log con contexto
logger.with_username("user123").with_monto("50000").info(
    "Pago procesado exitosamente"
)
```

## Seguridad

### Mejores Prácticas Implementadas

- Headers de autenticación Transbank
- Encriptación de datos sensibles en BD
- Rate limiting por endpoint
- Logs de auditoría completos
- Validación estricta de entrada
- Manejo seguro de errores

### Datos Sensibles

- **tbk_user**: Encriptado en base de datos
- **Números de tarjeta**: Solo últimos 4 dígitos almacenados
- **API Keys**: Solo en variables de entorno

## Testing

### Estrategia de Tests

- **Unit Tests**: Servicios y lógica de negocio
- **Integration Tests**: APIs y flujos completos
- **Mocking**: SDK Transbank para tests unitarios
- **Coverage**: Mínimo 80% requerido

### Tests con Transbank

```python
# Environment de integración con tarjetas de prueba
TEST_CARDS = {
    'visa_approved': '4051885600446623',
    'visa_rejected': '4051885600447528'
}
```

## Deployment

### Producción

1. **Certificación Transbank**
   - Completar proceso de certificación
   - Obtener códigos de comercio productivos

2. **Variables de Entorno**
```bash
ENVIRONMENT=production
TRANSBANK_ENVIRONMENT=production
TRANSBANK_COMMERCE_CODE=tu_codigo_productivo
TRANSBANK_API_KEY=tu_api_key_productiva
```

3. **Base de Datos**
   - PostgreSQL en producción
   - Backups automáticos configurados
   - Migraciones aplicadas

4. **Monitoreo**
   - Health checks configurados
   - Logs enviados a ELK Stack
   - Métricas de performance

## Monitoreo

### Health Checks

```bash
curl http://localhost:8000/health
```

### Métricas Importantes

- Tasa de éxito de inscripciones
- Tasa de aprobación de transacciones  
- Tiempo de respuesta promedio
- Volumen de transacciones
- Errores por minuto

## Soporte

### Documentación Transbank

- [Transbank Developers](https://www.transbankdevelopers.cl/)
- [SDK Python](https://github.com/TransbankDevelopers/transbank-sdk-python)
- [Referencia API](https://www.transbankdevelopers.cl/referencia/oneclick)

### Contacto

- **Soporte Técnico**: soporte@transbank.cl
- **Certificación**: certificacion@transbank.cl

## Licencia

[Especificar licencia del proyecto]