import { useCallback, useEffect, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Breadcrumbs,
  Button,
  Card,
  Container,
  Grid,
  Input,
  Link,
  Pagination,
  Typography
} from '@mui/material';
import CircularProgress from '@mui/material/CircularProgress';
import { Helmet } from 'react-helmet-async';
import useClient from '../../hooks/useClient';
import * as Defaults from '../../components/defaults';
import listOrganizations from '../../api/Organization/listOrganizations';
import SearchIcon from '../../icons/Search';
import ChevronRightIcon from '../../icons/ChevronRight';
import PlusIcon from '../../icons/Plus';
import useSettings from '../../hooks/useSettings';
import OrganizationListItem from './OrganizationListItem';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';

const OrganizationList = () => {
  const [items, setItems] = useState(Defaults.PagedResponseDefault);
  const [filter, setFilter] = useState(Defaults.DefaultFilter);
  const { settings } = useSettings();
  const dispatch = useDispatch();
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(true);
  const client = useClient();
  const fetchItems = useCallback(async () => {
    setLoading(true);
    const response = await client.query(listOrganizations({filter}));
    if (!response.errors) {
      setItems(response.data.listOrganizations);
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
  }, [client, filter.page, fetchItems, dispatch]);

  return (
    <>
      <Helmet>
        <title>Organizations | data.all</title>
      </Helmet>
      <Box
        sx={{
          backgroundColor: 'background.default',
          minHeight: '100%',
          py: 5
        }}
      >
        <Container maxWidth={settings.compact ? 'xl' : false}>
          <Grid
            alignItems="center"
            container
            justifyContent="space-between"
            spacing={3}
          >
            <Grid item>
              <Typography color="textPrimary" variant="h5">
                Organizations
              </Typography>
              <Breadcrumbs
                aria-label="breadcrumb"
                separator={<ChevronRightIcon fontSize="small" />}
                sx={{ mt: 1 }}
              >
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to="/console"
                  variant="subtitle2"
                >
                  Admin
                </Link>
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to="/console/organizations"
                  variant="subtitle2"
                >
                  Organizations
                </Link>
              </Breadcrumbs>
            </Grid>
            <Grid item>
              <Box sx={{ m: -1 }}>
                <Button
                  color="primary"
                  component={RouterLink}
                  startIcon={<PlusIcon fontSize="small" />}
                  sx={{ m: 1 }}
                  to="/console/organizations/new"
                  variant="contained"
                >
                  Create
                </Button>
              </Box>
            </Grid>
          </Grid>

          <Box sx={{ mt: 3 }}>
            <Card>
              <Box
                sx={{
                  alignItems: 'center',
                  display: 'flex',
                  p: 2
                }}
              >
                <SearchIcon fontSize="small" />
                <Box
                  sx={{
                    flexGrow: 1,
                    ml: 3
                  }}
                >
                  <Input
                    disableUnderline
                    fullWidth
                    onChange={handleInputChange}
                    onKeyUp={handleInputKeyup}
                    placeholder="Search"
                    value={inputValue}
                  />
                </Box>
              </Box>
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
                    <OrganizationListItem
                      key={node.organizationUri}
                      organization={node}
                    />
                  ))}
                </Grid>

                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'center',
                    mt: 6
                  }}
                >
                  <Pagination
                    count={items.pages}
                    page={items.page}
                    onChange={handlePageChange}
                  />
                </Box>
              </Box>
            )}
          </Box>
        </Container>
      </Box>
    </>
  );
};

export default OrganizationList;
