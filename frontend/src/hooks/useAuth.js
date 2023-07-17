import { useContext } from 'react';
import LocalContext from '../contexts/LocalContext';
import AuthContext from '../contexts/AmplifyContext';

const useAuth = () =>
  useContext(
    !process.env.REACT_APP_COGNITO_USER_POOL_ID ? LocalContext : AuthContext
  );

export default useAuth;
