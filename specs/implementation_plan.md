# SpareRoom Chat Assistant - Implementation Plan

## Overview
Chat interface to discuss room listings with AI assistant. Two-column layout: chat on left, listings + rules on right.

## Tech Stack
- **Frontend**: React (Vite) + Material UI
- **Backend**: FastAPI (hardcoded for MVP)
- **Future**: OpenAI (chat/reranking), Redis (RAG/rules)

---

## Phase 1: MVP Implementation

### Backend Endpoints (Hardcoded)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/chat` | POST | Send message, get response + rules + listings |
| `/api/listings/top` | GET | Get top N listings (query param: count) |
| `/api/rules` | GET | Get current extracted rules |
| `/api/rules` | PUT | Update rules, get new listings |

### Hardcoded Data
- 5-6 sample London room listings with: id, title, price, location, imageUrl, url, summary
- Sample rules: max_budget, location, pets_allowed, etc.

---

### Frontend Components

```
App.jsx
├── AppBar (title: "SpareRoom Assistant")
├── MainLayout (Grid - two columns)
│   ├── ChatPanel (left, 60% width)
│   │   ├── MessageList
│   │   │   └── MessageBubble (Paper/Card)
│   │   └── InputArea (TextField + Send button)
│   └── SidePanel (right, 40% width)
│       ├── ListingsPanel
│       │   └── ListingCard (x3)
│       └── RulesPanel
│           └── RuleChip (editable)
```

### UI Details
- **Chat**: Messages right-aligned (user) / left-aligned (assistant), auto-scroll to bottom
- **Listings**: 3 cards with image, title, price, location, summary, link
- **Rules**: Material UI Chips (e.g., "Max £700", "Zone 1"), clickable to edit

---

## File Structure

```
/backend
  main.py              # FastAPI app with all endpoints
  requirements.txt     # fastapi, uvicorn

/frontend
  package.json
  /src
    main.jsx
    App.jsx
    /components
      ChatPanel.jsx
      MessageBubble.jsx
      ListingsPanel.jsx
      ListingCard.jsx
      RulesPanel.jsx
      RuleChip.jsx
```

---

## API Contract

### POST /api/chat
```json
// Request
{ "message": "Looking for a room around £700 in London" }

// Response
{
  "assistantMessage": "Here are some options...",
  "hardRules": [
    { "field": "max_budget", "value": 700, "unit": "GBP" },
    { "field": "location", "value": "Central London" }
  ],
  "topListings": [
    {
      "id": "1",
      "title": "Room in Zone 1 Chelsea",
      "price": 680,
      "location": "SW3",
      "imageUrl": "https://via.placeholder.com/300x200",
      "url": "#",
      "summary": "Spacious ensuite room..."
    }
  ]
}
```

### GET /api/listings/top?count=3
```json
// Response
[
  { "id": "1", "title": "...", "price": 680, ... }
]
```

### GET /api/rules
```json
// Response
{
  "hardRules": [
    { "field": "max_budget", "value": 700 },
    { "field": "location", "value": "Zone 1" }
  ]
}
```

### PUT /api/rules
```json
// Request
{ "hardRules": [{ "field": "max_budget", "value": 800 }] }

// Response
{ "hardRules": [...], "topListings": [...] }
```

---

## Implementation Steps

1. [ ] Create backend folder with FastAPI app
2. [ ] Add hardcoded listings data
3. [ ] Implement all 4 endpoints
4. [ ] Test backend with curl
5. [ ] Create React app with Vite + MUI
6. [ ] Build ChatPanel component
7. [ ] Build ListingsPanel + ListingCard
8. [ ] Build RulesPanel + RuleChip
9. [ ] Wire up API calls
10. [ ] Test full flow in browser

---

## Testing Commands

```bash
# Start backend
cd backend && uvicorn main:app --reload --port 8000

# Test chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Looking for a room under £700"}'

# Test listings
curl http://localhost:8000/api/listings/top?count=3

# Test get rules
curl http://localhost:8000/api/rules

# Test update rules
curl -X PUT http://localhost:8000/api/rules \
  -H "Content-Type: application/json" \
  -d '{"hardRules": [{"field": "max_budget", "value": 800}]}'
```
