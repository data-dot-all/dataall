import { Link as RouterLink, useNavigate, useParams } from 'react-router-dom';
import * as Yup from 'yup';
import { Formik } from 'formik';
import { useSnackbar } from 'notistack';
import {
  Box,
  Breadcrumbs,
  Button,
  Card,
  CardContent,
  CardHeader,
  CircularProgress,
  Container,
  FormHelperText,
  Grid,
  Link,
  MenuItem,
  TextField,
  Typography
} from '@mui/material';
import { Helmet } from 'react-helmet-async';
import { LoadingButton } from '@mui/lab';
import React, { useCallback, useEffect, useState } from 'react';
import { useClient, listEnvironmentGroups, listEnvironments } from 'services';
import { getOmicsWorkflow } from '../services';
import {
  ArrowLeftIcon,
  ChevronRightIcon,
  // ChipInput,
  Defaults,
  useSettings
} from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { createOmicsRun } from '../services';

const OmicsRunCreateForm = (props) => {
  const params = useParams();
  const client = useClient();
  const dispatch = useDispatch();
  const [omicsWorkflow, setOmicsWorkflow] = useState(null);
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const { settings } = useSettings();
  const [loading, setLoading] = useState(true);
  const fetchItem = useCallback(async () => {
    setLoading(true);
    const response = await client.query(getOmicsWorkflow(params.workflowId));
    if (!response.errors) {
      setOmicsWorkflow(response.data.getOmicsWorkflow);
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Omics Workflow not found';
      dispatch({ type: SET_ERROR, error });
    }
    setLoading(false);
  }, [client, dispatch, params.uri]);

  const [groupOptions, setGroupOptions] = useState([]);
  const [environmentOptions, setEnvironmentOptions] = useState([]);
  const fetchEnvironments = useCallback(async () => {
    setLoading(true);
    const response = await client.query(
      listEnvironments({ filter: Defaults.SelectListFilter })
    );
    if (!response.errors) {
      setEnvironmentOptions(
        response.data.listEnvironments.nodes.map((e) => ({
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
  useEffect(() => {
    if (client) {
      fetchEnvironments().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
      fetchItem().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client, dispatch, fetchEnvironments, fetchItem]);

  useEffect(() => {
    if (client) {
      fetchItem().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client, dispatch, fetchItem]);

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = await client.mutate(
        createOmicsRun({
          label: values.label,
          environmentUri: values.environment.environmentUri,
          parameterTemplate: values.parameterTemplate,
          SamlAdminGroupName: values.SamlAdminGroupName,
          destination: values.destination
        })
      );
      setStatus({ success: true });
      setSubmitting(false);
      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        enqueueSnackbar('Omics run creation started', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        navigate(`/console/omics/${response.data.createOmicsRun.omicsRunUri}`);
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (err) {
      console.error(err);
      setStatus({ success: false });
      setErrors({ submit: err.message });
      setSubmitting(false);
    }
  }
  if (loading) {
    return <CircularProgress />;
  }

  return (
    <>
      <Helmet>
        <title>Omics: Create Run | data.all</title>
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
                Create a new Run
              </Typography>
              <Breadcrumbs
                aria-label="breadcrumb"
                separator={<ChevronRightIcon fontSize="small" />}
                sx={{ mt: 1 }}
              >
                <Typography color="textPrimary" variant="subtitle2">
                  Play
                </Typography>
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to="/console/omics"
                  variant="subtitle2"
                >
                  Workflows
                </Link>
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to="/console/omics/runs/new"
                  variant="subtitle2"
                >
                  Create Run
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
                  to="/console/omics"
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
                SamlAdminGroupName: '',
                environment: '',
                destination: '',
                parameterTemplate: omicsWorkflow.parameterTemplate
              }}
              validationSchema={Yup.object().shape({
                label: Yup.string().max(255).required('*Workflow is required'),
                parameterTemplate: Yup.string().max(5000),
                SamlAdminGroupName: Yup.string()
                  .max(255)
                  .required('*Team is required'),
                environment: Yup.object().required('*Environment is required'),
                destination: Yup.string()
                  .max(255)
                  .required('*Destination is required')
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
                    <Grid item lg={7} md={6} xs={12}>
                      <Card sx={{ mb: 3 }}>
                        <CardHeader title="Details" />
                        <CardContent>
                          <TextField
                            error={Boolean(touched.label && errors.label)}
                            fullWidth
                            helperText={touched.label && errors.label}
                            label="Workflow id"
                            name="label"
                            value={omicsWorkflow.id}
                            onBlur={handleBlur}
                            onChange={handleChange}
                            variant="outlined"
                          />
                        </CardContent>
                        <CardContent>
                          <TextField
                            error={Boolean(touched.label && errors.label)}
                            fullWidth
                            helperText={touched.label && errors.label}
                            label="Run Name"
                            name="name"
                            onBlur={handleBlur}
                            onChange={handleChange}
                            value={values.label}
                            variant="outlined"
                          />
                        </CardContent>
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
                            label="Region"
                            name="region"
                            value={
                              values.environment
                                ? values.environment.region
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
                            label="Owners"
                            name="SamlGroupName"
                            onChange={handleChange}
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
                          <TextField
                            fullWidth
                            label="Select S3 Output Destination"
                            name="destination"
                            value={values.destination} //TODO: datasetUri
                            variant="outlined"
                            onBlur={handleBlur}
                            onChange={handleChange}
                          />
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item lg={5} md={6} xs={12}>
                      <Card sx={{ mb: 3 }}>
                        <CardHeader title="Run Parameters" />
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
                              1000 - values.parameterTemplate.length
                            } characters left`}
                            label="Inline JSON Parameters Template"
                            name="JSON Parameters"
                            multiline
                            onBlur={handleBlur}
                            onChange={handleChange}
                            rows={12}
                            value={values.parameterTemplate}
                            variant="outlined"
                          />
                          {touched.parameterTemplate &&
                            errors.parameterTemplate && (
                              <Box sx={{ mt: 2 }}>
                                <FormHelperText error>
                                  {errors.parameterTemplate}
                                </FormHelperText>
                              </Box>
                            )}
                        </CardContent>
                      </Card>
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
                          Create Run
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

export default OmicsRunCreateForm;
