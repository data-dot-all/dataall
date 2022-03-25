import { useEffect, useRef, useState } from 'react';
import {
  Avatar,
  Badge,
  Box,
  IconButton,
  Link,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Popover,
  Tooltip,
  Typography
} from '@mui/material';
import countUnreadNotifications from '../../api/Notification/countUnreadNotifications';
import listNotifications from '../../api/Notification/listNotifications';
import BellIcon from '../../icons/Bell';
import useClient from '../../hooks/useClient';
import * as Defaults from '../defaults';
import { PagedResponseDefault } from '../defaults';

const NotificationsPopover = () => {
  const anchorRef = useRef(null);
  const [open, setOpen] = useState(false);
  const client = useClient();
  const [loading, setLoading] = useState(true);
  const [notifications, setNotifications] = useState(PagedResponseDefault);
  const [countInbox, setCountInbox] = useState(null);

  const handleOpen = () => {
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  const getCountInbox = async () => {
    setLoading(true);
    const response = await client.query(countUnreadNotifications());
    if (!response.errors) {
      setCountInbox(response.data.countUnreadNotifications);
    }
    setLoading(false);
  };

  const fetchItems = async () => {
    setLoading(true);
    const response = await client.query(
      listNotifications(Defaults.SelectListFilter)
    );
    if (!response.errors) {
      setNotifications(response.data.listNotifications);
      getCountInbox();
    }
    setLoading(false);
  };

  useEffect(() => {
    if (client) {
      fetchItems({ unread: true });
    }
  }, [client]);

  return (
    <>
      <Tooltip title="Notifications">
        <IconButton ref={anchorRef} color="inherit" onClick={handleOpen}>
          <Badge color="error" badgeContent={countInbox}>
            <BellIcon fontSize="small" />
          </Badge>
        </IconButton>
      </Tooltip>
      <Popover
        anchorEl={anchorRef.current}
        anchorOrigin={{
          horizontal: 'center',
          vertical: 'bottom'
        }}
        onClose={handleClose}
        open={open}
        PaperProps={{
          sx: { width: 320 }
        }}
      >
        <Box sx={{ p: 2 }}>
          <Typography color="textPrimary" variant="h6">
            Notifications
          </Typography>
        </Box>
        {loading || notifications.nodes.length === 0 ? (
          <Box sx={{ p: 2 }}>
            <Typography color="textPrimary" variant="subtitle2">
              There are no notifications
            </Typography>
          </Box>
        ) : (
          <>
            <List disablePadding>
              {notifications.nodes.length > 0 &&
                notifications.nodes.map((notification) => (
                  <ListItem divider key={notification.id}>
                    <ListItemAvatar>
                      <Avatar
                        sx={{
                          backgroundColor: 'primary.main',
                          color: 'primary.contrastText'
                        }}
                      />
                    </ListItemAvatar>
                    <ListItemText
                      primary={
                        <Link
                          underline="hover"
                          color="textPrimary"
                          sx={{ cursor: 'pointer' }}
                          underline="hover"
                          variant="subtitle2"
                        >
                          {notification.message}
                        </Link>
                      }
                    />
                  </ListItem>
                ))}
            </List>
          </>
        )}
      </Popover>
    </>
  );
};

export default NotificationsPopover;
