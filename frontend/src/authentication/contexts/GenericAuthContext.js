import { createContext, useEffect, useReducer, useRef } from 'react';
import { SET_ERROR } from 'globalErrors';
import PropTypes from 'prop-types';
import {
  fetchAuthSession,
  fetchUserAttributes,
  signInWithRedirect,
  signOut
} from 'aws-amplify/auth';
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
  const expirationTimerRef = useRef(null);

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

    // Cleanup: clear expiration timer on unmount
    return () => {
      if (expirationTimerRef.current) {
        clearTimeout(expirationTimerRef.current);
      }
    };
  }, []);

  const setupExpirationTimer = (exp) => {
    // Clear any existing timer
    if (expirationTimerRef.current) {
      clearTimeout(expirationTimerRef.current);
      expirationTimerRef.current = null;
    }

    if (!exp) return;

    // Calculate time until expiration (exp is in seconds, Date.now() is in ms)
    const expiresAt = exp * 1000;
    const now = Date.now();
    const timeUntilExpiry = expiresAt - now;

    // If already expired, redirect to login immediately
    if (timeUntilExpiry <= 0) {
      handleSessionExpired();
      return;
    }

    // Set timer to handle expiration (with 30s buffer for network latency)
    const bufferMs = 30 * 1000;
    const timerMs = Math.max(timeUntilExpiry - bufferMs, 0);

    expirationTimerRef.current = setTimeout(() => {
      handleSessionExpired();
    }, timerMs);
  };

  const handleSessionExpired = async () => {
    // Clear expiration timer
    if (expirationTimerRef.current) {
      clearTimeout(expirationTimerRef.current);
      expirationTimerRef.current = null;
    }

    // Try to clear cookies (ignore errors if already expired)
    try {
      await fetch('/auth/logout', {
        method: 'POST',
        credentials: 'include'
      });
    } catch (error) {
      // Ignore - cookies may already be expired
    }

    dispatch({
      type: 'LOGOUT',
      payload: {
        isAuthenticated: false,
        user: null
      }
    });
    sessionStorage.clear();

    // Redirect to homepage which will show login page
    window.location.href = window.location.origin;
  };

  const getAuthenticatedUser = async () => {
    if (CUSTOM_AUTH) {
      // Use relative URL - CloudFront proxies to API Gateway (same-origin)
      const response = await fetch('/auth/userinfo', {
        credentials: 'include'
      });
      if (!response.ok) throw Error('User not authenticated');
      const user = await response.json();

      // Set up expiration timer if exp claim is present
      if (user.exp) {
        setupExpirationTimer(user.exp);
      }

      return {
        email: user.email,
        id_token: 'cookie',
        access_token: 'cookie',
        short_id: user.sub
      };
    } else {
      const session = await fetchAuthSession();
      const userAttributes = await fetchUserAttributes();
      return {
        email: userAttributes.email,
        id_token: session.tokens?.idToken?.toString() || '',
        access_token: session.tokens?.accessToken?.toString() || '',
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
        await signInWithRedirect();
      }
    } catch (error) {
      console.error('Failed to authenticate user', error);
    }
  };

  const logout = async () => {
    try {
      // Clear expiration timer
      if (expirationTimerRef.current) {
        clearTimeout(expirationTimerRef.current);
        expirationTimerRef.current = null;
      }

      if (CUSTOM_AUTH) {
        // Silent logout - clears cookies but keeps Okta SSO session active
        // This matches the previous behavior using react-oidc-context's signoutSilent()
        await fetch('/auth/logout', {
          method: 'POST',
          credentials: 'include'
        });

        dispatch({
          type: 'LOGOUT',
          payload: {
            isAuthenticated: false,
            user: null
          }
        });
        sessionStorage.clear();

        // Redirect to homepage (login page)
        window.location.href = window.location.origin;
      } else {
        await signOut({ global: true });
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
        // Clear expiration timer
        if (expirationTimerRef.current) {
          clearTimeout(expirationTimerRef.current);
          expirationTimerRef.current = null;
        }

        // Clear cookies via backend (but don't redirect to Okta logout)
        await fetch('/auth/logout', {
          method: 'POST',
          credentials: 'include'
        });

        dispatch({
          type: 'REAUTH',
          payload: {
            reAuthStatus: false,
            requestInfo: null
          }
        });
        sessionStorage.clear();

        // Trigger new login flow
        await login();
      } catch (error) {
        console.error('Failed to ReAuth', error);
      }
    } else {
      await signOut({ global: true });
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
