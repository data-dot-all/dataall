import { DeleteOutlined, SyncAlt, Warning } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
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
import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState } from 'react';
import { BsTable } from 'react-icons/bs';
import { useNavigate } from 'react-router';
import { Link as RouterLink } from 'react-router-dom';
import {
  ArrowRightIcon,
  Defaults,
  DeleteObjectModal,
  Pager,
  RefreshTableMenu,
  Scrollbar,
  SearchIcon
} from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { listDatasetTables, deleteDatasetTable, useClient } from 'services';

import { syncTables } from '../services';

import { DatasetStartCrawlerModal } from './DatasetStartCrawlerModal';
import { emptyPrintUnauthorized, isFeatureEnabled } from 'utils';

export const DatasetTables = (props) => {
  const { dataset, isAdmin } = props;
  const client = useClient();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const [items, setItems] = useState(Defaults.pagedResponse);
  const [filter, setFilter] = useState(Defaults.filter);
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

  const fetchItems = useCallback(async () => {
    setLoading(true);
    const response = await client.query(
      listDatasetTables({
        datasetUri: dataset.datasetUri,
        filter: { ...filter }
      })
    );
    if (response.data.getDataset != null) {
      setItems({ ...response.data.getDataset.tables });
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [dispatch, client, dataset, filter]);

  const synchronizeTables = async () => {
    setSyncingTables(true);
    const response = await client.mutate(syncTables(dataset.datasetUri));
    if (!response.errors) {
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
      enqueueSnackbar(`Retrieved ${response.data.syncTables} tables`, {
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
    setFilter(Defaults.filter);
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

              {isFeatureEnabled('s3_datasets', 'glue_crawler') && (
                <LoadingButton
                  color="primary"
                  onClick={handleStartCrawlerModalOpen}
                  startIcon={<SearchIcon fontSize="small" />}
                  sx={{ m: 1 }}
                  variant="outlined"
                >
                  Start Crawler
                </LoadingButton>
              )}
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
                            to={`/console/s3-datasets/table/${table.tableUri}`}
                            variant="subtitle2"
                          >
                            {table.name}
                          </Link>
                        </TableCell>
                        <TableCell>
                          {emptyPrintUnauthorized(
                            table.restricted?.GlueDatabaseName
                          )}
                        </TableCell>
                        <TableCell>
                          {emptyPrintUnauthorized(table.restricted?.S3Prefix)}
                        </TableCell>
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
                                `/console/s3-datasets/table/${table.tableUri}`
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
