import React from 'react';
import {AppBar, Box, IconButton, Toolbar, Typography} from '@mui/material';
import { makeStyles } from '@mui/styles';
import { Menu } from '@mui/icons-material';
import PropTypes from 'prop-types';
import { AccountPopover, NotificationsPopover } from '../popovers';
import { Logo } from '../Logo';
import { SettingsDrawer } from '../SettingsDrawer';
import { ModuleNames, isModuleEnabled } from 'utils';
import {isMaintenanceMode} from "../../../services/graphql/MaintenanceWindow";

const useStyles = makeStyles((theme) => ({
  appBar: {
    zIndex: theme.zIndex.drawer + 1,
    backgroundColor: theme.palette.primary.main
  }
}));

export const DefaultNavbar = ({ openDrawer, onOpenDrawerChange }) => {
  const classes = useStyles();

  return (
    <AppBar position="fixed" className={classes.appBar}>
      {isMaintenanceMode() ? <AppBar position="sticky" sx={{ bgcolor: "red"}}>
          <Typography variant="subtitle2" align={'center'} fontSize={'20px'}>
            data.all is in maintenance mode. You can still navigate inside data.all but during this period, please do not make any modifications to any data.all assets ( datasets, environment, etc ).
          </Typography>
      </AppBar> : <></>}

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
