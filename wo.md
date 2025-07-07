# Servicios Transbank Oneclick Mall - Especificación Técnica

## 1. Introducción

Este documento especifica los servicios que deben ser construidos para implementar la integración con **Transbank Oneclick Mall** utilizando el SDK oficial de Python, permitiendo pagos en un solo clic mediante tarjetas previamente inscritas.

### 1.1 Objetivo
Desarrollar una API REST que permita a los usuarios:
- Inscribir tarjetas de crédito/débito de forma segura
- Realizar pagos recurrentes sin reingresar datos de tarjeta
- Gestionar múltiples comercios en una sola transacción
- Procesar transacciones con altos estándares de seguridad

### 1.2 Alcance
La implementación cubrirá todos los servicios necesarios para operar con Transbank Oneclick Mall utilizando el SDK oficial de Python en ambientes de integración y producción.

### 1.3 Tecnologías de Referencia
- **SDK**: transbank-sdk (versión 6.1.0+)
- **Lenguaje**: Python 3.8+
- **API**: Transbank REST API v1.2
- **Documentación oficial**: https://www.transbankdevelopers.cl/

## 2. Arquitectura de Servicios

### 2.1 Componentes Principales
- **Servicio de Inscripción Mall**: Gestiona el registro de tarjetas para múltiples comercios
- **Servicio de Transacciones Mall**: Procesa pagos Oneclick con múltiples tiendas
- **Servicio de Gestión**: Administra inscripciones y consultas
- **Servicio de Operaciones**: Maneja capturas, reversas y anulaciones

### 2.2 Consideraciones de Seguridad
- Comunicación HTTPS/TLS obligatoria
- Headers de autenticación: `Tbk-Api-Key-Id` y `Tbk-Api-Key-Secret`
- Encriptación de datos sensibles (tbk_user, información de tarjetas)
- Cumplimiento con estándares PCI DSS y normativas locales

## 3. Servicios a Construir

### 3.1 Servicio de Inscripción de Tarjetas Mall

#### 3.1.1 Iniciar Inscripción
**Endpoint**: `POST /api/oneclick/mall/inscription/start`

**Descripción**: Inicia el proceso de inscripción de una nueva tarjeta de crédito/débito para Oneclick Mall.

**Headers requeridos**:
```
Tbk-Api-Key-Id: {commerce_code}
Tbk-Api-Key-Secret: {api_key}
Content-Type: application/json
```

**Parámetros de entrada**:
```json
{
  "username": "string",      // Identificador único del usuario (max 256 chars)
  "email": "string",         // Email del usuario para notificaciones
  "response_url": "string"   // URL de retorno después del proceso
}
```

**Implementación en Python**:
```python
from transbank.oneclick.mall_inscription import MallInscription

# Configuración para integración
MallInscription.configure_for_testing()

# Para producción
# MallInscription.configure_for_production(commerce_code, api_key)

response = MallInscription.start(
    username=username,
    email=email,
    response_url=response_url
)
```

**Respuesta exitosa**:
```json
{
  "data": {
    "token": "string",           // Token de sesión para el proceso
    "url_webpay": "string",      // URL para redirección a Transbank
    "expires_at": "datetime"     // Tiempo de expiración (60 minutos)
  },
  "status": 200,
  "message": "Inscripción iniciada exitosamente"
}
```

**Funcionalidades**:
- Validar formato de email y username
- Generar token de sesión único
- Crear URL de redirección a Transbank
- Establecer tiempo de expiración

#### 3.1.2 Finalizar Inscripción
**Endpoint**: `PUT /api/oneclick/mall/inscription/finish`

**Descripción**: Completa el proceso de inscripción y obtiene el token de usuario permanente.

**Headers requeridos**:
```
Tbk-Api-Key-Id: {commerce_code}
Tbk-Api-Key-Secret: {api_key}
Content-Type: application/json
```

**Parámetros de entrada**:
```json
{
  "token": "string"     // Token TBK_TOKEN enviado por Transbank
}
```

**Implementación en Python**:
```python
from transbank.oneclick.mall_inscription import MallInscription

response = MallInscription.finish(token=tbk_token)

# Acceso a propiedades de respuesta
response_code = response.response_code
tbk_user = response.tbk_user
authorization_code = response.authorization_code
card_type = response.card_type
card_number = response.card_number  # Últimos 4 dígitos enmascarados
```

