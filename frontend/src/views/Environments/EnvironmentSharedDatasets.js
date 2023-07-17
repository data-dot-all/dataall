import PropTypes from 'prop-types';
import { useCallback, useEffect, useState } from 'react';
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
import useClient from '../../hooks/useClient';
import * as Defaults from '../../components/defaults';
import SearchIcon from '../../icons/Search';
import Scrollbar from '../../components/Scrollbar';
import ArrowRightIcon from '../../icons/ArrowRight';
import listDatasetsPublishedInEnvironment from '../../api/Environment/listDatasetsPublishedInEnvironment';
import RefreshTableMenu from '../../components/RefreshTableMenu';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import Pager from '../../components/Pager';

const EnvironmentOwnedDatasets = ({ environment }) => {
  const client = useClient();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [items, setItems] = useState(Defaults.PagedResponseDefault);
  const [filter, setFilter] = useState(Defaults.DefaultFilter);
  const [loading, setLoading] = useState(null);
  const [inputValue, setInputValue] = useState('');

  const fetchItems = useCallback(async () => {
    const response = await client.query(
      listDatasetsPublishedInEnvironment({
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
                      <TableCell>
                        {item.GlueTableName ? 'Table' : 'Folder'}
                      </TableCell>
                      <TableCell>
                        {item.GlueTableName || item.S3AccessPointName}
                      </TableCell>
                      <TableCell>{item.datasetName}</TableCell>
                      <TableCell>{item.environmentName}</TableCell>
                      <TableCell>{item.principalId}</TableCell>
                      <TableCell>
                        <IconButton
                          onClick={() => {
                            navigate(`/console/datasets/${item.datasetUri}`);
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

EnvironmentOwnedDatasets.propTypes = {
  environment: PropTypes.object.isRequired
};

export default EnvironmentOwnedDatasets;
