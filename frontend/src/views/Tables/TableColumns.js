import React, { useEffect, useState } from 'react';
import { DataGrid } from '@material-ui/data-grid';
import { Box, Card, CircularProgress } from '@material-ui/core';
import { useSnackbar } from 'notistack';
import { SyncAlt } from '@material-ui/icons';
import { LoadingButton } from '@material-ui/lab';
import * as PropTypes from 'prop-types';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import useClient from '../../hooks/useClient';
import listDatasetTableColumns from '../../api/DatasetTable/listDatasetTableColumns';
import updateColumnDescription from '../../api/DatasetTable/updateDatasetTableColumn';
import syncDatasetTableColumns from '../../api/DatasetTable/syncDatasetTableColumns';
import * as Defaults from '../../components/defaults';

const TableColumns = (props) => {
  const { table, isAdmin } = props;
  const dispatch = useDispatch();
  const client = useClient();
  const { enqueueSnackbar } = useSnackbar();
  const [loading, setLoading] = useState(true);
  const [columns, setColumns] = useState(null);
  const [refreshingColumns, setRefreshingColumns] = useState(false);
  const fetchItems = async () => {
    setLoading(true);
    const response = await client.query(listDatasetTableColumns({
      tableUri: table.tableUri,
      filter: Defaults.SelectListFilter
    }));
    if (!response.errors) {
      setColumns(response.data.listDatasetTableColumns.nodes.map((c) => ({
        id: c.columnUri,
        name: c.columnType && c.columnType !== 'column' ? `${c.name} (${c.columnType})` : c.name,
        type: c.typeName,
        description: c.description
      })));
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  };

  const updateDescription = async (column, description) => {
    const response = await client.mutate(updateColumnDescription({ columnUri: column.id, input: { description } }));
    try {
      if (!response.errors) {
        enqueueSnackbar(`Column ${column.name} description updated`, {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    }
  };

    const handleEditCellChangeCommitted = ({id, field, props}) => { /*eslint-disable-line*/
    const data = props;
    if (field === 'description') {
      columns.map((c) => {
        if (c.id === id) {
          return updateDescription(c, data.value.toString()).catch(
            (e) => dispatch({ type: SET_ERROR, error: e.message })
          );
        }
        return true;
      });
    }
  };

  const startSyncColumns = async () => {
    try {
      setRefreshingColumns(true);
      const response = await client.mutate(syncDatasetTableColumns(table.tableUri));
      if (!response.errors) {
        setColumns(response.data.syncDatasetTableColumns.nodes.map((c) => ({
          id: c.columnUri,
          name: c.columnType && c.columnType !== 'column' ? `${c.name} (${c.columnType})` : c.name,
          type: c.typeName,
          description: c.description
        })));
        enqueueSnackbar('Columns synchronized successfully', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    } finally {
      setRefreshingColumns(false);
    }
  };

  useEffect(() => {
    if (client) {
      fetchItems().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client]);

  if (loading) {
    return <CircularProgress />;
  }
  if (!columns) {
    return null;
  }
  const header = [
    { field: 'name', headerName: 'Name', width: 400, editable: false },
    { field: 'type', headerName: 'Type', width: 400, editable: false },
    { field: 'description', headerName: 'Description', width: 600, editable: isAdmin }
  ];

  return (
    <Box>
      {isAdmin && (
        <Box
          sx={{
            display: 'flex',
            flex: 1,
            justifyContent: 'flex-end',
            mb: 2
          }}
        >
          <LoadingButton
            pending={refreshingColumns}
            color="primary"
            onClick={startSyncColumns}
            startIcon={<SyncAlt fontSize="small" />}
            sx={{ m: 1 }}
            variant="outlined"
          >
            Synchronize
          </LoadingButton>
        </Box>
      )}
      <Card sx={{ height: 800, width: '100%' }}>
        {columns.length > 0 && (
        <DataGrid
          rows={columns}
          columns={header}
          onEditCellChangeCommitted={handleEditCellChangeCommitted}
        />
        )}
      </Card>
    </Box>
  );
};
TableColumns.propTypes = {
  table: PropTypes.object.isRequired,
  isAdmin: PropTypes.bool.isRequired
};
export default TableColumns;