**Respuesta exitosa**:
```json
{
  "data": {
    "tbk_user": "string",             // Token permanente del usuario
    "response_code": "number",        // 0 = éxito
    "authorization_code": "string",   // Código de autorización
    "card_type": "string",           // VISA, MASTERCARD, etc.
    "card_number": "string"          // Últimos 4 dígitos enmascarados
  },
  "status": 200,
  "message": "Tarjeta inscrita exitosamente"
}
```

**Funcionalidades**:
- Validar token TBK recibido de Transbank
- Comunicarse con API REST de Transbank
- Almacenar información de tarjeta (tokenizada y encriptada)
- Timeout máximo: 60 segundos desde recepción del token

### 3.2 Servicio de Transacciones Mall

#### 3.2.1 Autorizar Transacción Mall
**Endpoint**: `POST /api/oneclick/mall/transaction/authorize`

**Descripción**: Autoriza una nueva transacción mall utilizando una tarjeta previamente inscrita, permite múltiples comercios en una sola transacción.

**Headers requeridos**:
```
Tbk-Api-Key-Id: {commerce_code}
Tbk-Api-Key-Secret: {api_key}
Content-Type: application/json
```

**Parámetros de entrada**:
```json
{
  "username": "string",           // Usuario propietario de la tarjeta
  "tbk_user": "string",           // Token del usuario obtenido en finish
  "parent_buy_order": "string",   // Orden de compra padre única
  "details": [
    {
      "commerce_code": "string",      // Código de comercio hijo
      "buy_order": "string",          // Orden de compra del comercio hijo
      "amount": "number",             // Monto en pesos chilenos
      "installments_number": "number" // Número de cuotas
    }
  ]
}
```

**Implementación en Python**:
```python
from transbank.oneclick.mall_transaction import MallTransaction
from transbank.oneclick.mall_transaction_authorize_details import MallTransactionAuthorizeDetails

# Configuración
MallTransaction.configure_for_testing()

# Crear detalles de transacción
details = [
    MallTransactionAuthorizeDetails(
        commerce_code="597055555542",
        buy_order="child_buy_order_1",
        installments_number=1,
        amount=10000
    ),
    MallTransactionAuthorizeDetails(
        commerce_code="597055555543", 
        buy_order="child_buy_order_2",
        installments_number=3,
        amount=50000
    )
]

response = MallTransaction.authorize(
    username=username,
    tbk_user=tbk_user,
    parent_buy_order=parent_buy_order,
    details=details
)
```

**Respuesta exitosa**:
```json
{
  "data": {
    "parent_buy_order": "string",
    "session_id": "string",
    "card_detail": {
      "card_number": "string"     // Últimos 4 dígitos enmascarados
    },
    "accounting_date": "string",
    "transaction_date": "datetime",
    "details": [
      {
        "amount": "number",
        "status": "string",
        "authorization_code": "string",
        "payment_type_code": "string",
        "response_code": "number",    // 0 = aprobada
        "installments_number": "number",
        "commerce_code": "string",
        "buy_order": "string"
      }
    ]
  },
  "status": 200,
  "message": "Transacción autorizada exitosamente"
}
```

**Funcionalidades**:
- Validar tbk_user y username
- Verificar montos y cuotas por comercio
- Procesar autorización con múltiples tiendas
- Registrar transacción completa en base de datos
- Manejo de errores por detalle de comercio

### 3.3 Servicio de Gestión de Inscripciones

#### 3.3.1 Eliminar Inscripción
**Endpoint**: `DELETE /api/oneclick/mall/inscription/delete`

**Descripción**: Elimina una inscripción de tarjeta del sistema Oneclick Mall.

**Headers requeridos**:
```
Tbk-Api-Key-Id: {commerce_code}
Tbk-Api-Key-Secret: {api_key}
Content-Type: application/json
```

**Parámetros de entrada**:
```json
{
  "tbk_user": "string",       // Token del usuario a eliminar
  "username": "string"        // Username asociado a la inscripción
}
```

**Implementación en Python**:
```python
from transbank.oneclick.mall_inscription import MallInscription

response = MallInscription.delete(
    tbk_user=tbk_user,
    username=username
)
```

**Respuesta exitosa**:
```json
{
  "data": {
    "tbk_user": "string",
    "username": "string",
    "status": "deleted",
    "deletion_date": "datetime"
  },
  "status": 200,
  "message": "Inscripción eliminada exitosamente"
}
```

#### 3.3.2 Listar Inscripciones de Usuario
**Endpoint**: `GET /api/oneclick/inscriptions/{username}`

