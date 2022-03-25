import PropTypes from 'prop-types';
import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Divider,
  Grid,
  IconButton,
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
import { useNavigate } from 'react-router';
import { useSnackbar } from 'notistack';
import { DeleteOutlined, SyncAlt, Warning } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import { BsTable } from 'react-icons/bs';
import { Link as RouterLink } from 'react-router-dom';
import useClient from '../../hooks/useClient';
import * as Defaults from '../../components/defaults';
import SearchIcon from '../../icons/Search';
import Scrollbar from '../../components/Scrollbar';
import ArrowRightIcon from '../../icons/ArrowRight';
import RefreshTableMenu from '../../components/RefreshTableMenu';
import syncTables from '../../api/Dataset/syncTables';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import listDatasetTables from '../../api/Dataset/listDatasetTables';
import Pager from '../../components/Pager';
import DeleteObjectModal from '../../components/DeleteObjectModal';
import deleteDatasetTable from '../../api/DatasetTable/deleteDatasetTable';
import DatasetStartCrawlerModal from './DatasetStartCrawlerModal';

const DatasetTables = ({ dataset, isAdmin }) => {
  const client = useClient();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const [items, setItems] = useState(Defaults.PagedResponseDefault);
  const [filter, setFilter] = useState(Defaults.DefaultFilter);
  const [syncingTables, setSyncingTables] = useState(false);
  const [loading, setLoading] = useState(null);
  const [inputValue, setInputValue] = useState('');
  const [isDeleteObjectModalOpen, setIsDeleteObjectModalOpen] = useState(false);
  const [isStartCrawlerModalOpen, setIsStartCrawlerModalOpen] = useState(false);
  const [tableToDelete, setTableToDelete] = useState(null);

  const handleStartCrawlerModalOpen = () => {
    setIsStartCrawlerModalOpen(true);
  };
  const handleStartCrawlerModalClose = () => {
    setIsStartCrawlerModalOpen(false);
  };
  const handleDeleteObjectModalOpen = (table) => {
    setTableToDelete(table);
    setIsDeleteObjectModalOpen(true);
  };
  const handleDeleteObjectModalClose = () => {
    setTableToDelete(null);
    setIsDeleteObjectModalOpen(false);
  };

  const fetchItems = async () => {
    setLoading(true);
    const response = await client.query(
      listDatasetTables({
        datasetUri: dataset.datasetUri,
        filter: { ...filter }
      })
    );
    if (!response.errors) {
      setItems({ ...response.data.getDataset.tables });
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  };

  const synchronizeTables = async () => {
    setSyncingTables(true);
    const response = await client.mutate(syncTables(dataset.datasetUri));
    if (!response.errors) {
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
      enqueueSnackbar(`Retrieved ${response.data.syncTables.count} tables`, {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setSyncingTables(false);
    setFilter(Defaults.DefaultFilter);
  };

  const deleteTable = async () => {
    const response = await client.mutate(
      deleteDatasetTable({ tableUri: tableToDelete.tableUri })
    );
    if (!response.errors) {
      handleDeleteObjectModalClose();
      enqueueSnackbar('Table deleted', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
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
              <BsTable style={{ marginRight: '10px' }} />
              Tables
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
          <Grid item md={9} sm={6} xs={12}>
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
          {isAdmin && (
            <Grid item md={3} sm={6} xs={12}>
              <LoadingButton
                loading={syncingTables}
                color="primary"
                onClick={synchronizeTables}
                startIcon={<SyncAlt fontSize="small" />}
                sx={{ m: 1 }}
                variant="outlined"
              >
                Synchronize
              </LoadingButton>

              <LoadingButton
                color="primary"
                onClick={handleStartCrawlerModalOpen}
                startIcon={<SearchIcon fontSize="small" />}
                sx={{ m: 1 }}
                variant="outlined"
              >
                Start Crawler
              </LoadingButton>
            </Grid>
          )}
        </Box>
        <Scrollbar>
          <Box sx={{ minWidth: 600 }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Database</TableCell>
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
                        <TableCell>
                          <Link
                            underline="hover"
                            color="textPrimary"
                            component={RouterLink}
                            to={`/console/datasets/table/${table.tableUri}`}
                            variant="subtitle2"
                          >
                            {table.GlueTableName}
                          </Link>
                        </TableCell>
                        <TableCell>{table.GlueDatabaseName}</TableCell>
                        <TableCell>{table.S3Prefix}</TableCell>
                        <TableCell>
                          {isAdmin && (
                            <IconButton
                              onClick={() => {
                                setTableToDelete(table);
                                handleDeleteObjectModalOpen(table);
                              }}
                            >
                              <DeleteOutlined fontSize="small" />
                            </IconButton>
                          )}
                          <IconButton
                            onClick={() => {
                              navigate(
                                `/console/datasets/table/${table.tableUri}`
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
                      <TableCell>No tables found</TableCell>
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
      {isAdmin && isStartCrawlerModalOpen && (
        <DatasetStartCrawlerModal
          dataset={dataset}
          onApply={handleStartCrawlerModalClose}
          onClose={handleStartCrawlerModalClose}
          open={isStartCrawlerModalOpen}
        />
      )}
      {isAdmin && tableToDelete && (
        <DeleteObjectModal
          objectName={tableToDelete.GlueTableName}
          onApply={handleDeleteObjectModalClose}
          onClose={handleDeleteObjectModalClose}
          open={isDeleteObjectModalOpen}
          deleteFunction={deleteTable}
          deleteMessage={
            <Card>
              <CardContent>
                <Typography gutterBottom variant="body2">
                  <Warning /> Table will be deleted from data.all catalog, but
                  will still be available on AWS Glue catalog.
                </Typography>
              </CardContent>
            </Card>
          }
        />
      )}
    </Box>
  );
};

DatasetTables.propTypes = {
  dataset: PropTypes.object.isRequired,
  isAdmin: PropTypes.bool.isRequired
};

export default DatasetTables;
