import { useState, useRef, useEffect, ChangeEvent, KeyboardEvent } from 'react';
import { Box, Paper, TextField, IconButton, Typography, CircularProgress } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import type { ChatMessage } from '../types';

interface ChatPanelProps {
  messages: ChatMessage[];
  onSend: (message: string) => void;
  loading: boolean;
}

export default function ChatPanel({ messages, onSend, loading }: ChatPanelProps) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (input.trim() && !loading) {
      onSend(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Paper
      elevation={0}
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        p: 3,
        border: '1px solid',
        borderColor: 'divider',
        borderRadius: 2,
      }}
    >
      <Typography variant="h6" sx={{ mb: 3, color: 'text.primary' }}>
        Chat
      </Typography>

      <Box sx={{ flex: 1, overflow: 'auto', mb: 3 }}>
        {messages.length === 0 && !loading && (
          <Box sx={{
            textAlign: 'center',
            mt: 8,
            p: 3,
            borderRadius: 2,
            bgcolor: 'background.default',
            border: '1px solid',
            borderColor: 'divider'
          }}>
            <Typography variant="body1" color="text.primary" sx={{ fontWeight: 500 }}>
              Tell us anything we should know about what you're looking for in your flat, and we'll search SpareRoom for the closest matches
            </Typography>
          </Box>
        )}

        {messages.map((msg, idx) => (
          <Box
            key={idx}
            sx={{
              display: 'flex',
              justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
              mb: 2
            }}
          >
            <Paper
              elevation={0}
              sx={{
                p: 2,
                maxWidth: '75%',
                bgcolor: msg.role === 'user'
                  ? 'primary.main'
                  : 'background.default',
                color: msg.role === 'user' ? 'white' : 'text.primary',
                borderRadius: 2,
                border: msg.role === 'user' ? 'none' : '1px solid',
                borderColor: 'divider',
              }}
            >
              <Typography variant="body2" sx={{ lineHeight: 1.6 }}>
                {msg.content}
              </Typography>
            </Paper>
          </Box>
        ))}

        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 2 }}>
            <Paper
              elevation={0}
              sx={{
                p: 2,
                bgcolor: 'background.default',
                borderRadius: 2,
                border: '1px solid',
                borderColor: 'divider',
              }}
            >
              <CircularProgress size={20} />
            </Paper>
          </Box>
        )}

        <div ref={messagesEndRef} />
      </Box>

      <Box sx={{ display: 'flex', gap: 1.5 }}>
        <TextField
          fullWidth
          size="small"
          placeholder="Type your message..."
          value={input}
          onChange={(e: ChangeEvent<HTMLInputElement>) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
          sx={{
            '& .MuiOutlinedInput-root': {
              borderRadius: 2,
            }
          }}
        />
        <IconButton
          color="primary"
          onClick={handleSend}
          disabled={loading || !input.trim()}
          sx={{
            bgcolor: 'primary.main',
            color: 'white',
            '&:hover': {
              bgcolor: 'primary.dark',
            },
            '&.Mui-disabled': {
              bgcolor: 'action.disabledBackground',
            }
          }}
        >
          <SendIcon />
        </IconButton>
      </Box>
    </Paper>
  );
}
