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
  SearchIcon,
  StackStatus
} from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import { listDatasetsCreatedInEnvironment } from '../services';

export const EnvironmentOwnedDatasets = ({ environment }) => {
  const client = useClient();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [items, setItems] = useState(Defaults.pagedResponse);
  const [filter, setFilter] = useState(Defaults.filter);
  const [loading, setLoading] = useState(null);
  const [inputValue, setInputValue] = useState('');

  const fetchItems = useCallback(async () => {
    setLoading(true);
    const response = await client.query(
      listDatasetsCreatedInEnvironment({
        filter,
        environmentUri: environment.environmentUri
      })
    );
    if (!response.errors) {
      setItems({ ...response.data.listDatasetsCreatedInEnvironment });
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
        title="Datasets You Own"
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
                <TableCell>Dataset type</TableCell>
                <TableCell>Creator</TableCell>
                <TableCell>Owners</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            {loading ? (
              <CircularProgress sx={{ mt: 1 }} />
            ) : (
              <TableBody>
                {items.nodes.length > 0 ? (
                  items.nodes.map((dataset) => (
                    <TableRow hover key={dataset.environmentUri}>
                      <TableCell>{dataset.label}</TableCell>
                      <TableCell>
                        {dataset.datasetType === 'DatasetTypes.S3'
                          ? `S3/Glue Dataset`
                          : dataset.datasetType === 'DatasetTypes.Redshift'
                          ? `Redshift Dataset`
                          : '-'}
                      </TableCell>
                      <TableCell>{dataset.owner}</TableCell>
                      <TableCell>{dataset.SamlAdminGroupName}</TableCell>
                      <TableCell>
                        <StackStatus
                          status={
                            dataset.stack ? dataset.stack.status : 'NOT_FOUND'
                          }
                        />
                      </TableCell>
                      <TableCell>
                        <IconButton
                          onClick={() => {
                            let datasetTypeLink =
                              dataset.datasetType === 'DatasetTypes.S3'
                                ? `s3-datasets`
                                : dataset.datasetType ===
                                  'DatasetTypes.Redshift'
                                ? `redshift-datasets`
                                : '-';
                            navigate(
                              datasetTypeLink
                                ? `/console/${datasetTypeLink}/${dataset.datasetUri}`
                                : '-'
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
