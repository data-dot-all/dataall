import { CognitoAuthProvider } from 'authentication/contexts/CognitoAuthContext';
import { LocalAuthProvider } from 'authentication/contexts/LocalAuthContext';
import { OidcAuthProvider } from 'authentication/contexts/OidcAuthContext';

export const AuthProvider = !process.env.REACT_APP_CUSTOM_AUTH
  ? !process.env.REACT_APP_COGNITO_USER_POOL_ID
    ? LocalAuthProvider
    : CognitoAuthProvider
  : OidcAuthProvider;