**Descripción**: Obtiene todas las inscripciones activas para un usuario.

**Headers requeridos**:
```
Tbk-Api-Key-Id: {commerce_code}
Tbk-Api-Key-Secret: {api_key}
```

**Respuesta exitosa**:
```json
{
  "data": {
    "username": "string",
    "inscriptions": [
      {
        "tbk_user": "string",
        "card_type": "string",
        "card_number": "string",        // Últimos 4 dígitos enmascarados
        "inscription_date": "datetime",
        "status": "active",
        "is_default": "boolean"
      }
    ],
    "total_inscriptions": "number"
  },
  "status": 200
}
```

### 3.4 Servicio de Operaciones Especiales

#### 3.4.1 Captura Diferida
**Endpoint**: `PUT /api/oneclick/mall/transaction/capture`

**Descripción**: Captura una transacción previamente autorizada en modo diferido.

**Headers requeridos**:
```
Tbk-Api-Key-Id: {commerce_code}
Tbk-Api-Key-Secret: {api_key}
Content-Type: application/json
```

**Parámetros de entrada**:
```json
{
  "child_commerce_code": "string",    // Código de comercio hijo
  "child_buy_order": "string",        // Orden de compra del comercio hijo
  "authorization_code": "string",     // Código de autorización a capturar
  "capture_amount": "number"          // Monto a capturar
}
```

**Implementación en Python**:
```python
from transbank.oneclick.mall_transaction import MallTransaction

response = MallTransaction.capture(
    child_commerce_code=child_commerce_code,
    child_buy_order=child_buy_order,
    authorization_code=authorization_code,
    capture_amount=capture_amount
)
```

**Respuesta exitosa**:
```json
{
  "data": {
    "authorization_code": "string",
    "authorization_date": "datetime",
    "captured_amount": "number",
    "response_code": "number"
  },
  "status": 200,
  "message": "Captura realizada exitosamente"
}
```

#### 3.4.2 Reversar/Anular Transacción
**Endpoint**: `POST /api/oneclick/mall/transaction/refund`

**Descripción**: Revierte una transacción realizada (disponible hasta 90 días después).

**Headers requeridos**:
```
Tbk-Api-Key-Id: {commerce_code}
Tbk-Api-Key-Secret: {api_key}
Content-Type: application/json
```

**Parámetros de entrada**:
```json
{
  "child_commerce_code": "string",    // Código de comercio hijo
  "child_buy_order": "string",        // Orden de compra a reversar
  "amount": "number"                  // Monto a reversar
}
```

**Implementación en Python**:
```python
from transbank.oneclick.mall_transaction import MallTransaction

response = MallTransaction.refund(
    child_commerce_code=child_commerce_code,
    child_buy_order=child_buy_order,
    amount=amount
)
```

**Respuesta exitosa**:
```json
{
  "data": {
    "type": "REVERSED",
    "response_code": "number",        // 0 = éxito
    "reversal_date": "datetime",
    "reversed_amount": "number"
  },
  "status": 200,
  "message": "Transacción reversada exitosamente"
}
```

### 3.5 Servicio de Consultas

#### 3.5.1 Consultar Estado de Transacción
**Endpoint**: `GET /api/oneclick/mall/transaction/{child_buy_order}/status`

**Descripción**: Obtiene el estado actual de una transacción específica por su orden de compra.

**Headers requeridos**:
```
Tbk-Api-Key-Id: {commerce_code}
Tbk-Api-Key-Secret: {api_key}
```

**Parámetros de consulta**:
- `child_commerce_code`: Código de comercio hijo (requerido)

**Implementación en Python**:
```python
from transbank.oneclick.mall_transaction import MallTransaction

response = MallTransaction.status(
    child_buy_order=child_buy_order,
    child_commerce_code=child_commerce_code
)
```

**Respuesta exitosa**:
```json
{
  "data": {
    "buy_order": "string",
    "session_id": "string", 
    "card_detail": {
      "card_number": "string"
    },
    "accounting_date": "string",
    "transaction_date": "datetime",
    "details": [
      {
        "amount": "number",
        "status": "string",
        "authorization_code": "string",
        "payment_type_code": "string",
        "response_code": "number",
        "installments_number": "number",
        "commerce_code": "string",
        "buy_order": "string",
        "balance": "number"
      }
    ]
  },
  "status": 200
}
```

#### 3.5.2 Historial de Transacciones por Usuario
**Endpoint**: `GET /api/oneclick/transactions/{username}/history`

**Descripción**: Obtiene el historial de transacciones de un usuario específico.

