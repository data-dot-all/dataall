import {
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  CircularProgress,
  Typography,
  Divider,
  Grid,
  InputAdornment,
  TextField
} from '@mui/material';
import { DataGrid, GridActionsCellItem, GridRowModes } from '@mui/x-data-grid';
import {
  GroupAddOutlined,
  SupervisedUserCircleRounded,
  Warning
} from '@mui/icons-material';
import PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState } from 'react';

import { SET_ERROR, useDispatch } from 'globalErrors';
import { listTableDataFilters, useClient } from 'services';
import {
  Defaults,
  DeleteObjectWithFrictionModal,
  RefreshTableMenu,
  Scrollbar,
  SearchIcon
} from 'design';

import { TableDataFilterAddForm } from './TableDataFilterAddForm';
import { deleteTableDataFilter } from '../services';
import DeleteIcon from '@mui/icons-material/DeleteOutlined';
import { useSnackbar } from 'notistack';


export const TableFilters = ({ table }) => {
  const client = useClient();
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState(Defaults.pagedResponse);
  const [filter, setFilter] = useState(Defaults.filter);
  const [inputValue, setInputValue] = useState('');
  const [isCreateFilterModalOpen, setIsCreateFilterModalOpen] = useState(false);
  const [isDeleteFilterModalOpenId, setIsDeleteFilterModalOpen] = useState(0);


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
  const handleCreateFilterModalOpen = () => {
    setIsCreateFilterModalOpen(true);
  };

  const handleCreateFilterModalClose = () => {
    setIsCreateFilterModalOpen(false);
  };

  const handlePageChange = async (page) => {
    page += 1; //expecting 1-indexing
    if (page <= items.pages && page !== items.page) {
      await setFilter({ ...filter, page: page });
    }
  };

  const handleDeleteFilterModalOpen = (id) => {
    setIsDeleteFilterModalOpen(id);
  };
  const handleDeleteFilterModalClosed = () => {
    setIsDeleteFilterModalOpen(0);
  };

  const deleteDataFilter = async (filterUri) => {
    try {
      const response = await client.mutate(
        deleteTableDataFilter({
          filterUri: filterUri
        })
      );
      if (!response.errors) {
        enqueueSnackbar('Data filter removed from table', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        fetchItems();
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    }
  };

  const fetchItems = useCallback(async () => {
    try {
      // const response = await client.query(
      //   listTableDataFilters({
      //     filter: { ...filter, tableUri: table.tableUri }
      //   })
      // );
      setItems({
        count: 2,
        page: 1,
        pages: 1,
        hasNext: false,
        hasPrevious: false,
        nodes: [
          {
            filterUri: 'filterUri1',
            label: 'Name of filter',
            name: 'Name of filter',
            description: 'This is a description',
            filterType: 'ROW',
            includedCols: '-',
            rowExpression: '(region=AMER) AND (language=EN)'
          },
          {
            filterUri: 'filterUri2',
            label: 'Name of filter',
            name: 'Name of filter',
            description: 'This is a lengthy description of a particular data filter that restrcits teh data access of the consumeing group to only a subset of columns in particular 5 columns that are the ones included and a part of the included Columns section of the table',
            filterType: 'COLUMN',
            includedCols: ['price', 'product_id', 'cost', 'purchase_count'],
            rowExpression: '-'
          }
        ]
      });
      // if (!testResponse.errors) {
      //   setItems(response.data.listTableDataFilters);
      // } else {
      //   dispatch({ type: SET_ERROR, error: response.errors[0].message });
      // }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    } finally {
      setLoading(false);
    }
  }, [client, dispatch, filter, table.tableUri]);

  useEffect(() => {
    if (client) {
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, filter.page, fetchItems, dispatch]);

  if (loading) {
    return <CircularProgress />;
  }

  return (
    <Box>
      <Box sx={{ mt: 3 }}>
        <Card>
          <CardHeader
            action={<RefreshTableMenu refresh={fetchItems} />}
            title={
              <Box>
                <SupervisedUserCircleRounded style={{ marginRight: '10px' }} />{' '}
                Data Filters
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
                  placeholder="Search"
                  value={inputValue}
                  variant="outlined"
                />
              </Box>
            </Grid>
            <Grid item md={2} sm={6} xs={12}>
              <Button
                color="primary"
                startIcon={<GroupAddOutlined fontSize="small" />}
                sx={{ m: 1 }}
                onClick={handleCreateFilterModalOpen}
                variant="contained"
              >
                Add New Filter
              </Button>
              {isCreateFilterModalOpen && (
                <TableDataFilterAddForm
                  table={table}
                  open
                  reload={fetchItems}
                  onClose={handleCreateFilterModalClose}
                />
              )}
            </Grid>
          </Box>
          <Scrollbar>
            <Box sx={{ minWidth: 600 }}>
              <DataGrid
                autoHeight
                getRowId={(node) => node.filterUri}
                rows={items.nodes}
                columns={[
                  { field: 'id', hide: true },
                  {
                    field: 'name',
                    headerName: 'Filter Name',
                    flex: 1,
                    editable: false
                  },
                  {
                    field: 'description',
                    headerName: 'Description',
                    flex: 1,
                    editable: false
                  },
                  {
                    field: 'filterType',
                    headerName: 'Filter Type',
                    flex: 0.5,
                    editable: false
                  },
                  {
                    field: 'includedCols',
                    headerName: 'Included Columns',
                    flex: 1,
                    editable: false
                  },
                  {
                    field: 'rowExpression',
                    headerName: 'Row Expression',
                    flex: 1,
                    editable: false
                  },
                  {
                    field: 'actions',
                    headerName: 'Actions',
                    flex: 0.5,
                    type: 'actions',
                    cellClassName: 'actions',
                    getActions: ({ id, ...props }) => {
                      const name = props.row.name;
                      return [
                        <GridActionsCellItem
                          icon={<DeleteIcon />}
                          label="Delete"
                          onClick={() => handleDeleteFilterModalOpen(id)}
                          color="inherit"
                        />,
                        <DeleteObjectWithFrictionModal
                          objectName={name}
                          onApply={() => handleDeleteFilterModalClosed()}
                          onClose={() => handleDeleteFilterModalClosed()}
                          open={isDeleteFilterModalOpenId === id}
                          isAWSResource={false}
                          deleteFunction={() => deleteDataFilter(id)}
                          deleteMessage={
                            <Card variant="outlined" sx={{ mb: 2 }}>
                              <CardContent>
                                <Typography variant="subtitle2" color="error">
                                  <Warning sx={{ mr: 1 }} /> Revoke all share items where
                                  data filter <b>{name}</b> is used before proceeding with the deletion !
                                </Typography>
                              </CardContent>
                            </Card>
                          }
                        />
                      ];
                    }
                  }
                ]}
                rowCount={items.count}
                page={items.page - 1}
                pageSize={filter.pageSize}
                paginationMode="server"
                onPageChange={handlePageChange}
                onPageSizeChange={(pageSize) => {
                  setFilter({ ...filter, pageSize: pageSize });
                }}
                loading={loading}
                getRowHeight={() => 'auto'}
                disableSelectionOnClick
                sx={{ wordWrap: 'break-word' }}
              />
            </Box>
          </Scrollbar>
        </Card>
      </Box>
    </Box>
  );
};

TableFilters.propTypes = {
  table: PropTypes.object.isRequired
};
