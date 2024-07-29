import React, { useCallback, useEffect, useState } from 'react';
import { Box, Card, Grid } from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import * as PropTypes from 'prop-types';
import { useClient } from 'services';
import { Defaults, PlusIcon } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { LoadingButton } from '@mui/lab';
import { QualityRuleCreateModal } from './QualityRuleCreateModal';

// TODO: listRules API query
//import { listTableDataQualityRuleSets, deleteTableDataQualityRuleSets } from '../services';

export const TableQuality = (props) => {
  const { table, isAdmin } = props;
  const dispatch = useDispatch();
  const [items, setItems] = useState(Defaults.pagedResponse);
  const [filter, setFilter] = useState(Defaults.filter);
  const [loading, setLoading] = useState(true);
  const client = useClient();
  //const { enqueueSnackbar } = useSnackbar();
  const [selectionModel, setSelectionModel] = useState([]);
  const [isRuleCreateModalOpen, setIsRuleCreateModalOpen] = useState(false);

  const handleRuleCreateModalOpen = () => {
    setIsRuleCreateModalOpen(true);
  };

  const handleRuleCreateModalClose = () => {
    setIsRuleCreateModalOpen(false);
  };

  const fetchItems = useCallback(async () => {
    //TODO: REPLACE WITH LIST RESPONSE
    setLoading(true);
    setItems({
      totalCount: 1,
      nodes: [
        {
          rulesetUri: 'someUri',
          name: table.name,
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
    <Box>
      <Grid container wrap="wrap" justifyContent="flex-end">
        <Grid item md={9.5} sm={8} xs={12} />
        {isAdmin && (
          <Grid item md={2.5} sm={4} xs={12}>
            <Box sx={{ ml: 10 }}>
              <LoadingButton
                color="primary"
                onClick={handleRuleCreateModalOpen}
                startIcon={<PlusIcon fontSize="small" />}
                sx={{ m: 1 }}
                variant="contained"
              >
                Add new rule
              </LoadingButton>
            </Box>
          </Grid>
        )}
      </Grid>
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
      {isRuleCreateModalOpen && (
        <QualityRuleCreateModal
          table={table}
          onApply={handleRuleCreateModalClose}
          onClose={handleRuleCreateModalClose}
          open={isRuleCreateModalOpen}
        />
      )}
    </Box>
  );
};

TableQuality.propTypes = {
  table: PropTypes.object.isRequired,
  isAdmin: PropTypes.bool.isRequired
};
