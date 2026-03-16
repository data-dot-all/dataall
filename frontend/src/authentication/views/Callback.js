import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, CircularProgress, Typography } from '@mui/material';

const Callback = () => {
  const navigate = useNavigate();
  const [error, setError] = useState(null);

  useEffect(() => {
    const exchangeCode = async () => {
      try {
        const params = new URLSearchParams(window.location.search);
        const code = params.get('code');
        const state = params.get('state');
        const errorParam = params.get('error');

        if (errorParam) {
          throw new Error(params.get('error_description') || errorParam);
        }

        if (!code) {
          throw new Error('No authorization code received');
        }

        // Verify state matches
        const savedState = sessionStorage.getItem('pkce_state');
        if (state !== savedState) {
          throw new Error('State mismatch - possible CSRF attack');
        }

        // Get code verifier
        const codeVerifier = sessionStorage.getItem('pkce_verifier');
        if (!codeVerifier) {
          throw new Error('No code verifier found');
        }

        // Exchange code for tokens via backend
        // Add AbortController for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

        try {
          const response = await fetch('/auth/token-exchange', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
              code,
              code_verifier: codeVerifier
            }),
            signal: controller.signal
          });
          clearTimeout(timeoutId);

          if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || 'Token exchange failed');
          }
        } catch (fetchErr) {
          clearTimeout(timeoutId);
          if (fetchErr.name === 'AbortError') {
            throw new Error('Request timed out. Please try again.');
          }
          throw fetchErr;
        }

        // Clear PKCE values
        sessionStorage.removeItem('pkce_verifier');
        sessionStorage.removeItem('pkce_state');

        // Fetch user info to verify cookies are set correctly
        const userInfoResponse = await fetch('/auth/userinfo', {
          credentials: 'include'
        });

        if (!userInfoResponse.ok) {
          throw new Error('Failed to fetch user info after login');
        }

        // Full page reload to re-initialize auth context with new cookies
        window.location.href = '/console/environments';
      } catch (err) {
        console.error('Callback error:', err);
        setError(err.message);
      }
    };

    exchangeCode();
  }, [navigate]);

  if (error) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          mt: 8
        }}
      >
        <Typography color="error" variant="h6">
          Authentication Error
        </Typography>
        <Typography color="textSecondary">{error}</Typography>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        mt: 8
      }}
    >
      <CircularProgress />
      <Typography sx={{ mt: 2 }}>Completing sign in...</Typography>
    </Box>
  );
};

export default Callback;
