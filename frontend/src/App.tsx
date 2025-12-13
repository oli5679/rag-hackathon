import { useState, useEffect, useRef } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box, AppBar, Toolbar, Typography, Tabs, Tab, Badge, Button, CircularProgress } from '@mui/material';
import LogoutIcon from '@mui/icons-material/Logout';
import ChatPanel from './components/ChatPanel';
import ListingsPanel, { ListingWithScore } from './components/ListingsPanel';
import RulesPanel from './components/RulesPanel';
import { AuthProvider, useAuth } from './auth/AuthContext';
import { useConversation } from './hooks/useConversation';
import { useSavedListings } from './hooks/useSavedListings';
import { useRules } from './hooks/useRules';
import Login from './pages/Login';
import type { Listing, Rule, ChatMessage } from './types';

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
  ] as typeof createTheme.arguments[0] extends { shadows: infer S } ? S : never,
});

const API_BASE = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

// Convert weekly rent to monthly (52 weeks / 12 months)
const weeklyToMonthly = (weeklyPrice: number): number => Math.round(weeklyPrice * 52 / 12);

// Parse rent and normalize to monthly
const normalizeRent = (listing: Listing): ListingWithScore => {
  const summary = (listing.summary || '').toLowerCase();
  const isWeekly = summary.includes('pw') || summary.includes('per week') || summary.includes('/week');
  const price = listing.price || 0;
  return {
    ...listing,
    price: isWeekly ? weeklyToMonthly(price) : price,
    priceLabel: isWeekly ? `£${price}pw (£${weeklyToMonthly(price)}/mo)` : `£${price}/month`
  };
};

interface ChatResponse {
  assistantMessage: string;
  hardRules?: Rule[];
}

interface MatchResponse {
  matches?: Array<{
    listing: Listing;
    score: number;
    reasoning: string;
  }>;
}

