import PropTypes from 'prop-types';
import { useEffect, useState } from 'react';
import { isModuleEnabled, isTenantUser, ModuleNames } from 'utils';
import { useClient, useGroups } from 'services';
import { LoadingScreen, NoAccessMaintenanceWindow } from 'design';
import { getMaintenanceStatus } from '../../modules/Maintenance/services';
import {
  PENDING_STATUS,
  ACTIVE_STATUS
} from '../../modules/Maintenance/components/MaintenanceViewer';
import { SET_ERROR, useDispatch } from 'globalErrors';

export const MaintenanceGuard = (props) => {
  const { children } = props;
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
        !isTenantUser(groups)
      ) {
        setNoAccessMaintenanceFlag(true);
      } else {
        setNoAccessMaintenanceFlag(false);
      }
    }
  };

  useEffect(() => {
    // Check if the maintenance window is enabled and has NO-ACCESS Status
    // If yes then display a blank screen with a message that data.all is in maintenance mode ( Check use of isNoAccessMaintenance state )
    if (isModuleEnabled(ModuleNames.MAINTENANCE) === true) {
      if (client && groups) {
        checkMaintenanceMode().catch((e) => dispatch({ type: SET_ERROR, e }));
      }
    }
  }, [client, groups]);

  if (
    isNoAccessMaintenance == null &&
    isModuleEnabled(ModuleNames.MAINTENANCE) === true
  ) {
    return <LoadingScreen />;
  }

  if (isNoAccessMaintenance === true) {
    return <NoAccessMaintenanceWindow />;
  }

  return <>{children}</>;
};

MaintenanceGuard.propTypes = {
  children: PropTypes.node
};
