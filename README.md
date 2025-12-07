# SpareRoom Chat Assistant

A chat interface for finding rooms to rent in London. Uses OpenAI for conversational responses and filters listings based on extracted preferences.

## Setup

### Prerequisites
- Python 3.12+
- Node.js 18+
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- OpenAI API key

### Backend Setup

```bash
cd backend

# Create .env file with your OpenAI API key
cp .env.example .env
# Edit .env and add your API key: OPENAI_API_KEY=sk-...

# Install dependencies and run
uv sync
uv run uvicorn main:app --reload --port 8000
```

Backend runs at http://localhost:8000

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend runs at http://localhost:5173

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Send message, get AI response + rules + listings |
| `/api/listings/top` | GET | Get top N listings (query: `count`) |
| `/api/rules` | GET | Get current filters |
| `/api/rules` | PUT | Update filters |
| `/api/ideal-listing` | POST | Generate ideal listing from conversation history |
| `/api/conversation-summary` | POST | Summarize conversation preferences |
| `/api/score-listing` | POST | Score a listing against user preferences (1-100) |
| `/health` | GET | Health check |

## Usage

1. Start both backend and frontend
2. Open http://localhost:5173 in your browser
3. Chat with the assistant about your room preferences:
   - "Looking for a room under £700"
   - "I want something in Camden"
   - "Need a pet-friendly place"

The assistant will extract filters from your messages and show matching listings.

## Project Structure

```
├── backend/
│   ├── main.py           # FastAPI app
│   ├── data.py           # Sample listings
│   ├── clients/          # OpenAI & Redis clients (for future use)
│   └── .env.example      # Environment template
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── components/
│   │       ├── ChatPanel.jsx
│   │       ├── ListingsPanel.jsx
│   │       └── RulesPanel.jsx
│   └── package.json
└── specs/                # Design specs
```
