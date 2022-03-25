import PropTypes from 'prop-types';
import { useEffect, useState } from 'react';
import * as SiIcon from 'react-icons/si';
import {
  Box,
  Card,
  CardHeader,
  Divider,
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
import { useNavigate } from 'react-router';
import { LoadingButton } from '@mui/lab';
import useClient from '../../hooks/useClient';
import * as Defaults from '../../components/defaults';
import SearchIcon from '../../icons/Search';
import Scrollbar from '../../components/Scrollbar';
import StackStatus from '../../components/StackStatus';
import ArrowRightIcon from '../../icons/ArrowRight';
import RefreshTableMenu from '../../components/RefreshTableMenu';
import listEnvironmentAirflowClusters from '../../api/AirflowCluster/listEnvironmentAirflowClusters';
import getAirflowClusterWebLoginToken from '../../api/AirflowCluster/getAirflowUIAccess';
import ExternalLink from '../../icons/ExternalLink';
import { useDispatch } from '../../store';
import { SET_ERROR } from '../../store/errorReducer';
import Pager from '../../components/Pager';

const EnvironmentWorkflows = ({ environment }) => {
  const client = useClient();
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const [items, setItems] = useState(Defaults.PagedResponseDefault);
  const [filter, setFilter] = useState(Defaults.DefaultFilter);
  const [loading, setLoading] = useState(null);
  const [isLoadingUI, setIsLoadingUI] = useState(false);
  const [inputValue, setInputValue] = useState('');

  const fetchItems = async () => {
    setLoading(true);
    try {
      const response = await client.query(
        listEnvironmentAirflowClusters(environment.environmentUri, filter)
      );
      if (!response.errors) {
        setItems({ ...response.data.listEnvironmentAirflowClusters });
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
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, filter.page]);

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
  const goToAirflowUI = async (item) => {
    setIsLoadingUI(true);
    const response = await client.query(
      getAirflowClusterWebLoginToken(item.clusterUri)
    );
    if (!response.errors) {
      window.open(response.data.getAirflowClusterConsoleAccess, '_blank');
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setIsLoadingUI(false);
  };

  return (
    <Card>
      <CardHeader
        action={<RefreshTableMenu refresh={fetchItems} />}
        title={
          <Box>
            <SiIcon.SiApacheairflow style={{ marginRight: '10px' }} /> Airflow
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
      </Box>
      <Scrollbar>
        <Box sx={{ minWidth: 600 }}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Airflow UI</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            {loading ? (
              <CircularProgress sx={{ mt: 1 }} />
            ) : (
              <TableBody>
                {items.nodes.length > 0 ? (
                  items.nodes.map((workflow) => (
                    <TableRow hover key={workflow.clusterUri}>
                      <TableCell>{workflow.label}</TableCell>
                      <TableCell>
                        {workflow.webServerUrl ? (
                          <LoadingButton
                            loading={isLoadingUI}
                            color="primary"
                            onClick={() => goToAirflowUI(workflow)}
                          >
                            {workflow.webServerUrl} <ExternalLink />
                          </LoadingButton>
                        ) : (
                          <span>-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <StackStatus status={workflow.stack?.status} />
                      </TableCell>
                      <TableCell>
                        <IconButton
                          onClick={() => {
                            navigate(
                              `/console/workflows/${workflow.clusterUri}`
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
                    <TableCell>No Airflow environment found</TableCell>
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

EnvironmentWorkflows.propTypes = {
  environment: PropTypes.object.isRequired
};

export default EnvironmentWorkflows;
