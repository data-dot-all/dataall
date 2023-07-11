// TODO completely
import { useCallback, useEffect, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Breadcrumbs,
  Button,
  Container,
  Grid,
  Link,
  Typography
} from '@mui/material';
import CircularProgress from '@mui/material/CircularProgress';
import { Helmet } from 'react-helmet-async';
import useClient from '../../hooks/useClient';
import * as Defaults from '../../components/defaults';
import ChevronRightIcon from '../../icons/ChevronRight';
import PlusIcon from '../../icons/Plus';
import useSettings from '../../hooks/useSettings';
import SearchInput from '../../components/SearchInput';
import Pager from '../../components/Pager';
import { useDispatch } from '../../store';
import { SET_ERROR } from '../../store/errorReducer';
import OmicsWorkflowsListItem from './OmicsWorkflowsListItem';
import listSagemakerStudioUsers from '../../api/MLStudio/listSagemakerStudioUsers';

function MLStudioPageHeader() {
  return (
    <Grid
      alignItems="center"
      container
      justifyContent="space-between"
      spacing={3}
    >
      <Grid item>
        <Typography color="textPrimary" variant="h5">
          ML Studio
        </Typography>
        <Breadcrumbs
          aria-label="breadcrumb"
          separator={<ChevronRightIcon fontSize="small" />}
          sx={{ mt: 1 }}
        >
          <Link underline="hover" color="textPrimary" variant="subtitle2">
            Play
          </Link>
          <Link
            underline="hover"
            color="textPrimary"
            component={RouterLink}
            to="/console/mlstudio"
            variant="subtitle2"
          >
            ML Studio
          </Link>
        </Breadcrumbs>
      </Grid>
      <Grid item>
        <Box sx={{ m: -1 }}>
          <Button
            color="primary"
            component={RouterLink}
            startIcon={<PlusIcon fontSize="small" />}
            sx={{ m: 1 }}
            to="/console/mlstudio/new"
            variant="contained"
          >
            Create
          </Button>
        </Box>
      </Grid>
    </Grid>
  );
}

const OmicsWorkflowsList = () => {
  const dispatch = useDispatch();
  const [items, setItems] = useState(Defaults.PagedResponseDefault);
  const [filter, setFilter] = useState(Defaults.DefaultFilter);
  const { settings } = useSettings();
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(true);
  const client = useClient();

  const fetchItems = useCallback(async () => {
    setLoading(true);
    const response = await client.query(listSagemakerStudioUsers(filter));
    if (!response.errors) {
      setItems(response.data.listSagemakerStudioUsers);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [client, dispatch, filter]);

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
        <title>ML Studio | data.all</title>
      </Helmet>
      <Box
        sx={{
          backgroundColor: 'background.default',
          minHeight: '100%',
          py: 5
        }}
      >
        <Container maxWidth={settings.compact ? 'xl' : false}>
          <MLStudioPageHeader />
          <Box sx={{ mt: 3 }}>
            <SearchInput
              onChange={handleInputChange}
              onKeyUp={handleInputKeyup}
              value={inputValue}
            />
          </Box>

          <Box
            sx={{
              flexGrow: 1,
              mt: 3
            }}
          >
            {loading ? (
              <CircularProgress />
            ) : (
              <Box>
                <Grid container spacing={3}>
                  {items.nodes.map((node) => (
                    <OmicsWorkflowsListItem mlstudiouser={node} />
                  ))}
                </Grid>

                <Pager items={items} onChange={handlePageChange} />
              </Box>
            )}
          </Box>
        </Container>
      </Box>
    </>
  );
};

export default OmicsWorkflowsList;
