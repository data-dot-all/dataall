import React, { createContext, useContext, useState } from 'react';
import {
  from,
  ApolloClient,
  ApolloLink,
  InMemoryCache,
  HttpLink
} from '@apollo/client';
// import { useClient } from 'services';

// Create a context for API request headers
const RequestContext = createContext();

// Create a custom hook to access the context
export function useRequestContext() {
  return useContext(RequestContext);
}

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

export function RequestContextProvider({ children }) {
  const [requestInfo, setRequestInfo] = useState(null);

  const storeRequestInfo = (info) => {
    setRequestInfo(info);
  };

  const clearRequestInfo = () => {
    setRequestInfo(null);
  };

  const retryRequest = async (token) => {
    // const client = useClient();
    const httpLink = new HttpLink({
      uri: process.env.REACT_APP_GRAPHQL_API
    });

    const authLink = new ApolloLink((operation, forward) => {
      operation.setContext({
        headers: {
          AccessControlAllowOrigin: '*',
          AccessControlAllowHeaders: '*',
          'access-control-allow-origin': '*',
          Authorization: token ? `${token}` : '',
          AccessKeyId: 'none',
          SecretKey: 'none'
        }
      });
      return forward(operation);
    });
    const apolloClient = new ApolloClient({
      link: from([authLink, httpLink]),
      cache: new InMemoryCache(),
      defaultOptions
    });

    await apolloClient.query(requestInfo);
    clearRequestInfo();
  };

  return (
    <RequestContext.Provider
      value={{
        requestInfo,
        storeRequestInfo,
        clearRequestInfo,
        retryRequest
      }}
    >
      {children}
    </RequestContext.Provider>
  );
}
