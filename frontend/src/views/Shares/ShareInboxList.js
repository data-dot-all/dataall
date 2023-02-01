import { useCallback, useEffect, useState } from 'react';
import { Box, Container, Typography, Divider } from '@mui/material';
import CircularProgress from '@mui/material/CircularProgress';
import { Helmet } from 'react-helmet-async';
import PropTypes from 'prop-types';
import useClient from '../../hooks/useClient';
import * as Defaults from '../../components/defaults';
import useSettings from '../../hooks/useSettings';
import Pager from '../../components/Pager';
import ShareInboxListItem from './ShareInboxListItem';
import { useDispatch } from '../../store';
import { SET_ERROR } from '../../store/errorReducer';
import getShareRequestsToMe from '../../api/ShareObject/getShareRequestsToMe';
import listDatasetShareObjects from '../../api/Dataset/listShareObjects';
import getLFTagShareRequestsToMe from '../../api/ShareObject/getLFTagShareRequestsToMe';
import ShareInboxListLFTagItem from './ShareInboxListLFTagItem';

const ShareInboxList = (props) => {
  const { dataset } = props;
  const dispatch = useDispatch();
  const [items, setItems] = useState(Defaults.PagedResponseDefault);
  const [filter, setFilter] = useState(Defaults.DefaultFilter);
  const [lftagItems, setLFTagItems] = useState(Defaults.PagedResponseDefault);
  const { settings } = useSettings();
  const [loading, setLoading] = useState(true);
  const client = useClient();
  const fetchItems = useCallback(async () => {
    if (dataset) {
      await client
        .query(
          listDatasetShareObjects({ datasetUri: dataset.datasetUri, filter })
        )
        .then((response) => {
          setItems(response.data.getDataset.shares);
        })
        .catch((error) => {
          dispatch({ type: SET_ERROR, error: error.Error });
        })
        .finally(() => setLoading(false));
    } else {
      await client
        .query(
          getShareRequestsToMe({
            filter: {
              ...filter
            }
          })
        )
        .then((response) => {
          setItems(response.data.getShareRequestsToMe);
        })
        .catch((error) => {
          dispatch({ type: SET_ERROR, error: error.Error });
        })
        .finally(() => setLoading(false));
    }
  }, [client, dispatch, dataset, filter]);

  const handlePageChange = async (event, value) => {
    if (value <= items.pages && value !== items.page) {
      await setFilter({ ...filter, page: value });
    }
  };

  const fetchLFTagItems = useCallback(async () => {
    setLoading(true);
    const lftag_response = await client.query(
      getLFTagShareRequestsToMe({
        filter: {
          ...filter
        }
      })
    );
    if (!lftag_response.errors) {
      setLFTagItems(lftag_response.data.getLFTagShareRequestsToMe)
    } else {
      dispatch({ type: SET_ERROR, error: lftag_response.errors[0].message });
    }
    setLoading(false);
  }, [client, dispatch, filter]);

  useEffect(() => {
    if (client) {
      fetchItems().catch((error) => {
        dispatch({ type: SET_ERROR, error: error.message });
      });
      if (!dataset) {
        fetchLFTagItems().catch((error) => {
          dispatch({ type: SET_ERROR, error: error.message });
        });
      }
    }
  }, [client, filter.page, dispatch]);

  if (loading) {
    return <CircularProgress />;
  }

  return (
    <>
      <Helmet>
        <title>Shares Inbox | data.all</title>
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
              mt: 3
            }}
          >
            {items.nodes.length <= 0 ? (
              <Typography color="textPrimary" variant="subtitle2">
                No share requests received.
              </Typography>
            ) : (
              <Box>
                {items.nodes.map((node) => (
                  <ShareInboxListItem share={node} reload={fetchItems} />
                ))}

                <Pager items={items} onChange={handlePageChange} />
              </Box>
            )}
          </Box>
        </Container>
        <Divider />
        {!dataset &&
          <Container maxWidth={settings.compact ? 'xl' : false}>
            <Box
              sx={{
                flexGrow: 1,
                mt: 3
              }}
            >
              <Typography variant="h5" gutterBottom>
                LF Tag Share Requests
              </Typography>
              {lftagItems.nodes.length <= 0 ? (
                <Typography color="textPrimary" variant="subtitle2">
                  No LF Tag share requests sent.
                </Typography>
              ) : (
                <Box>
                  {lftagItems.nodes.map((node) => (
                    <ShareInboxListLFTagItem share={node} reload={fetchLFTagItems} />
                  ))}

                  <Pager items={lftagItems} onChange={handlePageChange} />
                </Box>
              )}
            </Box>
          </Container>
        }
      </Box>
    </>
  );
};

ShareInboxList.propTypes = {
  dataset: PropTypes.object
};

export default ShareInboxList;
