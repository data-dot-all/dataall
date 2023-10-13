import PropTypes from 'prop-types';
import { createContext, useEffect, useReducer } from 'react';
import { SET_ERROR } from 'globalErrors';

const anonymousUser = {
  id: 'someone@amazon.com',
  email: 'someone@amazon.com',
  name: 'someone@amazon.com'
};
const initialState = {
  isAuthenticated: true,
  isInitialized: true,
  user: anonymousUser
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

export const LocalAuthContext = createContext({
  ...initialState,
  platform: 'local',
  login: () => Promise.resolve(),
  logout: () => Promise.resolve()
});

export const LocalAuthProvider = (props) => {
  const { children } = props;
  const [state, dispatch] = useReducer(reducer, initialState);

  useEffect(() => {
    const initialize = async () => {
      try {
        dispatch({
          type: 'INITIALIZE',
          payload: {
            isAuthenticated: true,
            user: anonymousUser
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
    dispatch({
      type: 'LOGIN',
      payload: {
        user: anonymousUser
      }
    });
  };

  const logout = async () => {
    dispatch({
      type: 'LOGOUT'
    });
  };

  return (
    <LocalAuthContext.Provider
      value={{
        ...state,
        dispatch,
        platform: 'local',
        login,
        logout
      }}
    >
      {children}
    </LocalAuthContext.Provider>
  );
};

LocalAuthProvider.propTypes = {
  children: PropTypes.node.isRequired
};
