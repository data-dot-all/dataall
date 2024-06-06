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
  useSettings
} from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import {
  listEnvironmentGroups,
  listValidEnvironments,
  listEnvironmentRedshiftConnections,
  useClient
} from 'services';
import { importRedshiftDataset } from '../services';
import { Topics, ConfidentialityList } from '../../constants';
import config from '../../../generated/config.json';
import { isFeatureEnabled } from 'utils';

const RSDatasetImportForm = (props) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const client = useClient();
  const { settings } = useSettings();
  const [loading, setLoading] = useState(true);
  const [groupOptions, setGroupOptions] = useState([]);
  const [environmentOptions, setEnvironmentOptions] = useState([]);
  const [connectionOptions, setConnectionOptions] = useState([]);
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
            groupUri: groupUri
          }
        })
      );
      if (!response.errors) {
        setConnectionOptions(
          response.data.listEnvironmentRedshiftConnections.nodes.map((g) => ({
            value: g.connectionUri,
            label: g.name
          }))
        );
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    }
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
          SamlAdminGroupName: values.SamlGroupName,
          tags: values.tags,
          description: values.description,
          topics: values.topics ? values.topics.map((t) => t.value) : [],
          stewards: values.stewards,
          confidentiality: values.confidentiality,
          autoApprovalEnabled: values.autoApprovalEnabled,
          connectionUri: values.connectionUri,
          database: values.database,
          schema: values.schema,
          includePattern: values.includePattern,
          excludePattern: values.excludePattern
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
                businessOwnerEmail: '',
                businessOwnerDelegationEmails: [],
                SamlGroupName: '',
                stewards: '',
                tags: [],
                topics: [],
                confidentiality: '',
                autoApprovalEnabled: false,
                connectionUri: '',
                database: '',
                schema: '',
                includePattern: '',
                excludePattern: ''
              }}
              validationSchema={Yup.object().shape({
                label: Yup.string()
                  .max(255)
                  .required('*Dataset name is required'),
                description: Yup.string().max(5000),
                SamlGroupName: Yup.string()
                  .max(255)
                  .required('*Team is required'),
                topics: isFeatureEnabled('datasets_base', 'topics_dropdown')
                  ? Yup.array().min(1).required('*Topics are required')
                  : Yup.array(),
                environment: Yup.object().required('*Environment is required'),
                tags: Yup.array().min(1).required('*Tags are required'), //TODO: ADD REDSHIFT CONNECTION
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
                connectionUri: Yup.string().required('*Connection is required'),
                database: Yup.string().required(
                  '*Redshift Database is required'
                ),
                schema: Yup.string().required('*Schema is required'),
                includePattern: Yup.string(),
                excludePattern: Yup.string()
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
                          <TextField
                            fullWidth
                            error={Boolean(
                              touched.environment && errors.environment
                            )}
                            helperText={
                              touched.environment && errors.environment
                            }
                            label="Environment"
                            name="environment"
                            onChange={(event) => {
                              setFieldValue('SamlGroupName', '');
                              fetchGroups(
                                event.target.value.environmentUri
                              ).catch((e) =>
                                dispatch({ type: SET_ERROR, error: e.message })
                              );
                              setFieldValue('environment', event.target.value);
                            }}
                            select
                            value={values.environment}
                            variant="outlined"
                          >
                            {environmentOptions.map((environment) => (
                              <MenuItem
                                key={environment.environmentUri}
                                value={environment}
                              >
                                {environment.label}
                              </MenuItem>
                            ))}
                          </TextField>
                        </CardContent>
                        <CardContent>
                          <TextField
                            disabled
                            fullWidth
                            label="Organization"
                            name="organization"
                            value={
                              values.environment
                                ? values.environment.organization.label
                                : ''
                            }
                            variant="outlined"
                          />
                        </CardContent>
                        <CardContent>
                          <TextField
                            fullWidth
                            error={Boolean(
                              touched.SamlGroupName && errors.SamlGroupName
                            )}
                            helperText={
                              touched.SamlGroupName && errors.SamlGroupName
                            }
                            label="Team"
                            name="SamlGroupName"
                            onChange={(event) => {
                              fetchRedshiftConnections(
                                values.environment.environmentUri,
                                event.target.value
                              ).catch((e) =>
                                dispatch({ type: SET_ERROR, error: e.message })
                              );
                              setFieldValue(
                                'SamlGroupName',
                                event.target.value
                              );
                            }}
                            select
                            value={values.SamlGroupName}
                            variant="outlined"
                          >
                            {groupOptions.map((group) => (
                              <MenuItem key={group.value} value={group.value}>
                                {group.label}
                              </MenuItem>
                            ))}
                          </TextField>
                        </CardContent>
                        <CardContent>
                          <Autocomplete
                            id="stewards"
                            freeSolo
                            options={groupOptions.map((option) => option.value)}
                            onChange={(event, value) => {
                              setFieldValue('stewards', value);
                            }}
                            renderInput={(renderParams) => (
                              <TextField
                                {...renderParams}
                                label="Stewards"
                                margin="normal"
                                onChange={handleChange}
                                value={values.stewards}
                                variant="outlined"
                              />
                            )}
                          />
                        </CardContent>
                      </Card>
                      <Card sx={{ mt: 3 }}>
                        <CardHeader title="Deployment" />
                        <CardContent>
                          <TextField
                            fullWidth
                            error={Boolean(
                              touched.connectionUri && errors.connectionUri
                            )}
                            helperText={
                              touched.connectionUri && errors.connectionUri
                            }
                            label="Redshift Connection"
                            name="connectionUri"
                            onChange={handleChange}
                            select
                            value={values.connectionUri}
                            variant="outlined"
                          >
                            {connectionOptions.map((connection) => (
                              <MenuItem
                                key={connection.value}
                                value={connection.value}
                              >
                                {connection.label}
                              </MenuItem>
                            ))}
                          </TextField>
                        </CardContent>
                        <CardContent>
                          <TextField
                            error={Boolean(touched.database && errors.database)}
                            fullWidth
                            helperText={touched.database && errors.database}
                            label="Redshift database name"
                            name="database"
                            onBlur={handleBlur}
                            onChange={handleChange}
                            value={values.database}
                            variant="outlined"
                          />
                        </CardContent>
                        <CardContent>
                          <TextField
                            error={Boolean(touched.schema && errors.schema)}
                            fullWidth
                            helperText={touched.schema && errors.schema}
                            label="Redshift database schema"
                            name="schema"
                            onBlur={handleBlur}
                            onChange={handleChange}
                            value={values.schema}
                            variant="outlined"
                          />
                        </CardContent>
                        <CardContent>
                          <TextField
                            error={Boolean(
                              touched.includePattern && errors.includePattern
                            )}
                            fullWidth
                            helperText={
                              touched.includePattern && errors.includePattern
                            }
                            label="(optional) Include pattern"
                            name="includePattern"
                            onBlur={handleBlur}
                            onChange={handleChange}
                            value={values.includePattern}
                            variant="outlined"
                          />
                        </CardContent>
                        <CardContent>
                          <TextField
                            error={Boolean(
                              touched.excludePattern && errors.excludePattern
                            )}
                            fullWidth
                            helperText={
                              touched.excludePattern && errors.excludePattern
                            }
                            label="(optional) Exclude pattern"
                            name="excludePattern"
                            onBlur={handleBlur}
                            onChange={handleChange}
                            value={values.excludePattern}
                            variant="outlined"
                          />
                        </CardContent>
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