**Parámetros de consulta**:
- `start_date`: Fecha de inicio (YYYY-MM-DD) (opcional)
- `end_date`: Fecha de fin (YYYY-MM-DD) (opcional)
- `status`: Filtro por estado (opcional)
- `page`: Número de página (default: 1)
- `limit`: Límite de resultados por página (default: 50, max: 200)

**Respuesta exitosa**:
```json
{
  "data": {
    "username": "string",
    "transactions": [
      {
        "parent_buy_order": "string",
        "transaction_date": "datetime",
        "total_amount": "number",
        "card_number": "string",
        "status": "approved|rejected|reversed|nullified",
        "details": [
          {
            "child_buy_order": "string",
            "commerce_code": "string", 
            "amount": "number",
            "authorization_code": "string",
            "response_code": "number"
          }
        ]
      }
    ],
    "pagination": {
      "page": "number",
      "limit": "number",
      "total": "number",
      "total_pages": "number"
    }
  },
  "status": 200
}
```

## 4. Consideraciones de Implementación

### 4.1 Configuración del SDK de Python

#### 4.1.1 Instalación
```bash
pip install transbank-sdk
```

#### 4.1.2 Configuración de Ambientes
```python
from transbank.oneclick.mall_inscription import MallInscription
from transbank.oneclick.mall_transaction import MallTransaction

# Ambiente de Integración (Pruebas)
MallInscription.configure_for_testing()
MallTransaction.configure_for_testing()

# Ambiente de Producción
MallInscription.configure_for_production(
    commerce_code="tu_codigo_comercio_productivo",
    api_key="tu_api_key_productiva"
)
MallTransaction.configure_for_production(
    commerce_code="tu_codigo_comercio_productivo",
    api_key="tu_api_key_productiva"
)
```

#### 4.1.3 Códigos de Comercio de Integración
- **Oneclick Mall**: `597055555541`
- **Oneclick Mall Captura Diferida**: `597055555540`
- **API Key de Integración**: `579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C`
- **Tiendas Mall**: `597055555542`, `597055555543`

### 4.2 Autenticación y Seguridad
- Middleware para validar headers `Tbk-Api-Key-Id` y `Tbk-Api-Key-Secret`
- Encriptación de datos sensibles (tbk_user, información de tarjetas)
- Rate limiting específico por endpoint:
  - Inscripción: 10 requests/minuto por usuario
  - Transacciones: 100 requests/minuto por comercio
  - Consultas: 1000 requests/minuto por comercio
- Logging completo de operaciones para auditoría

### 4.3 Manejo de Errores

#### 4.3.1 Estructura de Error Estándar
```json
{
  "error": {
    "code": "TBK_001",              // Código interno de error
    "message": "string",            // Mensaje descriptivo
    "tbk_error_code": "string",     // Código de error de Transbank (si aplica)
    "tbk_error_message": "string",  // Mensaje de error de Transbank (si aplica)
    "timestamp": "datetime",
    "request_id": "string"          // ID único para trazabilidad
  },
  "status": "number"
}
```

#### 4.3.2 Códigos de Respuesta de Transbank
- `0`: Transacción aprobada
- `-1`: Rechazo de transacción
- `-2`: Transacción debe reintentarse
- `-3`: Error en transacción
- `-4`: Rechazo de transacción
- `-5`: Rechazo por error de tasa
- `-6`: Excede cupo máximo mensual
- `-7`: Excede límite diario por transacción
- `-8`: Rubro no autorizado

#### 4.3.3 Implementación de Manejo de Errores
```python
try:
    response = MallTransaction.authorize(...)
    if hasattr(response, 'details'):
        for detail in response.details:
            if detail.response_code != 0:
                # Manejar transacción rechazada por comercio
                handle_rejected_transaction(detail.response_code, detail.commerce_code)
except Exception as e:
    # Manejar errores de comunicación
    handle_communication_error(e)
```

### 4.4 Validaciones de Negocio

#### 4.4.1 Validaciones de Entrada
```python
import re

def validate_username(username):
    """Valida username según especificaciones Transbank"""
    if not username or len(username) > 256:
        raise ValueError("Username debe tener entre 1 y 256 caracteres")
    # Solo caracteres alfanuméricos y algunos especiales
    if not re.match(r'^[a-zA-Z0-9._-]+$', username):
        raise ValueError("Username contiene caracteres no permitidos")

def validate_email(email):
    """Valida formato de email"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValueError("Formato de email inválido")

def validate_amount(amount):
    """Valida monto de transacción"""
    if amount <= 0:
        raise ValueError("Monto debe ser mayor a 0")
    if amount > 999999999:  # Límite máximo de Transbank
        raise ValueError("Monto excede límite máximo permitido")

def validate_buy_order(buy_order):
    """Valida orden de compra"""
    if not buy_order or len(buy_order) > 255:
        raise ValueError("Orden de compra debe tener entre 1 y 255 caracteres")
```

