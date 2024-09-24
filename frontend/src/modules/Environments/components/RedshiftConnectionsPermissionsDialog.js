import {
  Button,
  CardContent,
  CardHeader,
  CircularProgress,
  Chip,
  Dialog,
  Divider
} from '@mui/material';
import PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState } from 'react';
import {
  GridRowModes,
  DataGrid,
  GridToolbarContainer,
  GridActionsCellItem,
  GridRowEditStopReasons
} from '@mui/x-data-grid';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/DeleteOutlined';
import SaveIcon from '@mui/icons-material/Save';
import CancelIcon from '@mui/icons-material/Close';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import { Defaults } from 'design';

import {
  listConnectionGroupPermissions,
  addConnectionGroupPermission,
  deleteConnectionGroupPermission
} from '../services';

/* eslint-disable no-console */

const grantablePermissions = [
  {
    value: 'CREATE_SHARE_REQUEST_WITH_CONNECTION',
    label: 'CREATE_SHARE_REQUEST'
  }
];

function GridToolbar(props) {
  const { loading, setRows, setRowModesModel } = props;

  const handleAddGroup = () => {
    const id = Date.now();
    setRows((oldRows) => [
      ...oldRows,
      {
        id,
        groupUri: '',
        permissions: grantablePermissions,
        isNew: true
      }
    ]);
    setRowModesModel((oldModel) => ({
      ...oldModel,
      [id]: { mode: GridRowModes.Edit, fieldToFocus: 'groupUri' }
    }));
  };

  return (
    <GridToolbarContainer>
      <Button
        color="primary"
        variant="contained"
        startIcon={<AddIcon />}
        onClick={handleAddGroup}
        disabled={loading}
      >
        Add group
      </Button>
    </GridToolbarContainer>
  );
}
export const RedshiftConnectionsPermissionsDialog = (props) => {
  const { connection, environment, onClose, open, ...other } = props;
  const dispatch = useDispatch();
  const client = useClient();
  const [loading, setLoading] = useState(false);
  const [rows, setRows] = useState([]);
  const [rowModesModel, setRowModesModel] = useState({});
  const [groupOptions, setGroupOptions] = useState({});

  const fetchConnectionPermissions = useCallback(async () => {
    setLoading(true);
    const response = await client.query(
      listConnectionGroupPermissions({
        connectionUri: connection.connectionUri,
        filter: Defaults.selectListFilter
      })
    );
    if (!response.errors) {
      setRows(
        response.data.listConnectionGroupPermissions.nodes.map((c) => ({
          id: c.groupUri,
          permissions: c.permissions
        }))
      );
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [client, dispatch, connection]);

  const fetchGroups = useCallback(async () => {
    setLoading(true);
    // const response = await client.query(
    //   listEnvironmentGroupsNoConnectionPermissions({
    //     connectionUri: connection.connectionUri,
    //   })
    // );
    const response = {
      data: {
        listEnvironmentGroupsNoConnectionPermissions: ['group1', 'group2']
      }
    };
    if (!response.errors) {
      setGroupOptions(
        response.data.listEnvironmentGroupsNoConnectionPermissions
      );
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [client, dispatch, connection]);

  useEffect(() => {
    if (client) {
      fetchConnectionPermissions().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
      fetchGroups().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, dispatch, connection, fetchConnectionPermissions, fetchGroups]);
  const handleRowEditStop = (params, event) => {
    if (params.reason === GridRowEditStopReasons.rowFocusOut) {
      event.defaultMuiPrevented = true;
    }
  };

  const handleSaveClick = (id) => () => {
    setRowModesModel({
      ...rowModesModel,
      [id]: { mode: GridRowModes.View }
    });
  };

  const savePermission = useCallback(
    async (row) => {
      console.log(
        'savePermissions input',
        row.groupUri,
        row.permissions.map((permission) => permission.value),
        connection.connectionUri
      );
      setLoading(true);

      const response = await client.mutate(
        addConnectionGroupPermission(
          connection.connectionUri,
          row.groupUri,
          row.permissions.map((permission) => permission.value)
        )
      );
      if (!response.errors) {
        console.log('all good');
        setGroupOptions(groupOptions.filter((g) => g !== row.groupUri));
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
      setLoading(false);
    },
    [client, dispatch, connection, rowModesModel, groupOptions]
  );

  const deletePermission = useCallback(
    async (id, row) => {
      console.log('handleDELETEClick');
      setLoading(true);
      //const row = rows[id];
      console.log('handleDELETEClick2', row);
      const response = await client.mutate(
        deleteConnectionGroupPermission({
          connectionUri: connection.connectionUri,
          groupUri: row.groupUri
        })
      );
      if (!response.errors) {
        setRows(rows.filter((row) => row.id !== id));
        setGroupOptions([...groupOptions, row.groupUri]);
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
      setLoading(false);
    },
    [client, dispatch, connection, rows, groupOptions]
  );
  const handleDeleteClick = (id, row) => () => {
    setRows(rows.filter((row) => row.id !== id));
    deletePermission(id, row);
  };

  const handleCancelClick = (id) => () => {
    setRowModesModel({
      ...rowModesModel,
      [id]: { mode: GridRowModes.View, ignoreModifications: true }
    });

    const editedRow = rows.find((row) => row.id === id);
    if (editedRow.isNew) {
      setRows(rows.filter((row) => row.id !== id));
    }
  };

  const handleRowEditStart = (params, event) => {
    event.defaultMuiPrevented = true;
  };

  const processRowUpdate = async (newRow) => {
    console.log('ProcessRowUpdate, id:', newRow);
    await savePermission(newRow);
    console.log('#### end process update');
    return newRow;
  };
  //NEW

  function renderArrayType(params) {
    console.log('params', params);
    console.log('params.value', params.value);

    return params.value.map((value) => {
      console.log('value', value);
      return <Chip label={value.label} />;
    });
  }

  const columns = [
    {
      field: 'groupUri',
      headerName: 'Team',
      flex: 3,
      editable: true,
      type: 'singleSelect',
      valueOptions: groupOptions
    },
    {
      field: 'permissions',
      headerName: 'Permissions',
      flex: 2,
      editable: false,
      type: 'string',
      renderCell: renderArrayType
    },
    {
      field: 'actions',
      type: 'actions',
      headerName: 'Actions',
      flex: 2,
      cellClassName: 'actions',
      getActions: ({ id, row }) => {
        const isInEditMode = rowModesModel[id]?.mode === GridRowModes.Edit;

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
            onClick={handleDeleteClick(id, row)}
            color="inherit"
          />
        ];
      }
    }
  ];

  return (
    <Dialog maxWidth="lg" fullWidth onClose={onClose} open={open} {...other}>
      {loading ? (
        <CircularProgress />
      ) : (
        <>
          <CardHeader title="Connection Permissions" />
          <Divider />
          <CardContent>
            <DataGrid
              fullWidth
              autoHeight
              rows={rows}
              columns={columns}
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
              // rowCount={roles.count}
              // page={roles.page - 1}
              // pageSize={filterRoles.pageSize}
              // paginationMode="server"
              // onPageChange={handlePageChangeRoles}
              loading={loading}
              // onPageSizeChange={(pageSize) => {
              //   setFilterRoles({ ...filterRoles, pageSize: pageSize });
              // }}
              getRowHeight={() => 'auto'}
              disableSelectionOnClick
              sx={{ wordWrap: 'break-word' }}
              components={{
                Toolbar: GridToolbar
              }}
              componentsProps={{
                toolbar: {
                  loading,
                  setRows,
                  setRowModesModel
                }
              }}
            />
          </CardContent>
        </>
      )}
    </Dialog>
  );
};

RedshiftConnectionsPermissionsDialog.propTypes = {
  connection: PropTypes.object.isRequired,
  onClose: PropTypes.func,
  open: PropTypes.bool.isRequired,
  environment: PropTypes.object.isRequired
};
