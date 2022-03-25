import { useEffect, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
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
import { Helmet } from 'react-helmet-async';
import useClient from '../../hooks/useClient';
import * as Defaults from '../../components/defaults';
import ChevronRightIcon from '../../icons/ChevronRight';
import useSettings from '../../hooks/useSettings';
import listEnvironments from '../../api/Environment/listEnvironments';
import SearchInput from '../../components/SearchInput';
import Pager from '../../components/Pager';
import EnvironmentListItem from './EnvironmentListItem';
import { useDispatch } from '../../store';
import { SET_ERROR } from '../../store/errorReducer';

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

  const [items, setItems] = useState(Defaults.PagedResponseDefault);
  const [filter, setFilter] = useState(Defaults.DefaultFilter);
  const { settings } = useSettings();
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(true);
  const client = useClient();
  const fetchItems = async () => {
    setLoading(true);
    await client
      .query(
        listEnvironments({
          filter: {
            ...filter
          }
        })
      )
      .then((response) => {
        const nodes = response.data.listEnvironments.nodes.map((env) => ({
          ...env
        }));
        setItems({ ...items, ...response.data.listEnvironments, nodes });
      })
      .catch((error) => {
        dispatch({ type: SET_ERROR, error: error.Error });
      })
      .finally(() => setLoading(false));
  };

  const handleInputChange = (event) => {
    setInputValue(event.target.value);
    setFilter({ ...filter, term: event.target.value });
  };

  const handleInputKeyup = (event) => {
    if (event.code === 'Enter') {
      fetchItems();
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
  }, [client, filter.page]);

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