#### 4.4.2 Validaciones de Timeout
- **Inscripción finish**: Máximo 60 segundos desde recepción del token
- **Autorización de transacción**: Timeout de 30 segundos
- **Operaciones de captura/reversa**: Timeout de 45 segundos

### 4.5 Modelos de Base de Datos

#### 4.5.1 Modelo de Inscripción
```python
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class OneclickInscription(Base):
    __tablename__ = 'oneclick_inscriptions'
    
    id = Column(String(36), primary_key=True)
    username = Column(String(256), nullable=False, index=True)
    email = Column(String(254), nullable=False)
    tbk_user = Column(Text, nullable=False)  # Encriptado
    card_type = Column(String(50))
    card_number_masked = Column(String(20))  # Solo últimos 4 dígitos
    authorization_code = Column(String(10))
    response_code = Column(Integer, nullable=False)
    inscription_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### 4.5.2 Modelo de Transacción Mall
```python
class OneclickMallTransaction(Base):
    __tablename__ = 'oneclick_mall_transactions'
    
    id = Column(String(36), primary_key=True)
    username = Column(String(256), nullable=False, index=True)
    parent_buy_order = Column(String(255), nullable=False, unique=True, index=True)
    session_id = Column(String(255))
    transaction_date = Column(DateTime, nullable=False)
    accounting_date = Column(String(10))
    total_amount = Column(Integer, nullable=False)
    card_number_masked = Column(String(20))
    status = Column(String(20), nullable=False)  # approved, rejected, reversed, etc.
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class OneclickMallTransactionDetail(Base):
    __tablename__ = 'oneclick_mall_transaction_details'
    
    id = Column(String(36), primary_key=True)
    transaction_id = Column(String(36), nullable=False, index=True)
    commerce_code = Column(String(20), nullable=False)
    buy_order = Column(String(255), nullable=False, index=True)
    amount = Column(Integer, nullable=False)
    authorization_code = Column(String(10))
    payment_type_code = Column(String(5))
    response_code = Column(Integer, nullable=False)
    installments_number = Column(Integer)
    status = Column(String(20), nullable=False)
    balance = Column(Integer)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
```

## 6. Testing y Certificación

### 6.1 Datos de Prueba para Integración

#### 6.1.1 Tarjetas de Prueba
```python
# Tarjetas proporcionadas por Transbank para testing
TEST_CARDS = {
    'visa_approved': {
        'number': '4051885600446623',
        'cvv': '123',
        'expiry': '11/25'
    },
    'mastercard_approved': {
        'number': '5186059559590568',
        'cvv': '123', 
        'expiry': '11/25'
    },
    'visa_rejected': {
        'number': '4051885600447528',
        'cvv': '123',
        'expiry': '11/25'
    }
}

# Datos de autenticación para pruebas
TEST_AUTH = {
    'rut': '11.111.111-1',
    'password': '123'
}
```

#### 6.1.2 Códigos de Comercio para Testing
```python
from transbank.common.integration_commerce_codes import IntegrationCommerceCodes
from transbank.common.integration_api_keys import IntegrationApiKeys

# Comercio principal mall
MALL_COMMERCE_CODE = IntegrationCommerceCodes.ONECLICK_MALL  # "597055555541"

# Tiendas del mall
STORE_1_CODE = "597055555542"
STORE_2_CODE = "597055555543"

# API Key
API_KEY = IntegrationApiKeys.WEBPAY
```

### 6.2 Tests Unitarios Críticos
```python
import unittest
from unittest.mock import patch, MagicMock

