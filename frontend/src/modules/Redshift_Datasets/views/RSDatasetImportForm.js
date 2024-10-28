import { LoadingButton } from '@mui/lab';
import {
  Autocomplete,
  Box,
  Breadcrumbs,
  Button,
  Card,
  CardContent,
  CardHeader,
  Chip,
  CircularProgress,
  Container,
  FormHelperText,
  Grid,
  Link,
  MenuItem,
  TextField,
  Typography
} from '@mui/material';
import LinearProgress from '@mui/material/LinearProgress';
import { Formik } from 'formik';
import { useSnackbar } from 'notistack';
import React, { useCallback, useEffect, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import * as Yup from 'yup';
import {
  ArrowLeftIcon,
  ChevronRightIcon,
  ChipInput,
  Defaults,
  Scrollbar,
  useSettings
} from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import {
  listEnvironmentGroups,
  listValidEnvironments,
  listEnvironmentRedshiftConnections,
  useClient
} from 'services';
import {
  importRedshiftDataset,
  listRedshiftConnectionSchemas,
  listRedshiftSchemaTables
} from '../services';
import { Topics, ConfidentialityList } from '../../constants';
import config from '../../../generated/config.json';
import { isFeatureEnabled } from 'utils';
import { DataGrid } from '@mui/x-data-grid';

const RSDatasetImportForm = (props) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const client = useClient();
  const { settings } = useSettings();
  const [loading, setLoading] = useState(true);
  const [loadingSchemas, setLoadingSchemas] = useState(false);
  const [loadingTables, setLoadingTables] = useState(false);
  const [groupOptions, setGroupOptions] = useState([]);
  const [environmentOptions, setEnvironmentOptions] = useState([]);
  const [connectionOptions, setConnectionOptions] = useState([]);
  const [schemaOptions, setSchemaOptions] = useState([]);
  const [tableOptions, setTableOptions] = useState(null);
  const [filter, setFilter] = useState(Defaults.filter);
  const [confidentialityOptions] = useState(
    config.modules.datasets_base.features.confidentiality_dropdown === true &&
      config.modules.datasets_base.features.custom_confidentiality_mapping
      ? Object.keys(
          config.modules.datasets_base.features.custom_confidentiality_mapping
        )
      : ConfidentialityList
  );

  const topicsData = Topics.map((t) => ({ label: t, value: t }));

  const fetchEnvironments = useCallback(async () => {
    setLoading(true);
    const response = await client.query(
      listValidEnvironments({
        filter: Defaults.selectListFilter
      })
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
    try {
      const response = await client.query(
        listEnvironmentGroups({
          filter: Defaults.selectListFilter,
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

  const fetchRedshiftConnections = async (environmentUri, groupUri) => {
    try {
      const response = await client.query(
        listEnvironmentRedshiftConnections({
          filter: {
            ...Defaults.selectListFilter,
            environmentUri: environmentUri,
            groupUri: groupUri,
            connectionType: 'DATA_USER'
          }
        })
      );
      if (!response.errors) {
        setConnectionOptions(
          response.data.listEnvironmentRedshiftConnections.nodes.map((g) => ({
            value: g.connectionUri,
            label: `${g.name} [DATABASE: ${g.database}]`
          }))
        );
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    }
  };

  const fetchSchemas = async (connectionUri) => {
    setLoadingSchemas(true);
    try {
      const response = await client.query(
        listRedshiftConnectionSchemas({
          connectionUri
        })
      );
      if (!response.errors) {
        setSchemaOptions(response.data.listRedshiftConnectionSchemas);
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    }
    setLoadingSchemas(false);
  };

  const fetchTables = async (connectionUri, schema) => {
    setLoadingTables(true);
    try {
      const response = await client.query(
        listRedshiftSchemaTables({
          connectionUri,
          schema
        })
      );
      if (!response.errors) {
        setTableOptions(response.data.listRedshiftSchemaTables);
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    }
    setLoadingTables(false);
  };

  useEffect(() => {
    if (client) {
      fetchEnvironments().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, dispatch, fetchEnvironments]);

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = await client.mutate(
        importRedshiftDataset({
          organizationUri: values.environment.organization.organizationUri,
          environmentUri: values.environment.environmentUri,
          owner: '',
          label: values.label,
          SamlAdminGroupName: values.SamlAdminGroupName,
          tags: values.tags,
          description: values.description,
          topics: values.topics ? values.topics.map((t) => t.value) : [],
          stewards: values.stewards,
          confidentiality: values.confidentiality,
          autoApprovalEnabled: values.autoApprovalEnabled,
          connectionUri: values.connection.value,
          schema: values.schema,
          tables: values.tables
        })
      );
      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        enqueueSnackbar('Dataset imported successfully', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        if (
          response.data.importRedshiftDataset.addedTables.successTables.length >
          0
        ) {
          enqueueSnackbar(
            `Tables added: ${response.data.importRedshiftDataset.addedTables.successTables}`,
            {
              anchorOrigin: {
                horizontal: 'right',
                vertical: 'top'
              },
              variant: 'success'
            }
          );
        }
        if (
          response.data.importRedshiftDataset.addedTables.errorTables.length > 0
        ) {
          dispatch({
            type: SET_ERROR,
            error: `The following tables could not be imported, either they do not exist or the connection used has no access to them: ${response.data.importRedshiftDataset.addedTables.errorTables}`
          });
        }
        navigate(
          `/console/redshift-datasets/${response.data.importRedshiftDataset.datasetUri}`
        );
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (err) {
      console.error(err);
      setStatus({ success: false });
      setErrors({ submit: err.message });
      setSubmitting(false);
      dispatch({ type: SET_ERROR, error: err.message });
    }
  }

  if (loading) {
    return <CircularProgress />;
  }

  return (
    <>
      <Helmet>
        <title>Dataset: Redshift Dataset Import | data.all</title>
      </Helmet>
      <Box
        sx={{
          backgroundColor: 'background.default',
          minHeight: '100%',
          py: 8
        }}
      >
        <Container maxWidth={settings.compact ? 'xl' : false}>
          <Grid container justifyContent="space-between" spacing={3}>
            <Grid item>
              <Typography color="textPrimary" variant="h5">
                Import a new Redshift dataset
              </Typography>
              <Breadcrumbs
                aria-label="breadcrumb"
                separator={<ChevronRightIcon fontSize="small" />}
                sx={{ mt: 1 }}
              >
                <Typography color="textPrimary" variant="subtitle2">
                  Contribute
                </Typography>
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to="/console/datasets"
                  variant="subtitle2"
                >
                  Datasets
                </Link>
                <Typography color="textPrimary" variant="subtitle2">
                  Import
                </Typography>
              </Breadcrumbs>
            </Grid>
            <Grid item>
              <Box sx={{ m: -1 }}>
                <Button
                  color="primary"
                  component={RouterLink}
                  startIcon={<ArrowLeftIcon fontSize="small" />}
                  sx={{ mt: 1 }}
                  to="/console/datasets"
                  variant="outlined"
                >
                  Cancel
                </Button>
              </Box>
            </Grid>
          </Grid>
          <Box sx={{ mt: 3 }}>
            <Formik
              initialValues={{
                label: '',
                description: '',
                environment: '',
                SamlAdminGroupName: '',
                stewards: '',
                tags: [],
                topics: [],
                confidentiality: '',
                autoApprovalEnabled: false,
                connection: '',
                schema: '',
                tables: []
              }}
              validationSchema={Yup.object().shape({
                label: Yup.string()
                  .max(255)
                  .required('*Dataset name is required'),
                description: Yup.string().max(5000),
                SamlAdminGroupName: Yup.string()
                  .max(255)
                  .required('*Team is required'),
                topics: isFeatureEnabled('datasets_base', 'topics_dropdown')
                  ? Yup.array().min(1).required('*Topics are required')
                  : Yup.array(),
                environment: Yup.object().required('*Environment is required'),
                tags: Yup.array().min(1).required('*Tags are required'),
                confidentiality: isFeatureEnabled(
                  'datasets_base',
                  'confidentiality_dropdown'
                )
                  ? Yup.string()
                      .max(255)
                      .required('*Confidentiality is required')
                  : Yup.string(),
                autoApprovalEnabled: Yup.boolean().required(
                  '*AutoApproval property is required'
                ),
                connection: Yup.object().required('*Connection is required'),
                schema: Yup.string().required('*Schema is required'),
                tables: Yup.array()
              })}
              onSubmit={async (
                values,
                { setErrors, setStatus, setSubmitting }
              ) => {
                await submit(values, setStatus, setSubmitting, setErrors);
              }}
            >
              {({
                errors,
                handleBlur,
                handleChange,
                handleSubmit,
                isSubmitting,
                setFieldValue,
                touched,
                values
              }) => (
                <form onSubmit={handleSubmit} {...props}>
                  <Grid container spacing={3}>
                    <Grid item lg={6} md={6} xs={12}>
                      <Card>
                        <CardHeader title="Details" />
                        <CardContent>
                          <TextField
                            error={Boolean(touched.label && errors.label)}
                            fullWidth
                            helperText={touched.label && errors.label}
                            label="Dataset name"
                            name="label"
                            onBlur={handleBlur}
                            onChange={handleChange}
                            value={values.label}
                            variant="outlined"
                          />
                        </CardContent>
                        <CardContent>
                          <TextField
                            FormHelperTextProps={{
                              sx: {
                                textAlign: 'right',
                                mr: 0
                              }
                            }}
                            fullWidth
                            error={Boolean(
                              touched.description && errors.description
                            )}
                            helperText={`${
                              200 - values.description.length
                            } characters left`}
                            label="Short description"
                            name="description"
                            multiline
                            onBlur={handleBlur}
                            onChange={handleChange}
                            rows={5}
                            value={values.description}
                            variant="outlined"
                          />
                          {touched.description && errors.description && (
                            <Box sx={{ mt: 2 }}>
                              <FormHelperText error>
                                {errors.description}
                              </FormHelperText>
                            </Box>
                          )}
                        </CardContent>
                      </Card>
                      <Card sx={{ mt: 3 }}>
                        <CardHeader title="Classification" />
                        {isFeatureEnabled(
                          'datasets_base',
                          'confidentiality_dropdown'
                        ) && (
                          <CardContent>
                            <TextField
                              fullWidth
                              error={Boolean(
                                touched.confidentiality &&
                                  errors.confidentiality
                              )}
                              helperText={
                                touched.confidentiality &&
                                errors.confidentiality
                              }
                              label="Confidentiality"
                              name="confidentiality"
                              onChange={handleChange}
                              select
                              value={values.confidentiality}
                              variant="outlined"
                            >
                              {confidentialityOptions.map((c) => (
                                <MenuItem key={c} value={c}>
                                  {c}
                                </MenuItem>
                              ))}
                            </TextField>
                          </CardContent>
                        )}
                        {isFeatureEnabled(
                          'datasets_base',
                          'topics_dropdown'
                        ) && (
                          <CardContent>
                            <Autocomplete
                              multiple
                              id="tags-filled"
                              options={topicsData}
                              getOptionLabel={(opt) => opt.label}
                              onChange={(event, value) => {
                                setFieldValue('topics', value);
                              }}
                              renderTags={(tagValue, getTagProps) =>
                                tagValue.map((option, index) => (
                                  <Chip
                                    label={option.label}
                                    {...getTagProps({ index })}
                                  />
                                ))
                              }
                              renderInput={(p) => (
                                <TextField
                                  {...p}
                                  variant="outlined"
                                  label="Topics"
                                  error={Boolean(
                                    touched.topics && errors.topics
                                  )}
                                  helperText={touched.topics && errors.topics}
                                />
                              )}
                            />
                          </CardContent>
                        )}
                        <CardContent>
                          <Box>
                            <ChipInput
                              fullWidth
                              error={Boolean(touched.tags && errors.tags)}
                              helperText={touched.tags && errors.tags}
                              variant="outlined"
                              label="Tags"
                              placeholder="Hit enter after typing value"
                              onChange={(chip) => {
                                setFieldValue('tags', [...chip]);
                              }}
                            />
                          </Box>
                        </CardContent>
                        <CardContent>
                          {config.modules.datasets_base.features
                            .auto_approval_for_confidentiality_level[
                            values.confidentiality
                          ] === true && (
                            <TextField
                              fullWidth
                              label="Auto Approval"
                              name="autoApprovalEnabled"
                              onChange={handleChange}
                              select
                              value={values.autoApprovalEnabled}
                              variant="outlined"
                            >
                              <MenuItem key={'Enabled'} value={true}>
                                Enabled
                              </MenuItem>
                              <MenuItem key={'Enabled'} value={false}>
                                Disabled
                              </MenuItem>
                            </TextField>
                          )}
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item lg={6} md={6} xs={12}>
                      <Card>
                        <CardHeader title="Governance" />
                        <CardContent>
                          <Autocomplete
                            id="environment"
                            disablePortal
                            options={environmentOptions.map((option) => option)}
                            onChange={(event, value) => {
                              setFieldValue('SamlAdminGroupName', '');
                              setFieldValue('stewards', '');
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
                                setFieldValue('SamlAdminGroup', '');
                                setFieldValue('connection', '');
                                setFieldValue('schema', '');
                                setFieldValue('tables', []);
                                setGroupOptions([]);
                                setConnectionOptions([]);
                                setSchemaOptions([]);
                                setTableOptions(null);
                              }
                            }}
                            renderInput={(params) => (
                              <TextField
                                {...params}
                                fullWidth
                                error={Boolean(
                                  touched.environmentUri &&
                                    errors.environmentUri
                                )}
                                helperText={
                                  touched.environmentUri &&
                                  errors.environmentUri
                                }
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
                            label="Organization"
                            name="organization"
                            value={
                              values.environment &&
                              values.environment.organization
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
                              if (value && value.value) {
                                setFieldValue(
                                  'SamlAdminGroupName',
                                  value.value
                                );
                                fetchRedshiftConnections(
                                  values.environment.environmentUri,
                                  value.value
                                ).catch((e) =>
                                  dispatch({
                                    type: SET_ERROR,
                                    error: e.message
                                  })
                                );
                              } else {
                                setFieldValue('SamlAdminGroupName', '');
                                setFieldValue('connection', '');
                                setFieldValue('schema', '');
                                setFieldValue('tables', []);
                                setConnectionOptions([]);
                                setSchemaOptions([]);
                                setTableOptions(null);
                              }
                            }}
                            inputValue={values.SamlAdminGroupName}
                            renderInput={(params) => (
                              <TextField
                                {...params}
                                fullWidth
                                error={Boolean(
                                  touched.SamlAdminGroupName &&
                                    errors.SamlAdminGroupName
                                )}
                                helperText={
                                  touched.SamlAdminGroupName &&
                                  errors.SamlAdminGroupName
                                }
                                label="Team"
                                onChange={handleChange}
                                variant="outlined"
                              />
                            )}
                          />
                        </CardContent>
                        <CardContent>
                          <Autocomplete
                            id="stewards"
                            disablePortal
                            options={groupOptions.map((option) => option)}
                            onChange={(event, value) => {
                              if (value && value.value) {
                                setFieldValue('stewards', value.value);
                              } else {
                                setFieldValue('stewards', '');
                              }
                            }}
                            inputValue={values.stewards}
                            renderInput={(params) => (
                              <TextField
                                {...params}
                                fullWidth
                                error={Boolean(
                                  touched.stewards && errors.stewards
                                )}
                                helperText={touched.stewards && errors.stewards}
                                label="Stewards"
                                onChange={handleChange}
                                variant="outlined"
                              />
                            )}
                          />
                        </CardContent>
                      </Card>
                      <Card sx={{ mt: 3 }}>
                        <CardHeader title="Deployment" />
                        <CardContent>
                          <Autocomplete
                            id="connection"
                            disablePortal
                            options={connectionOptions.map((option) => option)}
                            noOptionsText="No connections for the selected Team and Environment"
                            onChange={(event, value) => {
                              if (value && value) {
                                setFieldValue('connection', value);
                                fetchSchemas(value.value).catch((e) =>
                                  dispatch({
                                    type: SET_ERROR,
                                    error: e.message
                                  })
                                );
                              } else {
                                setFieldValue('connection', '');
                                setSchemaOptions([]);
                                setTableOptions(null);
                                setFieldValue('schema', '');
                                setFieldValue('tables', []);
                              }
                            }}
                            inputValue={values.connection.label}
                            renderInput={(params) => (
                              <TextField
                                {...params}
                                fullWidth
                                error={Boolean(
                                  touched.connection && errors.connection
                                )}
                                helperText={
                                  touched.connection && errors.connection
                                }
                                label="Redshift Connection"
                                name="connection"
                                onChange={handleChange}
                                variant="outlined"
                              />
                            )}
                          />
                        </CardContent>
                        <CardContent>
                          <Autocomplete
                            id="schema"
                            disablePortal
                            loading={loadingSchemas}
                            options={schemaOptions.map((option) => option)}
                            noOptionsText="No schemas for the selected Connection"
                            onChange={(event, value) => {
                              if (value) {
                                setFieldValue('schema', value);
                                fetchTables(
                                  values.connection.value,
                                  value
                                ).catch((e) =>
                                  dispatch({
                                    type: SET_ERROR,
                                    error: e.message
                                  })
                                );
                              } else {
                                setTableOptions(null);
                                setFieldValue('schema', '');
                                setFieldValue('tables', []);
                              }
                            }}
                            inputValue={values.schema}
                            renderInput={(params) => (
                              <TextField
                                {...params}
                                fullWidth
                                error={Boolean(touched.schema && errors.schema)}
                                helperText={touched.schema && errors.schema}
                                label="Redshift database schema"
                                name="schema"
                                onChange={handleChange}
                                variant="outlined"
                              />
                            )}
                          />
                        </CardContent>
                        {loadingTables && (
                          <Box>
                            <Typography
                              color="primary"
                              variant="subtitle2"
                              marginLeft={3}
                            >
                              Loading database tables
                            </Typography>
                            <LinearProgress />
                          </Box>
                        )}
                        {tableOptions && (
                          <CardContent>
                            <Scrollbar>
                              <Box sx={{ minWidth: 600 }}>
                                <DataGrid
                                  autoHeight
                                  checkboxSelection
                                  getRowId={(node) => node.name}
                                  rows={tableOptions}
                                  columns={[
                                    { field: 'id', hide: true },
                                    {
                                      field: 'name',
                                      headerName: 'Redshift tables',
                                      flex: 0.5,
                                      editable: false
                                    }
                                  ]}
                                  pageSize={filter.pageSize}
                                  rowsPerPageOptions={[filter.pageSize]}
                                  loading={loading}
                                  onPageSizeChange={(pageSize) => {
                                    setFilter({
                                      ...filter,
                                      pageSize: pageSize
                                    });
                                  }}
                                  getRowHeight={() => 'auto'}
                                  disableSelectionOnClick
                                  onSelectionModelChange={(
                                    newSelectionModel
                                  ) => {
                                    setFieldValue('tables', newSelectionModel);
                                  }}
                                  components={{
                                    LoadingOverlay: LinearProgress
                                  }}
                                  sx={{ wordWrap: 'break-word' }}
                                />
                              </Box>
                            </Scrollbar>
                          </CardContent>
                        )}
                      </Card>
                      <Box
                        sx={{
                          display: 'flex',
                          justifyContent: 'flex-end',
                          mt: 3
                        }}
                      >
                        <LoadingButton
                          color="primary"
                          loading={isSubmitting}
                          type="submit"
                          variant="contained"
                        >
                          Import Dataset
                        </LoadingButton>
                      </Box>
                    </Grid>
                  </Grid>
                </form>
              )}
            </Formik>
          </Box>
        </Container>
      </Box>
    </>
  );
};

export default RSDatasetImportForm;
