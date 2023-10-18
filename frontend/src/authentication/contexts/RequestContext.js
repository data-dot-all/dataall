import React, { createContext, useContext, useEffect, useState } from 'react';
import PropTypes from 'prop-types';
// import {
//   from,
//   ApolloClient,
//   ApolloLink,
//   InMemoryCache,
//   HttpLink
// } from '@apollo/client';
// import { useToken } from 'authentication';
import { useClient } from 'services';
// import { useClient } from 'services';

// Create a context for API request headers
const RequestContext = createContext();

// Create a custom hook to access the context
export const useRequestContext = () => {
  return useContext(RequestContext);
};

// const defaultOptions = {
//   watchQuery: {
//     fetchPolicy: 'no-cache',
//     errorPolicy: 'ignore'
//   },
//   query: {
//     fetchPolicy: 'no-cache',
//     errorPolicy: 'all'
//   },
//   mutate: {
//     fetchPolicy: 'no-cache',
//     errorPolicy: 'all'
//   }
// };
const REQUEST_INFO_KEY = 'requestInfo';

export const storeRequestInfoStorage = (requestInfo) => {
  console.error(requestInfo);
  window.localStorage.setItem(REQUEST_INFO_KEY, JSON.stringify(requestInfo));
};

export const restoreRetryRequest = () => {
  try {
    const storedRequestInfo = window.localStorage.getItem(REQUEST_INFO_KEY);
    if (storedRequestInfo != null) {
      return JSON.parse(storedRequestInfo);
    }
    return null;
  } catch (err) {
    console.error(err);
    return null;
  }
};

export const RequestContextProvider = (props) => {
  const { children } = props;
  const [requestInfo, setRequestInfo] = useState(null);
  // const token = useToken();
  const client = useClient();
  const storeRequestInfo = (info) => {
    setRequestInfo(info);
    storeRequestInfoStorage(info);
  };

  const clearRequestInfo = () => {
    setRequestInfo(null);
    window.localStorage.removeItem('requestInfo');
  };

  useEffect(() => {
    const restoredRequestInfo = restoreRetryRequest();
    const currentTime = new Date();
    const reauthTime = new Date(restoredRequestInfo.timestamp);
    console.error(currentTime);
    console.error(reauthTime);
    if (restoredRequestInfo && currentTime - reauthTime <= 5 * 60 * 1000) {
      // TODO: RETRY REQUEST AFTER TIMESTAMP CHECK
      console.error('RETRY');
      console.error(restoredRequestInfo);
      retryRequest(restoredRequestInfo);
      // setRequestInfo(restoredRequestInfo);
    }
  }, []);

  const retryRequest = async (restoredInfo) => {
    // const client = useClient();
    // const httpLink = new HttpLink({
    //   uri: process.env.REACT_APP_GRAPHQL_API
    // });
    await client.query(restoredInfo);
    // const authLink = new ApolloLink((operation, forward) => {
    //   operation.setContext({
    //     headers: {
    //       AccessControlAllowOrigin: '*',
    //       AccessControlAllowHeaders: '*',
    //       'access-control-allow-origin': '*',
    //       Authorization: token ? `${token}` : '',
    //       AccessKeyId: 'none',
    //       SecretKey: 'none'
    //     }
    //   });
    //   return forward(operation);
    // });
    // const apolloClient = new ApolloClient({
    //   link: from([authLink, httpLink]),
    //   cache: new InMemoryCache(),
    //   defaultOptions
    // });

    // await apolloClient.query(restoredInfo);
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
};

RequestContextProvider.propTypes = {
  children: PropTypes.node.isRequired
};
