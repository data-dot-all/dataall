import { CognitoAuthProvider } from './CognitoAuthContext';
import { LocalAuthProvider } from './LocalAuthContext';

export const AuthProvider = !process.env.REACT_APP_COGNITO_USER_POOL_ID
  ? LocalAuthProvider
  : CognitoAuthProvider;
