import { useState, useEffect, useRef } from 'react'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import { CssBaseline, Box, AppBar, Toolbar, Typography } from '@mui/material'
import ChatPanel from './components/ChatPanel'
import ListingsPanel from './components/ListingsPanel'
import RulesPanel from './components/RulesPanel'

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#6366f1',
      light: '#818cf8',
      dark: '#4f46e5',
    },
    secondary: {
      main: '#8b5cf6',
      light: '#a78bfa',
      dark: '#7c3aed',
    },
    background: {
      default: '#f8fafc',
      paper: '#ffffff',
    },
    text: {
      primary: '#1e293b',
      secondary: '#64748b',
    },
  },
  typography: {
    fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    h6: {
      fontWeight: 600,
      fontSize: '1.125rem',
    },
    button: {
      textTransform: 'none',
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 12,
  },
  shadows: [
    'none',
    '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
    '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
    '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
    '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
    ...Array(20).fill('0 25px 50px -12px rgb(0 0 0 / 0.25)'),
  ],
})

const API_BASE = 'http://localhost:8000'
const BLACKLIST_KEY = 'spareroom_blacklist'

// Convert weekly rent to monthly (52 weeks / 12 months)
const weeklyToMonthly = (weeklyPrice) => Math.round(weeklyPrice * 52 / 12)

// Parse rent and normalize to monthly
const normalizeRent = (listing) => {
  const summary = (listing.summary || '').toLowerCase()
  const isWeekly = summary.includes('pw') || summary.includes('per week') || summary.includes('/week')
  const price = listing.price || 0
  return {
    ...listing,
    price: isWeekly ? weeklyToMonthly(price) : price,
    priceLabel: isWeekly ? `£${price}pw (£${weeklyToMonthly(price)}/mo)` : `£${price}/month`
  }
}

function App() {
  const [messages, setMessages] = useState([])
  const [listings, setListings] = useState([])
  const [rules, setRules] = useState([])
  const [chatLoading, setChatLoading] = useState(false)
  const [listingsLoading, setListingsLoading] = useState(false)
  const [blacklist, setBlacklist] = useState(() => {
    const saved = localStorage.getItem(BLACKLIST_KEY)
    return saved ? JSON.parse(saved) : []
  })

  // AbortController refs to cancel in-flight requests
  const chatAbortRef = useRef(null)
  const matchAbortRef = useRef(null)

  // Reset backend state on page load
  useEffect(() => {
    fetch(`${API_BASE}/api/reset`, { method: 'POST' }).catch(() => {})
  }, [])

  // Persist blacklist to localStorage
  useEffect(() => {
    localStorage.setItem(BLACKLIST_KEY, JSON.stringify(blacklist))
  }, [blacklist])

  const sendMessage = async (text) => {
    // Cancel any in-flight requests
    if (chatAbortRef.current) chatAbortRef.current.abort()
    if (matchAbortRef.current) matchAbortRef.current.abort()

    // Create new AbortControllers
    chatAbortRef.current = new AbortController()
    matchAbortRef.current = new AbortController()

    const newMessages = [...messages, { role: 'user', content: text }]
    setMessages(newMessages)
    setChatLoading(true)

    try {
      // First, get chat response
      const chatRes = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
        signal: chatAbortRef.current.signal
      })
      const chatData = await chatRes.json()
      setMessages(prev => [...prev, { role: 'assistant', content: chatData.assistantMessage }])
      setRules(chatData.hardRules || [])
      setChatLoading(false)

      // Then, get reranked listings with scores (separate loading state)
      setListingsLoading(true)
      const conversation = [...newMessages, { role: 'assistant', content: chatData.assistantMessage }]
      const matchRes = await fetch(`${API_BASE}/api/find-matches`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ conversation }),
        signal: matchAbortRef.current.signal
      })
      const matchData = await matchRes.json()

      // Process listings with scores and normalize rent
      const rankedListings = (matchData.matches || []).map(m => ({
        ...normalizeRent(m.listing),
        score: m.score,
        reasoning: m.reasoning
      }))
      setListings(rankedListings)
    } catch (err) {
      // Ignore abort errors, show message for other errors
      if (err.name !== 'AbortError') {
        setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, something went wrong.' }])
      }
    } finally {
      setChatLoading(false)
      setListingsLoading(false)
    }
  }

  const deleteRule = async (field) => {
    // Cancel any in-flight match request
    if (matchAbortRef.current) matchAbortRef.current.abort()
    matchAbortRef.current = new AbortController()

    const newRules = rules.filter(r => r.field !== field)
    try {
      const res = await fetch(`${API_BASE}/api/rules`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hardRules: newRules })
      })
      const data = await res.json()
      setRules(data.hardRules || [])
      // Re-fetch with reranking
      if (messages.length > 0) {
        setListingsLoading(true)
        const matchRes = await fetch(`${API_BASE}/api/find-matches`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ conversation: messages }),
          signal: matchAbortRef.current.signal
        })
        const matchData = await matchRes.json()
        const rankedListings = (matchData.matches || []).map(m => ({
          ...normalizeRent(m.listing),
          score: m.score,
          reasoning: m.reasoning
        }))
        setListings(rankedListings)
        setListingsLoading(false)
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        console.error('Failed to update rules:', err)
      }
      setListingsLoading(false)
    }
  }

  const handleReject = (listingId) => {
    setBlacklist(prev => [...prev, listingId])
  }

  const handleUndo = () => {
    setBlacklist(prev => prev.slice(0, -1))
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
        <AppBar
          position="static"
          elevation={0}
          sx={{
            background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
            borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
          }}
        >
          <Toolbar sx={{ py: 1 }}>
            <Typography variant="h6" sx={{ fontWeight: 700, letterSpacing: '-0.02em' }}>
              SpareRoom Assistant
            </Typography>
          </Toolbar>
        </AppBar>

        <Box sx={{
          display: 'flex',
          flex: 1,
          gap: 3,
          p: 3,
          overflow: 'hidden',
          bgcolor: 'background.default'
        }}>
          <Box sx={{ width: '60%', height: '100%' }}>
            <ChatPanel messages={messages} onSend={sendMessage} loading={chatLoading} />
          </Box>
          <Box sx={{ width: '40%', height: '100%', overflow: 'auto' }}>
            <RulesPanel rules={rules} onDelete={deleteRule} loading={chatLoading} />
            <Box sx={{ mt: 2 }}>
              <ListingsPanel
                listings={listings}
                loading={listingsLoading}
                blacklist={blacklist}
                onReject={handleReject}
                onUndo={handleUndo}
              />
            </Box>
          </Box>
        </Box>
      </Box>
    </ThemeProvider>
  )
}

export default App
