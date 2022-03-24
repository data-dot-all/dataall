import React from 'react';
import { AppBar, Box, IconButton, makeStyles, Toolbar } from '@material-ui/core';
import { Menu } from '@material-ui/icons';
import PropTypes from 'prop-types';
import AccountPopover from '../popovers/AccountPopover';
import Logo from '../Logo';
import NotificationsPopover from '../popovers/NotificationsPopover';
import SettingsDrawer from '../SettingsDrawer';

const useStyles = makeStyles((theme) => ({
  appBar: {
    zIndex: theme.zIndex.drawer + 1
  }
}));

const DefaultNavbar = ({ openDrawer, onOpenDrawerChange }) => {
  const classes = useStyles();

  return (
    <AppBar
      position="fixed"
      className={classes.appBar}
    >
      <Toolbar sx={{ minHeight: 64, maxHeight: 64 }}>
        { !openDrawer && (
        <IconButton
          size="large"
          edge="start"
          color="inherit"
          aria-label="menu"
          sx={{ mr: 2 }}
          onClick={() => { onOpenDrawerChange(true); }}
        >
          <Menu />
        </IconButton>
        )}
        <Box
          width="350px"
          display={{ xs: 'block', lg: 'block', xl: 'block' }}
        >
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
        <Box sx={{ ml: 1 }}>
          <NotificationsPopover />
        </Box>
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

export default DefaultNavbar;
