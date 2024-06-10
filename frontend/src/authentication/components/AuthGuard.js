import PropTypes from 'prop-types';
import { useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Login } from '../views/Login';
import { useAuth } from '../hooks';
import {
  RegexToValidateWindowPathName,
  WindowPathLengthThreshold
} from 'utils';

export const AuthGuard = (props) => {
  const { children } = props;
  const auth = useAuth();
  const location = useLocation();
  const [requestedLocation, setRequestedLocation] = useState(null);

  if (!auth.isAuthenticated) {
    if (location.pathname !== requestedLocation) {
      setRequestedLocation(location.pathname);
    }

    // If the user is not authenticated and if the session storage is empty for the key 'window-location'
    // Also, another check of location.path is added to prevent overriding the window-location object when the user logs out and redirected to the landing page URL. Here, when the user is logged out the session storage stores '/' which is not needed
    if (
      !sessionStorage.getItem('window-location') &&
      location.pathname !== '/'
    ) {
      sessionStorage.setItem('window-location', location.pathname);
    }

    return <Login />;
  }

  if (requestedLocation && location.pathname !== requestedLocation) {
    setRequestedLocation(null);
    return <Navigate to={requestedLocation} />;
  }

  // When session storage contained path is not same as the current location.pathname ( usually after authentication )
  // Redirect the user to the session storage stored pathname.
  if (
    sessionStorage.getItem('window-location') &&
    location.pathname !== sessionStorage.getItem('window-location')
  ) {
    const windowPathLocation = sessionStorage.getItem('window-location');
    sessionStorage.removeItem('window-location');
    // Check if the window-location only contains alphanumeric and / in it and its not tampered
    if (!RegexToValidateWindowPathName.test(windowPathLocation))
      return <>{children}</>;
    // A guardrail to limit the string of the pathname to a certain characters
    if (windowPathLocation.length > WindowPathLengthThreshold)
      return <>{children}</>;
    return <Navigate to={windowPathLocation} replace={true} />;
  } else {
    sessionStorage.removeItem('window-location');
  }

  return <>{children}</>;
};

AuthGuard.propTypes = {
  children: PropTypes.node
};
