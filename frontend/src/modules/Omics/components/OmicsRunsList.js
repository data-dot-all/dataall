import React, { useCallback, useEffect, useState } from 'react';
import { Box, Card, CardHeader, Divider, Button } from '@mui/material';
import { Helmet } from 'react-helmet-async';
import { FaTrash } from 'react-icons/fa';
import { DataGrid } from '@mui/x-data-grid';
import { useSnackbar } from 'notistack';

import { useClient } from 'services';
import { Defaults } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';

import { listOmicsRuns, deleteOmicsRun } from '../services';

export const OmicsRunList = () => {
  const dispatch = useDispatch();
  const [items, setItems] = useState(Defaults.pagedResponse);
  const [filter, setFilter] = useState(Defaults.filter);
  const [loading, setLoading] = useState(true);
  const client = useClient();
  const { enqueueSnackbar } = useSnackbar();
  const [selectionModel, setSelectionModel] = useState([]);

  const fetchItems = useCallback(async () => {
    setLoading(true);
    const response = await client.query(listOmicsRuns(filter));
    if (!response.errors) {
      setItems(response.data.listOmicsRuns);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [client, dispatch, filter]);

  useEffect(() => {
    if (client) {
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, filter.page, dispatch, fetchItems]);

  const handleDeleteRuns = async () => {
    const response = await client.mutate(
      deleteOmicsRun({
        input: {
          runUris: selectionModel,
          deleteFromAWS: true
        }
      })
    );
    if (!response.errors) {
      enqueueSnackbar('Omics runs deleted', {
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
  };

  return (
    <>
      <Helmet>
        <title>Runs | data.all</title>
      </Helmet>
      <Box
        sx={{
          backgroundColor: 'background.default',
          minHeight: '100%',
          py: 5
        }}
      >
        <Card>
          <CardHeader
            title="Omics Run History"
            action={
              <Button
                color="primary"
                startIcon={<FaTrash size={15} />}
                onClick={handleDeleteRuns}
                type="button"
                variant="outlined"
              >
                Delete Runs
              </Button>
            }
          />
          <Divider />
          <Box sx={{ minWidth: 600, height: 400 }}>
            <DataGrid
              rows={items.nodes}
              columns={[
                { field: 'runUri', headerName: 'Run identifier', flex: 1 },
                {
                  field: 'label',
                  headerName: 'Run name',
                  flex: 1
                },
                {
                  field: 'workflow.id',
                  headerName: 'Workflow id',
                  flex: 1,
                  valueGetter: (params) => params.row.workflow.id
                },
                {
                  field: 'workflow.name',
                  headerName: 'Workflow name',
                  flex: 1,
                  valueGetter: (params) => params.row.workflow.name
                },
                { field: 'created', headerName: 'Created', flex: 1 },
                { field: 'owner', headerName: 'Owner', flex: 1 },
                { field: 'SamlAdminGroupName', headerName: 'Team', flex: 1 },
                {
                  field: 'environment.label',
                  headerName: 'Environment',
                  flex: 1,
                  valueGetter: (params) => params.row.environment.label
                },
                { field: 'outputUri', headerName: 'Output S3', flex: 1 },
                {
                  field: 'status.status',
                  headerName: 'Status',
                  flex: 1,
                  valueGetter: (params) => params.row.status.status
                }
              ]}
              getRowId={(row) => row.runUri}
              checkboxSelection
              disableRowSelectionOnClick
              pageSize={filter.limit}
              rowsPerPageOptions={[filter.limit]}
              pagination
              paginationMode="server"
              onPageChange={(newPage) =>
                setFilter({ ...filter, page: newPage + 1 })
              }
              onSelectionModelChange={(newSelection) => {
                setSelectionModel(newSelection);
              }}
              selectionModel={selectionModel}
              rowCount={items.totalCount}
              loading={loading}
            />
          </Box>
        </Card>
      </Box>
    </>
  );
};
