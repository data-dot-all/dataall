import { Box, Container, Typography } from '@mui/material';
import CircularProgress from '@mui/material/CircularProgress';
import { useCallback, useEffect, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { Defaults, Pager, useSettings } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import { getShareRequestsFromMe } from '../services';
import { ShareOutboxListItem } from '../components';

export const ShareOutboxList = () => {
  const dispatch = useDispatch();
  const [items, setItems] = useState(Defaults.pagedResponse);
  const [filter, setFilter] = useState(Defaults.filter);
  const { settings } = useSettings();
  const [loading, setLoading] = useState(true);
  const client = useClient();
  const fetchItems = useCallback(async () => {
    setLoading(true);
    const response = await client.query(
      getShareRequestsFromMe({
        filter: {
          ...filter
        }
      })
    );
    if (!response.errors) {
      setItems(response.data.getShareRequestsFromMe);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [client, dispatch, filter]);

  const handlePageChange = async (event, value) => {
    if (value <= items.pages && value !== items.page) {
      await setFilter({ ...filter, page: value });
    }
  };

  useEffect(() => {
    if (client) {
      fetchItems().catch((error) => {
        dispatch({ type: SET_ERROR, error: error.message });
      });
    }
  }, [client, filter.page, fetchItems, dispatch]);

  if (loading) {
    return <CircularProgress />;
  }

  return (
    <>
      <Helmet>
        <title>Share Requests Sent | data.all</title>
      </Helmet>
      <Box
        sx={{
          backgroundColor: 'background.default',
          minHeight: '100%',
          py: 1
        }}
      >
        <Container maxWidth={settings.compact ? 'xl' : false}>
          <Box
            sx={{
              flexGrow: 1,
              mt: 3
            }}
          >
            {items.nodes.length <= 0 ? (
              <Typography color="textPrimary" variant="subtitle2">
                No share requests sent.
              </Typography>
            ) : (
              <Box>
                {items.nodes.map((node) => (
                  <ShareOutboxListItem share={node} reload={fetchItems} />
                ))}

                <Pager items={items} onChange={handlePageChange} />
              </Box>
            )}
          </Box>
        </Container>
      </Box>
    </>
  );
};
