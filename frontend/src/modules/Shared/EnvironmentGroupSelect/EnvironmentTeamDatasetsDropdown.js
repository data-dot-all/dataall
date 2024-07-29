import {
  Autocomplete,
  Box,
  Card,
  CardContent,
  CardHeader,
  CircularProgress,
  TextField
} from '@mui/material';
import React, { useCallback, useEffect, useState } from 'react';
import { Defaults } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import {
  listEnvironmentGroups,
  listValidEnvironments,
  listS3DatasetsOwnedByEnvGroup,
  useClient
} from 'services';

import PropTypes from 'prop-types';

export const EnvironmentTeamDatasetsDropdown = (props) => {
  const { setFieldValue, handleChange, values, touched, errors } = props;
  const dispatch = useDispatch();
  const client = useClient();
  const [loading, setLoading] = useState(true);
  const [groupOptions, setGroupOptions] = useState([]);
  const [environmentOptions, setEnvironmentOptions] = useState([]);
  const [currentEnv, setCurrentEnv] = useState('');
  const [datasetOptions, setDatasetOptions] = useState([]);
  const fetchEnvironments = useCallback(async () => {
    setLoading(true);
    const response = await client.query(
      listValidEnvironments({ filter: Defaults.SelectListFilter })
    );
    if (!response.errors) {
      setEnvironmentOptions(
        response.data.listValidEnvironments.nodes.map((e) => ({
          ...e,
          value: e.environmentUri,
          label: e.label
        }))
      );
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [client, dispatch]);
  const fetchGroups = async (environmentUri) => {
    setCurrentEnv(environmentUri);
    try {
      const response = await client.query(
        listEnvironmentGroups({
          filter: Defaults.SelectListFilter,
          environmentUri
        })
      );
      if (!response.errors) {
        setGroupOptions(
          response.data.listEnvironmentGroups.nodes.map((g) => ({
            value: g.groupUri,
            label: g.groupUri
          }))
        );
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    }
  };
  const fetchDatasets = async (groupUri) => {
    let ownedDatasets = [];
    try {
      const response = await client.query(
        listS3DatasetsOwnedByEnvGroup({
          filter: Defaults.SelectListFilter,
          environmentUri: currentEnv,
          groupUri: groupUri
        })
      );
      if (!response.errors) {
        ownedDatasets = response.data.listS3DatasetsOwnedByEnvGroup.nodes?.map(
          (dataset) => ({
            value: dataset.datasetUri,
            label: dataset.label
          })
        );
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    }
    setDatasetOptions(ownedDatasets);
  };

  useEffect(() => {
    if (client) {
      fetchEnvironments().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, dispatch, fetchEnvironments]);

  if (loading) {
    return <CircularProgress />;
  }

  return (
    <Box>
      <Card sx={{ mb: 3 }}>
        <CardHeader title="Deployment" />
        <CardContent>
          <Autocomplete
            id="environment"
            disablePortal
            options={environmentOptions.map((option) => option)}
            onChange={(event, value) => {
              setFieldValue('SamlAdminGroupName', '');
              setFieldValue('dataset', '');
              if (value && value.environmentUri) {
                setFieldValue('environment', value);
                fetchGroups(value.environmentUri).catch((e) =>
                  dispatch({
                    type: SET_ERROR,
                    error: e.message
                  })
                );
              } else {
                setFieldValue('environment', '');
                setGroupOptions([]);
                setDatasetOptions([]);
              }
            }}
            renderInput={(params) => (
              <TextField
                {...params}
                fullWidth
                error={Boolean(touched.environmentUri && errors.environmentUri)}
                helperText={touched.environmentUri && errors.environmentUri}
                label="Environment"
                value={values.environment}
                onChange={handleChange}
                variant="outlined"
              />
            )}
          />
        </CardContent>
        <CardContent>
          <TextField
            disabled
            fullWidth
            label="Region"
            name="region"
            value={
              values.environment && values.environment.region
                ? values.environment.region
                : ''
            }
            variant="outlined"
          />
        </CardContent>
        <CardContent>
          <TextField
            disabled
            fullWidth
            label="Organization"
            name="organization"
            value={
              values.environment && values.environment.organization
                ? values.environment.organization.label
                : ''
            }
            variant="outlined"
          />
        </CardContent>
        <CardContent>
          <Autocomplete
            id="SamlAdminGroupName"
            disablePortal
            options={groupOptions.map((option) => option)}
            onChange={(event, value) => {
              setFieldValue('dataset', '');
              if (value && value.value) {
                setFieldValue('SamlAdminGroupName', value.value);
                fetchDatasets(value.value).catch((e) =>
                  dispatch({ type: SET_ERROR, error: e.message })
                );
              } else {
                setFieldValue('SamlAdminGroupName', '');
                setDatasetOptions([]);
              }
            }}
            inputValue={values.SamlAdminGroupName}
            renderInput={(params) => (
              <Box>
                {groupOptions.length > 0 ? (
                  <TextField
                    {...params}
                    fullWidth
                    error={Boolean(
                      touched.SamlAdminGroupName && errors.SamlAdminGroupName
                    )}
                    helperText={
                      touched.SamlAdminGroupName && errors.SamlAdminGroupName
                    }
                    label="Team"
                    onChange={handleChange}
                    variant="outlined"
                  />
                ) : (
                  <TextField
                    error={Boolean(
                      touched.SamlAdminGroupName && errors.SamlAdminGroupName
                    )}
                    helperText={
                      touched.SamlAdminGroupName && errors.SamlAdminGroupName
                    }
                    fullWidth
                    disabled
                    label="Team"
                    value="No teams found for this environment"
                    variant="outlined"
                  />
                )}
              </Box>
            )}
          />
        </CardContent>
        <CardContent>
          <Autocomplete
            id="dataset"
            disablePortal
            options={datasetOptions.map((option) => option)}
            onChange={(event, value) => {
              if (value && value.value) {
                setFieldValue('dataset', value.value);
              } else {
                setFieldValue('dataset', '');
              }
            }}
            inputValue={values.dataset}
            renderInput={(params) => (
              <Box>
                {datasetOptions.length > 0 ? (
                  <TextField
                    {...params}
                    fullWidth
                    error={Boolean(touched.dataset && errors.dataset)}
                    helperText={touched.dataset && errors.dataset}
                    label="Select S3 Output Dataset"
                    onChange={handleChange}
                    variant="outlined"
                  />
                ) : (
                  <TextField
                    error={Boolean(touched.dataset && errors.dataset)}
                    helperText={touched.dataset && errors.dataset}
                    fullWidth
                    disabled
                    label="Select S3 Output Dataset"
                    value="No datasets found for this team in this environment"
                    variant="outlined"
                  />
                )}
              </Box>
            )}
          />
        </CardContent>
      </Card>
    </Box>
  );
};

EnvironmentTeamDatasetsDropdown.propTypes = {
  setFieldValue: PropTypes.func.isRequired,
  handleChange: PropTypes.func.isRequired,
  values: PropTypes.object.isRequired,
  touched: PropTypes.object.isRequired,
  errors: PropTypes.object.isRequired
};
