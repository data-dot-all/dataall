import PropTypes from 'prop-types';
import { Box, CircularProgress, Dialog, Typography } from '@mui/material';
import React, { useCallback, useEffect, useState } from 'react';

import { listRedshiftSchemaTables } from '../services';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import { DataGrid } from '@mui/x-data-grid';
import { Defaults, Scrollbar } from 'design';
import LinearProgress from '@mui/material/LinearProgress';

export const AddTablesModal = (props) => {
  const { onClose, open, dataset } = props;
  const client = useClient();
  const dispatch = useDispatch();
  const [loading, setLoading] = useState(false);
  const [items, setItems] = useState(null);
  const [selectedTables, setSelectedTables] = useState(null);
  const [filter, setFilter] = useState(Defaults.filter);

  const fetchItems = useCallback(async () => {
    setLoading(true);
    try {
      const response = await client.query(
        listRedshiftSchemaTables({
          connectionUri: dataset.connection.connectionUri,
          schema: dataset.schema
        })
      );
      if (!response.errors) {
        setItems(response.data.listRedshiftSchemaTables);
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    }
    setLoading(false);
  }, [client, dispatch, dataset]);

  useEffect(() => {
    if (client && dataset) {
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, fetchItems, dispatch, dataset]);

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
            Loading database tables {selectedTables}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      </Dialog>
    );
  }
  if (!dataset || !items) {
    return null;
  }
  return (
    <Dialog maxWidth="md" fullWidth onClose={onClose} open={open}>
      <Scrollbar>
        <Box sx={{ minWidth: 600 }}>
          <DataGrid
            autoHeight
            checkboxSelection
            getRowId={(node) => node.name}
            rows={items}
            columns={[
              { field: 'id', hide: true },
              {
                field: 'name',
                headerName: 'Redshift tables',
                flex: 0.5,
                editable: false
              }
            ]}
            pageSize={filter.pageSize}
            rowsPerPageOptions={[filter.pageSize]}
            onPageChange={handlePageChange}
            loading={loading}
            onPageSizeChange={(pageSize) => {
              setFilter({
                ...filter,
                pageSize: pageSize
              });
            }}
            getRowHeight={() => 'auto'}
            disableSelectionOnClick
            onSelectionModelChange={(newSelectionModel) => {
              setSelectedTables(newSelectionModel);
            }}
            components={{
              LoadingOverlay: LinearProgress
            }}
            sx={{ wordWrap: 'break-word' }}
          />
        </Box>
      </Scrollbar>
    </Dialog>
  );
};
AddTablesModal.propTypes = {
  onApply: PropTypes.func,
  onClose: PropTypes.func,
  open: PropTypes.bool.isRequired,
  dataset: PropTypes.object.isRequired
};
