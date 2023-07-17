import { Button } from '@mui/material';
import useAuth from '../../../hooks/useAuth';

const LoginAmplify = () => {
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

export default LoginAmplify;
