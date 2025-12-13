import { useRef } from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline, Box, AppBar, Toolbar, Typography, Tabs, Tab, Badge, Button, CircularProgress } from '@mui/material';
import LogoutIcon from '@mui/icons-material/Logout';

import ChatPanel from './components/ChatPanel';
import ListingsPanel from './components/ListingsPanel';
import RulesPanel from './components/RulesPanel';
import Login from './pages/Login';

import { AuthProvider } from './contexts/AuthContext';
import { useChatController } from './hooks/useChatController';
import { theme } from './theme';

function AppContent() {
  const {
    user,
    authLoading,
    messages,
    rules,
    listings,
    shortlist,
    activeTab,
    chatLoading,
    listingsLoading,
    blacklistedIds,
    scoringProgress,
    searchSuggested,
    setActiveTab,
    sendMessage,
    searchListings,
    deleteRule,
    handleReject,
    handleShortlist,
    handleRemoveFromShortlist,
    handleNewConversation,
    handleSignOut
  } = useChatController();

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

  const shortlistListingIds = new Set(shortlist.map(s => s.listing_id));

  // Filter shortlist for display (ensure valid data)
  const shortlistWithScores = shortlist
    .map(s => s.listing_data as any) // Type assertion for now, relying on hook logic
    .filter(l => l !== null);

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
            Flat Finder
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
            onSearch={searchListings}
            loading={chatLoading || listingsLoading}
            searchSuggested={searchSuggested}
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
                  <Badge badgeContent={shortlistWithScores.length} color="primary" max={99}>
                    <span style={{ paddingRight: shortlistWithScores.length > 0 ? 12 : 0 }}>Shortlist</span>
                  </Badge>
                }
              />
            </Tabs>

            {activeTab === 0 && (
              <ListingsPanel
                listings={listings}
                loading={listingsLoading}
                blacklist={Array.from(blacklistedIds)}
                shortlist={shortlistWithScores}
                onReject={handleReject}
                onShortlist={handleShortlist}
                onUndo={() => { }} // TODO: implement undo
                mode="matches"
                scoringProgress={scoringProgress}
              />
            )}

            {activeTab === 1 && (
              <ListingsPanel
                listings={shortlistWithScores}
                loading={false}
                blacklist={[]}
                shortlist={shortlistWithScores}
                onReject={handleRemoveFromShortlist}
                onShortlist={() => { }}
                onUndo={() => { }}
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
