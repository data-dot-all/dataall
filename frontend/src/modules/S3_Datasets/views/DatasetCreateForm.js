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
import { createDataset } from '../services';
import {
  useClient,
  listEnvironmentGroups,
  listValidEnvironments
} from 'services';
import { Topics, ConfidentialityList } from '../../constants';
import config from '../../../generated/config.json';
import { isFeatureEnabled } from 'utils';

const DatasetCreateForm = (props) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const client = useClient();
  const { settings } = useSettings();
  const [loading, setLoading] = useState(true);
  const [groupOptions, setGroupOptions] = useState([]);
  const [environmentOptions, setEnvironmentOptions] = useState([]);
  const [confidentialityOptions] = useState(
    config.modules.datasets_base.features.confidentiality_dropdown === true &&
      config.modules.s3_datasets.features.custom_confidentiality_mapping
      ? Object.keys(
          config.modules.s3_datasets.features.custom_confidentiality_mapping
        )
      : ConfidentialityList
  );

  const topicsData = Topics.map((t) => ({ label: t, value: t }));

  const fetchEnvironments = useCallback(async () => {
    setLoading(true);
    const response = await client.query(
      listValidEnvironments({ filter: Defaults.selectListFilter })
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

  useEffect(() => {
    if (client) {
      fetchEnvironments().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, fetchEnvironments, dispatch]);

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = await client.mutate(
        createDataset({
          organizationUri: values.environment.organization.organizationUri,
          environmentUri: values.environment.environmentUri,
          owner: '',
          stewards: values.stewards,
          label: values.label,
          SamlAdminGroupName: values.SamlAdminGroupName,
          tags: values.tags,
          description: values.description,
          topics: values.topics ? values.topics.map((t) => t.value) : [],
          confidentiality: values.confidentiality,
          autoApprovalEnabled: values.autoApprovalEnabled
        })
      );
      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        enqueueSnackbar('Dataset creation started', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        navigate(
          `/console/s3-datasets/${response.data.createDataset.datasetUri}`
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
        <title>Dataset: Dataset Create | data.all</title>
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
                Create a new dataset
              </Typography>
              <Breadcrumbs
                aria-label="breadcrumb"
                separator={<ChevronRightIcon fontSize="small" />}
                sx={{ mt: 1 }}
              >
                <Link underline="hover" color="textPrimary" variant="subtitle2">
                  Contribute
                </Link>
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
                  Create
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
                stewards: '',
                confidentiality: '',
                SamlAdminGroupName: '',
                tags: [],
                topics: [],
                autoApprovalEnabled: false
              }}
              validationSchema={Yup.object().shape({
                label: Yup.string()
                  .max(255)
                  .required('*Dataset name is required'),
                description: Yup.string().max(5000),
                SamlAdminGroupName: Yup.string()
                  .max(255)
                  .required('*Owners team is required'),
                topics: isFeatureEnabled('datasets_base', 'topics_dropdown')
                  ? Yup.array().min(1).required('*Topics are required')
                  : Yup.array(),
                environment: Yup.object().required('*Environment is required'),
                tags: Yup.array().min(1).required('*Tags are required'),
                stewards: Yup.string().max(255).nullable(),
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
                )
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
                    <Grid item lg={7} md={7} xs={12}>
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
                    <Grid item lg={5} md={5} xs={12}>
                      <Card sx={{ mb: 3 }}>
                        <CardHeader title="Deployment" />
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
                                setGroupOptions([]);
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
                              values.environment &&
                              values.environment.organization
                                ? values.environment.organization.label
                                : ''
                            }
                            variant="outlined"
                          />
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader title="Governance" />
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
                              } else {
                                setFieldValue('SamlAdminGroupName', '');
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
                                ) : (
                                  <TextField
                                    error={Boolean(
                                      touched.SamlAdminGroupName &&
                                        errors.SamlAdminGroupName
                                    )}
                                    helperText={
                                      touched.SamlAdminGroupName &&
                                      errors.SamlAdminGroupName
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
                              <Box>
                                {groupOptions.length > 0 ? (
                                  <TextField
                                    {...params}
                                    fullWidth
                                    error={Boolean(
                                      touched.stewards && errors.stewards
                                    )}
                                    helperText={
                                      touched.stewards && errors.stewards
                                    }
                                    label="Stewards"
                                    onChange={handleChange}
                                    variant="outlined"
                                  />
                                ) : (
                                  <TextField
                                    error={Boolean(
                                      touched.stewards && errors.stewards
                                    )}
                                    helperText={
                                      touched.stewards && errors.stewards
                                    }
                                    fullWidth
                                    disabled
                                    label="Stewards"
                                    value="No teams found for this environment"
                                    variant="outlined"
                                  />
                                )}
                              </Box>
                            )}
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
                          Create Dataset
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

export default DatasetCreateForm;
