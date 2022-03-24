import PropTypes from 'prop-types';
import { useEffect, useState } from 'react';
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
} from '@material-ui/core';
import CircularProgress from '@material-ui/core/CircularProgress';
import { DeleteOutlined } from '@material-ui/icons';
import { LoadingButton } from '@material-ui/lab';
import { useSnackbar } from 'notistack';
import { BsTable } from 'react-icons/all';
import useClient from '../../hooks/useClient';
import * as Defaults from '../../components/defaults';
import Scrollbar from '../../components/Scrollbar';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import SearchIcon from '../../icons/Search';
import PlusIcon from '../../icons/Plus';
import Pager from '../../components/Pager';
import listClusterDatasetTables from '../../api/RedshiftCluster/listClusterDatasetTables';
import WarehouseCopyTableModal from './WarehouseCopyTableModal';
import disableRedshiftClusterDatasetCopy from '../../api/RedshiftCluster/disableClusterDatasetCopy';

const WarehouseTables = ({ warehouse }) => {
  const client = useClient();
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const [items, setItems] = useState(Defaults.PagedResponseDefault);
  const [filter, setFilter] = useState(Defaults.DefaultFilter);
  const [loading, setLoading] = useState(null);
  const [inputValue, setInputValue] = useState('');
  const [isCopyTablesOpen, setIsLoadDatasetsOpen] = useState(false);

  const fetchItems = async () => {
    setLoading(true);
    const response = await client
      .query(listClusterDatasetTables({
        clusterUri: warehouse.clusterUri,
        filter
      }));
    if (!response.errors) {
      setItems({ ...response.data.listRedshiftClusterCopyEnabledTables });
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  };

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
    if ((event.code === 'Enter')) {
      fetchItems().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  };

  const handlePageChange = async (event, value) => {
    if (value <= items.pages && value !== items.page) {
      await setFilter({ ...filter, page: value });
    }
  };

  const disableCopy = async (table) => {
    const res = await client.mutate(disableRedshiftClusterDatasetCopy({
      clusterUri: warehouse.clusterUri,
      datasetUri: table.datasetUri,
      tableUri: table.tableUri
    }));
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
  };

  useEffect(() => {
    if (client) {
      fetchItems().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client, filter.page]);

  return (
    <Box>
      <Card>
        <CardHeader
          action={(
            <LoadingButton
              color="primary"
              onClick={handleCopyTablesModalOpen}
              startIcon={<PlusIcon fontSize="small" />}
              sx={{ m: 1 }}
              variant="outlined"
            >
              Copy table
            </LoadingButton>
          )}
          title={(
            <Box>
              <BsTable style={{ marginRight: '10px' }} />
              Tables copied from loaded datasets
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
                    Schema
                  </TableCell>
                  <TableCell>
                    Location
                  </TableCell>
                  <TableCell>
                    Actions
                  </TableCell>
                </TableRow>
              </TableHead>
              {loading ? <CircularProgress sx={{ mt: 1 }} /> : (
                <TableBody>
                  {items.nodes.length > 0 ? items.nodes.map((table) => (
                    <TableRow
                      hover
                      key={table.tableUri}
                    >
                      <TableCell>
                        {table.name}
                      </TableCell>
                      <TableCell>
                        {table.RedshiftSchema}
                      </TableCell>
                      <TableCell>
                        {table.RedshiftCopyDataLocation}
                      </TableCell>
                      <TableCell>
                        <IconButton onClick={() => {
                          disableCopy(table).catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
                        }}
                        >
                          <DeleteOutlined fontSize="small" />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  )) : (
                    <TableRow
                      hover
                    >
                      <TableCell>
                        No tables found.
                      </TableCell>
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

      {isCopyTablesOpen
      && (
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
