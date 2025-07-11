# Integración de transbank-oneclick-api en otros proyectos

Este documento explica cómo integrar el paquete `transbank-oneclick-api` en otros proyectos Python, especialmente en aplicaciones FastAPI.

---

## 1. Instalación

Puedes instalar el paquete directamente desde GitHub usando `pip` y tu `requirements.txt`:

```
git+https://github.com/danielsotopino/api-transbank.git@main
```

O directamente desde la terminal:

```
pip install git+https://github.com/danielsotopino/api-transbank.git@main
```

> **Nota:** Cambia `main` por la rama, tag o commit que desees usar.

---

## 2. Configuración

El paquete espera ciertas variables de entorno para funcionar correctamente. Puedes definirlas en un archivo `.env` o en tu entorno de ejecución:

- `DATABASE_URL`: URL de conexión a tu base de datos PostgreSQL
- `TRANSBANK_ENVIRONMENT`: `integration` o `production`
- `TRANSBANK_COMMERCE_CODE`: Código de comercio entregado por Transbank
- `TRANSBANK_API_KEY`: API Key entregada por Transbank
- `SECRET_KEY`: Clave secreta para la app

Ejemplo de `.env`:
```
DATABASE_URL=postgresql://usuario:password@localhost:5432/mi_db
TRANSBANK_ENVIRONMENT=integration
TRANSBANK_COMMERCE_CODE=597055555541
TRANSBANK_API_KEY=579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C
SECRET_KEY=supersecreto
```

---

## 3. Uso en una app FastAPI

Puedes montar la API de transbank directamente en tu aplicación FastAPI:

```python
from fastapi import FastAPI
from app.main import app as transbank_app

main_app = FastAPI()

# Montar la API de transbank bajo un prefijo
main_app.mount("/transbank", transbank_app)

# Ahora los endpoints estarán disponibles en /transbank/api/v1/...
```

O puedes importar y usar los routers/endpoints específicos según tu necesidad.

---

## 4. Migraciones y base de datos

El paquete **no incluye migraciones Alembic**. Debes definir y ejecutar tus propias migraciones en el proyecto que integra este paquete.

---

## 5. Ejemplo de endpoints disponibles

- `POST /transbank/api/v1/oneclick/mall/inscription/start` — Iniciar inscripción
- `PUT /transbank/api/v1/oneclick/mall/inscription/finish` — Finalizar inscripción
- `DELETE /transbank/api/v1/oneclick/mall/inscription/delete` — Eliminar inscripción
- `POST /transbank/api/v1/oneclick/mall/transaction/authorize` — Autorizar transacción
- `GET /transbank/api/v1/oneclick/mall/transaction/status/{child_buy_order}` — Estado de transacción

---

## 6. Recomendaciones

- Usa un entorno virtual para aislar dependencias.
- Revisa y adapta las variables de entorno a tu infraestructura.
- Implementa tus propias migraciones y backups de base de datos.
- Consulta la documentación oficial de Transbank para flujos productivos.

---

¿Dudas o problemas? Abre un issue en el repositorio o contacta a soporte@transbank.cl 