class TestOneclickMallService(unittest.TestCase):
    
    def setUp(self):
        self.service = OneclickMallService()
    
    @patch('transbank.oneclick.mall_inscription.MallInscription.start')
    def test_start_inscription_success(self, mock_start):
        # Configurar mock
        mock_response = MagicMock()
        mock_response.token = 'test_token'
        mock_response.url_webpay = 'https://test.url'
        mock_start.return_value = mock_response
        
        # Ejecutar
        result = self.service.start_inscription(
            username='testuser',
            email='test@example.com',
            response_url='https://callback.url'
        )
        
        # Verificar
        self.assertEqual(result['token'], 'test_token')
        mock_start.assert_called_once()
    
    @patch('transbank.oneclick.mall_transaction.MallTransaction.authorize')
    def test_authorize_transaction_success(self, mock_authorize):
        # Configurar mock de respuesta exitosa
        mock_response = MagicMock()
        mock_response.parent_buy_order = 'test_order'
        mock_response.details = [
            MagicMock(response_code=0, authorization_code='123456')
        ]
        mock_authorize.return_value = mock_response
        
        # Ejecutar
        result = self.service.authorize_transaction(
            username='testuser',
            tbk_user='test_tbk_user',
            parent_buy_order='test_order',
            details=[
                {
                    'commerce_code': '597055555542',
                    'buy_order': 'child_order_1',
                    'amount': 10000,
                    'installments_number': 1
                }
            ]
        )
        
        # Verificar
        self.assertEqual(result['status'], 200)
        mock_authorize.assert_called_once()
    
    def test_validate_username_invalid(self):
        with self.assertRaises(ValueError):
            self.service.validate_username('user@invalid')
    
    def test_validate_amount_zero(self):
        with self.assertRaises(ValueError):
            self.service.validate_amount(0)
```

## 7. Cronograma de Desarrollo

### Fase 1: Infraestructura Base (1-2 semanas)
- Configuración del proyecto Python con SDK de Transbank
- Modelos de base de datos y migraciones
- Configuración de ambientes (integración/producción)
- Sistema de logging y manejo de errores básico
- Framework API (FastAPI/Django REST)

### Fase 2: Servicios de Inscripción (1-2 semanas)
- Implementación de inicio de inscripción (start)
- Implementación de finalización de inscripción (finish)
- Validaciones de entrada y timeout
- Encriptación de datos sensibles
- Tests de integración con ambiente de prueba

### Fase 3: Servicios de Transacción Mall (2 semanas)
- Implementación de autorización de transacciones mall
- Manejo de múltiples comercios por transacción
- Validaciones de monto y reglas de negocio
- Sistema de consulta de estado
- Tests con tarjetas de prueba y múltiples tiendas

### Fase 4: Gestión y Operaciones (1-2 semanas)
- Eliminación de inscripciones
- Captura diferida (si aplica)
- Operaciones de reversa/anulación
- Consultas y reportes
- Optimización de rendimiento

### Fase 5: Seguridad y Monitoreo (1 semana)
- Implementación de rate limiting
- Auditoría completa de seguridad
- Health checks y métricas
- Configuración de alertas
- Documentación de APIs

### Fase 6: Certificación y Producción (1-2 semanas)
- Pruebas exhaustivas en ambiente de integración
- Proceso de certificación con Transbank
- Configuración de ambiente productivo
- Pruebas de carga y estrés
- Capacitación del equipo

## 8. Criterios de Aceptación

### 8.1 Funcionales
- ✅ Inscripción exitosa de tarjetas usando el SDK de Python
- ✅ Autorización de transacciones mall con múltiples comercios
- ✅ Eliminación segura de inscripciones
- ✅ Operaciones de captura y reversa funcionando correctamente
- ✅ Consultas de estado en tiempo real
- ✅ Manejo correcto de todos los códigos de error de Transbank
- ✅ Soporte para múltiples tiendas en una transacción

### 8.2 No Funcionales
- ✅ Tiempo de respuesta < 3 segundos para inscripciones
- ✅ Tiempo de respuesta < 2 segundos para autorizaciones
- ✅ Disponibilidad mínima del 99.9%
- ✅ Capacidad de procesar 1000 transacciones/minuto
- ✅ Todos los datos sensibles encriptados
- ✅ Logging completo de auditoría
- ✅ Rate limiting configurado por endpoint

### 8.3 Técnicos
- ✅ Cobertura de tests unitarios > 90%
- ✅ Cobertura de tests de integración > 80%
- ✅ Zero downtime deployment
- ✅ Monitoreo y alertas configuradas
- ✅ Documentación técnica completa
- ✅ Certificación aprobada por Transbank
- ✅ Conformidad con SDK oficial de Python

## 9. Configuración de Variables de Entorno

### 9.1 Variables Requeridas para Producción
```bash
# Ambiente Transbank
TRANSBANK_ENVIRONMENT=production
TRANSBANK_COMMERCE_CODE=tu_codigo_comercio_productivo
TRANSBANK_API_KEY=tu_api_key_productiva

