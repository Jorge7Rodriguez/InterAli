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

Documentación Swagger:

- http://localhost:8000/docs

## Autenticación por token en Swagger

Los endpoints protegidos usan esquema Bearer. Para autenticarte en Swagger:

1. Ejecuta `POST /auth/login` o `POST /auth/register` y copia `access_token`.
2. En Swagger, pulsa `Authorize`.
3. Pega el token en formato:

```text
Bearer <tu_access_token>
```

4. Confirma y prueba endpoints protegidos.

## Endpoints y cómo funciona cada uno

### Salud

#### GET /health

- Público.
- Respuesta esperada:

```json
{
	"status": "ok"
}
```

### Auth

#### POST /auth/register

- Público.
- Crea usuario y devuelve token JWT + perfil.
- Reglas clave:
	- `email` normalizado a minúsculas.
	- `password` y `confirm_password` deben coincidir.
	- Contraseña no puede superar 72 bytes UTF-8 (limitación bcrypt).
	- No permite autorregistro con rol `admin`.
- Códigos frecuentes:
	- `201` creado.
	- `409` email ya registrado.
	- `422` validaciones de payload.

#### POST /auth/login

- Público.
- Valida credenciales y devuelve token JWT + perfil.
- Códigos frecuentes:
	- `200` correcto.
	- `401` credenciales inválidas.
	- `403` usuario inactivo.

#### GET /auth/me

- Protegido (Bearer token).
- Devuelve el usuario autenticado actual.
- Códigos frecuentes:
	- `200` correcto.
	- `401` token inválido/expirado.

### Food Listings

#### POST /food-listings

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

#### GET /food-listings

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

#### GET /food-listings/{id}

- Público.
- Obtiene detalle de un listing por UUID.
- Códigos frecuentes:
	- `200` encontrado.
	- `404` no encontrado.

#### PATCH /food-listings/{id}

- Protegido.
- Actualiza campos parciales de un listing.
- Solo el donor dueño del listing o un `admin` pueden modificarlo.
- Códigos frecuentes:
	- `200` actualizado.
	- `403` no autorizado.
	- `404` no encontrado.

#### DELETE /food-listings/{id}

- Protegido.
- Elimina un listing.
- Solo el donor dueño del listing o un `admin` pueden eliminar.
- Códigos frecuentes:
	- `204` eliminado.
	- `403` no autorizado.
	- `404` no encontrado.

### Claims

#### POST /food-listings/{id}/claim

- Protegido.
- Crea un reclamo sobre un listing.
- Reglas de negocio:
	- solo `receivers` pueden reclamar
	- no se puede reclamar un listing expirado
	- no se puede reclamar dos veces el mismo listing
	- al crear el claim, el status del listing cambia automáticamente a `claimed`
- Códigos frecuentes:
	- `201` creado.
	- `403` si no eres receiver.
	- `400` si el listing está expirado.
	- `409` si el listing ya fue reclamado o no está disponible.

#### GET /claims/me

- Protegido.
- Devuelve los claims del usuario autenticado.
- Cada item incluye el claim y el `food_listing` asociado.

#### PATCH /claims/{id}/status

- Protegido.
- Actualiza el status del claim.
- Lo pueden ejecutar el donor dueño del listing o un admin.
- Status soportados:
	- `pending`
	- `approved`
	- `rejected`
	- `cancelled`
