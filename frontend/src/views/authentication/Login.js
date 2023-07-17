import { Helmet } from 'react-helmet-async';
import { Box, Card, CardContent, Container, Typography } from '@mui/material';
import { LoginAmplify } from '../../components/authentication/login';
import Logo from '../../components/Logo';
import useAuth from '../../hooks/useAuth';

const platformIcons = {
  Amplify: '/static/icons/amplify.svg'
};

const Login = () => {
  const { platform } = useAuth();

  return (
    <>
      <Helmet>
        <title>Login | data.all</title>
      </Helmet>
      <Box
        sx={{
          backgroundColor: 'neutral.900',
          display: 'flex',
          flexDirection: 'column',
          minHeight: '100vh'
        }}
      >
        <Container maxWidth="sm" sx={{ py: '80px' }}>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'center',
              mb: 8,
              ml: 25
            }}
          >
            <Logo
              sx={{
                height: 40,
                width: 40,
                justifyContent: 'center',
                display: 'flex'
              }}
            />
          </Box>
          <Card>
            <CardContent
              sx={{
                display: 'flex',
                flexDirection: 'column',
                p: 4
              }}
            >
              <Box
                sx={{
                  alignItems: 'center',
                  display: 'flex',
                  justifyContent: 'space-between',
                  mb: 3
                }}
              >
                <div>
                  <Typography color="textPrimary" gutterBottom variant="h4">
                    Login
                  </Typography>
                </div>
                <Box
                  sx={{
                    height: 32,
                    '& > img': {
                      maxHeight: '100%',
                      width: 'auto'
                    }
                  }}
                >
                  <img alt="Auth platform" src={platformIcons[platform]} />
                </Box>
              </Box>
              <Box
                sx={{
                  flexGrow: 1,
                  mt: 3
                }}
              >
                {platform === 'Amplify' && <LoginAmplify />}
              </Box>
            </CardContent>
          </Card>
        </Container>
      </Box>
    </>
  );
};

export default Login;
