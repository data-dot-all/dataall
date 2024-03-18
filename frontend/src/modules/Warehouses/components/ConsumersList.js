import { Box, Button, Container, Typography } from '@mui/material';
import CircularProgress from '@mui/material/CircularProgress';
import React, { useCallback, useEffect, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { Defaults, Pager, PlusIcon, useSettings } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import { listWarehouseConsumers } from '../services';
import { ConsumersListItem } from './ConsumersListItem';

// TODO posibility to merge both ConsumerList and RolesList into a single component with conditions. Leaving it as is for demo purposes

export const ConsumersList = () => {
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
    const response = await client.query(listWarehouseConsumers(filter));
    if (!response.errors) {
      setItems(response.data.listWarehouseConsumers);
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

  if (loading) {
    return <CircularProgress />;
  }

  return (
    <>
      <Helmet>
        <title>Warehouse Roles | data.all</title>
      </Helmet>
      <Box sx={{ m: -1 }}>
        <Button
          color="primary"
          startIcon={<PlusIcon fontSize="small" />}
          sx={{ m: 1 }}
          //TODO: HANDLE window that opens for create
          //onClick={handleCreateConsumerModalOpen}
          variant="contained"
        >
          Create Warehouse Consumer
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
                No warehouse roles registered in data.all.
              </Typography>
            ) : (
              <Box>
                {items.nodes.map((node) => (
                  <ConsumersListItem consumer={node} />
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
