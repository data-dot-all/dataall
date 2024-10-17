import PropTypes from 'prop-types';
import {
  Box,
  Button,
  CircularProgress,
  Dialog,
  Divider,
  Typography
} from '@mui/material';
import PostAddIcon from '@mui/icons-material/PostAdd';
import { DataGrid, GridRowParams } from '@mui/x-data-grid';
import React, { useCallback, useEffect, useState } from 'react';

import { useSnackbar } from 'notistack';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { Defaults, Scrollbar } from 'design';
import { useClient } from 'services';
import {
  addRedshiftDatasetTables,
  listRedshiftSchemaDatasetTables
} from '../services';

export const AddTablesModal = (props) => {
  const { onClose, open, dataset } = props;
  const client = useClient();
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const [loading, setLoading] = useState(false);
  const [items, setItems] = useState(null);
  const [selectedTables, setSelectedTables] = useState(null);
  const [filter, setFilter] = useState(Defaults.filter);

  const fetchItems = useCallback(async () => {
    setLoading(true);
    try {
      const response = await client.query(
        listRedshiftSchemaDatasetTables({
          datasetUri: dataset.datasetUri
        })
      );
      if (!response.errors) {
        setItems(response.data.listRedshiftSchemaDatasetTables);
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    }
    setLoading(false);
  }, [client, dispatch, dataset]);

  const addTables = async (selected_tables) => {
    const response = await client.mutate(
      addRedshiftDatasetTables({
        datasetUri: dataset.datasetUri,
        tables: selected_tables
      })
    );
    if (!response.errors) {
      if (response.data.addRedshiftDatasetTables.successTables.length > 0) {
        enqueueSnackbar(
          `Tables added: ${response.data.addRedshiftDatasetTables.successTables}`,
          {
            anchorOrigin: {
              horizontal: 'right',
              vertical: 'top'
            },
            variant: 'success'
          }
        );
      }
      if (response.data.addRedshiftDatasetTables.errorTables.length > 0) {
        dispatch({
          type: SET_ERROR,
          error: `The following tables could not be imported, either they do not exist or the connection used has no access to them: ${response.data.addRedshiftDatasetTables.errorTables}`
        });
      }
      fetchItems();
      setSelectedTables(null);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };

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
            Loading database tables
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
      <Box sx={{ p: 3 }}>
        <Typography
          align="center"
          color="textPrimary"
          gutterBottom
          variant="h5"
        >
          Add tables to dataset: {dataset.label}
        </Typography>
        <Divider />
        <Scrollbar>
          <Box sx={{ minWidth: 600 }}>
            <DataGrid
              autoHeight
              checkboxSelection
              isRowSelectable={(params: GridRowParams) =>
                params.row.alreadyAdded === 'false'
              }
              getRowId={(node) => node.name}
              rows={items}
              columns={[
                { field: 'id', hide: true },
                {
                  field: 'name',
                  headerName: 'Redshift tables',
                  flex: 0.5,
                  editable: false
                },
                {
                  field: 'alreadyAdded',
                  headerName: 'Already added',
                  flex: 0.2,
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
              sx={{
                wordWrap: 'break-word',
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
        <Button
          color="primary"
          startIcon={<PostAddIcon fontSize="small" />}
          sx={{ m: 1 }}
          onClick={() => {
            addTables(selectedTables);
          }}
          variant="contained"
          disabled={!selectedTables || selectedTables.length === 0}
        >
          Add Tables
        </Button>
      </Box>
    </Dialog>
  );
};
AddTablesModal.propTypes = {
  onApply: PropTypes.func,
  onClose: PropTypes.func,
  open: PropTypes.bool.isRequired,
  dataset: PropTypes.object.isRequired
};
