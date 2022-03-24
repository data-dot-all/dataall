import { useEffect, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { Box, Breadcrumbs, Button, Container, Grid, Link, Typography } from '@material-ui/core';
import CircularProgress from '@material-ui/core/CircularProgress';
import { Helmet } from 'react-helmet-async';
import { CloudDownloadOutlined } from '@material-ui/icons';
import useClient from '../../hooks/useClient';
import * as Defaults from '../../components/defaults';
import ChevronRightIcon from '../../icons/ChevronRight';
import PlusIcon from '../../icons/Plus';
import useSettings from '../../hooks/useSettings';
import SearchInput from '../../components/SearchInput';
import Pager from '../../components/Pager';
import DatasetListItem from './DatasetListItem';
import { useDispatch } from '../../store';
import { SET_ERROR } from '../../store/errorReducer';
import listDatasets from '../../api/Dataset/listDatasets';

function DatasetsPageHeader() {
  return (
    <Grid
      alignItems="center"
      container
      justifyContent="space-between"
      spacing={3}
    >
      <Grid item>
        <Typography
          color="textPrimary"
          variant="h5"
        >
          Datasets
        </Typography>
        <Breadcrumbs
          aria-label="breadcrumb"
          separator={<ChevronRightIcon fontSize="small" />}
          sx={{ mt: 1 }}
        >
          <Link
            color="textPrimary"
            variant="subtitle2"
          >
            Contribute
          </Link>
          <Link
            color="textPrimary"
            component={RouterLink}
            to="/console/datasets"
            variant="subtitle2"
          >
            Datasets
          </Link>
        </Breadcrumbs>
      </Grid>
      <Grid item>
        <Box sx={{ m: -1 }}>
          <Button
            color="primary"
            component={RouterLink}
            startIcon={<CloudDownloadOutlined fontSize="small" />}
            sx={{ m: 1 }}
            to="/console/datasets/import"
            variant="outlined"
          >
            Import
          </Button>
          <Button
            color="primary"
            component={RouterLink}
            startIcon={<PlusIcon fontSize="small" />}
            sx={{ m: 1 }}
            to="/console/datasets/new"
            variant="contained"
          >
            Create
          </Button>
        </Box>
      </Grid>
    </Grid>
  );
}

const DatasetList = () => {
  const dispatch = useDispatch();
  const [items, setItems] = useState(Defaults.PagedResponseDefault);
  const [filter, setFilter] = useState({ term: '', page: 1, pageSize: 10 });
  const { settings } = useSettings();
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(true);
  const client = useClient();
  const fetchItems = async () => {
    setLoading(true);
    await client.query(listDatasets({ filter: {
      ...filter
    } })).then((response) => {
      const nodes = response.data.listDatasets.nodes.map((env) => ({
        ...env
      }));
      setItems({ ...items, ...response.data.listDatasets, nodes });
    }).catch((error) => {
      dispatch({ type: SET_ERROR, error: error.Error });
    }).finally(() => (setLoading(false)));
  };

  const handleInputChange = (event) => {
    setInputValue(event.target.value);
    setFilter({ ...filter, term: event.target.value });
  };

  const handleInputKeyup = (event) => {
    if ((event.code === 'Enter')) {
      fetchItems();
    }
  };

  const handlePageChange = async (event, value) => {
    if (value <= items.pages && value !== items.page) {
      await setFilter({ ...filter, page: value });
    }
  };

  useEffect(() => {
    if (client) {
      fetchItems();
    }
  }, [client, filter.page]);

  return (
    <>
      <Helmet>
        <title>Datasets | data.all</title>
      </Helmet>
      <Box
        sx={{
          backgroundColor: 'background.default',
          minHeight: '100%',
          py: 5
        }}
      >
        <Container maxWidth={settings.compact ? 'xl' : false}>
          <DatasetsPageHeader />
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
            {loading ? <CircularProgress />
              : (
                <Box>
                  <Grid
                    container
                    spacing={3}
                  >
                    {items.nodes.map((node) => (
                      <DatasetListItem dataset={node} />
                    ))}
                  </Grid>

                  <Pager
                    items={items}
                    onChange={handlePageChange}
                  />
                </Box>
              )}
          </Box>
        </Container>
      </Box>
    </>
  );
};

export default DatasetList;
