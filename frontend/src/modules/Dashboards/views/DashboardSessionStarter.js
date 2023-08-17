import { ArrowLeft, ArrowRightAlt, ChevronRight } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import {
  Box,
  Breadcrumbs,
  Button,
  Card,
  CardHeader,
  Container,
  Divider,
  Grid,
  InputAdornment,
  Link,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography
} from '@mui/material';
import CircularProgress from '@mui/material/CircularProgress';
import * as PropTypes from 'prop-types';
import { useCallback, useEffect, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { BsCloud } from 'react-icons/bs';
import { Link as RouterLink } from 'react-router-dom';
import { Defaults, Pager, Scrollbar, SearchIcon, useSettings } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { listEnvironments, useClient } from 'services';
import { getAuthorSession } from '../services';

function DashboardSessionStarterPageHeader() {
  return (
    <Grid
      alignItems="center"
      container
      justifyContent="space-between"
      spacing={3}
    >
      <Grid item>
        <Typography color="textPrimary" variant="h5">
          Start QuickSight session
        </Typography>
        <Breadcrumbs
          aria-label="breadcrumb"
          separator={<ChevronRight fontSize="small" />}
          sx={{ mt: 1 }}
        >
          <Typography color="textPrimary" variant="subtitle2">
            Play
          </Typography>
          <Link
            underline="hover"
            color="textPrimary"
            component={RouterLink}
            to="/console/dashboards"
            variant="subtitle2"
          >
            Dashboards
          </Link>
          <Typography color="textPrimary" variant="subtitle2">
            Start session
          </Typography>
        </Breadcrumbs>
      </Grid>
      <Grid item>
        <Box sx={{ m: -1 }}>
          <Button
            color="primary"
            component={RouterLink}
            startIcon={<ArrowLeft fontSize="small" />}
            sx={{ mt: 1 }}
            to="/console/dashboards"
            variant="outlined"
          >
            Cancel
          </Button>
        </Box>
      </Grid>
    </Grid>
  );
}

function EnvironmentRow({ env, client, dispatch }) {
  const [isOpeningSession, setIsOpeningSession] = useState(false);

  const startQSSession = async () => {
    setIsOpeningSession(true);
    const response = await client.query(getAuthorSession(env.environmentUri));
    if (!response.errors) {
      window.open(response.data.getAuthorSession, '_blank');
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setIsOpeningSession(false);
  };
  return (
    <TableRow hover>
      <TableCell>{env.label}</TableCell>
      <TableCell>{env.AwsAccountId}</TableCell>
      <TableCell>{env.region}</TableCell>
      <TableCell>
        <LoadingButton
          loading={isOpeningSession}
          color="primary"
          endIcon={<ArrowRightAlt fontSize="small" />}
          variant="outlined"
          onClick={startQSSession}
        >
          Start session
        </LoadingButton>
      </TableCell>
    </TableRow>
  );
}

EnvironmentRow.propTypes = {
  env: PropTypes.object.isRequired,
  dispatch: PropTypes.object.isRequired,
  client: PropTypes.object.isRequired
};
const DashboardSessionStarter = () => {
  const [items, setItems] = useState(Defaults.pagedResponse);
  const dispatch = useDispatch();
  const [loading, setLoading] = useState(true);
  const client = useClient();
  const { settings } = useSettings();
  const [inputValue, setInputValue] = useState('');
  const [filter, setFilter] = useState({
    page: 1,
    pageSize: 10,
    term: ''
  });

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
    setFilter({
      ...filter,
      roles: ['Admin', 'Owner', 'Invited', 'DatasetCreator'],
      term: event.target.value
    });
  };

  const handleInputKeyup = (event) => {
    if (event.code === 'Enter') {
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
  }, [client, dispatch, fetchItems]);

  return (
    <>
      <Helmet>
        <title>Dashboards: QuickSight Session | data.all</title>
      </Helmet>
      <Box
        sx={{
          backgroundColor: 'background.default',
          minHeight: '100%',
          py: 8
        }}
      >
        <Container maxWidth={settings.compact ? 'xl' : false}>
          <DashboardSessionStarterPageHeader />
          <Box sx={{ mt: 3 }}>
            <Card>
              <CardHeader
                title={
                  <Box>
                    <BsCloud style={{ marginRight: '10px' }} />
                    Environments
                  </Box>
                }
              />
              <Divider />
              <Box
                sx={{
                  alignItems: 'center',
                  display: 'flex',
                  flexWrap: 'wrap',
                  m: -1,
                  p: 2
                }}
              >
                <Grid item md={10} sm={6} xs={12}>
                  <Box
                    sx={{
                      m: 1,
                      maxWidth: '100%',
                      width: 500
                    }}
                  >
                    <TextField
                      fullWidth
                      InputProps={{
                        startAdornment: (
                          <InputAdornment position="start">
                            <SearchIcon fontSize="small" />
                          </InputAdornment>
                        )
                      }}
                      onChange={handleInputChange}
                      onKeyUp={handleInputKeyup}
                      placeholder="Search"
                      value={inputValue}
                      variant="outlined"
                    />
                  </Box>
                </Grid>
              </Box>
              <Scrollbar>
                <Box sx={{ minWidth: 600 }}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Environment</TableCell>
                        <TableCell>AWS Account</TableCell>
                        <TableCell>Region</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    {loading ? (
                      <CircularProgress sx={{ mt: 1 }} />
                    ) : (
                      <TableBody>
                        {items && items.nodes && items.nodes.length > 0 ? (
                          items.nodes.map((env) => (
                            <EnvironmentRow
                              key={env.environmentUri}
                              env={env}
                              client={client}
                              dispatch={dispatch}
                            />
                          ))
                        ) : (
                          <TableRow hover>
                            <TableCell>No environments found</TableCell>
                          </TableRow>
                        )}
                      </TableBody>
                    )}
                  </Table>
                  <Pager
                    mgTop={2}
                    mgBottom={2}
                    items={items}
                    onChange={handlePageChange}
                  />
                </Box>
              </Scrollbar>
            </Card>
          </Box>
        </Container>
      </Box>
    </>
  );
};

export default DashboardSessionStarter;
