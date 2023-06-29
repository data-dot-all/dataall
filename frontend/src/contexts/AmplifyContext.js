import { createContext, useEffect, useReducer } from 'react';
import PropTypes from 'prop-types';
import { Amplify, Auth } from 'aws-amplify';
import { SET_ERROR } from '../store/errorReducer';

Amplify.configure({
  Auth: {
    mandatorySignIn: true,
    region: process.env.REACT_APP_COGNITO_REGION,
    userPoolId: process.env.REACT_APP_COGNITO_USER_POOL_ID,
    userPoolWebClientId: process.env.REACT_APP_COGNITO_APP_CLIENT_ID,
    redirectSignIn: process.env.REACT_APP_COGNITO_REDIRECT_SIGNIN,
    redirectSignOut: process.env.REACT_APP_COGNITO_REDIRECT_SIGNOUT
  }
});

Auth.configure({
  oauth: {
    domain: process.env.REACT_APP_COGNITO_DOMAIN,
    redirectSignIn: process.env.REACT_APP_COGNITO_REDIRECT_SIGNIN,
    redirectSignOut: process.env.REACT_APP_COGNITO_REDIRECT_SIGNOUT,
    responseType: 'code'
  }
});

const initialState = {
  isAuthenticated: false,
  isInitialized: false,
  user: null
};

const handlers = {
  INITIALIZE: (state, action) => {
    const { isAuthenticated, user } = action.payload;

    return {
      ...state,
      isAuthenticated,
      isInitialized: true,
      user
    };
  },
  LOGIN: (state, action) => {
    const { user } = action.payload;

    return {
      ...state,
      isAuthenticated: true,
      user
    };
  },
  LOGOUT: (state) => ({
    ...state,
    isAuthenticated: false,
    user: null
  })
};

const reducer = (state, action) =>
  handlers[action.type] ? handlers[action.type](state, action) : state;

const AuthContext = createContext({
  ...initialState,
  platform: 'Amplify',
  login: () => Promise.resolve(),
  logout: () => Promise.resolve()
});

export const AuthProvider = (props) => {
  const { children } = props;
  const [state, dispatch] = useReducer(reducer, initialState);

  useEffect(() => {
    const initialize = async () => {
      try {
        const user = await Auth.currentAuthenticatedUser();
        dispatch({
          type: 'INITIALIZE',
          payload: {
            isAuthenticated: true,
            user: {
              id: user.attributes.email,
              email: user.attributes.email,
              name: user.attributes.email
            }
          }
        });
      } catch (error) {
        dispatch({
          type: 'INITIALIZE',
          payload: {
            isAuthenticated: false,
            user: null
          }
        });
      }
    };

    initialize().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
  }, []);

  const login = async () => {
    Auth.federatedSignIn()
      .then((user) => {
        dispatch({
          type: 'LOGIN',
          payload: {
            user: {
              id: user.attributes.email,
              email: user.attributes.email,
              name: user.attributes.email
            }
          }
        });
      })
      .catch((e) => {
        console.log('Failed to authenticate user', e);
      });
  };

  const logout = async () => {
    await Auth.signOut();
    dispatch({
      type: 'LOGOUT'
    });
  };

  return (
    <AuthContext.Provider
      value={{
        ...state,
        dispatch,
        platform: 'Amplify',
        login,
        logout
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

AuthProvider.propTypes = {
  children: PropTypes.node.isRequired
};

export default AuthContext;
