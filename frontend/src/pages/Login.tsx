import { useState, FormEvent } from 'react';
import { Box, Button, TextField, Typography, Paper, Alert, CircularProgress } from '@mui/material';
import { useAuth } from '../contexts/AuthContext';

export default function Login() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const { signInWithMagicLink } = useAuth();

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    const { error } = await signInWithMagicLink(email);

    if (error) {
      setMessage(`Error: ${error.message}`);
    } else {
      setMessage('Check your email for a magic link!');
    }
    setLoading(false);
  };

  return (
    <Box sx={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    }}>
      <Paper sx={{ p: 4, maxWidth: 400, width: '100%', mx: 2 }}>
        <Typography component="h1" variant="h4" sx={{ mb: 4, fontWeight: 700 }}>
          Flat Finder
        </Typography>

        <Typography component="h2" variant="h6" sx={{ mb: 4, color: 'text.secondary' }}>
          Sign in to your account
        </Typography>

        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            sx={{ mb: 2 }}
          />
          <Button
            fullWidth
            variant="contained"
            type="submit"
            disabled={loading}
            sx={{ mb: 2, py: 1.5 }}
          >
            {loading ? <CircularProgress size={24} /> : 'Send Magic Link'}
          </Button>
        </form>

        {message && (
          <Typography
            variant="body2"
            align="center"
            color={message.includes('Error') ? 'error' : 'success.main'}
          >
            {message}
          </Typography>
        )}
      </Paper>
    </Box>
  );
}
