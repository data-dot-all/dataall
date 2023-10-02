import { from } from '@apollo/client';
import { onError } from '@apollo/client/link/error';
import {
  ApolloClient,
  ApolloLink,
  HttpLink,
  InMemoryCache
} from 'apollo-boost';
import { Auth } from 'aws-amplify';
import { useEffect, useState } from 'react';
import { useToken, useAuth } from 'authentication';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useNavigate } from 'react-router';

const defaultOptions = {
  watchQuery: {
    fetchPolicy: 'no-cache',
    errorPolicy: 'ignore'
  },
  query: {
    fetchPolicy: 'no-cache',
    errorPolicy: 'all'
  },
  mutate: {
    fetchPolicy: 'no-cache',
    errorPolicy: 'all'
  }
};

export const useClient = () => {
  const dispatch = useDispatch();
  const [client, setClient] = useState(null);
  const token = useToken();

  useEffect(() => {
    const initClient = async () => {
      const t = token;
      const httpLink = new HttpLink({
        uri: process.env.REACT_APP_GRAPHQL_API
      });
      const authLink = new ApolloLink((operation, forward) => {
        operation.setContext({
          headers: {
            AccessControlAllowOrigin: '*',
            AccessControlAllowHeaders: '*',
            'access-control-allow-origin': '*',
            Authorization: t ? `${t}` : '',
            AccessKeyId: 'none',
            SecretKey: 'none',
            'operation-name': operation.operationName
          }
        });
        return forward(operation);
      });
      const errorLink = onError(
        ({ graphQLErrors, networkError, operation, forward }) => {
          // if (graphQLErrors) {
          //   for (let err of graphQLErrors) {
          //     switch (err.extensions.code) {
          //       // Apollo Server sets code to UNAUTHENTICATED
          //       // when an AuthenticationError is thrown in a resolver
          //       case "UNAUTHENTICATED":
          //         // Modify the operation context with a new token
          //         const oldHeaders = operation.getContext().headers;
          //         operation.setContext({
          //           headers: {
          //             ...oldHeaders,
          //             authorization: getNewToken(),
          //           },
          //         });
          //         // Retry the request, returning the new observable
          //         return forward(operation);
          //     }
          //   }
          // }
          if (graphQLErrors) {
            graphQLErrors.forEach(({ message, locations, path }) => {
              console.error(
                `[GraphQL error]: Message: ${message}, Location: ${locations}, Path: ${path}`
              );
              if (message === 'ReAuth Required') {
                const oldHeaders = operation.getContext().headers;
                const newToken = ReAuthtNewToken();
                operation.setContext({
                  headers: {
                    ...oldHeaders,
                    authorization: newToken
                  }
                });
                return forward(operation);
              }
            });
          }

          if (networkError) {
            console.error(`[Network error]: ${networkError}`);
            dispatch({ type: SET_ERROR, error: 'Network error occurred' });
          }
        }
      );

      const apolloClient = new ApolloClient({
        link: from([errorLink, authLink, httpLink]),
        cache: new InMemoryCache(),
        defaultOptions
      });
      setClient(apolloClient);
    };
    if (token) {
      initClient().catch((e) => console.error(e));
    }
    // if (token) {
    //   initClient().catch((e) => {
    //     // IF COMING FROM RE AUTH
    //     if (e.response.status === 401) {
    //       reAuthInitiate();
    //     } else {
    //       console.error(e);
    //     }
    //   });
    // }
  }, [token, dispatch]);
  return client;
};

// Step-up - initiate
// export function useNewToken() {
//   const { auth, logout, login } = useAuth();
//   // const dispatch = useDispatch();
//   const navigate = useNavigate();
//   const [token, setToken] = useState(null);
//   const fetchAuthToken = async () => {
//     try {
//       await logout();
//       navigate('/');
//       await login();
//       const session = await Auth.currentSession();
//       const t = session.getIdToken().getJwtToken();
//       setToken(t);
//     } catch (error) {
//       auth.dispatch({
//         type: 'LOGOUT'
//       });
//     }
//   };
//   useEffect(() => {
//     if (!token) {
//       fetchAuthToken().catch((e) =>
//         dispatch({ type: SET_ERROR, error: e.message })
//       );
//     }
//   });
//   return token;
// }
export const ReAuthtNewToken = () => {
  const { auth, logout, login } = useAuth();
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const [token, setToken] = useState(null);
  const fetchAuthToken = async () => {
    try {
      await logout();
      navigate('/');
      await login();
      const session = await Auth.currentSession();
      const t = session.getIdToken().getJwtToken();
      setToken(t);
    } catch (error) {
      auth.dispatch({
        type: 'LOGOUT'
      });
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

// const fetchEnvironments = useCallback(async () => {
//   setLoading(true);
//   const response = await client.query(
//     listEnvironments({ filter: Defaults.selectListFilter })
//   );
//   if (!response.errors) {
//     setEnvironmentOptions(
//       response.data.listEnvironments.nodes.map((e) => ({
//         ...e,
//         value: e.environmentUri,
//         label: e.label
//       }))
//     );
//   } else {
//     dispatch({ type: SET_ERROR, error: response.errors[0].message });
//   }
//   setLoading(false);
// }, [client, dispatch]);

// export function getNewToken() {
//   const { user, logout, login } = useAuth();
//   await logout();
//   navigate('/');
//   await login();
//   const session = await Auth.currentSession();
//   const t = await session.getIdToken().getJwtToken();
//   return t;
//   // const login = async () => {
//   //   Auth.federatedSignIn()
//   //     .then((user) => {
//   //       dispatch({
//   //         type: 'LOGIN',
//   //         payload: {
//   //           user: {
//   //             id: user.attributes.email,
//   //             email: user.attributes.email,
//   //             name: user.attributes.email
//   //           }
//   //         }
//   //       });
//   //     })
//   //     .catch((e) => {
//   //       console.error('Failed to authenticate user', e);
//   //     });
//   // };
//   // return () => {
//   //   // eslint-disable-next-line no-undef
//   //   console.error(`Re-Auth Required`);
//   //   return new Promise((resolve, reject) => {
//   //     useAuth();
//   //   });
//   // };
// }
