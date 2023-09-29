import { from } from '@apollo/client';
import { onError } from '@apollo/client/link/error';
import {
  ApolloClient,
  ApolloLink,
  HttpLink,
  InMemoryCache
} from 'apollo-boost';
import { useEffect, useState } from 'react';
import { useToken, useAuth } from 'authentication';
import { SET_ERROR, useDispatch } from 'globalErrors';

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
      const errorLink = onError(({ graphQLErrors, networkError }) => {
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
              operation.setContext({
                headers: {
                  ...oldHeaders,
                  authorization: getNewToken(),
                },
              });
              return forward(operation)
            }
          });
        }

        if (networkError) {
          console.error(`[Network error]: ${networkError}`);
          dispatch({ type: SET_ERROR, error: 'Network error occurred' });
        }
      });

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
async function getNewToken() {
  await Auth.signOut();
  useAuth();
  return useToken();
  // const login = async () => {
  //   Auth.federatedSignIn()
  //     .then((user) => {
  //       dispatch({
  //         type: 'LOGIN',
  //         payload: {
  //           user: {
  //             id: user.attributes.email,
  //             email: user.attributes.email,
  //             name: user.attributes.email
  //           }
  //         }
  //       });
  //     })
  //     .catch((e) => {
  //       console.error('Failed to authenticate user', e);
  //     });
  // };
  // return () => {
  //   // eslint-disable-next-line no-undef
  //   console.error(`Re-Auth Required`);
  //   return new Promise((resolve, reject) => {
  //     useAuth();
  //   });
  // };
}

