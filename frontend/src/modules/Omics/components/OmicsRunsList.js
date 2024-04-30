import React, { useCallback, useEffect, useState } from 'react';
import { Box, Card, CardHeader, Divider } from '@mui/material';
// import CircularProgress from '@mui/material/CircularProgress';
import { Helmet } from 'react-helmet-async';
import { DataGrid } from '@mui/x-data-grid';

import { useClient } from 'services';
import { Defaults } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';

import { listOmicsRuns } from '../services';

export const OmicsRunList = () => {
  const dispatch = useDispatch();
  const [items, setItems] = useState(Defaults.pagedResponse);
  const [filter, setFilter] = useState(Defaults.filter);
  const [loading, setLoading] = useState(true);
  const client = useClient();

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
          <CardHeader title="Omics Run History" />
          <Divider />
          <Box sx={{ minWidth: 600, height: 400 }}>
            <DataGrid
              rows={items.nodes}
              columns={[
                { field: 'runUri', headerName: 'Run identifier', flex: 1 },
                { field: 'label', headerName: 'Run name', flex: 1 },
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
              rowCount={items.totalCount}
              loading={loading}
            />
          </Box>
        </Card>
      </Box>
    </>
  );
};
