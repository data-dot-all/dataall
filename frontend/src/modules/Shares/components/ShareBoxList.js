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
  listAllGroups,
  listAllConsumptionRoles,
  listDatasetShareObjects,
  getShareRequestsToMe,
  useClient
} from 'services';
import { getShareRequestsFromMe, listOwnedDatasets } from '../services';

import { ShareBoxListItem } from './ShareBoxListItem';
import { ShareStatusList } from '../constants';

const icon = <CheckBoxOutlineBlankIcon fontSize="small" />;
const checkedIcon = <CheckBoxIcon fontSize="small" />;

export const ShareBoxList = (props) => {
  const { tab, dataset } = props;
  const dispatch = useDispatch();
  const { settings } = useSettings();
  const [loading, setLoading] = useState(true);
  const client = useClient();
  const [items, setItems] = useState(Defaults.pagedResponse);
  const [filter, setFilter] = useState(Defaults.filter);
  const [requestGroupOptions, setRequestGroupOptions] = useState([]);
  const [roleOptions, setRoleOptions] = useState([]);
  const [datasetGroupOptions, setDatasetGroupOptions] = useState([]);
  const [datasets, setDatasets] = useState([]);
  const statusOptions = ShareStatusList;

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
    } else if (filterLabel === 'DatasetOwners') {
      setFilter({ ...filter, dataset_owners: values });
    } else if (filterLabel === 'RequestOwners') {
      setFilter({ ...filter, share_requesters: values });
    } else if (filterLabel === 'RequestIAMRole') {
      setFilter({ ...filter, share_iam_roles: values });
    }
  };

  const fetchDatasetItems = useCallback(async () => {
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
    await client
      .query(
        getShareRequestsFromMe({
          filter: {
            ...filter
          }
        })
      )
      .then((response) => {
        setItems(response.data.getShareRequestsFromMe);
      })
      .catch((error) => {
        dispatch({ type: SET_ERROR, error: error.Error });
      })
      .finally(() => setLoading(false));
  }, [client, dispatch, filter]);

  const fetchInboxItems = useCallback(async () => {
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

  const fetchMyGroupsOptions = useCallback(async () => {
    const response = await client.query(
      listAllGroups({
        filter: Defaults.selectListFilter
      })
    );
    if (!response.errors) {
      if (tab === 'inbox') {
        setDatasetGroupOptions(
          response.data.listAllGroups.nodes.map((node) => node.groupUri)
        );
      } else {
        setRequestGroupOptions(
          response.data.listAllGroups.nodes.map((node) => node.groupUri)
        );
        const groupRoleOptions = response.data.listAllGroups.nodes.map(
          (node) => node.environmentIAMRoleName
        );
        const response2 = await client.query(
          listAllConsumptionRoles({
            filter: Defaults.selectListFilter
          })
        );
        if (!response2.errors) {
          /* eslint-disable no-console */
          console.log('good');
          console.log(groupRoleOptions);
          setRoleOptions(
            groupRoleOptions.concat(
              response2.data.listAllConsumptionRoles.nodes.map(
                (node) => node.IAMRoleName
              )
            )
          );
        } else {
          dispatch({ type: SET_ERROR, error: response2.errors[0].message });
        }
      }
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [client, dispatch, tab]);

  const fetchInboxGroupOptions = useCallback(async () => {
    await client
      .query(
        getShareRequestsToMe({
          filter: Defaults.selectListFilter
        })
      )
      .then((response) => {
        setRequestGroupOptions(
          Array.from(
            new Set(
              response.data.getShareRequestsToMe.nodes.map(
                (node) => node.principal.SamlGroupName
              )
            )
          )
        );
        setRoleOptions(
          Array.from(
            new Set(
              response.data.getShareRequestsToMe.nodes.map(
                (node) => node.principal.principalIAMRoleName
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

  const fetchInboxDatasetsOptions = useCallback(async () => {
    setLoading(true);
    const response = await client.query(
      listOwnedDatasets({ filter: Defaults.selectListFilter })
    );
    if (!response.errors) {
      setDatasets(
        response.data.listOwnedDatasets.nodes.map((node) => ({
          label: node.label,
          value: node.datasetUri
        }))
      );
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [client, dispatch]);

  const fetchOutboxGroupAndDatasetOptions = useCallback(async () => {
    await client
      .query(
        getShareRequestsFromMe({
          filter: Defaults.selectListFilter
        })
      )
      .then((response) => {
        const alldatasets = response.data.getShareRequestsFromMe.nodes.map(
          (node) => ({
            label: node.dataset.datasetName,
            value: node.dataset.datasetUri
          })
        );
        setDatasets(
          Array.from(
            new Map(alldatasets.map((item) => [item['value'], item])).values()
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
      })
      .catch((error) => {
        dispatch({ type: SET_ERROR, error: error.Error });
      })
      .finally(() => setLoading(false));
  }, [client, dispatch]);

  useEffect(() => {
    if (client) {
      fetchMyGroupsOptions().catch((error) => {
        dispatch({ type: SET_ERROR, error: error.message });
      });
      if (tab === 'inbox') {
        if (!dataset) {
          fetchInboxDatasetsOptions().catch((error) => {
            dispatch({ type: SET_ERROR, error: error.message });
          });
        }
        fetchInboxGroupOptions().catch((error) => {
          dispatch({ type: SET_ERROR, error: error.message });
        });
      } else {
        setRoleOptions([]);
        fetchOutboxGroupAndDatasetOptions().catch((error) => {
          dispatch({ type: SET_ERROR, error: error.message });
        });
      }
      setFilter(Defaults.filter);
    }
  }, [
    client,
    dispatch,
    tab,
    dataset,
    fetchInboxDatasetsOptions,
    fetchInboxGroupOptions,
    fetchOutboxGroupAndDatasetOptions,
    fetchMyGroupsOptions
  ]);

  useEffect(() => {
    if (client) {
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
  }, [
    client,
    dispatch,
    filter,
    tab,
    dataset,
    fetchDatasetItems,
    fetchInboxItems,
    fetchOutboxItems
  ]);

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
              <Grid item md={2} xs={12}>
                <Autocomplete
                  id={'Status-' + tab}
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
              <Grid item md={2.5} xs={12}>
                <Autocomplete
                  id={'RequestOwners-' + tab}
                  multiple
                  fullWidth
                  loading={loading}
                  options={requestGroupOptions}
                  onChange={(event, value) =>
                    handleFilterChange('RequestOwners', value)
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
              <Grid item md={2.5} xs={12}>
                <Autocomplete
                  id={'RequestIAMRole-' + tab}
                  multiple
                  fullWidth
                  loading={loading}
                  options={roleOptions}
                  onChange={(event, value) =>
                    handleFilterChange('RequestIAMRole', value)
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
                      label={'Request IAM role name'}
                      fullWidth
                      variant="outlined"
                    />
                  )}
                />
              </Grid>
              {!dataset && (
                <Grid item md={2.5} xs={12}>
                  <Autocomplete
                    id={'Datasets-' + tab}
                    multiple
                    fullWidth
                    disableCloseOnSelect
                    loading={loading}
                    options={datasets}
                    getOptionLabel={(option) => option.label || ''}
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
                <Grid item md={2.5} xs={12}>
                  <Autocomplete
                    id={'DatasetOwners-' + tab}
                    multiple
                    fullWidth
                    disableCloseOnSelect
                    loading={loading}
                    options={datasetGroupOptions}
                    onChange={(event, value) =>
                      handleFilterChange('DatasetOwners', value)
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
                        label={'Dataset Owners'}
                        fullWidth
                        variant="outlined"
                      />
                    )}
                  />
                </Grid>
              )}
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
