# SpareRoom Chat Assistant

A chat interface for finding rooms to rent in London. Uses OpenAI for conversational AI, Redis for vector search (RAG), and Supabase for authentication and data persistence.

## Architecture

- **Frontend**: React + TypeScript + Material UI
- **Backend**: FastAPI + Python (stateless API)
- **Auth**: Supabase Auth (magic links)
- **Database**: Supabase PostgreSQL with RLS
- **Vector Search**: Redis with OpenAI embeddings

## Prerequisites

- Python 3.12+
- Node.js 18+
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- [Supabase CLI](https://supabase.com/docs/guides/cli)
- Docker (for local Supabase)
- OpenAI API key
- Redis credentials (for vector search)

## Quick Start

### 1. Start Supabase (Local Development)

```bash
# Start local Supabase (requires Docker)
supabase start

# This will output your local credentials:
# - API URL: http://127.0.0.1:54321
# - anon key: eyJ...
# - Inbucket (email testing): http://127.0.0.1:54324
```

### 2. Backend Setup

```bash
cd backend

# Create .env file
cp .env.example .env
# Edit .env with your credentials:
# - OPENAI_API_KEY=sk-...
# - REDIS_HOST, REDIS_PORT, REDIS_PASSWORD

# Install dependencies and run
uv sync
uv run uvicorn main:app --reload --port 8000
```

Backend runs at http://localhost:8000

### 3. Frontend Setup

```bash
cd frontend

# Create .env.local for local development
cat > .env.local << 'EOF'
VITE_SUPABASE_URL=http://127.0.0.1:54321
VITE_SUPABASE_ANON_KEY=<your-anon-key-from-supabase-start>
VITE_BACKEND_URL=http://localhost:8000
VITE_APP_URL=http://localhost:5173
EOF

# Install dependencies and run
npm install
npm run dev
```

Frontend runs at http://localhost:5173

### 4. View Magic Link Emails

For local development, emails are captured by Inbucket:
- Open http://127.0.0.1:54324
- Find your magic link email and click to authenticate

## Database Schema

The schema is defined in `supabase/schema.sql`. Tables:

| Table | Purpose |
|-------|---------|
| `profiles` | User profiles (auto-created on signup) |
| `conversations` | Chat conversations per user |
| `messages` | Messages within conversations |
| `user_rules` | Extracted search filters per conversation |
| `saved_listings` | Shortlisted/blacklisted listings |

All tables have Row Level Security (RLS) - users can only access their own data.

## Database Commands

All database commands are run from the root directory:

| Command | Description |
|---------|-------------|
| `npm run db:start` | Start local Supabase |
| `npm run db:stop` | Stop local Supabase |
| `npm run db:status` | Show Supabase status and credentials |
| `npm run db:reset` | Reset database and apply migrations |
| `npm run db:diff -- <name>` | Generate migration from schema changes |
| `npm run db:types` | Regenerate TypeScript types from database |
| `npm run db:studio` | Open Supabase Studio in browser |

## Database Migrations

Schema changes follow this workflow:

```bash
# 1. Edit the source of truth
vim supabase/schema.sql

# 2. Reset local DB and apply schema
npm run db:reset

# 3. Generate migration from diff
npm run db:diff -- my_migration_name

# 4. Review the generated migration
cat supabase/migrations/*_my_migration_name.sql

# 5. Regenerate TypeScript types
npm run db:types
```

## Updating TypeScript Types

When you change the database schema, regenerate the TypeScript types:

```bash
npm run db:types
```

This updates `frontend/src/types/supabase.ts` with types matching your database tables. The app types in `frontend/src/types/index.ts` extend these generated types.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Send message, get AI response + extracted rules |
| `/api/find-matches` | POST | RAG pipeline: search + filter + rerank listings |
| `/health` | GET | Health check |

## Project Structure

```
├── backend/
│   ├── main.py                 # FastAPI app (typed)
│   └── clients/
│       ├── openai_client.py    # OpenAI embeddings, chat, vision
│       └── redis_client.py     # Vector search
├── frontend/
│   ├── src/
│   │   ├── App.tsx             # Main app component
│   │   ├── auth/
│   │   │   └── AuthContext.tsx # Supabase auth provider
│   │   ├── components/
│   │   │   ├── ChatPanel.tsx
│   │   │   ├── ListingsPanel.tsx
│   │   │   └── RulesPanel.tsx
│   │   ├── hooks/
│   │   │   ├── useConversation.ts
│   │   │   ├── useRules.ts
│   │   │   └── useSavedListings.ts
│   │   ├── lib/
│   │   │   └── supabase.ts     # Typed Supabase client
│   │   ├── pages/
│   │   │   └── Login.tsx
│   │   └── types/
│   │       ├── index.ts        # App types
│   │       └── supabase.ts     # Generated DB types
│   └── package.json
├── supabase/
│   ├── config.toml             # Supabase local config
│   ├── schema.sql              # Source of truth for DB schema
│   └── migrations/             # Generated migrations
└── package.json                # Root scripts for DB management
```

## Environment Variables

### Backend (.env)

```
OPENAI_API_KEY=sk-...
REDIS_HOST=...
REDIS_PORT=...
REDIS_PASSWORD=...
```

### Frontend (.env.local)

```
VITE_SUPABASE_URL=http://127.0.0.1:54321
VITE_SUPABASE_ANON_KEY=eyJ...
VITE_BACKEND_URL=http://localhost:8000
VITE_APP_URL=http://localhost:5173
```

## Usage

1. Start Supabase, backend, and frontend
2. Open http://localhost:5173
3. Enter your email to receive a magic link
4. Check Inbucket (http://127.0.0.1:54324) and click the link
5. Chat with the assistant about your room preferences:
   - "Looking for a room under £700"
   - "I work at Bank, max 30 min commute"
   - "Need a pet-friendly place"

The assistant extracts filters, searches the vector database, and ranks listings using GPT-4 vision.

## Production Deployment

### 1. Backend (Google Cloud Run)

The backend is deployed to Cloud Run using the `deploy.sh` script. It uses Google Secret Manager for sensitive configuration.

**One-time Setup:**
```bash
cd backend
./setup-secrets.sh
# Follow prompts to enter API keys (OpenAI, Supabase, Redis, etc.)
```

**Updating Secrets:**
If you need to update a secret (e.g., Supabase Anon Key), use the safe update script to avoid newline issues:
```bash
cd backend
./update_secret.sh
```

**Deploy:**
```bash
cd backend
./deploy.sh
```
This will deploy the container and map the secrets automatically.

### 2. Frontend (Vercel)

The frontend is deployed to Vercel.

**Environment Variables:**
You must set the following in **Vercel Dashboard > Settings > Environment Variables**:

| Variable | Description |
|----------|-------------|
| `VITE_SUPABASE_URL` | Your production Supabase Project URL |
| `VITE_SUPABASE_ANON_KEY` | Your production Supabase Anon Key |
| `VITE_BACKEND_URL` | The Cloud Run URL (from step 1) |
| `VITE_APP_URL` | Your Vercel production URL (e.g., `https://your-app.vercel.app`) |

**Deploy:**
```bash
cd frontend
vercel --prod
```

### 3. Supabase Auth Configuration

For Magic Links to work in production, you must whitelist your Vercel URL:
1. Go to **Supabase Dashboard > Authentication > URL Configuration**.
2. Add your Vercel URL to **Redirect URLs** (e.g., `https://your-app.vercel.app/**`).
