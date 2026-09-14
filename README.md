# Athena

Athena is a full-stack AI question-answering application with a Next.js frontend and FastAPI backend. Users submit a question through the web interface, receive an AI-generated response, and can optionally use text-to-speech output.

The project is deployed as separate frontend and backend services on Fly.io.

## Live Deployment

- Frontend: https://frontend-gentle-wildflower-1355.fly.dev
- Backend API: https://athena-soft-darkness-1468.fly.dev
- Ask endpoint: `POST /api/ask`
- Text-to-speech endpoint: `POST /api/tts`

## Features

- Submit natural-language questions through a responsive web UI.
- Receive AI-generated answers through a FastAPI API.
- Generate text-to-speech audio for returned answers.
- Separate frontend and backend deployments.
- Production-ready environment-variable configuration.
- Explicit cross-origin resource sharing (CORS) support for browser-to-API communication.
- Dockerized frontend build optimized for Next.js standalone output.

## Architecture

```text
Browser
  │
  │ HTTPS
  ▼
Next.js Frontend
[https://frontend-gentle-wildflower-1355.fly.dev](https://frontend-gentle-wildflower-1355.fly.dev)
  │
  │ POST /api/ask
  │ POST /api/tts
  ▼
FastAPI Backend
[https://athena-soft-darkness-1468.fly.dev](https://athena-soft-darkness-1468.fly.dev)
  │
  ▼
AI / Text-to-Speech Services
```

The browser loads the Next.js application from the frontend service. Client-side requests are sent directly to the FastAPI backend over HTTPS.

Because these services use separate origins, the backend explicitly authorizes the deployed frontend origin with FastAPI’s CORS middleware.

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | Next.js | Browser UI and client-side request handling |
| Backend | FastAPI | API routes, request validation, AI orchestration, and TTS handling |
| Runtime | Node.js 20 | Frontend build and production server |
| Language | TypeScript / Python | Frontend and backend implementation |
| Deployment | Fly.io | Separate frontend and backend application hosting |
| Containerization | Docker | Reproducible production builds and deployments |

## Local Development

### Prerequisites

- Node.js 20+
- npm
- Python 3.10+ (or the version specified by the backend)
- Fly.io CLI, if you want to deploy

### Frontend setup

```bash
cd frontend
npm install
```

Create a local environment file:

```bash
# frontend/.env.local
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Start the frontend:

```bash
npm run dev
```

The frontend should be available at:

```text
http://localhost:3000
```

### Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Configure the backend environment variables required by your AI and text-to-speech providers. For example:

```bash
# backend/.env
OPENAI_API_KEY=your_key_here
```

Start the API server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend should be available at:

```text
http://127.0.0.1:8000
```

## Environment Variables

### Frontend

| Variable | Required | Example | Description |
|---|---:|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Yes | `https://athena-soft-darkness-1468.fly.dev` | Base URL for browser requests to the backend API |

`NEXT_PUBLIC_*` values used by client-side Next.js code are embedded during `next build`. They must be available during the Docker image build, not only at container runtime.

### Backend

| Variable | Required | Description |
|---|---:|---|
| `OPENAI_API_KEY` | Depends on provider | API key used for AI generation |
| Provider-specific TTS variables | Depends on provider | Credentials and configuration for text-to-speech |
| Other server configuration | Optional | Logging, environment, model, or rate-limit settings |

Do not commit secrets or `.env` files to version control.

## CORS Configuration

