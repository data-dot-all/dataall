import { Box, CardContent, Dialog, Typography, Button } from '@mui/material';
import { useAuth } from 'authentication';
import { useRequestContext } from 'reauthentication';
import { useLocation } from 'react-router-dom';
import React, { useEffect } from 'react';

const REAUTH_SESSION_KEY = 'reauth_session';

export const ReAuthModal = () => {
  const { user, reAuthStatus, requestInfo, reauth, dispatch } = useAuth();
  const { storeRequestInfo, clearRequestInfo } = useRequestContext();
  const location = useLocation();

  const continueSession = async () => {
    clearRequestInfo();
    dispatch({
      type: 'REAUTH',
      payload: {
        reAuthStatus: false,
        requestInfo: null
      }
    });
  };

  useEffect(() => {
    if (reAuthStatus && requestInfo) {
      const timestamp = new Date();
      const pathname = location.pathname;
      const username = user.name;
      const id_token = user.id_token;
      // Generate a unique session marker for httpOnly cookie auth
      const reauth_session = Date.now().toString();
      // Store the current session marker so we can detect when user returns
      sessionStorage.setItem(REAUTH_SESSION_KEY, reauth_session);
      storeRequestInfo({
        requestInfo,
        timestamp,
        pathname,
        username,
        id_token,
        reauth_session
      });
    }
  }, [reAuthStatus, requestInfo]);

  return (
    <Dialog maxWidth="md" fullWidth open={reAuthStatus} sx={{ zIndex: 99999 }}>
      <Box sx={{ p: 3 }}>
        <Typography
          align="center"
          color="textPrimary"
          gutterBottom
          variant="h4"
        >
          ReAuth Credentials
        </Typography>

        <Box sx={{ p: 3 }}>
          <CardContent>
            <Typography color="textSecondary" variant="subtitle2">
              In order to perform this action you are required to log in again
              to the data.all UI. Click the below button to be redirected to log
              back in before proceeding further or Click away to continue with
              other data.all operations.
              <Box
                display="flex"
                alignItems="center"
                justifyContent="center"
                sx={{ mt: 2 }}
              >
                <Button
                  color="primary"
                  size="large"
                  type="submit"
                  variant="contained"
                  onClick={reauth}
                >
                  Re-Authenticate
                </Button>
                <Button
                  color="primary"
                  size="large"
                  type="submit"
                  variant="contained"
                  onClick={() => continueSession()}
                >
                  Continue Session
                </Button>
              </Box>
            </Typography>
          </CardContent>
        </Box>
      </Box>
    </Dialog>
  );
};
