# InterAli

Backend de InterAli construido con FastAPI, SQLAlchemy async y PostgreSQL.

## Stack

- Python 3.12
- FastAPI
- SQLAlchemy 2.0 async + asyncpg
- PostgreSQL
- Docker + Docker Compose

## Levantar el proyecto

```powershell
docker compose up --build -d
```

Swagger UI:

- http://localhost:8000/docs

## Autenticación por token en Swagger

Los endpoints protegidos usan Bearer. Para autenticarte en Swagger:

1. Ejecuta `POST /auth/login` o `POST /auth/register` y copia `access_token`.
2. En Swagger, pulsa `Authorize`.
3. Pega el token en formato:

```text
Bearer <tu_access_token>
```

4. Confirma y prueba endpoints protegidos.

## Resumen de endpoints

| Método | Ruta | Público | Uso |
| --- | --- | --- | --- |
| GET | `/health` | Sí | Verificar que la API está viva |
| POST | `/auth/register` | Sí | Crear usuario y obtener token |
| POST | `/auth/login` | Sí | Iniciar sesión y obtener token |
| GET | `/auth/me` | No | Obtener usuario autenticado |
| POST | `/food-listings` | No | Crear un listing como donor |
| GET | `/food-listings` | Sí | Listar listings con paginación/filtros |
| GET | `/food-listings/{id}` | Sí | Ver detalle de un listing |
| PATCH | `/food-listings/{id}` | No | Editar un listing |
| DELETE | `/food-listings/{id}` | No | Eliminar un listing |
| POST | `/food-listings/{id}/claim` | No | Reclamar un listing |
| GET | `/claims/me` | No | Ver los claims del usuario actual |
| GET | `/claims/donor` | No | Ver claims asociados al donor |
| PATCH | `/claims/{id}/status` | No | Cambiar estado de un claim |

## Auth

### POST `/auth/register`

- Público.
- Crea usuario y devuelve token JWT + perfil.
- Reglas clave:
  - `email` normalizado a minúsculas.
  - `password` y `confirm_password` deben coincidir.
  - La contraseña no puede superar 72 bytes UTF-8 por compatibilidad con bcrypt.
  - No permite autorregistro con rol `admin`.
- Códigos frecuentes:
  - `201` creado.
  - `409` email ya registrado.
  - `422` validaciones de payload.

### POST `/auth/login`

- Público.
- Valida credenciales y devuelve token JWT + perfil.
- Códigos frecuentes:
  - `200` correcto.
  - `401` credenciales inválidas.
  - `403` usuario inactivo.

### GET `/auth/me`

- Protegido con Bearer token.
- Devuelve el usuario autenticado actual.
- Códigos frecuentes:
  - `200` correcto.
  - `401` token inválido o expirado.

## Food Listings

### POST `/food-listings`

- Protegido.
- Crea un listing de comida.
- Regla de negocio: solo usuarios con rol `donor` pueden crear.
- Códigos frecuentes:
  - `201` creado.
  - `403` si el usuario no es donor.
  - `422` validaciones de payload.

Campos del listing:

- `id` UUID
- `donor_id`
- `title`
- `description`
- `quantity`
- `category`
- `expiration_date`
- `pickup_address`
- `status` (`active`, `claimed`, `cancelled`)
- `created_at`

### GET `/food-listings`

- Público.
- Lista listings con paginación y filtros.
- Query params:
  - `limit` (1-100, default 20)
  - `offset` (>= 0, default 0)
  - `category` (opcional)
  - `status` (opcional)
- Respuesta:
  - `items`: lista de listings
  - `total`: total global de resultados para ese filtro
  - `limit`, `offset`

### GET `/food-listings/{id}`

- Público.
- Obtiene detalle de un listing por UUID.
- Códigos frecuentes:
  - `200` encontrado.
  - `404` no encontrado.

### PATCH `/food-listings/{id}`

- Protegido.
- Actualiza campos parciales de un listing.
- Solo el donor dueño del listing o un `admin` pueden modificarlo.
- Códigos frecuentes:
  - `200` actualizado.
  - `403` no autorizado.
  - `404` no encontrado.

### DELETE `/food-listings/{id}`

- Protegido.
- Elimina un listing.
- Solo el donor dueño del listing o un `admin` pueden eliminarlo.
- Si el listing tiene claims asociados, la API responde `409` y no lo borra.
- Códigos frecuentes:
  - `204` eliminado.
  - `403` no autorizado.
  - `404` no encontrado.
  - `409` si existen claims asociados.

## Claims

### POST `/food-listings/{id}/claim`

- Protegido.
- Crea un reclamo sobre un listing.
- Reglas de negocio:
  - solo `receivers` pueden reclamar
  - no se puede reclamar un listing expirado
  - mientras exista un claim en estado `pending`, nadie más puede reclamar ese listing
  - si el claim anterior fue `rejected` o `cancelled`, el listing vuelve a estar disponible para cualquier `receiver`
  - al crear un claim nuevo, el status del listing cambia automáticamente a `claimed`
- Códigos frecuentes:
  - `201` creado.
  - `403` si no eres receiver.
  - `400` si el listing está expirado.
  - `409` si existe un claim `pending` o el listing no está disponible.

### GET `/claims/me`

- Protegido.
- Devuelve los claims del usuario autenticado.
- Cada item incluye el claim y el `food_listing` asociado.

### GET `/claims/donor`

- Protegido.
- Devuelve los claims asociados a los listings del donor autenticado.
- También lo puede usar un `admin` para ver todos los claims.

### PATCH `/claims/{id}/status`

- Protegido.
- Actualiza el status del claim.
- Lo pueden ejecutar el donor dueño del listing o un admin.
- Status soportados:
  - `pending`
  - `approved`
  - `rejected`
  - `cancelled`
- Cambio automático del listing:
  - `approved` mantiene el listing en `claimed`
  - `rejected` devuelve el listing a `active`
  - `cancelled` devuelve el listing a `active`

## Flujo actualizado de reclamos

El sistema ahora funciona así:

1. Un `donor` publica un listing y queda en `active`.
2. Un `receiver` lo reclama y el listing pasa a `claimed`.
3. Si el `donor` rechaza o cancela ese claim, el claim queda guardado con ese estado y el listing vuelve a `active`.
4. Desde ese momento, cualquier otro `receiver` puede reclamar el mismo listing.
5. Solo los claims en estado `pending` bloquean un nuevo reclamo.

## Verificación

La secuencia de publicación, reclamo, rechazo, nuevo reclamo y bloqueo de eliminación quedó cubierta en `tests/test_claim_flow.py`.
