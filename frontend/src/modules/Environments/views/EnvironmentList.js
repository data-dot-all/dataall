import {
  Box,
  Breadcrumbs,
  Card,
  Container,
  Grid,
  Link,
  Typography
} from '@mui/material';
import CircularProgress from '@mui/material/CircularProgress';
import { useCallback, useEffect, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { Link as RouterLink } from 'react-router-dom';
import {
  ChevronRightIcon,
  Defaults,
  Pager,
  SearchInput,
  useSettings
} from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { listEnvironments, useClient } from 'services';
import { EnvironmentListItem } from '../components';

function EnvironmentsPageHeader() {
  return (
    <Grid
      alignItems="center"
      container
      justifyContent="space-between"
      spacing={3}
    >
      <Grid item>
        <Typography color="textPrimary" variant="h5">
          Environments
        </Typography>
        <Breadcrumbs
          aria-label="breadcrumb"
          separator={<ChevronRightIcon fontSize="small" />}
          sx={{ mt: 1 }}
        >
          <Link underline="hover" color="textPrimary" variant="subtitle2">
            Organize
          </Link>
          <Link
            underline="hover"
            color="textPrimary"
            component={RouterLink}
            to="/console/environments"
            variant="subtitle2"
          >
            Environments
          </Link>
        </Breadcrumbs>
      </Grid>
    </Grid>
  );
}

const EnvironmentList = () => {
  const dispatch = useDispatch();

  const [items, setItems] = useState(Defaults.pagedResponse);
  const [filter, setFilter] = useState(Defaults.filter);
  const { settings } = useSettings();
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(true);
  const client = useClient();
  const fetchItems = useCallback(async () => {
    setLoading(true);
    const response = await client.query(listEnvironments({ filter }));
    if (!response.errors) {
      setItems(response.data.listEnvironments);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [client, dispatch, filter]);

  const handleInputChange = (event) => {
    setInputValue(event.target.value);
    setFilter({ ...filter, term: event.target.value });
  };

  const handleInputKeyup = (event) => {
    if (event.code === 'Enter') {
      setFilter({ page: 1, term: event.target.value });
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  };

  const handlePageChange = async (event, value) => {
    if (value <= items.pages && value !== items.page) {
      await setFilter({ ...filter, page: value });
    }
  };

  useEffect(() => {
    if (client) {
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, filter.page, dispatch, fetchItems]);

  return (
    <>
      <Helmet>
        <title>Environments | data.all</title>
      </Helmet>
      <Box
        sx={{
          backgroundColor: 'background.default',
          minHeight: '100%',
          py: 5
        }}
      >
        <Container maxWidth={settings.compact ? 'xl' : false}>
          <EnvironmentsPageHeader />
          <Box sx={{ mt: 3 }}>
            <Card>
              <SearchInput
                onChange={handleInputChange}
                onKeyUp={handleInputKeyup}
                value={inputValue}
              />
            </Card>
          </Box>
          <Box
            sx={{
              flexGrow: 1,
              mt: 3
            }}
          >
            {loading ? (
              <CircularProgress />
            ) : (
              <Box>
                <Grid container spacing={3}>
                  {items.nodes.map((node) => (
                    <EnvironmentListItem environment={node} />
                  ))}
                </Grid>

                <Pager items={items} onChange={handlePageChange} />
              </Box>
            )}
          </Box>
        </Container>
      </Box>
    </>
  );
};

export default EnvironmentList;
