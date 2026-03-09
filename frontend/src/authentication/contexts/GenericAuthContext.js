import { createContext, useEffect, useReducer } from 'react';
import { SET_ERROR } from 'globalErrors';
import PropTypes from 'prop-types';
import { Auth } from 'aws-amplify';
import { generatePKCE, generateState } from '../../utils';

const CUSTOM_AUTH = process.env.REACT_APP_CUSTOM_AUTH;

const initialState = {
  isAuthenticated: false,
  isInitialized: false,
  user: null,
  reAuthStatus: false,
  requestInfo: null
};

const handlers = {
  INITIALIZE: (state, action) => {
    const { isAuthenticated, user, isInitialized } = action.payload;

    return {
      ...state,
      isAuthenticated,
      isInitialized,
      reAuthStatus: false,
      user
    };
  },
  LOGIN: (state, action) => {
    const { user } = action.payload;
    return {
      ...state,
      isAuthenticated: true,
      isInitialized: true,
      user
    };
  },
  LOGOUT: (state) => ({
    ...state,
    isAuthenticated: false,
    user: null
  }),
  REAUTH: (state, action) => {
    const { reAuthStatus, requestInfo } = action.payload;

    return {
      ...state,
      reAuthStatus,
      requestInfo
    };
  }
};

const reducer = (state, action) =>
  handlers[action.type] ? handlers[action.type](state, action) : state;

export const GenericAuthContext = createContext({
  ...initialState,
  platform: CUSTOM_AUTH ? CUSTOM_AUTH : 'Amplify',
  login: () => Promise.resolve(),
  logout: () => Promise.resolve(),
  reauth: () => Promise.resolve()
});

export const GenericAuthProvider = (props) => {
  const { children } = props;
  const [state, dispatch] = useReducer(reducer, initialState);

  useEffect(() => {
    const initialize = async () => {
      try {
        const user = await getAuthenticatedUser();
        dispatch({
          type: 'INITIALIZE',
          payload: {
            isAuthenticated: true,
            isInitialized: true,
            user: {
              id: user.email,
              email: user.email,
              name: user.email,
              id_token: user.id_token,
              short_id: user.short_id,
              access_token: user.access_token
            }
          }
        });
      } catch (error) {
        dispatch({
          type: 'INITIALIZE',
          payload: {
            isAuthenticated: false,
            isInitialized: true,
            user: null
          }
        });
      }
    };

    initialize().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
  }, []);

  const getAuthenticatedUser = async () => {
    if (CUSTOM_AUTH) {
      // Use relative URL - CloudFront proxies to API Gateway (same-origin)
      const response = await fetch('/auth/userinfo', {
        credentials: 'include'
      });
      if (!response.ok) throw Error('User not authenticated');
      const user = await response.json();
      return {
        email: user.email,
        id_token: 'cookie',
        access_token: 'cookie',
        short_id: user.sub
      };
    } else {
      const user = await Auth.currentAuthenticatedUser();
      return {
        email: user.attributes.email,
        id_token: user.signInUserSession.idToken.jwtToken,
        access_token: user.signInUserSession.accessToken.jwtToken,
        short_id: 'none'
      };
    }
  };

  const login = async () => {
    try {
      if (CUSTOM_AUTH) {
        const { verifier, challenge } = await generatePKCE();
        const state = generateState();

        sessionStorage.setItem('pkce_verifier', verifier);
        sessionStorage.setItem('pkce_state', state);

        const params = new URLSearchParams({
          client_id: process.env.REACT_APP_CUSTOM_AUTH_CLIENT_ID,
          redirect_uri: window.location.origin + '/callback',
          response_type: 'code',
          scope: process.env.REACT_APP_CUSTOM_AUTH_SCOPES,
          code_challenge: challenge,
          code_challenge_method: 'S256',
          state
        });

        window.location.href = `${process.env.REACT_APP_CUSTOM_AUTH_URL}/v1/authorize?${params}`;
      } else {
        await Auth.federatedSignIn();
      }
    } catch (error) {
      console.error('Failed to authenticate user', error);
    }
  };

  const logout = async () => {
    try {
      if (CUSTOM_AUTH) {
        // Use relative URL - CloudFront proxies to API Gateway (same-origin)
        const response = await fetch('/auth/logout', {
          method: 'POST',
          credentials: 'include'
        });
        const data = await response.json();

        dispatch({
          type: 'LOGOUT',
          payload: {
            isAuthenticated: false,
            user: null
          }
        });
        sessionStorage.clear();

        // Redirect to Okta logout to end SSO session, or homepage as fallback
        if (data.logout_url) {
          window.location.href = data.logout_url;
        } else {
          window.location.href = window.location.origin;
        }
      } else {
        await Auth.signOut({ global: true });
        dispatch({
          type: 'LOGOUT',
          payload: {
            isAuthenticated: false,
            user: null
          }
        });
        sessionStorage.removeItem('window-location');
      }
    } catch (error) {
      console.error('Failed to signout', error);
    }
  };

  const reauth = async () => {
    if (CUSTOM_AUTH) {
      try {
        await logout();
        dispatch({
          type: 'REAUTH',
          payload: {
            reAuthStatus: false,
            requestInfo: null
          }
        });
      } catch (error) {
        console.error('Failed to ReAuth', error);
      }
    } else {
      await Auth.signOut({ global: true });
      dispatch({
        type: 'REAUTH',
        payload: {
          reAuthStatus: false,
          requestInfo: null
        }
      });
      sessionStorage.removeItem('window-location');
    }
  };

  return (
    <GenericAuthContext.Provider
      value={{
        ...state,
        dispatch,
        platform: CUSTOM_AUTH ? CUSTOM_AUTH : 'Amplify',
        login,
        logout,
        reauth,
        isLoading: !state.isInitialized
      }}
    >
      {children}
    </GenericAuthContext.Provider>
  );
};

GenericAuthProvider.propTypes = {
  children: PropTypes.node.isRequired
};
