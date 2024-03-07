import PropTypes from 'prop-types';
import { useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Login } from '../views/Login';
import { useAuth } from '../hooks';
import {regexToValidateWindowPathName} from "../../utils";

export const AuthGuard = (props) => {
  const { children } = props;
  const auth = useAuth();
  const location = useLocation();
  const [requestedLocation, setRequestedLocation] = useState(null);

  if (!auth.isAuthenticated) {
    if (location.pathname !== requestedLocation) {
      setRequestedLocation(location.pathname);
    }

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

  if (
    sessionStorage.getItem('window-location') &&
    location.pathname !== sessionStorage.getItem('window-location')
  ) {

    const windowPathLocation = sessionStorage.getItem('window-location');
    sessionStorage.removeItem('window-location');
    // Check if the window-location only contains alphanumeric and / in it and its not tampered
    if (!regexToValidateWindowPathName.test(windowPathLocation))
      return <>{children}</>;
    // A guardrail to limit the string of the pathname to a certain characters
    if (windowPathLocation.length > 50)
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
