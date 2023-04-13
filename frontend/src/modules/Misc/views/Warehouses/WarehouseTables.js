import { DeleteOutlined } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import {
  Box,
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
import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
import { useCallback, useEffect, useState } from 'react';
import { BsTable } from 'react-icons/bs';
import {
  Defaults,
  Pager,
  PlusIcon,
  Scrollbar,
  SearchIcon
} from '../../../../design';
import { SET_ERROR, useDispatch } from '../../../../globalErrors';
import {
  disableRedshiftClusterDatasetCopy,
  listClusterDatasetTables,
  useClient
} from '../../../../services';
import WarehouseCopyTableModal from './WarehouseCopyTableModal';

const WarehouseTables = ({ warehouse }) => {
  const client = useClient();
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const [items, setItems] = useState(Defaults.pagedResponse);
  const [filter, setFilter] = useState(Defaults.filter);
  const [loading, setLoading] = useState(null);
  const [inputValue, setInputValue] = useState('');
  const [isCopyTablesOpen, setIsLoadDatasetsOpen] = useState(false);

  const fetchItems = useCallback(async () => {
    setLoading(true);
    const response = await client.query(
      listClusterDatasetTables({
        clusterUri: warehouse.clusterUri,
        filter
      })
    );
    if (!response.errors) {
      setItems({ ...response.data.listRedshiftClusterCopyEnabledTables });
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [client, dispatch, filter, warehouse.clusterUri]);

  const handleCopyTablesModalOpen = () => {
    setIsLoadDatasetsOpen(true);
  };

  const handleCopyTablesModalClose = () => {
    setIsLoadDatasetsOpen(false);
  };

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

  const disableCopy = useCallback(
    async (table) => {
      const res = await client.mutate(
        disableRedshiftClusterDatasetCopy({
          clusterUri: warehouse.clusterUri,
          datasetUri: table.datasetUri,
          tableUri: table.tableUri
        })
      );
      if (!res.errors) {
        enqueueSnackbar('Table copy disabled', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        await fetchItems();
      } else {
        dispatch({ type: SET_ERROR, error: res.errors[0].message });
      }
    },
    [client, enqueueSnackbar, dispatch, warehouse.clusterUri, fetchItems]
  );

  useEffect(() => {
    if (client) {
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, dispatch, filter.page, fetchItems]);

  return (
    <Box>
      <Card>
        <CardHeader
          action={
            <LoadingButton
              color="primary"
              onClick={handleCopyTablesModalOpen}
              startIcon={<PlusIcon fontSize="small" />}
              sx={{ m: 1 }}
              variant="outlined"
            >
              Copy table
            </LoadingButton>
          }
          title={
            <Box>
              <BsTable style={{ marginRight: '10px' }} />
              Tables copied from loaded datasets
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
        </Box>
        <Scrollbar>
          <Box sx={{ minWidth: 600 }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Schema</TableCell>
                  <TableCell>Location</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              {loading ? (
                <CircularProgress sx={{ mt: 1 }} />
              ) : (
                <TableBody>
                  {items.nodes.length > 0 ? (
                    items.nodes.map((table) => (
                      <TableRow hover key={table.tableUri}>
                        <TableCell>{table.name}</TableCell>
                        <TableCell>{table.RedshiftSchema}</TableCell>
                        <TableCell>{table.RedshiftCopyDataLocation}</TableCell>
                        <TableCell>
                          <IconButton
                            onClick={() => {
                              disableCopy(table).catch((e) =>
                                dispatch({ type: SET_ERROR, error: e.message })
                              );
                            }}
                          >
                            <DeleteOutlined fontSize="small" />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow hover>
                      <TableCell>No tables found.</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              )}
            </Table>
            {items.nodes.length > 0 && (
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

      {isCopyTablesOpen && (
        <WarehouseCopyTableModal
          warehouse={warehouse}
          open={isCopyTablesOpen}
          reload={fetchItems}
          onApply={handleCopyTablesModalClose}
          onClose={handleCopyTablesModalClose}
        />
      )}
    </Box>
  );
};

WarehouseTables.propTypes = {
  warehouse: PropTypes.object.isRequired
};

export default WarehouseTables;
