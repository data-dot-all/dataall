import React, { useEffect, useState } from 'react';
import { AppBar, Box, IconButton, Toolbar, Typography } from '@mui/material';
import { makeStyles } from '@mui/styles';
import { Menu } from '@mui/icons-material';
import PropTypes from 'prop-types';
import { AccountPopover, NotificationsPopover } from '../popovers';
import { Logo } from '../Logo';
import { SettingsDrawer } from '../SettingsDrawer';
import { ModuleNames, isModuleEnabled } from 'utils';
import config from '../../../generated/config.json';
import {
  PENDING_STATUS,
  ACTIVE_STATUS
} from '../../../modules/Maintenance/components/MaintenanceViewer';
import { useClient } from 'services';
import { getMaintenanceStatus } from '../../../modules/Maintenance/services';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { SanitizedHTML } from '../SanitizedHTML';

const useStyles = makeStyles((theme) => ({
  appBar: {
    zIndex: theme.zIndex.drawer + 1,
    backgroundColor: theme.palette.primary.main
  }
}));

export const DefaultNavbar = ({ openDrawer, onOpenDrawerChange }) => {
  const classes = useStyles();
  const [isMaintenance, setMaintenanceFlag] = useState(false);
  const dispatch = useDispatch();
  const client = useClient();

  const _getMaintenanceStatus = async () => {
    const response = await client.query(getMaintenanceStatus());
    if (!response.errors && response.data.getMaintenanceWindowStatus !== null) {
      if (
        response.data.getMaintenanceWindowStatus.status === ACTIVE_STATUS ||
        response.data.getMaintenanceWindowStatus.status === PENDING_STATUS
      ) {
        setMaintenanceFlag(true);
      }
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Could not fetch status of maintenance window';
      dispatch({ type: SET_ERROR, error });
    }
  };

  useEffect(async () => {
    if (client && isModuleEnabled(ModuleNames.MAINTENANCE)) {
      _getMaintenanceStatus().catch((err) =>
        dispatch({ type: SET_ERROR, err })
      );
    }
  }, [client]);

  return (
    <AppBar position="fixed" className={classes.appBar}>
      {isModuleEnabled(ModuleNames.MAINTENANCE) && isMaintenance ? (
        <AppBar position="sticky" sx={{ bgcolor: 'red' }}>
          {config.modules.maintenance.custom_maintenance_text !== undefined ? (
            <Typography variant="subtitle2" align={'center'} fontSize={'20px'}>
              <SanitizedHTML
                dirtyHTML={config.modules.maintenance.custom_maintenance_text}
              />
            </Typography>
          ) : (
            <Typography variant="subtitle2" align={'center'} fontSize={'20px'}>
              data.all is in maintenance mode. You can still navigate inside
              data.all but during this period, please do not make any
              modifications to any data.all assets ( datasets, environment, etc
              ).
            </Typography>
          )}
        </AppBar>
      ) : (
        <></>
      )}

      <Toolbar sx={{ minHeight: 64, maxHeight: 64 }}>
        {!openDrawer && (
          <IconButton
            size="large"
            edge="start"
            color="inherit"
            aria-label="menu"
            sx={{ mr: 2 }}
            onClick={() => {
              onOpenDrawerChange(true);
            }}
          >
            <Menu />
          </IconButton>
        )}
        <Box width="350px" display={{ xs: 'block', lg: 'block', xl: 'block' }}>
          <Logo />
        </Box>
        <Box
          sx={{
            flexGrow: 1,
            ml: 2
          }}
        />
        <Box sx={{ ml: 1 }}>
          <SettingsDrawer />
        </Box>
        {isModuleEnabled(ModuleNames.NOTIFICATIONS) ? (
          <Box sx={{ ml: 1 }}>
            <NotificationsPopover />
          </Box>
        ) : (
          <Box sx={{ ml: 1 }}></Box>
        )}
        <Box sx={{ ml: 2 }}>
          <AccountPopover />
        </Box>
      </Toolbar>
    </AppBar>
  );
};

DefaultNavbar.propTypes = {
  openDrawer: PropTypes.bool,
  onOpenDrawerChange: PropTypes.func
};
