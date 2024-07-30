import { Box, Card, CircularProgress } from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import * as PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState } from 'react';
import { Defaults, Scrollbar } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import { getRedshiftDatasetTableColumns } from '../services';

export const TableColumns = (props) => {
  const { table } = props;
  const dispatch = useDispatch();
  const client = useClient();
  const [loading, setLoading] = useState(true);
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
    return <CircularProgress />;
  }

  if (!table || !items) {
    return null;
  }

  return (
    <Box>
      <Card sx={{ width: '100%' }}>
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
                },
                '&.MuiDataGrid-root--densityStandard .MuiDataGrid-cell': {
                  py: '15px'
                }
              }}
            />
          </Box>
        </Scrollbar>
      </Card>
    </Box>
  );
};

TableColumns.propTypes = {
  table: PropTypes.object.isRequired
};
