import { from } from '@apollo/client';
import { onError } from '@apollo/client/link/error';
import {
  ApolloClient,
  ApolloLink,
  HttpLink,
  InMemoryCache
} from 'apollo-boost';
import { useEffect, useState, useCallback } from 'react';
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
  const auth = useAuth();

  const setReAuth = useCallback(
    async (requestInfo) => {
      auth.dispatch({
        type: 'REAUTH',
        payload: {
          reAuthStatus: true,
          requestInfo: requestInfo
        }
      });
    },
    [auth]
  );

  useEffect(() => {
    const initClient = async () => {
      const t = token;
      const httpLink = new HttpLink({
        uri: process.env.REACT_APP_GRAPHQL_API
      });

      const authLink = new ApolloLink((operation, forward) => {
        operation.setContext({
          headers: {
            Authorization: t ? `Bearer ${t}` : '',
            AccessKeyId: 'none',
            SecretKey: 'none'
          }
        });
        return forward(operation);
      });
      const errorLink = onError(
        ({ graphQLErrors, networkError, operation, forward }) => {
          if (graphQLErrors) {
            graphQLErrors.forEach(
              ({ message, locations, path, extensions }) => {
                console.error(
                  `[GraphQL error]: Message: ${message}, Location: ${locations}, Path: ${path}`
                );
                if (extensions?.code === 'REAUTH') {
                  setReAuth(operation);
                }
                // Dispatch to show message when a 4xx network error is returned
                if (networkError) {
                  dispatch({ type: SET_ERROR, error: `${message}` });
                }
              }
            );
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
  }, [token, dispatch]);
  return client;
};
