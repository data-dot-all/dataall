import { useContext } from 'react';
import { CognitoAuthContext } from '../contexts/CognitoAuthContext';
import { LocalAuthContext } from '../contexts/LocalAuthContext';

export const useAuth = () =>
  useContext(
    !process.env.REACT_APP_COGNITO_USER_POOL_ID
      ? LocalAuthContext
      : CognitoAuthContext
  );
