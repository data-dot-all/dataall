import { Box, Button, Container, Typography } from '@mui/material';
import CircularProgress from '@mui/material/CircularProgress';
import React, { useCallback, useEffect, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { Defaults, Pager, PlusIcon, useSettings } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
//import { listWarehousesConnections } from '../services';
import { ConnectionsListItem } from './ConnectionsListItem';

//TODO: we could also use DataGrid, but then the filtering is not that nice, to decide

export const ConnectionsList = () => {
  const dispatch = useDispatch();
  const [items, setItems] = useState(Defaults.pagedResponse);
  const [filter, setFilter] = useState(Defaults.filter);
  const { settings } = useSettings();
  // const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(true);
  const client = useClient();

  // const handleInputChange = (event) => {
  //   setInputValue(event.target.value);
  //   setFilter({ ...filter, term: event.target.value });
  // };
  //
  // const handleInputKeyup = (event) => {
  //   if (event.code === 'Enter') {
  //     setFilter({ page: 1, term: event.target.value });
  //     fetchItems().catch((e) =>
  //       dispatch({ type: SET_ERROR, error: e.message })
  //     );
  //   }
  // };
  const handlePageChange = async (event, value) => {
    if (value <= items.pages && value !== items.page) {
      await setFilter({ ...filter, page: value });
    }
  };

  const fetchItems = useCallback(async () => {
    setLoading(true);
    setItems({
      nodes: [
        {
          name: 'item1',
          connectionUri: 'item1',
          type: 'Secrets Manager',
          content: 'arn:aws:secretsmanager:Region:AccountId:secret:SecretName1',
          warehouseType: 'RedshiftCluster',
          warehouseId: 'clusterId1',
          SamlAdminGroupName: 'Engineers'
        },
        {
          name: 'item2',
          connectionUri: 'item2',
          type: 'Secrets Manager',
          content: 'arn:aws:secretsmanager:Region:AccountId:secret:SecretName2',
          warehouseType: 'RedshiftServerless',
          warehouseId: 'namespaceId1',
          SamlAdminGroupName: 'Engineers'
        },
        {
          name: 'item3',
          connectionUri: 'item3',
          type: 'Federated user',
          content: 'arn:aws:iam::AccountId:role/role3',
          warehouseType: 'RedshiftServerless',
          warehouseId: 'namespaceId1',
          SamlAdminGroupName: 'Engineers'
        }
      ]
    });
    // TODO: implement methods
    // const response = await client.query(listWarehousesConnections(filter));
    // if (!response.errors) {
    //   setItems(response.data.listWarehousesConnections);
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

  if (loading) {
    return <CircularProgress />;
  }

  return (
    <>
      <Helmet>
        <title>Warehouse Connections | data.all</title>
      </Helmet>
      <Box sx={{ m: -1 }}>
        <Button
          color="primary"
          startIcon={<PlusIcon fontSize="small" />}
          sx={{ m: 1 }}
          //TODO: HANDLE window that opens for create
          //onClick={handleCreateConnectionModalOpen}
          variant="contained"
        >
          Create Warehouse Connection
        </Button>
      </Box>
      <Box
        sx={{
          backgroundColor: 'background.default',
          minHeight: '100%',
          py: 1
        }}
      >
        <Container maxWidth={settings.compact ? 'xl' : false}>
          <Box
            sx={{
              mt: 3
            }}
          >
            {items.nodes.length <= 0 ? (
              <Typography color="textPrimary" variant="subtitle2">
                No warehouse connections registered in data.all.
              </Typography>
            ) : (
              <Box>
                {items.nodes.map((node) => (
                  <ConnectionsListItem connection={node} />
                ))}

                <Pager items={items} onChange={handlePageChange} />
              </Box>
            )}
          </Box>
        </Container>
      </Box>
    </>
  );
};
