import { Button } from '@mui/material';
import { useAuth } from 'authentication/hooks';

export const LoginButton = () => {
  const { login } = useAuth();

  return (
    <Button
      color="primary"
      fullWidth
      size="large"
      type="submit"
      variant="contained"
      onClick={login}
    >
      Federated Authentication
    </Button>
  );
};
