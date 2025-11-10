import { Amplify } from 'aws-amplify';
import PropTypes from 'prop-types';
import { GenericAuthProvider } from './GenericAuthContext';
import { RequestContextProvider } from 'reauthentication';

Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: process.env.REACT_APP_COGNITO_USER_POOL_ID,
      userPoolClientId: process.env.REACT_APP_COGNITO_APP_CLIENT_ID,
      loginWith: {
        oauth: {
          domain: process.env.REACT_APP_COGNITO_DOMAIN,
          scopes: [],
          redirectSignIn: [process.env.REACT_APP_COGNITO_REDIRECT_SIGNIN],
          redirectSignOut: [process.env.REACT_APP_COGNITO_REDIRECT_SIGNOUT],
          responseType: 'code'
        }
      }
    }
  }
});

export const CognitoAuthProvider = (props) => {
  const { children } = props;

  return (
    <RequestContextProvider>
      <GenericAuthProvider>{children}</GenericAuthProvider>
    </RequestContextProvider>
  );
};

CognitoAuthProvider.propTypes = {
  children: PropTypes.node.isRequired
};
