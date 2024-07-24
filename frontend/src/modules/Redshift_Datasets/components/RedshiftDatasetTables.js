import { DeleteOutlined, Warning } from '@mui/icons-material';
import PostAddIcon from '@mui/icons-material/PostAdd';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import {
  Box,
  Button,
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
import { useClient } from 'services';

import {
  deleteRedshiftDatasetTable,
  listRedshiftDatasetTables
} from '../services';

import { AddTablesModal } from './AddTablesModal';
import { TableSchemaModal } from './TableSchemaModal';

export const RedshiftDatasetTables = (props) => {
  const { dataset, isAdmin } = props;
  const client = useClient();
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const navigate = useNavigate();
  const [items, setItems] = useState(Defaults.pagedResponse);
  const [filter, setFilter] = useState(Defaults.filter);
  const [loading, setLoading] = useState(null);
  const [inputValue, setInputValue] = useState('');
  const [isDeleteObjectModalOpen, setIsDeleteObjectModalOpen] = useState(false);
  const [isTableSchemaModalOpen, setIsTableSchemaModalOpen] = useState(false);
  const [tableToDelete, setTableToDelete] = useState(null);
  const [tableToSee, setTableToSee] = useState(null);
  const [isAddTablesModalOpen, setIsAddTablesModalOpen] = useState(false);

  const handleDeleteObjectModalOpen = (table) => {
    setTableToDelete(table);
    setIsDeleteObjectModalOpen(true);
  };
  const handleDeleteObjectModalClose = () => {
    setTableToDelete(null);
    setIsDeleteObjectModalOpen(false);
  };

  const handleAddTablesModalOpen = () => {
    setIsAddTablesModalOpen(true);
  };
  const handleAddTablesModalClose = () => {
    setIsAddTablesModalOpen(false);
    fetchItems().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
  };

  const handleTableSchemaModalOpen = () => {
    setIsTableSchemaModalOpen(true);
  };
  const handleTableSchemaModalClose = () => {
    setIsTableSchemaModalOpen(false);
  };

  const fetchItems = useCallback(async () => {
    setLoading(true);
    const response = await client.query(
      listRedshiftDatasetTables({
        datasetUri: dataset.datasetUri,
        filter: { ...filter }
      })
    );
    if (!response.errors) {
      setItems({ ...response.data.listRedshiftDatasetTables });
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [dispatch, client, dataset, filter]);

  const deleteTable = async () => {
    const response = await client.mutate(
      deleteRedshiftDatasetTable({
        rsTableUri: tableToDelete.rsTableUri
      })
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
    <>
      <Box sx={{ mb: 3 }}>
        <Card>
          <CardContent>
            <Grid container spacing={2}>
              <Grid item md={2} sm={2} xs={3}>
                <Typography color="textSecondary" variant="subtitle2">
                  Database
                </Typography>
                <Typography color="textPrimary" variant="body2">
                  {dataset.connection.database}
                </Typography>
              </Grid>
              <Grid item md={2} sm={2} xs={3}>
                <Typography color="textSecondary" variant="subtitle2">
                  Schema
                </Typography>
                <Typography color="textPrimary" variant="body2">
                  {dataset.schema}
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Box>
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
        <Grid container spacing={2}>
          <Grid item md={4} sm={4} xs={6}>
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
          </Grid>
          <Grid item md={2} sm={6} xs={12}>
            <Button
              color="primary"
              startIcon={<PostAddIcon fontSize="small" />}
              sx={{ m: 1 }}
              onClick={handleAddTablesModalOpen}
              variant="contained"
            >
              Add Tables
            </Button>
            {isAddTablesModalOpen && (
              <AddTablesModal
                onApply={handleAddTablesModalClose}
                onClose={handleAddTablesModalClose}
                open={isAddTablesModalOpen}
                dataset={dataset}
              />
            )}
          </Grid>
        </Grid>
        <Scrollbar>
          <Box sx={{ minWidth: 600 }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Description</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              {loading ? (
                <CircularProgress sx={{ mt: 1 }} />
              ) : (
                <TableBody>
                  {items.nodes.length > 0 ? (
                    items.nodes.map((table) => (
                      <TableRow hover key={table.rsTableUri}>
                        <TableCell>
                          <Link
                            underline="hover"
                            color="textPrimary"
                            component={RouterLink}
                            to={`/console/redshift-datasets/table/${table.rsTableUri}`}
                            variant="subtitle2"
                          >
                            {table.name}
                          </Link>
                        </TableCell>
                        <TableCell>{table.description}</TableCell>
                        <TableCell>
                          <Button
                            color="primary"
                            startIcon={<OpenInNewIcon fontSize="small" />}
                            sx={{ mr: 1 }}
                            variant="outlined"
                            onClick={() => {
                              handleTableSchemaModalOpen();
                              setTableToSee(table);
                            }}
                          >
                            Open table schema
                          </Button>
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
                                `/console/redshift-datasets/table/${table.rsTableUri}`
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
      {isAdmin && tableToDelete && (
        <DeleteObjectModal
          objectName={tableToDelete.name}
          onApply={handleDeleteObjectModalClose}
          onClose={handleDeleteObjectModalClose}
          open={isDeleteObjectModalOpen}
          deleteFunction={deleteTable}
          deleteMessage={
            <Card>
              <CardContent>
                <Typography gutterBottom variant="body2">
                  <Warning /> Redshift Table will be deleted from data.all
                  catalog, but will still be available in Amazon Redshift.
                </Typography>
              </CardContent>
            </Card>
          }
        />
      )}
      <TableSchemaModal
        onApply={handleTableSchemaModalClose}
        onClose={handleTableSchemaModalClose}
        open={isTableSchemaModalOpen}
        table={tableToSee}
      />
    </>
  );
};

RedshiftDatasetTables.propTypes = {
  dataset: PropTypes.object.isRequired,
  isAdmin: PropTypes.bool.isRequired
};
