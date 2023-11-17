import {
  Autocomplete,
  Box,
  Checkbox,
  Container,
  Grid,
  TextField,
  Typography
} from '@mui/material';
import CircularProgress from '@mui/material/CircularProgress';
import CheckBoxOutlineBlankIcon from '@mui/icons-material/CheckBoxOutlineBlank';
import CheckBoxIcon from '@mui/icons-material/CheckBox';
import PropTypes from 'prop-types';
import { useCallback, useEffect, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { Defaults, Pager, ShareStatus, useSettings } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import {
  listDatasetShareObjects,
  getShareRequestsToMe,
  useClient
} from 'services';
import { getShareRequestsFromMe } from '../services';

import { ShareBoxListItem } from './ShareBoxListItem';
import { listDatasets } from '../../Datasets/services';
//TODO MANAGE DEPENDENCY

const icon = <CheckBoxOutlineBlankIcon fontSize="small" />;
const checkedIcon = <CheckBoxIcon fontSize="small" />;

export const ShareBoxList = (props) => {
  const { tab, dataset } = props;
  const dispatch = useDispatch();
  const [items, setItems] = useState(Defaults.pagedResponse);
  const [filter, setFilter] = useState(Defaults.filter);
  const [requestGroupOptions, setRequestGroupOptions] = useState([]);
  const [datasetGroupOptions, setDatasetGroupOptions] = useState([]);
  const [datasets, setDatasets] = useState([]); //all in listDatasets, either shared with me or owned by my teams
  const statusOptions = [
    'Draft',
    'Submitted',
    'Approved',
    'Rejected',
    'Revoked',
    'Share_In_Progress',
    'Revoke_In_Progress',
    'Processed'
  ];
  // In Received, dataset_owners : All groups I belong to
  // In Received, request_owners: All groups that have a request open to one of my datasets or All groups alternatively
  // In Sent, dataset_owners : All groups that have a dataset with a request open by one of my share requests. or All groups
  // In Sent, request_owners: All groups I belong to
  const { settings } = useSettings();
  const [loading, setLoading] = useState(true);
  const client = useClient();

  const handlePageChange = async (event, value) => {
    if (value <= items.pages && value !== items.page) {
      await setFilter({ ...filter, page: value });
    }
  };

  const handleFilterChange = (filterLabel, values) => {
    if (filterLabel === 'Status') {
      setFilter({ ...filter, status: values });
    } else if (filterLabel === 'Datasets') {
      const selectedDatasetsUris = values.map((dataset) => dataset.value);
      setFilter({ ...filter, datasets_uris: selectedDatasetsUris });
    } else if (filterLabel === 'Dataset Owners') {
      setFilter({ ...filter, dataset_owners: values });
    } else if (filterLabel === 'Request Owners') {
      setFilter({ ...filter, share_requesters: values });
    }
  };

  const fetchDatasetItems = useCallback(async () => {
    /* eslint-disable no-console */
    console.log('NEW FETCH Dataset');
    console.log(filter);
    await client
      .query(
        listDatasetShareObjects({ datasetUri: dataset.datasetUri, filter })
      )
      .then((response) => {
        setItems(response.data.getDataset.shares);
      })
      .catch((error) => {
        dispatch({ type: SET_ERROR, error: error.Error });
      })
      .finally(() => setLoading(false));
  }, [client, dispatch, dataset, filter]);

  const fetchOutboxItems = useCallback(async () => {
    /* eslint-disable no-console */
    console.log('NEW FETCH Outbox');
    console.log(filter);
    setLoading(true);
    const response = await client.query(
      getShareRequestsFromMe({
        filter: {
          ...filter
        }
      })
    );
    if (!response.errors) {
      setItems(response.data.getShareRequestsFromMe);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [client, dispatch, dataset, filter]);

  const fetchInboxItems = useCallback(async () => {
    /* eslint-disable no-console */
    console.log('NEW Inbox');
    console.log(filter);
    await client
      .query(
        getShareRequestsToMe({
          filter: {
            ...filter
          }
        })
      )
      .then((response) => {
        setItems(response.data.getShareRequestsToMe);
      })
      .catch((error) => {
        dispatch({ type: SET_ERROR, error: error.Error });
      })
      .finally(() => setLoading(false));
  }, [client, dispatch, filter]);

  function fetchItems() {
    if (tab === 'inbox') {
      if (dataset) {
        fetchDatasetItems().catch((error) => {
          dispatch({ type: SET_ERROR, error: error.message });
        });
      } else {
        fetchInboxItems().catch((error) => {
          dispatch({ type: SET_ERROR, error: error.message });
        });
      }
    } else {
      fetchOutboxItems().catch((error) => {
        dispatch({ type: SET_ERROR, error: error.message });
      });
    }
  }

  const fetchInboxGroupOptions = useCallback(async () => {
    /* eslint-disable no-console */
    await client
      .query(
        getShareRequestsToMe({
          filter: {
            ...filter
          }
        })
      )
      .then((response) => {
        setItems(response.data.getShareRequestsToMe);
        setDatasetGroupOptions(['myGroup']);
        /* eslint-disable no-console */
        setRequestGroupOptions(
          Array.from(
            new Set(
              response.data.getShareRequestsToMe.nodes.map(
                (node) => node.principal.SamlGroupName
              )
            )
          )
        );
      })
      .catch((error) => {
        dispatch({ type: SET_ERROR, error: error.Error });
      })
      .finally(() => setLoading(false));
  }, [client, dispatch]);

  const fetchOutboxGroupAndDatasetOptions = useCallback(async () => {
    /* eslint-disable no-console */
    console.log('fetch outbox options');
    await client
      .query(
        getShareRequestsFromMe({
          filter: {
            ...filter
          }
        })
      )
      .then((response) => {
        setItems(response.data.getShareRequestsFromMe); //todo MAYBE REMOVE
        setDatasets(
          Array.from(
            new Set(
              response.data.getShareRequestsFromMe.nodes.map(
                (node) => node.dataset.datasetName
              )
            )
          )
        );
        setDatasetGroupOptions(
          Array.from(
            new Set(
              response.data.getShareRequestsFromMe.nodes.map(
                (node) => node.dataset.SamlAdminGroupName
              )
            )
          )
        );
        /* eslint-disable no-console */
        setRequestGroupOptions(['myGroup']);
      })
      .catch((error) => {
        dispatch({ type: SET_ERROR, error: error.Error });
      })
      .finally(() => setLoading(false));
  }, [client, dispatch]);

  const fetchMyDatasetsOptions = useCallback(async () => {
    setLoading(true);
    const response = await client.query(
      listDatasets(Defaults.selectListFilter)
    );
    if (!response.errors) {
      setDatasets(
        response.data.listDatasets.nodes.map((node) => ({
          ...node,
          label: node.label,
          value: node.datasetUri
        }))
      );
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [client, dispatch, filter]);

  useEffect(() => {
    console.log(tab);
    if ((client, tab)) {
      fetchItems();
    }
  }, [client, filter.page, tab, dispatch]);

  useEffect(() => {
    console.log('tab change');
    if (client) {
      if (tab === 'inbox') {
        if (!dataset) {
          fetchMyDatasetsOptions().catch((error) => {
            dispatch({ type: SET_ERROR, error: error.message });
          });
        }
        fetchInboxGroupOptions().catch((error) => {
          dispatch({ type: SET_ERROR, error: error.message });
        });
      } else {
        fetchOutboxGroupAndDatasetOptions().catch((error) => {
          dispatch({ type: SET_ERROR, error: error.message });
        });
      }
    }
  }, [client, dispatch, tab]);

  if (loading) {
    return <CircularProgress />;
  }

  return (
    <>
      <Helmet>
        <title>Shares {tab} | data.all</title>
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
            <Grid container spacing={2} xs={12}>
              <Grid item md={3} xs={12}>
                <Autocomplete
                  id={'Status'}
                  multiple
                  fullWidth
                  disableCloseOnSelect
                  loading={loading}
                  options={statusOptions}
                  onChange={(event, value) =>
                    handleFilterChange('Status', value)
                  }
                  renderOption={(props, option, { selected }) => (
                    <li {...props}>
                      <Checkbox
                        icon={icon}
                        checkedIcon={checkedIcon}
                        style={{ marginRight: 8 }}
                        checked={selected}
                      />
                      <ShareStatus status={option} />
                    </li>
                  )}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label={'Status'}
                      fullWidth
                      variant="outlined"
                    />
                  )}
                />
              </Grid>
              {!dataset && (
                <Grid item md={3} xs={12}>
                  <Autocomplete
                    id={'Datasets'}
                    multiple
                    fullWidth
                    disableCloseOnSelect
                    loading={loading}
                    options={datasets}
                    getOptionLabel={(option) => option.label}
                    onChange={(event, value) =>
                      handleFilterChange('Datasets', value)
                    }
                    renderOption={(props, option, { selected }) => (
                      <li {...props}>
                        <Checkbox
                          icon={icon}
                          checkedIcon={checkedIcon}
                          style={{ marginRight: 8 }}
                          checked={selected}
                        />
                        {option.label}
                      </li>
                    )}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        label={'Datasets'}
                        fullWidth
                        variant="outlined"
                      />
                    )}
                  />
                </Grid>
              )}
              {!dataset && (
                <Grid item md={3} xs={12}>
                  <Autocomplete
                    id={'Datasets Owners'}
                    multiple
                    fullWidth
                    disableCloseOnSelect
                    loading={loading}
                    options={datasetGroupOptions}
                    onChange={(event, value) =>
                      handleFilterChange('Datasets Owners', value)
                    }
                    renderOption={(props, option, { selected }) => (
                      <li {...props}>
                        <Checkbox
                          icon={icon}
                          checkedIcon={checkedIcon}
                          style={{ marginRight: 8 }}
                          checked={selected}
                        />
                        {option}
                      </li>
                    )}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        label={'Datasets Owners'}
                        fullWidth
                        variant="outlined"
                      />
                    )}
                  />
                </Grid>
              )}
              <Grid item md={3} xs={12}>
                <Autocomplete
                  id={'Request Owners'}
                  multiple
                  fullWidth
                  loading={loading}
                  options={requestGroupOptions}
                  onChange={(event, value) =>
                    handleFilterChange('Request Owners', value)
                  }
                  renderOption={(props, option, { selected }) => (
                    <li {...props}>
                      <Checkbox
                        icon={icon}
                        checkedIcon={checkedIcon}
                        style={{ marginRight: 8 }}
                        checked={selected}
                      />
                      {option}
                    </li>
                  )}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label={'Request Owners'}
                      fullWidth
                      variant="outlined"
                    />
                  )}
                />
              </Grid>
            </Grid>
          </Box>
          <Box
            sx={{
              mt: 3
            }}
          >
            {items.nodes.length <= 0 ? (
              <Typography color="textPrimary" variant="subtitle2">
                No share requests received.
              </Typography>
            ) : (
              <Box>
                {items.nodes.map((node) => (
                  <ShareBoxListItem share={node} reload={fetchItems} />
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

ShareBoxList.propTypes = {
  tab: PropTypes.string.isRequired,
  dataset: PropTypes.object
};
