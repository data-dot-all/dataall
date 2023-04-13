import {
  Box,
  Card,
  CardHeader,
  Chip,
  Divider,
  Grid,
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
import React, { useCallback, useEffect, useState } from 'react';
import { FaNetworkWired } from 'react-icons/fa';
import {
  Defaults,
  Label,
  Pager,
  RefreshTableMenu,
  Scrollbar,
  SearchIcon
} from '../../design';
import { SET_ERROR, useDispatch } from '../../globalErrors';
import { listEnvironmentNetworks, useClient } from '../../services';

function VpcRow({ vpc }) {
  return (
    <TableRow hover>
      <TableCell>
        {vpc.label} {vpc.default && <Label color="primary">Default</Label>}
      </TableCell>
      <TableCell>{vpc.VpcId}</TableCell>
      <TableCell>
        {vpc.privateSubnetIds && (
          <Box
            sx={{
              pb: 2,
              px: 3
            }}
          >
            {vpc.privateSubnetIds.map((subnet) => (
              <Chip
                size="small"
                sx={{ mr: 0.5 }}
                color="primary"
                key={subnet}
                label={subnet}
                variant="outlined"
              />
            ))}
          </Box>
        )}
      </TableCell>
      <TableCell>
        {vpc.publicSubnetIds && (
          <Box
            sx={{
              pb: 2,
              px: 3
            }}
          >
            {vpc.publicSubnetIds.map((subnet) => (
              <Chip
                size="small"
                sx={{ mr: 0.5 }}
                color="primary"
                key={subnet}
                label={subnet}
                variant="outlined"
              />
            ))}
          </Box>
        )}
      </TableCell>
    </TableRow>
  );
}

VpcRow.propTypes = {
  vpc: PropTypes.any
};
const EnvironmentNetworks = ({ environment }) => {
  const client = useClient();
  const dispatch = useDispatch();
  const [items, setItems] = useState(Defaults.pagedResponse);
  const [filter, setFilter] = useState(Defaults.filter);
  const [loading, setLoading] = useState(true);
  const [inputValue, setInputValue] = useState('');

  const fetchItems = useCallback(async () => {
    try {
      const response = await client.query(
        listEnvironmentNetworks({
          environmentUri: environment.environmentUri,
          filter
        })
      );
      if (!response.errors) {
        setItems({ ...response.data.listEnvironmentNetworks });
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    } finally {
      setLoading(false);
    }
  }, [client, dispatch, environment, filter]);

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

  return (
    <Box>
      <Card>
        <CardHeader
          action={<RefreshTableMenu refresh={fetchItems} />}
          title={
            <Box>
              <FaNetworkWired style={{ marginRight: '10px' }} /> Networks
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
          <Grid item md={2} sm={6} xs={12} />
        </Box>
        <Scrollbar>
          <Box sx={{ minWidth: 600 }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Vpc ID</TableCell>
                  <TableCell>Private Subnets</TableCell>
                  <TableCell>Public Subnets</TableCell>
                </TableRow>
              </TableHead>
              {loading ? (
                <CircularProgress sx={{ mt: 1 }} />
              ) : (
                <TableBody>
                  {items.nodes.length > 0 ? (
                    items.nodes.map((vpc) => (
                      <VpcRow
                        vpc={vpc}
                        environment={environment}
                        fetchItems={fetchItems}
                      />
                    ))
                  ) : (
                    <TableRow hover>
                      <TableCell>No VPC found</TableCell>
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
    </Box>
  );
};

EnvironmentNetworks.propTypes = {
  environment: PropTypes.object.isRequired
};

export default EnvironmentNetworks;
