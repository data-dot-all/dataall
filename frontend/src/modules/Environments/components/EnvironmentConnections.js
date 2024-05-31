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
import { DataGrid } from '@mui/x-data-grid';
import {
  GroupAddOutlined,
  SupervisedUserCircleRounded
} from '@mui/icons-material';
import PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState } from 'react';

import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import { Defaults, RefreshTableMenu, Scrollbar, SearchIcon } from 'design';

import { EnvironmentRedshiftConnectionAddForm } from './EnvironmentRedshiftConnectionAddForm';
import { listEnvironmentConnections } from '../services';

export const EnvironmentConnections = ({ environment }) => {
  const client = useClient();
  const dispatch = useDispatch();
  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState(Defaults.pagedResponse);
  const [filter, setFilter] = useState(Defaults.filter);
  const [inputValue, setInputValue] = useState('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

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
  const handleCreateModalOpen = () => {
    setIsCreateModalOpen(true);
  };

  const handleCreateModalClose = () => {
    setIsCreateModalOpen(false);
  };

  const handlePageChange = async (page) => {
    page += 1; //expecting 1-indexing
    if (page <= items.pages && page !== items.page) {
      await setFilter({ ...filter, page: page });
    }
  };

  const [rowModesModel, setRowModesModel] = useState({});

  const handleRowEditStart = (params, event) => {
    event.defaultMuiPrevented = true;
  };

  const handleRowEditStop = (params, event) => {
    event.defaultMuiPrevented = true;
  };

  const processRowUpdate = async (newRow) => {
    //INTRODUCE HERE FUNCTION TO UPDATE THE CONNECTION
    return newRow;
  };

  const fetchItems = useCallback(async () => {
    try {
      const response = await client.query(
        listEnvironmentConnections({
          filter: { ...filter, environmentUri: environment.environmentUri }
        })
      );
      if (!response.errors) {
        setItems({ ...response.data.listEnvironmentConnections });
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    } finally {
      setLoading(false);
    }
  }, [client, dispatch, filter, environment.environmentUri]);

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
                Environment Connections
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
                onClick={handleCreateModalOpen}
                variant="contained"
              >
                Add Connection
              </Button>
              {isCreateModalOpen && (
                <EnvironmentRedshiftConnectionAddForm //TODO make generic like Dataset creation
                  environment={environment}
                  open
                  reload={fetchItems}
                  onClose={handleCreateModalClose}
                />
              )}
            </Grid>
          </Box>
          <Scrollbar>
            <Box sx={{ minWidth: 600 }}>
              <DataGrid
                autoHeight
                getRowId={(node) => node.connectionUri}
                rows={items.nodes}
                columns={[
                  { field: 'id', hide: true },
                  {
                    field: 'name',
                    headerName: 'Name',
                    flex: 0.5,
                    editable: true
                  },
                  {
                    field: 'connectionType',
                    headerName: 'Type',
                    flex: 1
                  },
                  {
                    field: 'SamlGroupName',
                    headerName: 'Team',
                    flex: 1,
                    editable: false
                  } //TODO: add other columns and deletion
                ]}
                editMode="row"
                rowModesModel={rowModesModel}
                onRowModesModelChange={setRowModesModel}
                onRowEditStart={handleRowEditStart}
                onRowEditStop={handleRowEditStop}
                processRowUpdate={processRowUpdate}
                onProcessRowUpdateError={(error) =>
                  dispatch({ type: SET_ERROR, error: error.message })
                }
                experimentalFeatures={{ newEditingApi: true }}
                rowCount={items.count}
                page={items.page - 1}
                pageSize={filter.pageSize}
                paginationMode="server"
                onPageChange={handlePageChange}
                loading={loading}
                onPageSizeChange={(pageSize) => {
                  setFilter({ ...filter, pageSize: pageSize });
                }}
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

EnvironmentConnections.propTypes = {
  environment: PropTypes.object.isRequired
};
