import React, { createContext, useContext, useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { useClient } from 'services';
import { gql } from '@apollo/client';
import { print } from 'graphql/language';
import { useNavigate } from 'react-router';
import { SET_ERROR, useDispatch } from 'globalErrors';

// Create a context for API request headers
const RequestContext = createContext();

// Create a custom hook to access the context
export const useRequestContext = () => {
  return useContext(RequestContext);
};

const REQUEST_INFO_KEY = 'requestInfo';
const REAUTH_TTL = parseInt(process.env.REACT_APP_REAUTH_TTL, 10)

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
  const navigate = useNavigate();
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
        if (currentTime - reauthTime <= REAUTH_TTL * 60 * 1000) {
          console.error('RETRY');
          console.error(restoredRequestInfo);
          retryRequest(restoredRequestInfo).catch((e) =>
            dispatch({ type: SET_ERROR, error: e.message })
          );
        }
        clearRequestInfo();
      }
    }
  }, [client]);

  const retryRequest = async (restoredInfo) => {
    const gqlTemplateLiteral = gql(print(restoredInfo.requestInfo.query));
    if (restoredInfo.requestInfo.query.definitions[0].operation === 'query') {
      const response = client.query({
        query: gqlTemplateLiteral,
        variables: restoredInfo.requestInfo.variables
      });
      if (!response.errors) {
        navigate(restoredInfo.pathname);
      } else {
        dispatch({
          type: SET_ERROR,
          error: `ReAuth for operation ${restoredInfo.requestInfo.operationName} Failed with error message: ${response.errors[0].message}`
        });
      }
    } else if (restoredInfo.requestInfo.query.definitions[0].operation === 'mutation')  {
      const response = client.mutate({
        mutation: gqlTemplateLiteral,
        variables: restoredInfo.requestInfo.variables
      });
      if (!response.errors) {
        navigate(restoredInfo.pathname);
      } else {
        dispatch({
          type: SET_ERROR,
          error: `ReAuth for operation ${restoredInfo.requestInfo.operationName} Failed with error message: ${response.errors[0].message}`
        });
      }
    }
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