# Códigos de tiendas mall
TRANSBANK_STORE_1_CODE=codigo_tienda_1
TRANSBANK_STORE_2_CODE=codigo_tienda_2

# Base de datos
DATABASE_URL=postgresql://user:pass@localhost/oneclick_db
DATABASE_ENCRYPT_KEY=clave_para_encriptar_datos_sensibles

# Seguridad
JWT_SECRET_KEY=clave_secreta_para_jwt
API_RATE_LIMIT_PER_MINUTE=100
CORS_ALLOWED_ORIGINS=https://tu-dominio.com

# Logging
LOG_LEVEL=INFO
LOG_FILE_PATH=/var/log/oneclick/service.log

# Timeouts
TRANSBANK_TIMEOUT_SECONDS=30
INSCRIPTION_FINISH_TIMEOUT_SECONDS=60
```

### 9.2 Variables para Integración/Testing
```bash
# Ambiente Transbank
TRANSBANK_ENVIRONMENT=integration

# Base de datos de testing
DATABASE_URL=postgresql://user:pass@localhost/oneclick_test_db

# Logging para desarrollo
LOG_LEVEL=DEBUG
LOG_TO_CONSOLE=true
```

## 10. Monitoreo y Logging

### 10.1 Configuración de Logging
```python
import logging
import json
from datetime import datetime
import sys

def setup_logging():
    """Configura el sistema de logging"""
    
    # Formateo estructurado para logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Handler para archivo
    file_handler = logging.FileHandler('/var/log/oneclick/service.log')
    file_handler.setFormatter(formatter)
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Configurar logger principal
    logger = logging.getLogger('oneclick_service')
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def log_transaction_event(event_type, username, data, logger):
    """Registra eventos de transacciones para auditoría"""
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'username': username,
        'data': data,
        'source': 'oneclick_mall_service'
    }
    logger.info(json.dumps(log_entry))
```

### 10.2 Eventos Críticos a Registrar
- Inicio y finalización de inscripciones
- Autorizaciones de transacciones (exitosas y fallidas)
- Operaciones de captura, reversa y anulación
- Eliminación de inscripciones
- Errores de comunicación con Transbank
- Intentos de acceso no autorizado
- Timeouts y errores de validación
- Cambios en configuración de ambiente

### 10.3 Health Checks
```python
from fastapi import FastAPI, HTTPException
import asyncio
import aiohttp
from sqlalchemy import text

app = FastAPI()

