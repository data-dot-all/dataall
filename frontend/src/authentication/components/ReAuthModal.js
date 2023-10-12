import { Box, CardContent, Dialog, Typography, Button } from '@mui/material';
import { useAuth } from 'authentication';
// import { SET_ERROR, useDispatch } from 'globalErrors';

export const ReAuthModal = () => {
  const { reAuthStatus, reauth, auth } = useAuth();
  const continueSession = async () => {
    auth
      .dispatch({
        type: 'REAUTH',
        payload: {
          reAuthStatus: false
        }
      })
      .catch((e) => {
        console.error('Failed to reauth user', e);
      });
  };

  return (
    <Dialog maxWidth="md" fullWidth open={reAuthStatus}>
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
