import {
  Box,
  CircularProgress,
  Divider,
  Drawer,
  Link,
  Typography
} from '@mui/material';
import { useTheme } from '@mui/styles';
import PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { Defaults, Label, Scrollbar, TextAvatar } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { listFeedMessages, useClient } from 'services';
import { dayjs } from 'utils';
import { FeedCommentAdd } from './FeedCommentAdd';

export const FeedComments = (props) => {
  const { targetUri, targetType, objectOwner, open, onClose } = props;
  const dispatch = useDispatch();
  const client = useClient();
  const theme = useTheme();
  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState(Defaults.pagedResponse);
  const [filter] = useState(Defaults.selectListFilter);
  const fetchItems = useCallback(async () => {
    setLoading(true);
    const response = await client.query(
      listFeedMessages({ targetType, targetUri, filter })
    );
    if (!response.errors) {
      setItems(response.data.getFeed.messages);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [client, dispatch, filter, targetUri, targetType]);

  useEffect(() => {
    if (client) {
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, filter.page, dispatch, fetchItems]);

  return (
    <>
      <Drawer
        anchor="right"
        onClose={onClose}
        open={open}
        style={{ zIndex: 1250 }}
        PaperProps={{
          sx: {
            width: 420
          }
        }}
      >
        <Box sx={{ p: 2 }}>
          <Typography color="textPrimary" variant="h5">
            Chat
          </Typography>
        </Box>
        <Divider sx={{ mb: 2 }} />
        {items.nodes && items.nodes.length > 0 ? (
          <Box sx={{ p: 1 }}>
            <Scrollbar>
              {loading ? (
                <CircularProgress size={40} />
              ) : (
                <Box>
                  {items.nodes.map((message) => (
                    <Box>
                      <Box
                        sx={{
                          display: 'flex',
                          mb: 2
                        }}
                      >
                        <TextAvatar name={message.creator} />
                        <Box
                          sx={{
                            backgroundColor:
                              theme.palette.mode !== 'dark'
                                ? '#F4F5F7'
                                : 'background.default',
                            borderRadius: 1,
                            flexGrow: 1,
                            ml: 2,
                            p: 2
                          }}
                        >
                          <Box
                            sx={{
                              alignItems: 'center',
                              display: 'flex',
                              mb: 1
                            }}
                          >
                            <Link
                              underline="hover"
                              color="textPrimary"
                              component={RouterLink}
                              to="#"
                              variant="subtitle2"
                              sx={{ mr: 1 }}
                            >
                              {message.creator}{' '}
                            </Link>
                            <span>
                              {message.creator === objectOwner && (
                                <Label color="primary">Owner</Label>
                              )}
                            </span>
                            <Box sx={{ flexGrow: 1 }} />
                            <Typography color="textSecondary" variant="caption">
                              {dayjs(message.created).fromNow()}
                            </Typography>
                          </Box>
                          <Typography color="textPrimary" variant="body2">
                            {message.content}
                          </Typography>
                        </Box>
                      </Box>
                    </Box>
                  ))}
                </Box>
              )}
            </Scrollbar>
          </Box>
        ) : (
          <Box sx={{ p: 2 }}>
            <Typography color="textPrimary" variant="subtitle2">
              No messages published.
            </Typography>
          </Box>
        )}
        <Box
          sx={{
            backgroundColor: 'background.default',
            flexGrow: 1
          }}
        />
        <Divider sx={{ mb: 2 }} />
        <FeedCommentAdd
          targetUri={targetUri}
          targetType={targetType}
          reloadMessages={fetchItems}
        />
      </Drawer>
    </>
  );
};
FeedComments.propTypes = {
  targetUri: PropTypes.string.isRequired,
  targetType: PropTypes.string.isRequired,
  objectOwner: PropTypes.string,
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired
};
