import React, { createContext, useContext, useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { useClient } from 'services';
import { gql } from '@apollo/client';
import { print } from 'graphql/language';
import { useNavigate } from 'react-router';
import { useSnackbar } from 'notistack';
import { Auth } from 'aws-amplify';
import { useAuth, useToken } from 'authentication';

// Create a context for API request headers
const RequestContext = createContext();

// Create a custom hook to access the context
export const useRequestContext = () => {
  return useContext(RequestContext);
};

const REQUEST_INFO_KEY = 'requestInfo';
const REAUTH_TTL = process.env.REACT_APP_REAUTH_TTL
  ? parseInt(process.env.REACT_APP_REAUTH_TTL, 10)
  : 5;

export const storeRequestInfoStorage = (requestInfo) => {
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

export const retrieveCurrentUsername = async () => {
  try {
    const user = await Auth.currentAuthenticatedUser();
    return user.attributes.email;
  } catch (err) {
    console.error(err);
    return null;
  }
};

export const RequestContextProvider = (props) => {
  const { children } = props;
  const [requestInfo, setRequestInfo] = useState(null);
  const navigate = useNavigate();
  const client = useClient();
  const token = useToken();
  const auth = useAuth();
  const { enqueueSnackbar } = useSnackbar();
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
      if (
        restoredRequestInfo &&
        restoredRequestInfo.timestamp &&
        token !== restoredRequestInfo.id_token
      ) {
        const currentTime = new Date();
        const reauthTime = new Date(
          restoredRequestInfo.timestamp.replace(/\s/g, '')
        );
        // If the user waited too long to reAuth - clear storage
        // Else retry the ReAuth API Request
        if (currentTime - reauthTime <= REAUTH_TTL * 60 * 1000) {
          retryRequest(restoredRequestInfo)
            .then((r) => {
              if (r && !r.errors) {
                enqueueSnackbar(
                  `ReAuth Retry Operation Successful ${restoredRequestInfo.requestInfo.operationName}`,
                  {
                    anchorOrigin: {
                      horizontal: 'right',
                      vertical: 'top'
                    },
                    variant: 'success'
                  }
                );
                if (
                  restoredRequestInfo.requestInfo.query.definitions[0]
                    .operation === 'query'
                ) {
                  navigate(restoredRequestInfo.pathname);
                }
              } else if (r) {
                enqueueSnackbar(
                  `ReAuth Retry Operation Failed ${restoredRequestInfo.requestInfo.operationName} with error ${r.errors[0].message}`,
                  {
                    anchorOrigin: {
                      horizontal: 'right',
                      vertical: 'top'
                    },
                    variant: 'error'
                  }
                );
              }
            })
            .finally(() => clearRequestInfo());
        } else {
          enqueueSnackbar(
            `ReAuth Retry Operation Failed ${restoredRequestInfo.requestInfo.operationName} - waited over ${REAUTH_TTL} minutes`,
            {
              anchorOrigin: {
                horizontal: 'right',
                vertical: 'top'
              },
              variant: 'error'
            }
          );
          clearRequestInfo();
        }
      }
    }
  }, [client]);

  const retryRequest = async (restoredInfo) => {
    const gqlTemplateLiteral = gql(print(restoredInfo.requestInfo.query));
    const username = process.env.REACT_APP_CUSTOM_AUTH
      ? auth.user.email
      : await retrieveCurrentUsername();
    if (username !== restoredInfo.username) {
      return null;
    } else if (
      restoredInfo.requestInfo.query.definitions[0].operation === 'query'
    ) {
      const response = await client.query({
        query: gqlTemplateLiteral,
        variables: restoredInfo.requestInfo.variables
      });
      return response;
    } else if (
      restoredInfo.requestInfo.query.definitions[0].operation === 'mutation'
    ) {
      const response = await client.mutate({
        mutation: gqlTemplateLiteral,
        variables: restoredInfo.requestInfo.variables
      });
      return response;
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
