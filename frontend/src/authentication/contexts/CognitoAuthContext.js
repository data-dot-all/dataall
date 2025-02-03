import { Auth, Amplify } from 'aws-amplify';
import PropTypes from 'prop-types';
import { GenericAuthProvider } from './GenericAuthContext';
import { RequestContextProvider } from 'reauthentication';

Amplify.configure({
  Auth: {
    mandatorySignIn: true,
    region: process.env.REACT_APP_COGNITO_REGION,
    userPoolId: process.env.REACT_APP_COGNITO_USER_POOL_ID,
    userPoolWebClientId: process.env.REACT_APP_COGNITO_APP_CLIENT_ID,
    redirectSignIn: process.env.REACT_APP_COGNITO_REDIRECT_SIGNIN,
    redirectSignOut: process.env.REACT_APP_COGNITO_REDIRECT_SIGNOUT
  }
});

Auth.configure({
  oauth: {
    domain: process.env.REACT_APP_COGNITO_DOMAIN,
    redirectSignIn: process.env.REACT_APP_COGNITO_REDIRECT_SIGNIN,
    redirectSignOut: process.env.REACT_APP_COGNITO_REDIRECT_SIGNOUT,
    responseType: 'code'
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
