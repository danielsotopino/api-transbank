# Configuración Docker para API Transbank

## Configuración de Variables de Entorno

### 1. Crear archivo `.env`

Copia el contenido del archivo `docker-env-template.txt` a un nuevo archivo llamado `.env`:

```bash
cp docker-env-template.txt .env
```

### 2. Modificar variables en `.env`

Edita el archivo `.env` con tus valores específicos:

#### Variables críticas que DEBES cambiar:
- `SECRET_KEY`: Genera una clave secreta fuerte
- `POSTGRES_PASSWORD`: Cambia la contraseña de la base de datos
- `DATABASE_ENCRYPT_KEY`: Clave de 32 caracteres para cifrado
- `REDIS_PASSWORD`: Contraseña para Redis
- `DATABASE_URL`: Actualiza con la nueva contraseña de PostgreSQL
- `REDIS_URL`: Actualiza con la nueva contraseña de Redis

#### Para entorno de producción también cambiar:
- `TRANSBANK_COMMERCE_CODE`: Tu código de comercio real
- `TRANSBANK_API_KEY`: Tu API key real de Transbank
- `TRANSBANK_ENVIRONMENT`: Cambiar a "production"
- `ENVIRONMENT`: Cambiar a "production"
- `DEBUG`: Cambiar a "false"

### 3. Generar claves seguras

#### SECRET_KEY (32+ caracteres):
```bash
openssl rand -hex 32
```

#### DATABASE_ENCRYPT_KEY (exactamente 32 caracteres):
```bash
openssl rand -hex 16
```

## Uso del Docker Compose

### Iniciar servicios:
```bash
docker-compose up -d
```

### Ver logs:
```bash
docker-compose logs -f api
```

### Detener servicios:
```bash
docker-compose down
```

### Reiniciar solo la API:
```bash
docker-compose restart api
```

## Servicios Disponibles

- **API**: http://localhost:8000
- **Base de datos**: PostgreSQL en puerto 5432
- **Redis**: Puerto 6379
- **Adminer** (UI de BD): http://localhost:8080

## Configuración de Puertos

Puedes cambiar los puertos en el archivo `.env`:
- `API_PORT`: Puerto de la API (default: 8000)
- `POSTGRES_PORT`: Puerto de PostgreSQL (default: 5432)
- `REDIS_PORT`: Puerto de Redis (default: 6379)
- `ADMINER_PORT`: Puerto de Adminer (default: 8080)

## Troubleshooting

### Error de conexión a la base de datos:
1. Verifica que `DATABASE_URL` tenga la contraseña correcta
2. Asegúrate de que `POSTGRES_PASSWORD` coincida con la URL

### Error de Redis:
1. Verifica que `REDIS_URL` tenga la contraseña correcta
2. Asegúrate de que `REDIS_PASSWORD` esté configurado

### Regenerar volúmenes:
```bash
docker-compose down -v
docker-compose up -d
``` 