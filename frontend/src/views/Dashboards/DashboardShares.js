import { useEffect, useState } from 'react';
import { Box, Container, Typography } from '@mui/material';
import CircularProgress from '@mui/material/CircularProgress';
import { Helmet } from 'react-helmet-async';
import PropTypes from 'prop-types';
import useClient from '../../hooks/useClient';
import * as Defaults from '../../components/defaults';
import useSettings from '../../hooks/useSettings';
import Pager from '../../components/Pager';
import { useDispatch } from '../../store';
import { SET_ERROR } from '../../store/errorReducer';
import listDashboardShares from '../../api/Dashboard/listDashboardShares';
import DashboardShareItem from './DashboardShareItem';

const DashboardShares = (props) => {
  const { dashboard } = props;
  const dispatch = useDispatch();
  const [items, setItems] = useState(Defaults.PagedResponseDefault);
  const [filter, setFilter] = useState(Defaults.DefaultFilter);
  const { settings } = useSettings();
  const [loading, setLoading] = useState(true);
  const client = useClient();
  const fetchItems = async () => {
    setLoading(true);
    const response = await client.query(
      listDashboardShares({ dashboardUri: dashboard.dashboardUri, filter })
    );
    if (!response.errors) {
      setItems(response.data.listDashboardShares);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  };

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
  }, [client, filter.page]);

  if (loading) {
    return <CircularProgress />;
  }

  return (
    <>
      <Helmet>
        <title>Dashboard Sahres | data.all</title>
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
                No shares found.
              </Typography>
            ) : (
              <Box>
                {items.nodes.map((node) => (
                  <DashboardShareItem
                    share={node}
                    dashboard={dashboard}
                    reload={fetchItems}
                  />
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

DashboardShares.propTypes = {
  dashboard: PropTypes.object
};

export default DashboardShares;
