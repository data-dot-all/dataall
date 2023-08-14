import { Auth } from 'aws-amplify';
import { useEffect, useState } from 'react';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useAuth } from './useAuth';

export const useToken = () => {
  const dispatch = useDispatch();
  const auth = useAuth();
  const [token, setToken] = useState(null);
  const fetchAuthToken = async () => {
    if (
      !process.env.REACT_APP_COGNITO_USER_POOL_ID &&
      process.env.REACT_APP_GRAPHQL_API.includes('localhost')
    ) {
      setToken('localToken');
    } else {
      try {
        const session = await Auth.currentSession();
        const t = await session.getIdToken().getJwtToken();
        setToken(t);
      } catch (error) {
        auth.dispatch({
          type: 'LOGOUT'
        });
      }
    }
  };

  useEffect(() => {
    if (!token) {
      fetchAuthToken().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  });
  return token;
};
