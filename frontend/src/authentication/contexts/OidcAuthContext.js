import { AuthProvider } from 'react-oidc-context';
import PropTypes from 'prop-types';
import { WebStorageStateStore } from 'oidc-client-ts';
import { GenericAuthProvider } from './GenericAuthContext';
import { RequestContextProvider } from 'reauthentication';

const oidcConfig = {
  authority: process.env.REACT_APP_CUSTOM_AUTH_URL,
  client_id: process.env.REACT_APP_CUSTOM_AUTH_CLIENT_ID,
  redirect_uri: process.env.REACT_APP_CUSTOM_AUTH_REDIRECT_URL,
  response_type: process.env.REACT_APP_CUSTOM_AUTH_RESP_TYPES,
  scope: process.env.REACT_APP_CUSTOM_AUTH_SCOPES,
  automaticSilentRenew: false,
  userStore: new WebStorageStateStore({ store: window.localStorage }),
  // onSigninCallback function is used to remove the query parameters from the URL
  // https://www.npmjs.com/package/react-oidc-context#:~:text=an%20implementation%20of-,onSigninCallback,-to%20oidcConfig%20to
  onSigninCallback: (_user) => {
    window.history.replaceState({}, document.title, window.location.pathname);
  }
};

export const OidcAuthProvider = (props) => {
  const { children } = props;

  return (
    <AuthProvider {...oidcConfig}>
      <GenericAuthProvider>
        <RequestContextProvider>{children}</RequestContextProvider>
      </GenericAuthProvider>
    </AuthProvider>
  );
};

OidcAuthProvider.propTypes = {
  children: PropTypes.node.isRequired
};
