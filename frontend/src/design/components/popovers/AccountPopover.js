import {
  Box,
  Button,
  ButtonBase,
  Divider,
  ListItemIcon,
  ListItemText,
  MenuItem,
  Popover,
  Typography
} from '@mui/material';
import { useSnackbar } from 'notistack';
import { useRef, useState } from 'react';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { useGroups } from 'services';
import { CogIcon } from '../../icons';
import { TextAvatar } from '../TextAvatar';
import { useAuth } from 'authentication';
import { isTenantUser } from 'utils';

export const AccountPopover = () => {
  const anchorRef = useRef(null);
  const { user, logout } = useAuth();
  const groups = useGroups();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const [open, setOpen] = useState(false);

  const handleOpen = () => {
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  const handleLogout = async () => {
    try {
      handleClose();
      await logout();
      navigate('/');
    } catch (err) {
      console.error(err);
      enqueueSnackbar('Unable to logout', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'error'
      });
    }
  };

  return (
    <>
      <Box
        component={ButtonBase}
        onClick={handleOpen}
        ref={anchorRef}
        sx={{
          alignItems: 'center',
          display: 'flex'
        }}
      >
        <TextAvatar name={user.name} />
      </Box>
      <Popover
        anchorEl={anchorRef.current}
        anchorOrigin={{
          horizontal: 'center',
          vertical: 'bottom'
        }}
        getContentAnchorEl={null}
        keepMounted
        onClose={handleClose}
        open={open}
        PaperProps={{
          sx: { width: 240 }
        }}
      >
        <Box sx={{ p: 2 }}>
          <Typography color="textPrimary" variant="subtitle2">
            {user?.name}
          </Typography>
        </Box>
        <Divider />
        <Box sx={{ mt: 2 }}>
          {isTenantUser(groups) && (
            <MenuItem component={RouterLink} to="/console/administration">
              <ListItemIcon>
                <CogIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText
                primary={
                  <Typography color="textPrimary" variant="subtitle2">
                    Admin Settings
                  </Typography>
                }
              />
            </MenuItem>
          )}
        </Box>
        <Box sx={{ p: 2 }}>
          <Button
            color="primary"
            fullWidth
            onClick={handleLogout}
            variant="outlined"
          >
            Logout
          </Button>
        </Box>
      </Popover>
    </>
  );
};