function AppContent() {
  const { user, loading: authLoading, signOut } = useAuth();
  const {
    conversation,
    messages,
    createConversation,
    addMessages,
    clearConversation
  } = useConversation();
  const {
    shortlist,
    addToList,
    removeFromList,
    isShortlisted,
    blacklistedIds
  } = useSavedListings();
  const { rules, saveRules } = useRules(conversation?.id);

  const [listings, setListings] = useState<ListingWithScore[]>([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [listingsLoading, setListingsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState(0);

  // AbortController refs to cancel in-flight requests
  const chatAbortRef = useRef<AbortController | null>(null);
  const matchAbortRef = useRef<AbortController | null>(null);

  // Create a conversation on first load if user is authenticated
  useEffect(() => {
    if (user && !conversation) {
      createConversation();
    }
  }, [user, conversation, createConversation]);

  // Headers for API calls
  const getHeaders = (): HeadersInit => ({ 'Content-Type': 'application/json' });

  const sendMessage = async (text: string) => {
    if (!conversation) {
      console.error('No conversation available');
      return;
    }

    // Cancel any in-flight requests
    if (chatAbortRef.current) chatAbortRef.current.abort();
    if (matchAbortRef.current) matchAbortRef.current.abort();

    // Create new AbortControllers
    chatAbortRef.current = new AbortController();
    matchAbortRef.current = new AbortController();

    // Build conversation history for API
    const conversationHistory: ChatMessage[] = [
      ...messages.map(m => ({ role: m.role, content: m.content })),
      { role: 'user' as const, content: text }
    ];

    setChatLoading(true);

    try {
      // First, get chat response
      const chatRes = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
          message: text,
          conversation_history: conversationHistory.slice(0, -1) // Exclude the new message, backend adds it
        }),
        signal: chatAbortRef.current.signal
      });
      const chatData: ChatResponse = await chatRes.json();

      // Save both messages to Supabase
      await addMessages([
        { role: 'user', content: text },
        { role: 'assistant', content: chatData.assistantMessage }
      ]);

      // Save rules to Supabase
      if (chatData.hardRules) {
        await saveRules(chatData.hardRules);
      }

      setChatLoading(false);

      // Then, get reranked listings with scores
      setListingsLoading(true);
      const fullConversation: ChatMessage[] = [...conversationHistory, { role: 'assistant', content: chatData.assistantMessage }];
      const matchRes = await fetch(`${API_BASE}/api/find-matches`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ conversation: fullConversation }),
        signal: matchAbortRef.current.signal
      });
      const matchData: MatchResponse = await matchRes.json();

      // Process listings with scores and normalize rent
      const rankedListings = (matchData.matches || []).map(m => ({
        ...normalizeRent(m.listing),
        score: m.score,
        reasoning: m.reasoning
      }));
      setListings(rankedListings);
    } catch (err) {
      if (err instanceof Error && err.name !== 'AbortError') {
        console.error('Error:', err);
        await addMessages([
          { role: 'user', content: text },
          { role: 'assistant', content: 'Sorry, something went wrong.' }
        ]);
      }
    } finally {
      setChatLoading(false);
      setListingsLoading(false);
    }
  };

  const deleteRule = async (field: string) => {
    // Cancel any in-flight match request
    if (matchAbortRef.current) matchAbortRef.current.abort();
    matchAbortRef.current = new AbortController();

    const newRules = rules.filter(r => r.field !== field);

    try {
      // Save updated rules to Supabase
      await saveRules(newRules);

      // Re-fetch with reranking
      if (messages.length > 0) {
        setListingsLoading(true);
        const conversationHistory: ChatMessage[] = messages.map(m => ({ role: m.role, content: m.content }));
        const matchRes = await fetch(`${API_BASE}/api/find-matches`, {
          method: 'POST',
          headers: getHeaders(),
          body: JSON.stringify({ conversation: conversationHistory }),
          signal: matchAbortRef.current.signal
        });
        const matchData: MatchResponse = await matchRes.json();
        const rankedListings = (matchData.matches || []).map(m => ({
          ...normalizeRent(m.listing),
          score: m.score,
          reasoning: m.reasoning
        }));
        setListings(rankedListings);
        setListingsLoading(false);
      }
    } catch (err) {
      if (err instanceof Error && err.name !== 'AbortError') {
        console.error('Failed to update rules:', err);
      }
      setListingsLoading(false);
    }
  };

  const handleReject = async (listingId: string) => {
    await addToList(listingId, 'blacklist');
    // Remove from shortlist if present
    if (isShortlisted(listingId)) {
      await removeFromList(listingId);
      await addToList(listingId, 'blacklist');
    }
  };

  const handleShortlist = async (listing: ListingWithScore) => {
    if (!isShortlisted(listing.id)) {
      await addToList(listing.id, 'shortlist', listing as Listing);
    }
  };

  const handleRemoveFromShortlist = async (listingId: string) => {
    await removeFromList(listingId);
  };

  const handleNewConversation = async () => {
    clearConversation();
    setListings([]);
    await createConversation();
  };

  const handleSignOut = async () => {
    await signOut();
    clearConversation();
    setListings([]);
  };

  // Show loading spinner while checking auth
  if (authLoading) {
    return (
      <Box sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      }}>
        <CircularProgress sx={{ color: 'white' }} />
      </Box>
    );
  }

  // Show login page if not authenticated
  if (!user) {
    return <Login />;
  }

  // Get blacklisted IDs for filtering
  const blacklistedIdSet = blacklistedIds();

  // Convert shortlist from Supabase format to listing format for display
  const shortlistListings: ListingWithScore[] = shortlist
    .map(s => s.listing_data as ListingWithScore | null)
    .filter((l): l is ListingWithScore => l !== null);

  return (
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
          <Typography variant="h6" sx={{ fontWeight: 700, letterSpacing: '-0.02em', flexGrow: 1 }}>
            SpareRoom Assistant
          </Typography>
          <Typography variant="body2" sx={{ mr: 2, opacity: 0.9 }}>
            {user.email}
          </Typography>
          <Button
            color="inherit"
            size="small"
            onClick={handleNewConversation}
            sx={{ mr: 1 }}
          >
            New Chat
          </Button>
          <Button
            color="inherit"
            size="small"
            startIcon={<LogoutIcon />}
            onClick={handleSignOut}
          >
            Logout
          </Button>
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
          <ChatPanel
            messages={messages.map(m => ({ role: m.role, content: m.content }))}
            onSend={sendMessage}
            loading={chatLoading}
          />
        </Box>
        <Box sx={{ width: '40%', height: '100%', overflow: 'auto' }}>
          <RulesPanel rules={rules} onDelete={deleteRule} loading={chatLoading} />
          <Box sx={{ mt: 2 }}>
            <Tabs
              value={activeTab}
              onChange={(_e, v: number) => setActiveTab(v)}
              sx={{ mb: 2 }}
            >
              <Tab label="Top Matches" />
              <Tab
                label={
                  <Badge badgeContent={shortlistListings.length} color="primary" max={99}>
                    <span style={{ paddingRight: shortlistListings.length > 0 ? 12 : 0 }}>Shortlist</span>
                  </Badge>
                }
              />
            </Tabs>

            {activeTab === 0 && (
              <ListingsPanel
                listings={listings}
                loading={listingsLoading}
                blacklist={Array.from(blacklistedIdSet)}
                shortlist={shortlistListings}
                onReject={handleReject}
                onShortlist={handleShortlist}
                onUndo={() => {}} // TODO: implement undo with Supabase
                mode="matches"
              />
            )}

            {activeTab === 1 && (
              <ListingsPanel
                listings={shortlistListings}
                loading={false}
                blacklist={[]}
                shortlist={shortlistListings}
                onReject={handleRemoveFromShortlist}
                onShortlist={() => {}}
                onUndo={() => {}}
                mode="shortlist"
              />
            )}
          </Box>
        </Box>
      </Box>
    </Box>
  );
}

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
