import { useState } from 'react'
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

function App() {
  const [messages, setMessages] = useState([])
  const [listings, setListings] = useState([])
  const [rules, setRules] = useState([])
  const [loading, setLoading] = useState(false)

  const sendMessage = async (text) => {
    setMessages(prev => [...prev, { role: 'user', content: text }])
    setLoading(true)

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      })
      const data = await res.json()
      setMessages(prev => [...prev, { role: 'assistant', content: data.assistantMessage }])
      setListings(data.topListings || [])
      setRules(data.hardRules || [])
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, something went wrong.' }])
    } finally {
      setLoading(false)
    }
  }

  const deleteRule = async (field) => {
    const newRules = rules.filter(r => r.field !== field)
    try {
      const res = await fetch(`${API_BASE}/api/rules`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hardRules: newRules })
      })
      const data = await res.json()
      setRules(data.hardRules || [])
      setListings(data.topListings || [])
    } catch (err) {
      console.error('Failed to update rules:', err)
    }
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
            <ChatPanel messages={messages} onSend={sendMessage} loading={loading} />
          </Box>
          <Box sx={{ width: '40%', height: '100%', overflow: 'auto' }}>
            <RulesPanel rules={rules} onDelete={deleteRule} loading={loading} />
            <ListingsPanel listings={listings} loading={loading} />
          </Box>
        </Box>
      </Box>
    </ThemeProvider>
  )
}

export default App
