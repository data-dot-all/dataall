import {
  Button,
  ButtonGroup,
  CardContent,
  CardHeader,
  CircularProgress,
  Dialog,
  Divider
} from '@mui/material';
import LoadingButton from '@mui/lab/LoadingButton';
import PropTypes from 'prop-types';
import { useCallback, useEffect, useState, useMemo, useRef } from 'react';
import {
  GridRowModes,
  DataGrid,
  GridToolbarContainer,
  GridActionsCellItem,
  useGridApiRef,
  gridClasses
} from '@mui/x-data-grid';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/DeleteOutlined';
import SaveIcon from '@mui/icons-material/Save';
import CancelIcon from '@mui/icons-material/Close';
import RestoreIcon from '@mui/icons-material/Restore';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import { darken } from '@mui/material/styles';
import * as React from 'react';
//import { Defaults } from 'design';

// todo: listConnectionPermissions
// todo UI: table with group + permissions
// todo Add button to add a group permissions

function GridToolbar(props) {
  const {
    rows,
    setRows,
    setRowModesModel,
    hasUnsavedRows,
    setIsSaving,
    isSaving
  } = props;

  const handleAddGroup = () => {
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

  const handleSave = () => {
    setIsSaving(true);
    setRows(rows.map((row) => ({ ...row, isNew: false })));
    setRowModesModel((prevRowModesModel) => {
      const updatedRowModesModel = {};
      Object.keys(prevRowModesModel).forEach((id) => {
        updatedRowModesModel[id] = { mode: GridRowModes.View };
      });
      return updatedRowModesModel;
      setIsSaving(false);
    });
  };

  const handleDiscard = () => {
    setRows(rows.map((row) => ({ ...row, isNew: false })));
    setRowModesModel((prevRowModesModel) => {
      const updatedRowModesModel = {};
      Object.keys(prevRowModesModel).forEach((id) => {
        updatedRowModesModel[id] = { mode: GridRowModes.View };
      });
      return updatedRowModesModel;
    });
  };

  return (
    <GridToolbarContainer>
      <ButtonGroup>
        <Button
          color="primary"
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleAddGroup}
          disabled={isSaving}
        >
          Add group
        </Button>
        <LoadingButton
          color="primary"
          variant="outlined"
          startIcon={<SaveIcon />}
          onClick={handleSave}
          loading={isSaving}
          disabled={!hasUnsavedRows}
        >
          Save changes
        </LoadingButton>
        <Button
          color="primary"
          variant="outlined"
          startIcon={<RestoreIcon />}
          onClick={handleDiscard}
          disabled={!hasUnsavedRows || isSaving}
        >
          Discard changes
        </Button>
      </ButtonGroup>
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
  const apiRef = useGridApiRef();
  const [isSaving, setIsSaving] = useState(false);
  const [hasUnsavedRows, setHasUnsavedRows] = useState(false);
  const unsavedChangesRef = useRef({
    unsavedRows: {},
    rowsBeforeChange: {}
  });

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

  const processRowUpdate = useCallback((newRow, oldRow) => {
    const rowId = newRow.id;

    unsavedChangesRef.current.unsavedRows[rowId] = newRow;
    if (!unsavedChangesRef.current.rowsBeforeChange[rowId]) {
      unsavedChangesRef.current.rowsBeforeChange[rowId] = oldRow;
    }
    setHasUnsavedRows(true);
    return newRow;
  }, []);

  const getRowClassName = useCallback(({ id }) => {
    const unsavedRow = unsavedChangesRef.current.unsavedRows[id];
    if (unsavedRow) {
      if (unsavedRow._action === 'delete') {
        return 'row--removed';
      }
      return 'row--edited';
    }
    return '';
  }, []);

  const columns = useMemo(() => {
    return [
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
        getActions: ({ id, row }) => {
          const isInEditMode = rowModesModel[id]?.mode === GridRowModes.Edit;

          if (isInEditMode) {
            return [
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
              icon={<RestoreIcon />}
              label="Discard changes"
              disabled={unsavedChangesRef.current.unsavedRows[id] === undefined}
              onClick={() => {
                apiRef.current.updateRows([
                  unsavedChangesRef.current.rowsBeforeChange[id]
                ]);
                delete unsavedChangesRef.current.rowsBeforeChange[id];
                delete unsavedChangesRef.current.unsavedRows[id];
                setHasUnsavedRows(
                  Object.keys(unsavedChangesRef.current.unsavedRows).length > 0
                );
              }}
            />,
            <GridActionsCellItem
              icon={<DeleteIcon />}
              label="Delete"
              onClick={() => {
                unsavedChangesRef.current.unsavedRows[id] = {
                  ...row,
                  _action: 'delete'
                };
                if (!unsavedChangesRef.current.rowsBeforeChange[id]) {
                  unsavedChangesRef.current.rowsBeforeChange[id] = row;
                }
                setHasUnsavedRows(true);
                apiRef.current.updateRows([row]); // to trigger row render
              }}
            />
          ];
        }
      }
    ];
  }, [groupOptions, unsavedChangesRef, apiRef]);

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
              apiRef={apiRef}
              disableRowSelectionOnClick
              processRowUpdate={processRowUpdate}
              ignoreValueFormatterDuringExport
              sx={{
                [`& .${gridClasses.row}.row--removed`]: {
                  backgroundColor: (theme) => {
                    if (theme.palette.mode === 'light') {
                      return 'rgba(255, 170, 170, 0.3)';
                    }
                    return darken('rgba(255, 170, 170, 1)', 0.7);
                  }
                },
                [`& .${gridClasses.row}.row--edited`]: {
                  backgroundColor: (theme) => {
                    if (theme.palette.mode === 'light') {
                      return 'rgba(255, 254, 176, 0.3)';
                    }
                    return darken('rgba(255, 254, 176, 1)', 0.6);
                  }
                }
              }}
              loading={isSaving}
              getRowClassName={getRowClassName}
              components={{
                Toolbar: GridToolbar
              }}
              componentsProps={{
                toolbar: {
                  rows,
                  setRows,
                  setRowModesModel,
                  hasUnsavedRows,
                  setIsSaving,
                  isSaving
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
