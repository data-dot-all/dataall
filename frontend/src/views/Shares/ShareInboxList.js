import { useCallback, useEffect, useState } from 'react';
import { Box, Container, Typography } from '@mui/material';
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

const ShareInboxList = (props) => {
  const { dataset } = props;
  const dispatch = useDispatch();
  const [items, setItems] = useState(Defaults.PagedResponseDefault);
  const [filter, setFilter] = useState(Defaults.DefaultFilter);
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

  useEffect(() => {
    if (client) {
      fetchItems().catch((error) => {
        dispatch({ type: SET_ERROR, error: error.message });
      });
    }
  }, [client, filter.page, dispatch, fetchItems]);

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
      </Box>
    </>
  );
};

ShareInboxList.propTypes = {
  dataset: PropTypes.object
};

export default ShareInboxList;
