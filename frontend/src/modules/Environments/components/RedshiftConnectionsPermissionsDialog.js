import {
  Button,
  CardContent,
  CardHeader,
  CircularProgress,
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
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
//import { Defaults } from 'design';

// todo: listConnectionPermissions
// todo UI: table with group + permissions
// todo Add button to add a group permissions

function EditToolbar(props) {
  const { setRows, setRowModesModel } = props;

  const handleClick = () => {
    const id = Date.now();
    setRows((oldRows) => [
      ...oldRows,
      { id, groupUri: '', permissions: 'CREATE_SHARE_REQUEST', isNew: true }
    ]);
    setRowModesModel((oldModel) => ({
      ...oldModel,
      [id]: { mode: GridRowModes.Edit, fieldToFocus: 'groupUri' }
    }));
  };

  return (
    <GridToolbarContainer>
      <Button color="primary" startIcon={<AddIcon />} onClick={handleClick}>
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
    // const response = await client.query(
    //   listConnectionPermissions({
    //     connectionUri: connection.connectionUri,
    //     filter: Defaults.selectListFilter
    //   })
    // );
    const response = {
      data: {
        listConnectionPermissions: {
          nodes: [{ groupUri: 'one', permissions: ['first', 'second'] }]
        }
      }
    };
    if (!response.errors) {
      setRows(
        response.data.listConnectionPermissions.nodes.map((c) => ({
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

  const handleDeleteClick = (id) => () => {
    setRows(rows.filter((row) => row.id !== id));
  };

  const processRowUpdate = (newRow) => {
    const updatedRow = { ...newRow, isNew: false };
    setRows(rows.map((row) => (row.id === newRow.id ? updatedRow : row)));
    return updatedRow;
  };

  const handleRowModesModelChange = (newRowModesModel) => {
    setRowModesModel(newRowModesModel);
  };

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
      type: 'singleSelect',
      valueOptions: ['CREATE_SHARE_REQUEST']
    },
    {
      field: 'actions',
      type: 'actions',
      headerName: 'Actions',
      flex: 2,
      cellClassName: 'actions',
      getActions: ({ id }) => {
        return [
          <GridActionsCellItem
            icon={<DeleteIcon />}
            label="Delete"
            onClick={handleDeleteClick(id)}
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
              onRowModesModelChange={handleRowModesModelChange}
              onRowEditStop={handleRowEditStop}
              processRowUpdate={processRowUpdate}
              onProcessRowUpdateError={(error) =>
                dispatch({
                  type: SET_ERROR,
                  error: error.message
                })
              }
              components={{
                Toolbar: EditToolbar
              }}
              componentsProps={{
                toolbar: {
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
