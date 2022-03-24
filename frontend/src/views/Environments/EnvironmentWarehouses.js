import PropTypes from 'prop-types';
import { useEffect, useState } from 'react';
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
} from '@material-ui/core';
import CircularProgress from '@material-ui/core/CircularProgress';
import { useNavigate } from 'react-router';
import { CloudDownloadOutlined } from '@material-ui/icons';
import { Link as RouterLink } from 'react-router-dom';
import { GoDatabase } from 'react-icons/all';
import useClient from '../../hooks/useClient';
import * as Defaults from '../../components/defaults';
import SearchIcon from '../../icons/Search';
import Scrollbar from '../../components/Scrollbar';
import StackStatus from '../../components/StackStatus';
import ArrowRightIcon from '../../icons/ArrowRight';
import RefreshTableMenu from '../../components/RefreshTableMenu';
import listEnvironmentClusters from '../../api/RedshiftCluster/listEnvironmentClusters';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import Pager from '../../components/Pager';
import PlusIcon from '../../icons/Plus';

const EnvironmentWarehouses = ({ environment }) => {
  const client = useClient();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [items, setItems] = useState(Defaults.PagedResponseDefault);
  const [filter, setFilter] = useState(Defaults.DefaultFilter);
  const [loading, setLoading] = useState(null);
  const [inputValue, setInputValue] = useState('');

  const fetchItems = async () => {
    try {
      const response = await client.query(listEnvironmentClusters(environment.environmentUri, filter));
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
  };

  useEffect(() => {
    if (client) {
      fetchItems().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client, filter.page]);

  const handleInputChange = (event) => {
    setInputValue(event.target.value);
    setFilter({ ...filter, term: event.target.value });
  };

  const handleInputKeyup = (event) => {
    if ((event.code === 'Enter')) {
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
        title={(
          <Box>
            <GoDatabase style={{ marginRight: '10px' }} />
            {' '}
            Redshift Clusters
          </Box>
)}
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
        <Grid
          item
          md={10}
          sm={6}
          xs={12}
        >
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
        <Grid
          item
          md={2}
          sm={6}
          xs={12}
        >
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
                <TableCell>
                  Name
                </TableCell>
                <TableCell>
                  Endpoint
                </TableCell>
                <TableCell>
                  Status
                </TableCell>
                <TableCell>
                  Actions
                </TableCell>
              </TableRow>
            </TableHead>
            {loading ? <CircularProgress sx={{ mt: 1 }} /> : (
              <TableBody>
                {items.nodes.length > 0 ? items.nodes.map((warehouse) => (
                  <TableRow
                    hover
                    key={warehouse.clusterUri}
                  >
                    <TableCell>
                      {warehouse.label}
                    </TableCell>
                    <TableCell>
                      {warehouse.endpoint}
                    </TableCell>
                    <TableCell>
                      <StackStatus status={(warehouse.stack?.status)} />
                    </TableCell>
                    <TableCell>
                      <IconButton onClick={() => { navigate(`/console/warehouse/${warehouse.clusterUri}`); }}>
                        <ArrowRightIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                )) : (
                  <TableRow
                    hover
                  >
                    <TableCell>
                      No Redshift cluster found
                    </TableCell>
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
