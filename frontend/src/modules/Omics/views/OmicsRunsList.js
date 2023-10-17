import React, { useCallback, useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardHeader,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow
} from '@mui/material';
import CircularProgress from '@mui/material/CircularProgress';
import { Helmet } from 'react-helmet-async';

import { useClient } from 'services';
import { Defaults, Pager, Scrollbar } from 'design';
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

  const handlePageChange = async (event, value) => {
    if (value <= items.pages && value !== items.page) {
      await setFilter({ ...filter, page: value });
    }
  };

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
          <CardHeader title="Omics runs" />
          <Divider />
          <Scrollbar>
            <Box sx={{ minWidth: 600 }}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Run identifier</TableCell>
                    <TableCell>Run name</TableCell>
                    <TableCell>Workflow id</TableCell>
                    <TableCell>Created</TableCell>
                    <TableCell>Owner</TableCell>
                    <TableCell>Team</TableCell>
                    <TableCell>Environment</TableCell>
                    <TableCell>Output S3</TableCell>
                  </TableRow>
                </TableHead>
                <Divider />
                {loading ? (
                  <CircularProgress sx={{ mt: 1 }} size={20} />
                ) : (
                  <TableBody>
                    {items.nodes.length > 0 ? (
                      items.nodes.map((item) => (
                        <TableRow hover>
                          <TableCell>{item.runUri}</TableCell>
                          <TableCell>{item.label}</TableCell>
                          <TableCell>{item.workflowId}</TableCell>
                          <TableCell>{item.created}</TableCell>
                          <TableCell>{item.owner}</TableCell>
                          <TableCell>{item.SamlAdminGroupName}</TableCell>
                          <TableCell>{item.environment.label}</TableCell>
                          <TableCell>{item.outputUri}</TableCell>
                        </TableRow>
                      ))
                    ) : (
                      <TableRow>
                        <TableCell>No items added.</TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                )}
              </Table>
              {items.nodes.length > 0 && (
                <Pager
                  mgTop={2}
                  mgBottom={2}
                  items={items}
                  onChange={handlePageChange}
                />
              )}
            </Box>
          </Scrollbar>
        </Card>
      </Box>
    </>
  );
};