- Cambio automático del listing:
	# InterAli

	Backend de InterAli construido con FastAPI, SQLAlchemy async y PostgreSQL.

	Esta guía está orientada al equipo de frontend. Explica cómo consumir la API, qué mandar en cada request y qué esperar en cada response.

	## Stack

	- Python 3.12
	- FastAPI
	- SQLAlchemy 2.0 async + asyncpg
	- PostgreSQL
	- Docker + Docker Compose

	## Cómo levantar el backend

	```powershell
	docker compose up --build -d
	```

	Swagger UI:

	- http://localhost:8000/docs

	## Autenticación en el frontend

	La API usa JWT Bearer Authentication.

	Flujo recomendado:

	1. El usuario hace login con `POST /auth/login`.
	2. La API responde con `access_token`.
	3. El frontend guarda ese token en su estrategia de sesión.
	4. Para endpoints protegidos, el frontend envía:

	```http
	Authorization: Bearer <access_token>
	```

	## Convenciones generales

	- Los identificadores son UUID.
	- Los endpoints protegidos devuelven `401` si el token falta o es inválido.
	- Los errores de validación devuelven `422`.
	- Todos los cuerpos JSON se envían con `Content-Type: application/json`.

	## Resumen rápido de endpoints

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
	| PATCH | `/claims/{id}/status` | No | Cambiar estado de un claim |

	## Auth

	### POST `/auth/register`

	Registra un usuario y devuelve token.

	Body:

	```json
	{
		"email": "donor@example.com",
		"full_name": "Donor Test",
		"password": "Secret123!",
		"confirm_password": "Secret123!",
		"role": "donor"
	}
	```

	Reglas:

	- `email` se normaliza a minúsculas.
	- `password` y `confirm_password` deben coincidir.
	- No se permite autorregistro con rol `admin`.
	- La contraseña no puede superar 72 bytes UTF-8 por compatibilidad con bcrypt.

	Respuesta `201`:

	```json
	{
		"access_token": "<jwt>",
		"token_type": "bearer",
		"expires_in": 1800,
		"user": {
			"id": "uuid",
			"email": "donor@example.com",
			"full_name": "Donor Test",
			"role": "donor",
			"is_active": true,
			"created_at": "...",
			"updated_at": "..."
		}
	}
	```

	Errores comunes:

	- `409` si el correo ya existe.
	- `422` si el payload no pasa validaciones.

	### POST `/auth/login`

	Inicia sesión y devuelve token.

	Body:

	```json
	{
		"email": "donor@example.com",
		"password": "Secret123!"
	}
	```

	Respuesta `200`:

	```json
	{
		"access_token": "<jwt>",
		"token_type": "bearer",
		"expires_in": 1800,
		"user": {
			"id": "uuid",
			"email": "donor@example.com",
			"full_name": "Donor Test",
			"role": "donor",
			"is_active": true,
			"created_at": "...",
			"updated_at": "..."
		}
	}
	```

	Errores comunes:

	- `401` credenciales inválidas.
	- `403` usuario inactivo.

	### GET `/auth/me`

	Devuelve el usuario autenticado.

	Headers:

	```http
	Authorization: Bearer <access_token>
	```

	Respuesta `200`:

	```json
	{
		"id": "uuid",
		"email": "donor@example.com",
		"full_name": "Donor Test",
		"role": "donor",
		"is_active": true
	}
	```

	## Food Listings

	### Modelo de listing

	Campos principales que el frontend verá en respuestas:

	- `id`
	- `donor_id`
	- `title`
	- `description`
	- `quantity`
	- `category`
	- `expiration_date`
	- `pickup_address`
	- `status` (`active`, `claimed`, `cancelled`)
	- `created_at`

	### POST `/food-listings`

	Solo `donor` puede crear listings.

	Headers:

	```http
	Authorization: Bearer <access_token>
	Content-Type: application/json
	```

	Body:

	```json
	{
		"title": "Paquetes de arroz",
		"description": "10 bolsas de arroz",
		"quantity": 10,
		"category": "grains",
		"expiration_date": "2026-05-30T12:00:00Z",
		"pickup_address": "Mercado Central 100"
	}
	```

	Respuesta `201`:

	```json
	{
		"id": "uuid",
		"donor_id": "uuid",
		"title": "Paquetes de arroz",
		"description": "10 bolsas de arroz",
		"quantity": 10,
		"category": "grains",
		"expiration_date": "2026-05-30T12:00:00Z",
		"pickup_address": "Mercado Central 100",
		"status": "active",
		"created_at": "..."
	}
	```

	Errores comunes:

	- `403` si el usuario no es donor.
	- `422` si faltan campos o son inválidos.

	### GET `/food-listings`

	Lista listings con paginación y filtros.

	Query params:

	- `limit` número de elementos por página, default `20`, máximo `100`
	- `offset` desplazamiento, default `0`
	- `category` filtro opcional
	- `status` filtro opcional

	Ejemplos:

	```text
	GET /food-listings?limit=10&offset=0
	GET /food-listings?category=fruits&status=active&limit=10&offset=0
	```

	Respuesta `200`:

	```json
	{
		"items": [
			{
				"id": "uuid",
				"donor_id": "uuid",
				"title": "Frutas mixtas",
				"description": "Caja con manzanas y peras",
				"quantity": 5,
				"category": "fruits",
				"expiration_date": "2026-05-30T12:00:00Z",
				"pickup_address": "Av. Central 456",
				"status": "active",
				"created_at": "..."
			}
		],
		"total": 1,
		"limit": 10,
		"offset": 0
	}
	```

	### GET `/food-listings/{id}`

	Devuelve el detalle de un listing por UUID.

	Ejemplo:

	```text
	GET /food-listings/70194df1-6756-4222-be00-ffdabece7d3c
	```

	Errores comunes:

	- `404` si el listing no existe.
	- `422` si el UUID no es válido.

	### PATCH `/food-listings/{id}`

	Solo el donor dueño o un admin pueden editarlo.

	Headers:

	```http
	Authorization: Bearer <access_token>
	Content-Type: application/json
	```

	Body parcial ejemplo:

	```json
	{
		"quantity": 3,
		"status": "claimed"
	}
	```

	Campos editables:

	- `title`
	- `description`
	- `quantity`
	- `category`
	- `expiration_date`
	- `pickup_address`
	- `status`

	### DELETE `/food-listings/{id}`

	Solo el donor dueño o un admin pueden eliminarlo.

	Respuesta `204`: sin body.

	## Claims

	### POST `/food-listings/{id}/claim`

	Solo `receiver` puede reclamar.

	Headers:

	```http
	Authorization: Bearer <access_token>
	```

	Qué hace:

	- crea un claim para ese listing
	- bloquea reclamos duplicados
	- rechaza listings expirados
	- cambia automáticamente el status del listing a `claimed`

	Errores comunes:

	- `403` si el usuario no es receiver.
	- `400` si el listing está expirado.
	- `409` si el listing ya fue reclamado o no está disponible.

	Respuesta `201`:

	```json
	{
		"id": "uuid",
		"food_listing_id": "uuid",
		"receiver_id": "uuid",
		"status": "pending",
		"created_at": "...",
		"updated_at": "...",
		"food_listing": {
			"id": "uuid",
			"donor_id": "uuid",
			"title": "Paquetes de arroz",
			"description": "10 bolsas de arroz",
			"quantity": 10,
			"category": "grains",
			"expiration_date": "2026-05-30T12:00:00Z",
			"pickup_address": "Mercado Central 100",
			"status": "claimed",
			"created_at": "..."
		}
	}
	```

	### GET `/claims/me`

	Devuelve los claims del usuario autenticado.

	Headers:

	```http
	Authorization: Bearer <access_token>
	```

	Respuesta `200`:

	```json
	[
		{
			"id": "uuid",
			"food_listing_id": "uuid",
			"receiver_id": "uuid",
			"status": "pending",
			"created_at": "...",
			"updated_at": "...",
			"food_listing": {
				"id": "uuid",
				"title": "Paquetes de arroz",
				"status": "claimed"
			}
		}
	]
	```

	### PATCH `/claims/{id}/status`

	Solo el donor dueño del listing o un admin puede cambiarlo.

	Headers:

	```http
	Authorization: Bearer <access_token>
	Content-Type: application/json
	```

	Body:

	```json
	{
		"status": "rejected"
	}
	```

	Status disponibles:

	- `pending`
	- `approved`
	- `rejected`
	- `cancelled`

	Efecto automático en listing:

	- `approved` deja el listing en `claimed`
	- `rejected` o `cancelled` regresan el listing a `active`

	## Cómo usarlo desde frontend

	### Ejemplo de login con fetch

	```javascript
	async function login(email, password) {
		const response = await fetch('http://localhost:8000/auth/login', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ email, password }),
		});

		if (!response.ok) throw new Error('Login falló');

		return response.json();
	}
	```

	### Ejemplo de llamada protegida

	```javascript
	async function getMyClaims(token) {
		const response = await fetch('http://localhost:8000/claims/me', {
			headers: {
				Authorization: `Bearer ${token}`,
			},
		});

		if (!response.ok) throw new Error('No se pudieron cargar los claims');

		return response.json();
	}
	```

	## Pruebas manuales realizadas

	Se validó en Docker:

	- `POST /auth/register` → `201`
	- `POST /auth/login` → `200`
	- `GET /auth/me` → `200`
	- `POST /food-listings` con `receiver` → `403`
	- `POST /food-listings` con `donor` → `201`
	- `GET /food-listings` → `200`
	- `GET /food-listings/{id}` → `200`
	- `PATCH /food-listings/{id}` → `200`
	- `DELETE /food-listings/{id}` → `204`
	- `POST /food-listings/{id}/claim` con `receiver` → `201`
	- `POST /food-listings/{id}/claim` repetido → `409`
	- `GET /claims/me` → `200`
	- `PATCH /claims/{id}/status` → `200`

	## Comandos útiles para probar rápido

	```powershell
	Invoke-RestMethod -Uri 'http://localhost:8000/health' -Method Get

	$login = @{ email='tu@email.com'; password='tu_password' } | ConvertTo-Json -Compress
	$res = Invoke-RestMethod -Uri 'http://localhost:8000/auth/login' -Method Post -ContentType 'application/json' -Body $login
	$token = $res.access_token

	Invoke-RestMethod -Uri 'http://localhost:8000/auth/me' -Method Get -Headers @{ Authorization = "Bearer $token" }
	Invoke-RestMethod -Uri 'http://localhost:8000/food-listings?limit=10&offset=0' -Method Get
	```