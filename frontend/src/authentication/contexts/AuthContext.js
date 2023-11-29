import { CognitoAuthProvider } from './CognitoAuthContext';
import { LocalAuthProvider } from './LocalAuthContext';
import { OidcAuthProvider } from './OidcAuthContext';

export const AuthProvider = !process.env.REACT_APP_CUSTOM_AUTH
  ? !process.env.REACT_APP_COGNITO_USER_POOL_ID
    ? LocalAuthProvider
    : CognitoAuthProvider
  : OidcAuthProvider;
