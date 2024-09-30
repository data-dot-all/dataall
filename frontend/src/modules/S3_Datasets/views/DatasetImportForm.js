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
  Collapse,
  Container,
  FormHelperText,
  Grid,
  Link,
  MenuItem,
  Switch,
  TextField,
  Typography
} from '@mui/material';
import { Formik } from 'formik';
import { useSnackbar } from 'notistack';
import React, { useCallback, useEffect, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import * as Yup from 'yup';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import {
  ArrowLeftIcon,
  ChevronRightIcon,
  ChipInput,
  Defaults,
  useSettings
} from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import {
  fetchEnums,
  listEnvironmentGroups,
  listValidEnvironments,
  useClient
} from 'services';
import { importDataset } from '../services';
import { Topics, ConfidentialityList } from '../../constants';
import config from '../../../generated/config.json';
import { isFeatureEnabled } from 'utils';

const DatasetImportForm = (props) => {
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
  const [showAdvancedControls, setShowAdvancedControl] = useState(false);
  const [expirationMenu, setExpirationMenu] = useState([]);
  const [enableShareExpiration, setEnableShareExpiration] = useState(false);
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

  const fetchExpirationOptions = async () => {
    try {
      const enumExpirationsOptions = await fetchEnums(client, ['Expiration']);
      if (enumExpirationsOptions['Expiration'].length > 0) {
        let datasetExpirationOptions = [];
        enumExpirationsOptions['Expiration'].map((x) => {
          let expirationType = { key: x.name, value: x.value };
          datasetExpirationOptions.push(expirationType);
        });
        setExpirationMenu(datasetExpirationOptions);
      } else {
        const error = 'Could not fetch expiration options';
        dispatch({ type: SET_ERROR, error });
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
      fetchExpirationOptions().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, dispatch, fetchEnvironments]);

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = await client.mutate(
        importDataset({
          organizationUri: values.environment.organization.organizationUri,
          environmentUri: values.environment.environmentUri,
          owner: '',
          label: values.label,
          SamlAdminGroupName: values.SamlAdminGroupName,
          tags: values.tags,
          description: values.description,
          topics: values.topics ? values.topics.map((t) => t.value) : [],
          bucketName: values.bucketName,
          KmsKeyAlias: values.KmsKeyAlias,
          glueDatabaseName: values.glueDatabaseName,
          stewards: values.stewards,
          confidentiality: values.confidentiality,
          autoApprovalEnabled: values.autoApprovalEnabled,
          enableExpiration: enableShareExpiration,
          expirySetting: enableShareExpiration
            ? values.expirationSetting
            : null,
          expiryMinDuration: enableShareExpiration ? values.minValidity : null,
          expiryMaxDuration: enableShareExpiration ? values.maxValidity : null
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
          `/console/s3-datasets/${response.data.importDataset.datasetUri}`
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
        <title>Dataset: Dataset Import | data.all</title>
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
                Import a new dataset
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
                SamlAdminGroupName: '',
                stewards: '',
                tags: [],
                topics: [],
                glueDatabaseName: '',
                bucketName: '',
                KmsKeyAlias: '',
                confidentiality: '',
                autoApprovalEnabled: false,
                expirationSetting: '',
                minValidity: 0,
                maxValidity: 0
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
                glueDatabaseName: Yup.string().max(255),
                KmsKeyAlias: Yup.string().max(255),
                bucketName: Yup.string()
                  .max(255)
                  .required('*S3 bucket name is required'),
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
                expirationSetting: enableShareExpiration
                  ? Yup.string().required('Expiration Setting required')
                  : Yup.string().nullable(),
                minValidity: enableShareExpiration
                  ? Yup.number()
                      .positive()
                      .required('*Minimum allowed expiration is required')
                  : Yup.number().nullable(),
                maxValidity: enableShareExpiration
                  ? Yup.number()
                      .positive()
                      .required('*Maximum allowed expiration is required')
                  : Yup.number().nullable()
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

                      <Card sx={{ mt: 3 }}>
                        <Box alignItems="center" display="flex" sx={{ p: 1 }}>
                          <Box sx={{ flexGrow: 1 }}>
                            <CardHeader title="Advanced Controls" />
                          </Box>
                          <ExpandMoreIcon
                            sx={{ m: 1 }}
                            variant="outlined"
                            onClick={() => {
                              setShowAdvancedControl(!showAdvancedControls);
                            }}
                          />
                        </Box>
                        <Collapse in={showAdvancedControls}>
                          <CardContent>
                            <Box display="flex" alignItems="center">
                              <Typography>Enable Share Expiration</Typography>
                              <Switch
                                checked={enableShareExpiration}
                                onChange={() => {
                                  setEnableShareExpiration(
                                    !enableShareExpiration
                                  );
                                }}
                              />
                            </Box>
                          </CardContent>
                          <Collapse in={enableShareExpiration}>
                            <CardContent>
                              <TextField
                                fullWidth
                                error={Boolean(
                                  touched.expirationSetting &&
                                    errors.expirationSetting
                                )}
                                helperText={
                                  touched.expirationSetting &&
                                  errors.expirationSetting
                                }
                                label="Expiration Setting For Dataset"
                                name="expirationSetting"
                                onChange={handleChange}
                                select
                                value={values.expirationSetting}
                                variant="outlined"
                              >
                                {expirationMenu.map((item) => (
                                  <MenuItem key={item.key} value={item.value}>
                                    {item.key}
                                  </MenuItem>
                                ))}
                              </TextField>
                            </CardContent>
                            <CardContent>
                              <TextField
                                error={Boolean(
                                  touched.minValidity && errors.minValidity
                                )}
                                fullWidth
                                helperText={
                                  touched.minValidity && errors.minValidity
                                }
                                label="Minimum access period in months / quarters"
                                name="minValidity"
                                onBlur={handleBlur}
                                onChange={handleChange}
                                variant="outlined"
                                inputProps={{ type: 'number' }}
                              />
                            </CardContent>
                            <CardContent>
                              <TextField
                                error={Boolean(
                                  touched.maxValidity && errors.maxValidity
                                )}
                                fullWidth
                                helperText={
                                  touched.maxValidity && errors.maxValidity
                                }
                                label="Maximum access period in months / quarters"
                                name="maxValidity"
                                onBlur={handleBlur}
                                onChange={handleChange}
                                variant="outlined"
                                inputProps={{ type: 'number' }}
                              />
                            </CardContent>
                          </Collapse>
                        </Collapse>
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
                        <CardContent>
                          <TextField
                            error={Boolean(
                              touched.bucketName && errors.bucketName
                            )}
                            fullWidth
                            helperText={touched.bucketName && errors.bucketName}
                            label="Amazon S3 bucket name"
                            name="bucketName"
                            onBlur={handleBlur}
                            onChange={handleChange}
                            value={values.bucketName}
                            variant="outlined"
                          />
                        </CardContent>
                        <CardContent>
                          <TextField
                            error={Boolean(
                              touched.KmsKeyAlias && errors.KmsKeyAlias
                            )}
                            fullWidth
                            helperText={
                              touched.KmsKeyAlias && errors.KmsKeyAlias
                            }
                            label="Amazon KMS key Alias (if SSE-KMS encryption is used)"
                            name="KmsKeyAlias"
                            onBlur={handleBlur}
                            onChange={handleChange}
                            value={values.KmsKeyAlias}
                            variant="outlined"
                          />
                        </CardContent>
                        <CardContent>
                          <TextField
                            error={Boolean(
                              touched.glueDatabaseName &&
                                errors.glueDatabaseName
                            )}
                            fullWidth
                            helperText={
                              touched.glueDatabaseName &&
                              errors.glueDatabaseName
                            }
                            label="AWS Glue database name"
                            name="glueDatabaseName"
                            onBlur={handleBlur}
                            onChange={handleChange}
                            value={values.glueDatabaseName}
                            variant="outlined"
                          />
                        </CardContent>
                      </Card>
                      <Card sx={{ mt: 3 }}>
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

export default DatasetImportForm;
