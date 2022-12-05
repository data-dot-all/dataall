import { useEffect, useState } from 'react';
import {
  ApolloClient,
  ApolloLink,
  HttpLink,
  InMemoryCache
} from 'apollo-boost';
import { onError } from '@apollo/client/link/error';
import { from } from '@apollo/client';
import useToken from './useToken';
import { useDispatch } from '../store';
import { SET_ERROR } from '../store/errorReducer';

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

const useClient = (module='core') => {
  const dispatch = useDispatch();
  const [client, setClient] = useState(null);
  const token = useToken();
  // const mod = module ? `${module}` : 'core'
  const react_app_graphql_apis = JSON.parse(process.env.REACT_APP_GRAPHQL_API_DICT)
  useEffect(() => {
    const initClient = async () => {
      console.log(process.env.REACT_APP_GRAPHQL_API_DICT)
      console.log("REACT APP GRAPHQLS")
      console.log(react_app_graphql_apis[module])
      const t = token;
      const httpLink = new HttpLink({
        uri: react_app_graphql_apis[module]
      });
      const authLink = new ApolloLink((operation, forward) => {
        operation.setContext({
          headers: {
            AccessControlAllowOrigin: '*',
            AccessControlAllowHeaders: '*',
            'access-control-allow-origin': '*',
            Authorization: t ? `${t}` : '',
            AccessKeyId: 'none',
            SecretKey: 'none'
          }
        });
        return forward(operation);
      });
      const errorLink = onError(({ graphQLErrors, networkError }) => {
        if (graphQLErrors) {
          graphQLErrors.forEach(({ message, locations, path }) => {
            console.log(
              `[GraphQL error]: Message: ${message}, Location: ${locations}, Path: ${path}`
            );
          });
        }

        if (networkError) {
          console.log(`[Network error]: ${networkError}`);
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
      initClient().catch((e) => console.log(e));
    }
  }, [token, dispatch]);
  return client;
};

export default useClient;
