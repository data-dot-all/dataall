import { Auth, Amplify } from 'aws-amplify';
import PropTypes from 'prop-types';
import { createContext, useEffect, useReducer } from 'react';
import { SET_ERROR } from 'globalErrors';

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
  user: null,
  reAuthStatus: false
};

const handlers = {
  INITIALIZE: (state, action) => {
    const { isAuthenticated, user } = action.payload;

    return {
      ...state,
      isAuthenticated,
      isInitialized: true,
      user,
      reAuthStatus: false
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
  }),
  REAUTH: (state, action) => {
    const { reAuthStatus } = action.payload;

    return {
      ...state,
      reAuthStatus
    };
  }
};

const reducer = (state, action) =>
  handlers[action.type] ? handlers[action.type](state, action) : state;

export const CognitoAuthContext = createContext({
  ...initialState,
  platform: 'Amplify',
  login: () => Promise.resolve(),
  logout: () => Promise.resolve(),
  reauth: () => Promise.resolve()
});

export const CognitoAuthProvider = (props) => {
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
        console.error('Failed to authenticate user', e);
      });
  };

  const reauth = async (status) => {
    dispatch({
      type: 'REAUTH',
      payload: {
        reAuthStatus: status
      }
    }).catch((e) => {
      console.error('Failed to authenticate user', e);
    });
  };

  const logout = async () => {
    await Auth.signOut();
    dispatch({
      type: 'LOGOUT'
    });
  };

  return (
    <CognitoAuthContext.Provider
      value={{
        ...state,
        dispatch,
        platform: 'Amplify',
        login,
        logout,
        reauth
      }}
    >
      {children}
    </CognitoAuthContext.Provider>
  );
};

CognitoAuthProvider.propTypes = {
  children: PropTypes.node.isRequired
};
