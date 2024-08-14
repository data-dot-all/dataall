import PropTypes from 'prop-types';
import {
  Box,
  CircularProgress,
  Dialog,
  Divider,
  Typography
} from '@mui/material';
import React, { useCallback, useEffect, useState } from 'react';

import { getRedshiftDatasetTableColumns } from '../services';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import { DataGrid } from '@mui/x-data-grid';
import { Defaults, Scrollbar } from 'design';

export const TableSchemaModal = (props) => {
  const { onClose, open, table } = props;
  const client = useClient();
  const dispatch = useDispatch();
  const [loading, setLoading] = useState(false);
  const [items, setItems] = useState(null);
  const [filter, setFilter] = useState(Defaults.filter);

  const fetchItems = useCallback(async () => {
    setLoading(true);
    const response = await client.query(
      getRedshiftDatasetTableColumns({
        rsTableUri: table.rsTableUri,
        filter: filter
      })
    );
    if (
      !response.errors &&
      response.data.getRedshiftDatasetTableColumns !== null
    ) {
      setItems(response.data.getRedshiftDatasetTableColumns);
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Redshift table not found';
      dispatch({ type: SET_ERROR, error });
    }
    setLoading(false);
  }, [client, dispatch, table]);

  useEffect(() => {
    if (client && table) {
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, fetchItems, dispatch, table]);

  const handlePageChange = async (page) => {
    page += 1; //expecting 1-indexing
    if (page <= items.pages && page !== items.page) {
      await setFilter({ ...filter, page: page });
    }
  };

  if (loading) {
    return (
      <Dialog open={open}>
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <Typography color="textPrimary" variant="subtitle2">
            Loading table schema
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      </Dialog>
    );
  }
  if (!table || !items) {
    return null;
  }
  return (
    <Dialog maxWidth="md" fullWidth onClose={onClose} open={open}>
      <Box sx={{ p: 3 }}>
        <Typography
          align="center"
          color="textPrimary"
          gutterBottom
          variant="h5"
        >
          Redshift table: {table.label}
        </Typography>
        <Divider />
        <Scrollbar>
          <Box sx={{ minWidth: 600 }}>
            <DataGrid
              autoHeight
              getRowId={(node) => node.name}
              rows={items.nodes}
              columns={[
                { field: 'id', hide: true },
                {
                  field: 'name',
                  headerName: 'Name',
                  flex: 1.5,
                  editable: false
                },
                {
                  field: 'typeName',
                  headerName: 'Type',
                  flex: 1,
                  editable: false
                },
                {
                  field: 'length',
                  headerName: 'Length',
                  flex: 1,
                  editable: false
                },
                {
                  field: 'nullable',
                  headerName: 'Nullable',
                  flex: 1,
                  editable: false
                },
                {
                  field: 'columnDefault',
                  headerName: 'Default value',
                  flex: 1,
                  editable: false
                }
              ]}
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
              sx={{
                wordWrap: 'break-word', //TODO: create a generic styled datagrid to be used across features
                '& .MuiDataGrid-row': {
                  borderBottom: '1px solid rgba(145, 158, 171, 0.24)'
                },
                '& .MuiDataGrid-columnHeaders': {
                  borderBottom: 0.5
                }
              }}
            />
          </Box>
        </Scrollbar>
      </Box>
    </Dialog>
  );
};
TableSchemaModal.propTypes = {
  onApply: PropTypes.func,
  onClose: PropTypes.func,
  open: PropTypes.bool.isRequired,
  table: PropTypes.object.isRequired
};
