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
import PropTypes from 'prop-types';
import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router';
import {
  ArrowRightIcon,
  Defaults,
  Pager,
  RefreshTableMenu,
  Scrollbar,
  SearchIcon
} from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import { searchEnvironmentDataItems } from '../services';

export const EnvironmentSharedDatasets = ({ environment }) => {
  const client = useClient();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [items, setItems] = useState(Defaults.pagedResponse);
  const [filter, setFilter] = useState(Defaults.filter);
  const [loading, setLoading] = useState(null);
  const [inputValue, setInputValue] = useState('');

  const fetchItems = useCallback(async () => {
    const response = await client.query(
      searchEnvironmentDataItems({
        filter,
        environmentUri: environment.environmentUri
      })
    );
    if (!response.errors) {
      setItems({ ...response.data.searchEnvironmentDataItems });
    }
    setLoading(false);
  }, [client, environment, filter]);

  useEffect(() => {
    if (client) {
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, filter.page, fetchItems, dispatch]);

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
        title="Data Shared With You"
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
                <TableCell>Type</TableCell>
                <TableCell>Name</TableCell>
                <TableCell>Dataset</TableCell>
                <TableCell>Environment</TableCell>
                <TableCell>Shared with Team</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            {loading ? (
              <CircularProgress sx={{ mt: 1 }} />
            ) : (
              <TableBody>
                {items.nodes.length > 0 ? (
                  items.nodes.map((item) => (
                    <TableRow hover key={item.itemUri}>
                      <TableCell>{item.itemType}</TableCell>
                      <TableCell>{item.itemName}</TableCell>
                      <TableCell>{item.datasetName}</TableCell>
                      <TableCell>{item.environmentName}</TableCell>
                      <TableCell>{item.principalId}</TableCell>
                      <TableCell>
                        <IconButton
                          onClick={() => {
                            navigate(`/console/s3-datasets/${item.datasetUri}`);
                          }}
                        >
                          <ArrowRightIcon fontSize="small" />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow hover>
                    <TableCell>No datasets found</TableCell>
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

EnvironmentSharedDatasets.propTypes = {
  environment: PropTypes.object.isRequired
};