@app.get("/health")
async def health_check():
    """Endpoint de health check completo"""
    checks = {
        'service': 'healthy',
        'database': await check_database_connection(),
        'transbank_api': await check_transbank_connectivity(),
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if not all(checks.values()):
        raise HTTPException(status_code=503, detail=checks)
    
    return checks

async def check_database_connection():
    """Verifica conectividad con la base de datos"""
    try:
        # Intentar una consulta simple
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return result.fetchone()[0] == 1
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

async def check_transbank_connectivity():
    """Verifica conectividad con Transbank"""
    try:
        # Verificar configuración del SDK
        from transbank.oneclick.mall_inscription import MallInscription
        
        # Intentar obtener configuración actual
        config = MallInscription.default_options()
        return config is not None
    except Exception as e:
        logger.error(f"Transbank connectivity check failed: {e}")
        return False
```

## 11. Recursos Adicionales

### 11.1 Documentación Oficial
- [Transbank Developers](https://www.transbankdevelopers.cl/)
- [SDK Python en GitHub](https://github.com/TransbankDevelopers/transbank-sdk-python)
- [PyPI - transbank-sdk](https://pypi.org/project/transbank-sdk/)
- [Referencia API REST Oneclick Mall](https://www.transbankdevelopers.cl/referencia/oneclick)
- [Documentación de Oneclick](https://www.transbankdevelopers.cl/documentacion/oneclick)

### 11.2 Códigos de Comercio y Constantes
```python
# Importar constantes del SDK oficial
from transbank.common.integration_commerce_codes import IntegrationCommerceCodes
from transbank.common.integration_api_keys import IntegrationApiKeys

# Códigos de comercio para integración
ONECLICK_MALL = IntegrationCommerceCodes.ONECLICK_MALL  # "597055555541"
ONECLICK_MALL_DEFERRED = IntegrationCommerceCodes.ONECLICK_MALL_DEFERRED  # "597055555540"

# Códigos de tienda para mall
STORE_CODES = {
    'store_1': "597055555542",
    'store_2': "597055555543"
}

# API Keys
WEBPAY_API_KEY = IntegrationApiKeys.WEBPAY
```

### 11.3 Ejemplos de Implementación

#### 11.3.1 Servicio Completo de Inscripción
```python
from transbank.oneclick.mall_inscription import MallInscription
from datetime import datetime, timedelta
import uuid

class OneclickInscriptionService:
    
    def __init__(self):
        # Configurar ambiente según configuración
        if settings.TRANSBANK_ENVIRONMENT == 'production':
            MallInscription.configure_for_production(
                settings.TRANSBANK_COMMERCE_CODE,
                settings.TRANSBANK_API_KEY
            )
        else:
            MallInscription.configure_for_testing()
    
    async def start_inscription(self, username: str, email: str, response_url: str):
        """Inicia proceso de inscripción"""
        try:
            # Validaciones
            self.validate_username(username)
            self.validate_email(email)
            
            # Llamar al SDK
            response = MallInscription.start(
                username=username,
                email=email,
                response_url=response_url
            )
            
            # Registrar en base de datos
            inscription_record = {
                'id': str(uuid.uuid4()),
                'username': username,
                'email': email,
                'token': response.token,
                'status': 'pending',
                'expires_at': datetime.utcnow() + timedelta(minutes=60),
                'created_at': datetime.utcnow()
            }
            
            await self.save_inscription_record(inscription_record)
            
            # Log del evento
            log_transaction_event(
                'inscription_started',
                username,
                {'token': response.token, 'email': email},
                logger
            )
            
            return {
                'token': response.token,
                'url_webpay': response.url_webpay,
                'expires_at': inscription_record['expires_at']
            }
            
        except Exception as e:
            logger.error(f"Error starting inscription for {username}: {e}")
            raise
    
    async def finish_inscription(self, token: str):
        """Finaliza proceso de inscripción"""
        try:
            # Verificar que el token no haya expirado
            record = await self.get_inscription_by_token(token)
            if not record or record['expires_at'] < datetime.utcnow():
                raise ValueError("Token expirado o inválido")
            
            # Llamar al SDK
            response = MallInscription.finish(token=token)
            
            # Actualizar registro
            update_data = {
                'tbk_user': self.encrypt_sensitive_data(response.tbk_user),
                'response_code': response.response_code,
                'authorization_code': response.authorization_code,
                'card_type': response.card_type,
                'card_number_masked': response.card_number,
                'status': 'completed' if response.response_code == 0 else 'failed',
                'completed_at': datetime.utcnow()
            }
            
            await self.update_inscription_record(record['id'], update_data)
            
            # Log del evento
            log_transaction_event(
                'inscription_finished',
                record['username'],
                {
                    'response_code': response.response_code,
                    'card_type': response.card_type,
                    'success': response.response_code == 0
                },
                logger
            )
            
            return {
                'tbk_user': response.tbk_user,
                'response_code': response.response_code,
                'authorization_code': response.authorization_code,
                'card_type': response.card_type,
                'card_number': response.card_number
            }
            
        except Exception as e:
            logger.error(f"Error finishing inscription with token {token}: {e}")
            raise
```

### 11.4 Contactos y Soporte
- **Soporte Técnico**: soporte@transbank.cl
- **Certificación**: certificacion@transbank.cl
- **Documentación**: https://www.transbankdevelopers.cl/
- **GitHub Issues**: https://github.com/TransbankDevelopers/transbank-sdk-python/issues

### 11.5 Herramientas y Frameworks Recomendados
- **Framework API**: FastAPI (recomendado) o Django REST Framework
- **Base de datos**: PostgreSQL 12+ con extensiones de encriptación
- **ORM**: SQLAlchemy 1.4+ o Django ORM
- **Testing**: pytest con pytest-asyncio y coverage
- **Validación**: Pydantic (con FastAPI)
- **Monitoreo**: Prometheus + Grafana + AlertManager
- **Logging**: Structured logging con JSON
- **CI/CD**: GitHub Actions, GitLab CI, o Jenkins
- **Containerización**: Docker con multi-stage builds
- **Secrets Management**: HashiCorp Vault o AWS Secrets Manager

---

**Versión del documento**: 2.0  
**Fecha**: Julio 2025  
**Autor**: Equipo de Desarrollo  
**Basado en**: SDK oficial Python de Transbank v6.1.0+  
**Tipo de integración**: Oneclick Mall REST API