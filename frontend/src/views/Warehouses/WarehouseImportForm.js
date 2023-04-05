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
  FormHelperText,
  Grid,
  Link,
  MenuItem,
  TextField,
  Typography
} from '@mui/material';
import { Formik } from 'formik';
import { useSnackbar } from 'notistack';
import { useCallback, useEffect, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { Link as RouterLink, useNavigate, useParams } from 'react-router-dom';
import * as Yup from 'yup';
import {
  importRedshiftCluster,
  listEnvironmentGroups,
  listEnvironments
} from '../../api';
import { ChipInput, Defaults } from '../../components';
import { SET_ERROR, useDispatch } from '../../globalErrors';
import { useClient, useSettings } from '../../hooks';
import { ChevronRightIcon } from '../../icons';
import { ArrowLeftIcon } from '../../icons/';

const WarehouseCreateForm = (props) => {
  const navigate = useNavigate();
  const params = useParams();
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const client = useClient();
  const { settings } = useSettings();
  const [loading, setLoading] = useState(true);
  const [groupOptions, setGroupOptions] = useState([]);
  const [environmentOptions, setEnvironmentOptions] = useState([]);
  const [environment, setEnvironment] = useState(null);

  const fetchEnvironments = useCallback(async () => {
    setLoading(true);
    const response = await client.query(
      listEnvironments({ filter: Defaults.selectListFilter })
    );
    if (!response.errors) {
      setEnvironmentOptions(
        response.data.listEnvironments.nodes.map((e) => ({
          ...e,
          value: e.environmentUri,
          label: e.label
        }))
      );
      setEnvironment(
        response.data.listEnvironments.nodes[
          response.data.listEnvironments.nodes.findIndex(
            (e) => e.environmentUri === params.uri
          )
        ]
      );
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [client, dispatch, params.uri]);

  const fetchGroups = useCallback(
    async (environmentUri) => {
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
    },
    [client, dispatch]
  );

  useEffect(() => {
    if (client) {
      fetchEnvironments().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, fetchEnvironments, dispatch]);

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const input = {
        label: values.label,
        description: values.description,
        clusterIdentifier: values.clusterIdentifier,
        tags: values.tags,
        SamlGroupName: values.SamlGroupName,
        databaseName: values.databaseName
      };
      const response = await client.mutate(
        importRedshiftCluster({
          environmentUri: values.environment.environmentUri,
          input
        })
      );
      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        enqueueSnackbar('Amazon Redshift cluster import started', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        navigate(
          `/console/warehouse/${response.data.importRedshiftCluster.clusterUri}`
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
  if (loading || !environmentOptions.length > 0 || !environment) {
    return <CircularProgress />;
  }

  return (
    <>
      <Helmet>
        <title>Warehouses: Warehouse Import | data.all</title>
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
                Import warehouse
              </Typography>
              <Breadcrumbs
                aria-label="breadcrumb"
                separator={<ChevronRightIcon fontSize="small" />}
                sx={{ mt: 1 }}
              >
                <Typography color="textPrimary" variant="subtitle2">
                  Organize
                </Typography>
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
                  to={`/console/environments/${environment.environmentUri}`}
                  variant="subtitle2"
                >
                  {environment.label}
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
                  to={`/console/environments/${params.uri}`}
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
                clusterIdentifier: '',
                databaseName: 'datahubdb',
                environment: '',
                SamlGroupName: '',
                tags: []
              }}
              validationSchema={Yup.object().shape({
                label: Yup.string()
                  .min(2, '*Cluster name must have at least 2 characters')
                  .max(63, "*Cluster name can't be longer than 63 characters")
                  .required('*Cluster name is required'),
                clusterIdentifier: Yup.string()
                  .min(2, '*Cluster name must have at least 2 characters')
                  .max(63, "*Cluster name can't be longer than 63 characters")
                  .required('*Cluster name is required'),
                description: Yup.string().max(5000),
                SamlGroupName: Yup.string()
                  .max(255)
                  .required('*Team is required'),
                environment: Yup.object().required('*Environment is required'),
                tags: Yup.array().nullable()
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
                            label="Warehouse name"
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
                      <Card sx={{ mb: 3 }}>
                        <CardHeader title="Redshift cluster" />
                        <CardContent>
                          <TextField
                            error={Boolean(
                              touched.clusterIdentifier &&
                                errors.clusterIdentifier
                            )}
                            fullWidth
                            helperText={
                              touched.clusterIdentifier &&
                              errors.clusterIdentifier
                            }
                            label="Amazon Redshift cluster identifier"
                            name="clusterIdentifier"
                            onBlur={handleBlur}
                            onChange={handleChange}
                            value={values.clusterIdentifier}
                            variant="outlined"
                          />
                        </CardContent>
                        <CardContent>
                          <TextField
                            error={Boolean(
                              touched.databaseName && errors.databaseName
                            )}
                            fullWidth
                            helperText={
                              touched.databaseName && errors.databaseName
                            }
                            label="data.all database name"
                            name="databaseName"
                            onBlur={handleBlur}
                            onChange={handleChange}
                            value={values.databaseName}
                            variant="outlined"
                          />
                        </CardContent>
                        <CardContent />
                      </Card>
                    </Grid>
                    <Grid item lg={5} md={6} xs={12}>
                      <Card sx={{ mb: 3 }}>
                        <CardHeader title="Deployment" />
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
                            defaultValue={() =>
                              environmentOptions[
                                environmentOptions.findIndex(
                                  (e) => e.environmentUri === params.uri
                                )
                              ]
                            }
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
                            {environmentOptions.map((e) => (
                              <MenuItem key={e.environmentUri} value={e}>
                                {e.label}
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
                      </Card>
                      <Card>
                        <CardHeader title="Organize" />
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
                          Import Warehouse
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

export default WarehouseCreateForm;
