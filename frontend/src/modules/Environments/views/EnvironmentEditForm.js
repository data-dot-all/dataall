import { LoadingButton } from '@mui/lab';
import {
  Box,
  Breadcrumbs,
  Button,
  Card,
  CardContent,
  CardHeader,
  CircularProgress,
  Container,
  FormControlLabel,
  FormGroup,
  FormHelperText,
  Grid,
  Link,
  Switch,
  TextField,
  Typography
} from '@mui/material';
import { Formik } from 'formik';
import { useSnackbar } from 'notistack';
import React, { useCallback, useEffect, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { Link as RouterLink, useNavigate, useParams } from 'react-router-dom';
import * as Yup from 'yup';
import {
  ArrowLeftIcon,
  ChevronRightIcon,
  ChipInput,
  useSettings
} from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { getEnvironmentMLStudioDomain, useClient } from 'services';
import { getEnvironment, updateEnvironment } from '../services';
import {
  isAnyEnvironmentModuleEnabled,
  isModuleEnabled,
  ModuleNames
} from 'utils';

const EnvironmentEditForm = (props) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const params = useParams();
  const client = useClient();
  const { settings } = useSettings();
  const [loading, setLoading] = useState(true);
  const [env, setEnv] = useState('');
  const [envMLStudioDomain, setEnvMLStudioDomain] = useState('');
  const [previousEnvMLStudioEnabled, setPreviousEnvMLStudioEnabled] =
    useState(false);

  const fetchItem = useCallback(async () => {
    const response = await client.query(
      getEnvironment({ environmentUri: params.uri })
    );
    if (!response.errors && response.data.getEnvironment) {
      const environment = response.data.getEnvironment;
      environment.parameters = Object.fromEntries(
        environment.parameters.map((x) => [x.key, x.value])
      );
      setEnv(environment);
      if (environment.parameters['mlStudiosEnabled'] === 'true') {
        setPreviousEnvMLStudioEnabled(true);
        const response2 = await client.query(
          getEnvironmentMLStudioDomain({ environmentUri: params.uri })
        );
        if (!response2.errors && response2.data.getEnvironmentMLStudioDomain) {
          setEnvMLStudioDomain(response2.data.getEnvironmentMLStudioDomain);
        } else {
          const error = response2.errors
            ? response2.errors[0].message
            : 'Environment ML Studio Domain not found';
          dispatch({ type: SET_ERROR, error });
        }
      }
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Environment not found';
      dispatch({ type: SET_ERROR, error });
    }
    setLoading(false);
  }, [client, dispatch, params.uri]);

  useEffect(() => {
    if (client) {
      fetchItem().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client, fetchItem, dispatch]);

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = await client.mutate(
        updateEnvironment({
          environmentUri: env.environmentUri,
          input: {
            label: values.label,
            tags: values.tags,
            description: values.description,
            resourcePrefix: values.resourcePrefix,
            vpcId: values.vpcId,
            subnetIds: values.subnetIds,
            parameters: [
              {
                key: 'notebooksEnabled',
                value: String(values.notebooksEnabled)
              },
              {
                key: 'mlStudiosEnabled',
                value: String(values.mlStudiosEnabled)
              },
              {
                key: 'pipelinesEnabled',
                value: String(values.pipelinesEnabled)
              },
              {
                key: 'dashboardsEnabled',
                value: String(values.dashboardsEnabled)
              },
              {
                key: 'omicsEnabled',
                value: String(values.omicsEnabled)
              }
            ]
          }
        })
      );
      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        enqueueSnackbar('Environment updated', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        navigate(
          `/console/environments/${response.data.updateEnvironment.environmentUri}`
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
        <title>Environments: Environment Update | data.all</title>
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
                Edit environment {env.label}
              </Typography>
              <Breadcrumbs
                aria-label="breadcrumb"
                separator={<ChevronRightIcon fontSize="small" />}
                sx={{ mt: 1 }}
              >
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to="/console/organizations"
                  variant="subtitle2"
                >
                  Admin
                </Link>
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to="/console/environments"
                  variant="subtitle2"
                >
                  Environments
                </Link>
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to={`/console/environments/${env.environmentUri}`}
                  variant="subtitle2"
                >
                  {env.label}
                </Link>
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to={`/console/environments/${env.environmentUri}`}
                  variant="subtitle2"
                >
                  Edit
                </Link>
              </Breadcrumbs>
            </Grid>
            <Grid item>
              <Box sx={{ m: -1 }}>
                <Button
                  color="primary"
                  component={RouterLink}
                  startIcon={<ArrowLeftIcon fontSize="small" />}
                  sx={{ mt: 1 }}
                  to={`/console/environments/${env.environmentUri}`}
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
                label: env.label,
                description: env.description,
                tags: env.tags || [],
                vpcId: envMLStudioDomain.vpcId || '',
                subnetIds: envMLStudioDomain.subnetIds || [],
                notebooksEnabled: env.parameters['notebooksEnabled'] === 'true',
                mlStudiosEnabled: env.parameters['mlStudiosEnabled'] === 'true',
                pipelinesEnabled: env.parameters['pipelinesEnabled'] === 'true',
                dashboardsEnabled:
                  env.parameters['dashboardsEnabled'] === 'true',
                omicsEnabled: env.parameters['omicsEnabled'] === 'true',
                resourcePrefix: env.resourcePrefix
              }}
              validationSchema={Yup.object().shape({
                label: Yup.string()
                  .max(255)
                  .required('*Environment name is required'),
                description: Yup.string().max(5000),
                tags: Yup.array().nullable(),
                subnetIds: Yup.array().when('vpcId', {
                  is: (value) => !!value,
                  then: Yup.array()
                    .min(1)
                    .required(
                      'At least 1 Subnet Id required if VPC Id specified'
                    )
                }),
                vpcId: Yup.string().nullable(),
                resourcePrefix: Yup.string()
                  .trim()
                  .matches(
                    '^[a-z-]*$',
                    '*Resource prefix is not valid (^[a-z-]*$)'
                  )
                  .min(1, '*Resource prefix must have at least 1 character')
                  .max(
                    20,
                    "*Resource prefix can't be longer than 20 characters"
                  )
                  .required('*Resource prefix is required')
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
                    <Grid item lg={5} md={6} xs={12}>
                      <Card>
                        <CardHeader title="Details" />
                        <CardContent>
                          <TextField
                            error={Boolean(touched.label && errors.label)}
                            fullWidth
                            helperText={touched.label && errors.label}
                            label="Environment Name"
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
                      <Box sx={{ mt: 3 }}>
                        <Card>
                          <CardHeader title="Organize" />
                          <CardContent>
                            <TextField
                              disabled
                              fullWidth
                              label="Team"
                              name="label"
                              onBlur={handleBlur}
                              onChange={handleChange}
                              value={env.SamlGroupName}
                              variant="outlined"
                            />
                          </CardContent>
                          <CardContent>
                            <ChipInput
                              fullWidth
                              defaultValue={env.tags}
                              error={Boolean(touched.tags && errors.tags)}
                              helperText={touched.tags && errors.tags}
                              variant="outlined"
                              label="Tags"
                              onChange={(chip) => {
                                setFieldValue('tags', [...chip]);
                              }}
                            />
                          </CardContent>
                        </Card>
                      </Box>
                    </Grid>
                    <Grid item lg={7} md={6} xs={12}>
                      <Box>
                        <Card>
                          <CardHeader title="AWS Information" />
                          <CardContent>
                            <TextField
                              disabled
                              fullWidth
                              label="Account Number"
                              name="AwsAccountId"
                              onBlur={handleBlur}
                              onChange={handleChange}
                              value={env.AwsAccountId}
                              variant="outlined"
                            />
                          </CardContent>
                          <CardContent>
                            <TextField
                              disabled
                              fullWidth
                              label="Region"
                              name="region"
                              onBlur={handleBlur}
                              onChange={handleChange}
                              value={env.region}
                              variant="outlined"
                            />
                          </CardContent>
                          <CardContent>
                            <TextField
                              error={Boolean(
                                touched.resourcePrefix && errors.resourcePrefix
                              )}
                              fullWidth
                              helperText={
                                touched.resourcePrefix && errors.resourcePrefix
                              }
                              label="Resources Prefix"
                              placeholder="Prefix will be applied to All AWS resources created on this environment"
                              name="resourcePrefix"
                              onBlur={handleBlur}
                              onChange={handleChange}
                              value={values.resourcePrefix}
                              variant="outlined"
                            />
                          </CardContent>
                        </Card>
                      </Box>
                      {!previousEnvMLStudioEnabled &&
                        values.mlStudiosEnabled && (
                          <Box sx={{ mt: 3 }}>
                            <Card>
                              <CardHeader title="(Optional) ML Studio Configuration" />
                              <CardContent>
                                <TextField
                                  {...params}
                                  disabled={previousEnvMLStudioEnabled}
                                  label="(Optional) ML Studio VPC ID"
                                  placeholder="(Optional) Bring your own VPC - Specify VPC ID"
                                  name="vpcId"
                                  fullWidth
                                  error={Boolean(touched.vpcId && errors.vpcId)}
                                  helperText={touched.vpcId && errors.vpcId}
                                  onBlur={handleBlur}
                                  onChange={handleChange}
                                  value={values.vpcId}
                                  variant="outlined"
                                />
                              </CardContent>
                              <CardContent>
                                <ChipInput
                                  disabled={previousEnvMLStudioEnabled}
                                  fullWidth
                                  error={Boolean(
                                    touched.subnetIds && errors.subnetIds
                                  )}
                                  helperText={
                                    touched.subnetIds && errors.subnetIds
                                  }
                                  variant="outlined"
                                  label="(Optional) ML Studio Subnet ID(s)"
                                  placeholder="(Optional) Bring your own VPC - Specify Subnet ID (Hit enter after typing value)"
                                  onChange={(chip) => {
                                    setFieldValue('subnetIds', [...chip]);
                                  }}
                                />
                              </CardContent>
                            </Card>
                          </Box>
                        )}
                      {isAnyEnvironmentModuleEnabled() && (
                        <Box sx={{ mt: 3 }}>
                          <Card>
                            <CardHeader title="Features management" />
                            <CardContent>
                              {isModuleEnabled(ModuleNames.DASHBOARDS) && (
                                <Box sx={{ ml: 2 }}>
                                  <FormGroup>
                                    <FormControlLabel
                                      color="primary"
                                      control={
                                        <Switch
                                          defaultChecked={
                                            values.dashboardsEnabled
                                          }
                                          color="primary"
                                          onChange={handleChange}
                                          edge="start"
                                          name="dashboardsEnabled"
                                          value={values.dashboardsEnabled}
                                        />
                                      }
                                      label={
                                        <Typography
                                          color="textSecondary"
                                          gutterBottom
                                          variant="subtitle2"
                                        >
                                          Dashboards{' '}
                                          <small>
                                            (Requires Amazon QuickSight
                                            Enterprise Subscription)
                                          </small>
                                        </Typography>
                                      }
                                      labelPlacement="end"
                                      value={values.dashboardsEnabled}
                                    />
                                  </FormGroup>
                                </Box>
                              )}
                              {isModuleEnabled(ModuleNames.NOTEBOOKS) && (
                                <Box sx={{ ml: 2 }}>
                                  <FormGroup>
                                    <FormControlLabel
                                      color="primary"
                                      control={
                                        <Switch
                                          defaultChecked={
                                            values.notebooksEnabled
                                          }
                                          color="primary"
                                          onChange={handleChange}
                                          edge="start"
                                          name="notebooksEnabled"
                                          value={values.notebooksEnabled}
                                        />
                                      }
                                      label={
                                        <Box>
                                          <Typography
                                            color="textSecondary"
                                            gutterBottom
                                            variant="subtitle2"
                                          >
                                            Notebooks{' '}
                                            <small>
                                              (Requires Amazon Sagemaker
                                              notebook instances)
                                            </small>
                                          </Typography>
                                        </Box>
                                      }
                                      labelPlacement="end"
                                      value={values.notebooksEnabled}
                                    />
                                  </FormGroup>
                                </Box>
                              )}
                              {isModuleEnabled(ModuleNames.MLSTUDIO) && (
                                <Box sx={{ ml: 2 }}>
                                  <FormGroup>
                                    <FormControlLabel
                                      color="primary"
                                      control={
                                        <Switch
                                          defaultChecked={
                                            values.mlStudiosEnabled
                                          }
                                          color="primary"
                                          onChange={handleChange}
                                          edge="start"
                                          name="mlStudiosEnabled"
                                          value={values.mlStudiosEnabled}
                                        />
                                      }
                                      label={
                                        <Typography
                                          color="textSecondary"
                                          gutterBottom
                                          variant="subtitle2"
                                        >
                                          ML Studio{' '}
                                          <small>
                                            (Requires Amazon Sagemaker Studio)
                                          </small>
                                        </Typography>
                                      }
                                      labelPlacement="end"
                                      value={values.mlStudiosEnabled}
                                    />
                                  </FormGroup>
                                </Box>
                              )}
                              {isModuleEnabled(ModuleNames.DATAPIPELINES) && (
                                <Box sx={{ ml: 2 }}>
                                  <FormGroup>
                                    <FormControlLabel
                                      color="primary"
                                      control={
                                        <Switch
                                          defaultChecked={
                                            values.pipelinesEnabled
                                          }
                                          color="primary"
                                          onChange={handleChange}
                                          edge="start"
                                          name="pipelinesEnabled"
                                          value={values.pipelinesEnabled}
                                        />
                                      }
                                      label={
                                        <Typography
                                          color="textSecondary"
                                          gutterBottom
                                          variant="subtitle2"
                                        >
                                          Pipelines{' '}
                                          <small>(Requires AWS DevTools)</small>
                                        </Typography>
                                      }
                                      labelPlacement="end"
                                      value={values.pipelinesEnabled}
                                    />
                                  </FormGroup>
                                </Box>
                              )}
                              {isModuleEnabled(ModuleNames.OMICS) && (
                                <Box sx={{ ml: 2 }}>
                                  <FormGroup>
                                    <FormControlLabel
                                      color="primary"
                                      control={
                                        <Switch
                                          defaultChecked={values.omicsEnabled}
                                          color="primary"
                                          onChange={handleChange}
                                          edge="start"
                                          name="omicsEnabled"
                                          value={values.omicsEnabled}
                                        />
                                      }
                                      label={
                                        <Typography
                                          color="textSecondary"
                                          gutterBottom
                                          variant="subtitle2"
                                        >
                                          Omics{' '}
                                          <small>
                                            (Requires AWS HealthOmics)
                                          </small>
                                        </Typography>
                                      }
                                      labelPlacement="end"
                                      value={values.omicsEnabled}
                                    />
                                  </FormGroup>
                                </Box>
                              )}
                            </CardContent>
                          </Card>
                        </Box>
                      )}
                      {errors.submit && (
                        <Box sx={{ mt: 3 }}>
                          <FormHelperText error>{errors.submit}</FormHelperText>
                        </Box>
                      )}
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
                          Save
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

export default EnvironmentEditForm;
