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
import { gql } from '@apollo/client';
import { print } from 'graphql/language';
import { useNavigate } from 'react-router';
import { useSnackbar } from 'notistack';
import { SET_ERROR, useDispatch } from 'globalErrors';
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
  const navigate = useNavigate();
  const enqueueSnackbar = useSnackbar();
  const { dispatch } = useDispatch();
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
    if (client) {
      const restoredRequestInfo = restoreRetryRequest();
      // If request info is restored from previous user session
      if (restoredRequestInfo && restoredRequestInfo.timestamp) {
        const currentTime = new Date();
        const reauthTime = new Date(
          restoredRequestInfo.timestamp.replace(/\s/g, '')
        );
        console.error(currentTime);
        console.error(reauthTime);
        // If the time is within the TTL, Retry the Request
        // and navigate to the previous page
        if (currentTime - reauthTime <= 5 * 60 * 1000) {
          console.error('RETRY');
          console.error(restoredRequestInfo);
          retryRequest(restoredRequestInfo).catch((e) =>
            dispatch({ type: SET_ERROR, error: e.message })
          );
          // setRequestInfo(restoredRequestInfo);
        }
        // clearRequestInfo();
      }
    }
  }, [client]);

  const retryRequest = async (restoredInfo) => {
    const gqlTemplateLiteral = gql(print(restoredInfo.operation.query));
    const response = client.query({
      query: gqlTemplateLiteral,
      variables: restoredInfo.operation.variables
    });
    if (!response.errors) {
      enqueueSnackbar(
        `Operation Retried Successful: ${restoredInfo.operation.operationName}`,
        {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        }
      );
      navigate(restoredInfo.pathname);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }

    // const httpLink = new HttpLink({
    //   uri: process.env.REACT_APP_GRAPHQL_API
    // });
    // await client.query(restoredInfo);
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
