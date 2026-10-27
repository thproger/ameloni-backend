# Афіша подій — Event Poster API

Production-ready **FastAPI** backend for an Event Poster / Recommendation platform.

| Layer | Stack |
|---|---|
| Framework | Python 3.11+, FastAPI |
| Database | MongoDB via Motor + Beanie (Pydantic v2) |
| Auth | JWT (`python-jose`) + `passlib[bcrypt]` |
| Media | Cloudflare Images (direct upload URL + multipart) |
| Spec | OpenAPI 3 (Swagger UI, JSON & YAML export) |

---

## Project layout

```
app/
  core/          # config, security, database, dependencies, exceptions
  models/        # Beanie documents (User, Event, Comment)
  schemas/       # Pydantic v2 DTOs
  api/v1/        # HTTP routers (auth, events, media, openapi)
  services/      # business logic + Cloudflare client
  main.py        # app factory, CORS, custom OpenAPI
scripts/
  export_openapi.py
docker-compose.yml
Dockerfile
requirements.txt
```

---

## Quick start (Docker)

```bash
cp .env.example .env
# edit SECRET_KEY and Cloudflare credentials as needed

docker compose up --build
```

- API: http://localhost:8000  
- Swagger UI: http://localhost:8000/docs  
- ReDoc: http://localhost:8000/redoc  
- OpenAPI JSON: http://localhost:8000/api/v1/openapi.json  
- OpenAPI YAML: http://localhost:8000/api/v1/openapi.yaml  

---

## Local development (without Docker for the API)

```bash
# 1. Start MongoDB (Docker)
docker compose up mongo -d

# 2. Python env
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env

# 3. Run API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Set `MONGODB_URI=mongodb://localhost:27017` in `.env` when Mongo runs locally.

---

## Export OpenAPI schemas

```bash
python scripts/export_openapi.py
```

Writes `openapi.json` and `openapi.yaml` to the project root (for Orval / openapi-generator).

---

## Roles & access

| Role | Capabilities |
|---|---|
| Anonymous | Read events, event details, **public** comments |
| `USER` | + like events, post comments |
| `NGO` | + CRUD **own** events, upload media, see **organizer-only** comments |

### Auth

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/auth/register/user` | Register USER |
| POST | `/api/v1/auth/register/ngo` | Register NGO (+ org fields) |
| POST | `/api/v1/auth/login` | JWT access token |
| GET | `/api/v1/auth/me` | Current profile |

### Events

| Method | Path | Access |
|---|---|---|
| GET | `/api/v1/events` | Public (filters + pagination) |
| GET | `/api/v1/events/{id}` | Public |
| POST | `/api/v1/events` | NGO |
| PUT | `/api/v1/events/{id}` | NGO (owner) |
| DELETE | `/api/v1/events/{id}` | NGO (owner) |
| POST | `/api/v1/events/{id}/like` | Authenticated |
| POST | `/api/v1/events/{id}/comments` | Authenticated |
| GET | `/api/v1/events/{id}/comments` | Public (visibility filtered) |

**List filters:** `search`, `tags`, `location`, `is_multiday`, `days_of_week`, `is_reimbursable`, `start_date_from`, `start_date_to`, `page`, `limit`.

### Media (Cloudflare Images)

| Method | Path | Access |
|---|---|---|
| POST | `/api/v1/media/upload-url` | NGO — returns direct upload URL + predicted CDN URL |
| POST | `/api/v1/media/upload` | NGO — server-side multipart proxy |

Configure in `.env`:

```env
CLOUDFLARE_ACCOUNT_ID=...
CLOUDFLARE_API_TOKEN=...
CLOUDFLARE_IMAGES_DELIVERY_URL=https://imagedelivery.net/<account_hash>
```

---

## Example flow

```bash
# Register NGO
curl -s -X POST http://localhost:8000/api/v1/auth/register/ngo \
  -H "Content-Type: application/json" \
  -d '{"email":"org@example.com","password":"secret123","full_name":"Admin","organization_name":"Культурний хаб","contact_info":"+380..."}'

# Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"org@example.com","password":"secret123"}' | jq -r .access_token)

# Create event
curl -s -X POST http://localhost:8000/api/v1/events \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Jazz Night","description_markdown":"**Live jazz**","start_date_time":"2026-11-01T19:00:00Z","location":"м. Миколаїв","tags":["#Музичний","#Культура"],"is_reimbursable":true}'
```
