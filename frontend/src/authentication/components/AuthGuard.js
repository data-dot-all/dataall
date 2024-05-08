import PropTypes from 'prop-types';
import { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Login } from '../views/Login';
import { useAuth } from '../hooks';
import {
  isModuleEnabled,
  ModuleNames,
  RegexToValidateWindowPathName,
  WindowPathLengthThreshold
} from '../../utils';
import { useClient, useGroups } from '../../services';
import { LoadingScreen, NoAccessMaintenanceWindow } from '../../design';
import { getMaintenanceStatus } from '../../modules/Maintenance/services';
import {
  PENDING_STATUS,
  ACTIVE_STATUS
} from '../../modules/Maintenance/views/MaintenanceViewer';
import { SET_ERROR, useDispatch } from '../../globalErrors';

export const AuthGuard = (props) => {
  const { children } = props;
  const auth = useAuth();
  const location = useLocation();
  const [requestedLocation, setRequestedLocation] = useState(null);
  const [isNoAccessMaintenance, setNoAccessMaintenanceFlag] = useState(null);
  const client = useClient();
  const groups = useGroups();
  const dispatch = useDispatch();

  const checkMaintenanceMode = async () => {
    const response = await client.query(getMaintenanceStatus());
    if (!response.errors && response.data.getMaintenanceWindowStatus != null) {
      if (
        [PENDING_STATUS, ACTIVE_STATUS].includes(
          response.data.getMaintenanceWindowStatus.status
        ) &&
        response.data.getMaintenanceWindowStatus.mode === 'NO-ACCESS' &&
        !groups.includes('DAAdministrators')
      ) {
        setNoAccessMaintenanceFlag(true);
      } else {
        setNoAccessMaintenanceFlag(false);
      }
    }
  };

  useEffect(async () => {
    // Check if the maintenance window is enabled and has NO-ACCESS Status
    // If yes then display a blank screen with a message that data.all is in maintenance mode ( Check use of isNoAccessMaintenance state )
    if (isModuleEnabled(ModuleNames.MAINTENANCE) === true) {
      if (client) {
        checkMaintenanceMode().catch((e) => dispatch({ type: SET_ERROR, e }));
      }
    }
  }, [client, groups]);

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

  if (
    isNoAccessMaintenance == null &&
    isModuleEnabled(ModuleNames.MAINTENANCE) === true
  ) {
    return <LoadingScreen />;
  }

  if (isNoAccessMaintenance === true) {
    return <NoAccessMaintenanceWindow />;
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
