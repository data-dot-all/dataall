import { useEffect, useState } from 'react';
import { Auth } from 'aws-amplify';
import { SET_ERROR } from '../store/errorReducer';
import { useDispatch } from '../store';

const useToken = () => {
  const dispatch = useDispatch();
  const [token, setToken] = useState(null);
  const fetchAuthToken = async () => {
    if (!process.env.REACT_APP_COGNITO_USER_POOL_ID && process.env.REACT_APP_GRAPHQL_API.includes('localhost')) {
      setToken('localToken');
    } else {
      const session = await Auth.currentSession();
      const t = await session.getIdToken().getJwtToken();
      setToken(t);
    }
  };

  useEffect(() => {
    if (!token) {
      fetchAuthToken().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  });
  return token;
};

export default useToken;
