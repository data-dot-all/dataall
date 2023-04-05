import { useContext } from 'react';
import { CognitoAuthContext, LocalAuthContext } from '../contexts';

export const useAuth = () =>
  useContext(
    !process.env.REACT_APP_COGNITO_USER_POOL_ID
      ? LocalAuthContext
      : CognitoAuthContext
  );
