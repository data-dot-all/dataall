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
        if (graphQLErrors) {
          graphQLErrors.forEach(({ message, locations, path }) => {
            console.error(
              `[GraphQL error]: Message: ${message}, Location: ${locations}, Path: ${path}`
            );
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
      initClient().catch((e) => {
        if (err.response.status === 401) { // IF COMING FROM RE AUTH
          reAuthInitiate();
        } else {
          console.error(e);
        }

    });
    }
  }, [token, dispatch]);
  return client;
};

// Step-up - initiate
export function reAuthInitiate() {
  return () => {
    // eslint-disable-next-line no-undef
    console.error(`Re-Auth Required`);
    return new Promise((resolve, reject) => {
      useAuth();
      // <RequestDashboardAccessModal
      //   hit={hit}
      //   onApply={handleRequestDashboardAccessModalClose}
      //   onClose={handleRequestDashboardAccessModalClose}
      //   open={isRequestDashboardAccessOpen}
      //   stopLoader={() => setIsOpeningDashboardModal(false)}
      // />
      // Auth.currentSession()
        // .then((session) => {
        //   const accessToken = session.getAccessToken().getJwtToken();
        //   const idToken = session.getIdToken().getJwtToken();
        //   return {accessToken, idToken};
        // })
        // .then((tokens) => {
        //   const { accessToken, idToken } = tokens;
        //   // API call
        //   API.post(config.REST_API_ENDPOINTS[0].name, "initiate-auth", {
        //     headers: {
        //       Identification: `Bearer ${idToken}`,
        //       Authorization: `Bearer ${accessToken}`,
        //     },
        //     response: true // OPTIONAL (return the entire Axios response object instead of only response.data)
        //   })
        //   // handle API success
        //   .then((response) => {
        //     console.log("StepUpActions.stepUpInitiate(): response:", response);
        //     if (response && response.data &&
        //         (
        //           response.data.code === "SOFTWARE_TOKEN_STEP_UP" ||
        //           response.data.code === "SMS_STEP_UP" ||
        //           response.data.code === "EMAIL_STEP_UP" ||
        //           response.data.code === "MAYBE_SOFTWARE_TOKEN_STEP_UP"
        //         )
        //       ) {
        //       dispatch({
        //         type: STEP_UP_INITIATED,
        //         payload: {
        //           code: response.data.code
        //         }
        //       });
        //       resolve(true); // resolve with dummy value
        //     } else {
        //       dispatch({
        //         type: STEP_UP_ERROR,
        //         payload: {
        //           message: "Invalid step-up initiate response",
        //           origin: STEP_UP_INITIATED
        //         }
        //       });
        //       resolve(true); // resolve with dummy value
        //     }
        //   })
        //   // catch API.post() error
        //   .catch((err) => {
        //     console.log("StepUpActions.stepUpInitiate(): error response:", err);
        //     // const errorMessage = `${err.message}. ${err.response.data}`;
        //     dispatch({
        //       type: STEP_UP_ERROR,
        //       payload: {
        //         message: err.message,
        //         origin: STEP_UP_INITIATED
        //       }
        //     });
        //     reject(false); // reject with dummy value
        //   });
        // })
        // // catch Auth.currentSession() error
        // .catch((err) => {
        //   console.log("StepUpActions.stepUpInitiate(): error response:", err);
        //   dispatch({
        //     type: STEP_UP_ERROR,
        //     payload: {
        //       message: err.message,
        //       origin: STEP_UP_INITIATED
        //     }
        //   });
        //   reject(false); // reject with dummy value
        // });
    });
  };
}