The frontend and backend are hosted on different origins, so the backend must explicitly allow browser requests from the frontend.

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "[https://frontend-gentle-wildflower-1355.fly.dev](https://frontend-gentle-wildflower-1355.fly.dev)",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
```

The production origin must match exactly:

```text
[https://frontend-gentle-wildflower-1355.fly.dev](https://frontend-gentle-wildflower-1355.fly.dev)
```

Do not include a trailing slash. CORS compares origins precisely, and a trailing slash makes the configured value fail to match the browser’s `Origin` header.

## Docker Build Configuration

The frontend image uses a multi-stage Docker build and Next.js standalone output.

```dockerfile
FROM node:20-alpine AS base

FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

FROM base AS builder
WORKDIR /app

ARG NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL

COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000

CMD ["node", "server.js"]
```

The `ARG` and `ENV` declarations in the builder stage are intentional. Without them, the frontend client bundle can build with an undefined API base URL.

## Deployment

### Deploy the backend

Deploy the FastAPI service from the backend directory:

```bash
cd backend
fly deploy -a athena-soft-darkness-1468
```

Set secrets through Fly.io rather than committing them:

```bash
fly secrets set OPENAI_API_KEY="your_key_here" -a athena-soft-darkness-1468
```

### Deploy the frontend

The public API URL is a build-time value for the Next.js client bundle:

```bash
cd frontend

fly deploy -a frontend-gentle-wildflower-1355 \
  --build-arg NEXT_PUBLIC_API_BASE_URL="[https://athena-soft-darkness-1468.fly.dev](https://athena-soft-darkness-1468.fly.dev)"
```

## Production Debugging Notes

During deployment, the application surfaced two related configuration problems.

### 1. Client bundle API URL was undefined

The browser initially attempted to call:

```text
[https://frontend-gentle-wildflower-1355.fly.dev/undefined/api/ask](https://frontend-gentle-wildflower-1355.fly.dev/undefined/api/ask)
```

The issue was that `NEXT_PUBLIC_API_BASE_URL` was not available during the Next.js Docker build. Since client-exposed Next.js environment values are compiled into the browser bundle, setting the variable only at runtime was insufficient.

The fix was to pass the value through the Docker builder stage with:

```dockerfile
ARG NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
```

and provide it during deployment:

```bash
fly deploy \
  --build-arg NEXT_PUBLIC_API_BASE_URL="[https://athena-soft-darkness-1468.fly.dev](https://athena-soft-darkness-1468.fly.dev)"
```

### 2. Backend CORS configuration rejected the frontend

Once requests reached the correct backend URL, the browser still blocked the response because the backend did not return `Access-Control-Allow-Origin`.

The underlying issue was a subtle Python syntax problem in the CORS origin list: a missing comma between two adjacent string literals caused Python to concatenate them silently.

Incorrect:

```python
origins = [
    "[https://frontend-gentle-wildflower-1355.fly.dev](https://frontend-gentle-wildflower-1355.fly.dev)"
    "http://localhost:3000",
]
```

Correct:

```python
origins = [
    "[https://frontend-gentle-wildflower-1355.fly.dev](https://frontend-gentle-wildflower-1355.fly.dev)",
    "http://localhost:3000",
]
```

This debugging process reinforced two deployment practices:

- Treat browser-exposed Next.js environment variables as build-time configuration.
- Validate CORS origins exactly and inspect preflight `OPTIONS` requests when cross-origin calls fail.

## API Usage

### Ask a question

```bash
curl -X POST "[https://athena-soft-darkness-1468.fly.dev/api/ask](https://athena-soft-darkness-1468.fly.dev/api/ask)" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the main benefits of containerized deployments?"
  }'
```

Replace the request body with the schema used by your API if your route expects a field other than `question`.

### Generate speech

```bash
curl -X POST "[https://athena-soft-darkness-1468.fly.dev/api/tts](https://athena-soft-darkness-1468.fly.dev/api/tts)" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello from Athena."
  }'
```

Replace the request body with the schema used by your text-to-speech route.

## Future Improvements

- Add automated integration tests for frontend-to-backend requests.
- Add a health-check endpoint and uptime monitoring.
- Add rate limiting and abuse protection to public API routes.
- Add structured application logging and request IDs.
- Add frontend error states that distinguish network, API, and configuration failures.
- Add a CI/CD workflow that validates Docker builds and required deployment configuration.
- Add authentication if the API becomes publicly accessible beyond a demonstration environment.