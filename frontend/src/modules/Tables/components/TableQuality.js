import React, { useCallback, useEffect, useState } from 'react';
import { Box, Card } from '@mui/material';
import { Helmet } from 'react-helmet-async';
import { DataGrid } from '@mui/x-data-grid';
import * as PropTypes from 'prop-types';
import { useClient } from 'services';
import { Defaults } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';

// TODO: listRules API query
//import { listTableDataQualityRuleSets, deleteTableDataQualityRuleSets } from '../services';

export const TableQuality = (props) => {
  //const { table, isAdmin } = props; Needed for listTableDataQualityRuleSets
  const dispatch = useDispatch();
  const [items, setItems] = useState(Defaults.pagedResponse);
  const [filter, setFilter] = useState(Defaults.filter);
  const [loading, setLoading] = useState(true);
  const client = useClient();
  //const { enqueueSnackbar } = useSnackbar();
  const [selectionModel, setSelectionModel] = useState([]);

  const fetchItems = useCallback(async () => {
    setLoading(true);
    setItems({
      totalCount: 1,
      nodes: [
        {
          rulesetUri: 'someUri',
          name: 'ruleNumber1',
          description: 'checks for null values',
          ruleSyntax: 'NULLexp',
          dqExpression: '',
          columns: 'column1'
        }
      ]
    });
    // const response = await client.query(listTableDataQualityRuleSets(filter));
    // if (!response.errors) {
    //   setItems(response.data.listTableDataQualityRuleSets);
    // } else {
    //   dispatch({ type: SET_ERROR, error: response.errors[0].message });
    // }
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
        <title>Data Quality Rules | data.all</title>
      </Helmet>
      <Box
        sx={{
          backgroundColor: 'background.default',
          minHeight: '100%',
          py: 5
        }}
      >
        <Card>
          <Box sx={{ minWidth: 600, height: 400 }}>
            <DataGrid
              rows={items.nodes}
              columns={[
                {
                  field: 'rulesetUri',
                  headerName: 'Ruleset identifier',
                  flex: 1
                },
                {
                  field: 'name',
                  headerName: 'Rule name',
                  flex: 1
                },
                {
                  field: 'description',
                  headerName: 'Rule description',
                  flex: 1
                },
                {
                  field: 'ruleSyntax',
                  headerName: 'Rule syntax',
                  flex: 1
                },
                {
                  field: 'dqExpression',
                  headerName: 'Rule expression',
                  flex: 1
                },
                {
                  field: 'columns',
                  headerName: 'Columns',
                  flex: 1
                }
              ]}
              getRowId={(row) => row.rulesetUri}
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

TableQuality.propTypes = {
  table: PropTypes.object.isRequired,
  isAdmin: PropTypes.bool.isRequired
};
