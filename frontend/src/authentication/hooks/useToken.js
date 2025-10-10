import { Auth } from 'aws-amplify';
import { useEffect, useState } from 'react';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useAuth } from 'authentication';

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
        if (process.env.REACT_APP_CUSTOM_AUTH) {
          try {
            if (!auth.user) {
              await auth.signinSilent();
            }
            const t = auth.user.access_token;
            setToken(t);
          } catch (error) {
            if (!auth) throw Error('User Token Not Found !');
          }
        } else {
          const session = await Auth.currentSession();
          const t = await session.getAccessToken().getJwtToken();
          setToken(t);
        }
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
