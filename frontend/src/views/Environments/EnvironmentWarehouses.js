import { CloudDownloadOutlined } from '@mui/icons-material';
import {
  Box,
  Button,
  Card,
  CardHeader,
  Divider,
  Grid,
  IconButton,
  InputAdornment,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField
} from '@mui/material';
import CircularProgress from '@mui/material/CircularProgress';
import PropTypes from 'prop-types';
import { useCallback, useEffect, useState } from 'react';
import { GoDatabase } from 'react-icons/go';
import { useNavigate } from 'react-router';
import { Link as RouterLink } from 'react-router-dom';
import { listEnvironmentClusters } from '../../api';
import {
  Defaults,
  Pager,
  RefreshTableMenu,
  Scrollbar,
  StackStatus
} from '../../components';
import { SET_ERROR, useDispatch } from '../../globalErrors';
import { useClient } from '../../hooks';
import { ArrowRightIcon, PlusIcon, SearchIcon } from '../../icons';

const EnvironmentWarehouses = ({ environment }) => {
  const client = useClient();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [items, setItems] = useState(Defaults.pagedResponse);
  const [filter, setFilter] = useState(Defaults.filter);
  const [loading, setLoading] = useState(null);
  const [inputValue, setInputValue] = useState('');

  const fetchItems = useCallback(async () => {
    try {
      const response = await client.query(
        listEnvironmentClusters(environment.environmentUri, filter)
      );
      if (!response.errors) {
        setItems({ ...response.data.listEnvironmentClusters });
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    } finally {
      setLoading(false);
    }
  }, [client, dispatch, filter, environment]);

  useEffect(() => {
    if (client) {
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, filter.page, dispatch, fetchItems]);

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

  return (
    <Card>
      <CardHeader
        action={<RefreshTableMenu refresh={fetchItems} />}
        title={
          <Box>
            <GoDatabase style={{ marginRight: '10px' }} /> Redshift Clusters
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
              placeholder="SearchIcon"
              value={inputValue}
              variant="outlined"
            />
          </Box>
        </Grid>
        <Grid item md={2} sm={6} xs={12}>
          <Button
            color="primary"
            component={RouterLink}
            startIcon={<CloudDownloadOutlined fontSize="small" />}
            sx={{ m: 1 }}
            to={`/console/environments/${environment.environmentUri}/warehouses/import`}
            variant="outlined"
          >
            Import
          </Button>
          <Button
            color="primary"
            component={RouterLink}
            startIcon={<PlusIcon fontSize="small" />}
            sx={{ m: 1 }}
            to={`/console/environments/${environment.environmentUri}/warehouses/new`}
            variant="contained"
          >
            Create
          </Button>
        </Grid>
      </Box>
      <Scrollbar>
        <Box sx={{ minWidth: 600 }}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Endpoint</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            {loading ? (
              <CircularProgress sx={{ mt: 1 }} />
            ) : (
              <TableBody>
                {items.nodes.length > 0 ? (
                  items.nodes.map((warehouse) => (
                    <TableRow hover key={warehouse.clusterUri}>
                      <TableCell>{warehouse.label}</TableCell>
                      <TableCell>{warehouse.endpoint}</TableCell>
                      <TableCell>
                        <StackStatus status={warehouse.stack?.status} />
                      </TableCell>
                      <TableCell>
                        <IconButton
                          onClick={() => {
                            navigate(
                              `/console/warehouse/${warehouse.clusterUri}`
                            );
                          }}
                        >
                          <ArrowRightIcon fontSize="small" />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow hover>
                    <TableCell>No Redshift cluster found</TableCell>
                  </TableRow>
                )}
              </TableBody>
            )}
          </Table>
          {!loading && items.nodes.length > 0 && (
            <Pager
              mgTop={2}
              mgBottom={2}
              items={items}
              onChange={handlePageChange}
            />
          )}
        </Box>
      </Scrollbar>
    </Card>
  );
};

EnvironmentWarehouses.propTypes = {
  environment: PropTypes.object.isRequired
};

export default EnvironmentWarehouses;
