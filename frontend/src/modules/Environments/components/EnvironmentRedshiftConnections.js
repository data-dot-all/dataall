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
import { DataGrid, GridActionsCellItem, GridRowModes } from '@mui/x-data-grid';
import {
  GroupAddOutlined,
  SupervisedUserCircleRounded
} from '@mui/icons-material';
import PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState } from 'react';

import { SET_ERROR, useDispatch } from 'globalErrors';
import { listEnvironmentRedshiftConnections, useClient } from 'services';
import {
  Defaults,
  DeleteObjectWithFrictionModal,
  Label,
  RefreshTableMenu,
  Scrollbar,
  SearchIcon
} from 'design';

import { EnvironmentRedshiftConnectionAddForm } from './EnvironmentRedshiftConnectionAddForm';
import { RedshiftConnectionsPermissionsDialog } from './RedshiftConnectionsPermissionsDialog';
import { deleteRedshiftConnection } from '../services';
import SaveIcon from '@mui/icons-material/Save';
import CancelIcon from '@mui/icons-material/Close';
import DeleteIcon from '@mui/icons-material/DeleteOutlined';
import PermContactCalendarIcon from '@mui/icons-material/PermContactCalendar';
import { useSnackbar } from 'notistack';

export const EnvironmentRedshiftConnections = ({ environment }) => {
  const client = useClient();
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState(Defaults.pagedResponse);
  const [filter, setFilter] = useState(Defaults.filter);
  const [inputValue, setInputValue] = useState('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [rowModesModel, setRowModesModel] = useState({});
  const [isDeleteModalOpenId, setIsDeleteModalOpen] = useState(0);
  const [openPermissionsDialog, setOpenPermissionsDialog] = useState(false);
  const [selectedConnection, setSelectedConnection] = useState(false);

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

  const handleSaveClick = (id) => () => {
    setRowModesModel({ ...rowModesModel, [id]: { mode: GridRowModes.View } });
  };

  const handleCancelClick = (id) => () => {
    setRowModesModel({
      ...rowModesModel,
      [id]: { mode: GridRowModes.View, ignoreModifications: true }
    });
  };

  const handleRowEditStart = (params, event) => {
    event.defaultMuiPrevented = true;
  };

  const handleRowEditStop = (params, event) => {
    event.defaultMuiPrevented = true;
  };

  const handleDeleteModalOpen = (id) => {
    setIsDeleteModalOpen(id);
  };
  const handleDeleteModalClosed = (id) => {
    setIsDeleteModalOpen(0);
  };

  const deleteConnection = async (connectionUri) => {
    try {
      const response = await client.mutate(
        deleteRedshiftConnection({
          connectionUri: connectionUri
        })
      );
      if (!response.errors) {
        enqueueSnackbar('Redshift connection removed from environment', {
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
        listEnvironmentRedshiftConnections({
          filter: { ...filter, environmentUri: environment.environmentUri }
        })
      );
      if (!response.errors) {
        setItems({
          ...response.data.listEnvironmentRedshiftConnections,
          nodes: [
            ...response.data.listEnvironmentRedshiftConnections.nodes.map(
              (item) => ({
                ...item,
                id: item.connectionUri,
                redshiftId:
                  item.redshiftType === 'serverless'
                    ? item.workgroup
                    : item.clusterId,
                connectionDetails: item.secretArn
                  ? item.secretArn
                  : item.redshiftUser
              })
            )
          ]
        });
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
                Redshift Connections
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
                <EnvironmentRedshiftConnectionAddForm
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
                    headerName: 'Connection Type',
                    flex: 1,
                    editable: false,
                    renderCell: (params) => {
                      return (
                        <Label
                          color={params.value === 'ADMIN' ? 'success' : 'info'}
                        >
                          {params.value}
                        </Label>
                      );
                    }
                  },
                  {
                    field: 'SamlGroupName',
                    headerName: 'Team',
                    flex: 1,
                    editable: false
                  },
                  {
                    field: 'permissions',
                    headerName: 'Permissions',
                    flex: 0.8,
                    renderCell: (params) => {
                      return (
                        <Button
                          variant="outlined"
                          size="small"
                          disabled={params.row.connectionType === 'DATA_USER'}
                          endIcon={<PermContactCalendarIcon />}
                          onClick={() => {
                            setSelectedConnection(params.row);
                            setOpenPermissionsDialog(true);
                          }}
                        >
                          View and Edit
                        </Button>
                      );
                    }
                  },
                  {
                    field: 'redshiftType',
                    headerName: 'Redshift Type',
                    flex: 1,
                    editable: false
                  },
                  {
                    field: 'nameSpaceId',
                    headerName: 'Namespace Id',
                    flex: 1,
                    editable: false
                  },
                  {
                    field: 'redshiftId',
                    headerName: 'Workgroup/ClusterId',
                    flex: 1,
                    editable: false
                  },
                  {
                    field: 'database',
                    headerName: 'Database',
                    flex: 1,
                    editable: false
                  },
                  {
                    field: 'connectionDetails',
                    headerName: 'SecretArn/Redshift user',
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
                      const isInEditMode =
                        rowModesModel[id]?.mode === GridRowModes.Edit;

                      if (isInEditMode) {
                        return [
                          <GridActionsCellItem
                            icon={<SaveIcon />}
                            label="Save"
                            sx={{
                              color: 'primary.main'
                            }}
                            onClick={handleSaveClick(id)}
                          />,
                          <GridActionsCellItem
                            icon={<CancelIcon />}
                            label="Cancel"
                            className="textPrimary"
                            onClick={handleCancelClick(id)}
                            color="inherit"
                          />
                        ];
                      }
                      return [
                        <GridActionsCellItem
                          icon={<DeleteIcon />}
                          label="Delete"
                          onClick={() => handleDeleteModalOpen(id)}
                          color="inherit"
                        />,
                        <DeleteObjectWithFrictionModal
                          objectName={name}
                          onApply={() => handleDeleteModalClosed(id)}
                          onClose={() => handleDeleteModalClosed(id)}
                          open={isDeleteModalOpenId === id}
                          isAWSResource={false}
                          deleteFunction={() => deleteConnection(id)}
                        />
                      ];
                    }
                  }
                ]}
                editMode="row"
                rowModesModel={rowModesModel}
                onRowModesModelChange={setRowModesModel}
                onRowEditStart={handleRowEditStart}
                onRowEditStop={handleRowEditStop}
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
      {openPermissionsDialog && (
        <RedshiftConnectionsPermissionsDialog
          open={openPermissionsDialog}
          onClose={() => setOpenPermissionsDialog(false)}
          connection={selectedConnection}
          environment={environment}
        />
      )}
    </Box>
  );
};

EnvironmentRedshiftConnections.propTypes = {
  environment: PropTypes.object.isRequired
};
