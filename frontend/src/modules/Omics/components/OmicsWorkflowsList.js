import { Box, Container, Grid, Typography } from '@mui/material';
import CircularProgress from '@mui/material/CircularProgress';
import { useCallback, useEffect, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { Defaults, Pager, SearchInput, useSettings } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import { listOmicsWorkflows } from '../services';
import { OmicsWorkflowsListItem } from './OmicsWorkflowsListItem';

export const OmicsWorkflowsList = () => {
  const dispatch = useDispatch();
  const [items, setItems] = useState(Defaults.pagedResponse);
  const [filter, setFilter] = useState(Defaults.filter);
  const { settings } = useSettings();
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(true);
  const client = useClient();

  const handleInputChange = (event) => {
    setInputValue(event.target.value);
    setFilter({ ...filter, term: event.target.value });
  };

  const handleInputKeyup = (event) => {
    if (event.code === 'Enter') {
      setFilter({ page: 1, term: event.target.value });
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  };
  const handlePageChange = async (event, value) => {
    if (value <= items.pages && value !== items.page) {
      await setFilter({ ...filter, page: value });
    }
  };

  const fetchItems = useCallback(async () => {
    setLoading(true);
    const response = await client.query(listOmicsWorkflows(filter));
    if (!response.errors) {
      setItems(response.data.listOmicsWorkflows);
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
        <title>Workflows | data.all</title>
      </Helmet>
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
              mt: 2
            }}
          >
            <Grid container spacing={0} xs={12}>
              <Grid item md={12} xs={12}>
                <SearchInput
                  onChange={handleInputChange}
                  onKeyUp={handleInputKeyup}
                  value={inputValue}
                />
              </Grid>
            </Grid>
          </Box>
          <Box
            sx={{
              mt: 3
            }}
          >
            {loading ? (
              <CircularProgress />
            ) : (
              <Box>
                {items.nodes.length <= 0 ? (
                  <Typography color="textPrimary" variant="subtitle2">
                    No workflows registered in data.all.
                  </Typography>
                ) : (
                  <Box>
                    {items.nodes.map((node) => (
                      <OmicsWorkflowsListItem workflow={node} />
                    ))}

                    <Pager items={items} onChange={handlePageChange} />
                  </Box>
                )}
              </Box>
            )}
          </Box>
        </Container>
      </Box>
    </>
  );
};
