import {
  Box,
  Button,
  Card,
  CardHeader,
  CircularProgress,
  Divider,
  Grid,
  InputAdornment,
  TextField
} from '@mui/material';
import {
  GroupAddOutlined,
  SupervisedUserCircleRounded
} from '@mui/icons-material';
import PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState } from 'react';

import { SET_ERROR, useDispatch } from 'globalErrors';
import { listTableDataFilters, useClient } from 'services';
import { Defaults, RefreshTableMenu, Scrollbar, SearchIcon } from 'design';

import { TableDataFilterAddForm } from './TableDataFilterAddForm';
import { TableFiltersDataGrid } from './TableFiltersDataGrid';
import { deleteTableDataFilter } from '../services';
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

  const handleInputChange = (event) => {
    setInputValue(event.target.value);
    setFilter({ ...filter, term: event.target.value });
  };

  const handlePageSizeChange = (pageSize) => {
    setFilter({ ...filter, pageSize: pageSize });
  };

  const handlePageChange = async (page) => {
    page += 1; //expecting 1-indexing
    if (page <= items.pages && page !== items.page) {
      await setFilter({ ...filter, page: page });
    }
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
      const response = await client.query(
        listTableDataFilters({
          tableUri: table.tableUri,
          filter: filter
        })
      );
      if (!response.errors) {
        setItems(response.data.listTableDataFilters);
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
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
            <Box sx={{ paddingTop: 2, minWidth: 600 }}>
              {!loading && (
                <TableFiltersDataGrid
                  items={items}
                  filter={filter}
                  loading={loading}
                  handlePageChange={handlePageChange}
                  handlePageSizeChange={handlePageSizeChange}
                  deleteFunction={deleteDataFilter}
                />
              )}
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
