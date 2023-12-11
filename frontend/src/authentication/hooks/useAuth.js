import { GenericAuthContext } from '../contexts/GenericAuthContext';
import { useContext } from 'react';
import { LocalAuthContext } from '../contexts/LocalAuthContext';

export const useAuth = () => {
  return useContext(
    !process.env.REACT_APP_COGNITO_USER_POOL_ID &&
      !process.env.REACT_APP_CUSTOM_AUTH
      ? LocalAuthContext
      : GenericAuthContext
  );
};
