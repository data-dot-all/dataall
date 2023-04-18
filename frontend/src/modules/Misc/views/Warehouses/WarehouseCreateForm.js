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
  ArrowLeftIcon,
  ChevronRightIcon,
  ChipInput,
  Defaults,
  useSettings
} from '../../../../design';
import { SET_ERROR, useDispatch } from '../../../../globalErrors';
import {
  createRedshiftCluster,
  listEnvironmentGroups,
  listEnvironments,
  useClient
} from '../../../../services';

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
  const nodeTypes = [
    { label: 'dc2.large', value: 'dc2.large' },
    { label: 'ds2.xlarge', value: 'ds2.xlarge' },
    { label: 'ds2.8xlarge', value: 'ds2.8xlarge' },
    { label: 'dc1.large', value: 'dc1.large' },
    { label: 'dc2.8xlarge', value: 'dc2.8xlarge' },
    { label: 'ra3.16xlarge', value: 'ra3.16xlarge' }
  ];

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
        vpc: values.vpcId,
        tags: values.tags,
        nodeType: values.nodeType,
        masterDatabaseName: values.masterDatabaseName,
        masterUsername: values.masterUsername,
        numberOfNodes: parseInt(values.numberOfNodes, 10),
        SamlGroupName: values.SamlGroupName,
        databaseName: values.databaseName
      };
      const response = await client.mutate(
        createRedshiftCluster({
          environmentUri: values.environment.environmentUri,
          input
        })
      );
      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        enqueueSnackbar('Amazon Redshift cluster creation started', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        navigate(
          `/console/warehouse/${response.data.createRedshiftCluster.clusterUri}`
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
        <title>Warehouses: Warehouse Create | data.all</title>
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
                Create a new warehouse
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
                <Typography color="textPrimary" variant="subtitle2">
                  Warehouses
                </Typography>
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
                nodeType: '',
                masterDatabaseName: '',
                masterUsername: '',
                databaseName: 'datahubdb',
                vpcId: '',
                numberOfNodes: 2,
                clusterType: '',
                environment: '',
                SamlGroupName: '',
                tags: []
              }}
              validationSchema={Yup.object().shape({
                label: Yup.string()
                  .min(2, '*Cluster name must have at least 2 characters')
                  .max(63, "*Cluster name can't be longer than 63 characters")
                  .required('*Cluster name is required'),
                description: Yup.string().max(5000),
                SamlGroupName: Yup.string()
                  .max(255)
                  .required('*Team is required'),
                environment: Yup.object().required('*Environment is required'),
                tags: Yup.array().nullable(),
                masterDatabaseName: Yup.string()
                  .matches(
                    '^[a-zA-Z]*$',
                    '*Database name is not valid (^[a-zA-Z]*$)'
                  )
                  .min(2, '*Database name must have at least 2 characters')
                  .max(
                    60,
                    "*Database name name can't be longer than 60 characters"
                  )
                  .required('*Database name is required'),
                databaseName: Yup.string()
                  .matches(
                    '^[a-zA-Z]*$',
                    '*Master database name is not valid (^[a-zA-Z]*$)'
                  )
                  .min(
                    2,
                    '*Master database name must have at least 2 characters'
                  )
                  .max(
                    60,
                    "*Master database name name can't be longer than 60 characters"
                  )
                  .required('*Master database name is required'),
                masterUsername: Yup.string()
                  .matches(
                    '^[a-zA-Z]*$',
                    '*Master user is not valid (^[a-zA-Z]*$)'
                  )
                  .min(2, '*Master user must have at least 2 characters')
                  .max(
                    60,
                    "*Master user name can't be longer than 60 characters"
                  )
                  .required('*Master user is required'),
                numberOfNodes: Yup.number().required(
                  '*Number of nodes is required'
                ),
                nodeType: Yup.string().required('*Node type is required'),
                vpcId: Yup.string()
                  .matches('vpc-*', '*VPC Id is not valid')
                  .required('*VPC Id is required')
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
                        <CardHeader title="Database" />
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
                        <CardContent>
                          <TextField
                            error={Boolean(
                              touched.masterDatabaseName &&
                                errors.masterDatabaseName
                            )}
                            fullWidth
                            helperText={
                              touched.masterDatabaseName &&
                              errors.masterDatabaseName
                            }
                            label="Master database name"
                            name="masterDatabaseName"
                            onBlur={handleBlur}
                            onChange={handleChange}
                            value={values.masterDatabaseName}
                            variant="outlined"
                          />
                        </CardContent>
                        <CardContent>
                          <TextField
                            error={Boolean(
                              touched.masterUsername && errors.masterUsername
                            )}
                            fullWidth
                            helperText={
                              touched.masterUsername && errors.masterUsername
                            }
                            label="Master user"
                            name="masterUsername"
                            onBlur={handleBlur}
                            onChange={handleChange}
                            value={values.masterUsername}
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
                        <CardContent>
                          <TextField
                            error={Boolean(touched.vpcId && errors.vpcId)}
                            fullWidth
                            placeholder="vpc-1233456"
                            helperText={touched.vpcId && errors.vpcId}
                            label="VPC ID"
                            name="vpcId"
                            onBlur={handleBlur}
                            onChange={handleChange}
                            value={values.vpcId}
                            variant="outlined"
                          />
                        </CardContent>
                        <CardContent>
                          <TextField
                            fullWidth
                            error={Boolean(touched.nodeType && errors.nodeType)}
                            helperText={touched.nodeType && errors.nodeType}
                            label="Node type"
                            name="nodeType"
                            onChange={handleChange}
                            select
                            value={values.nodeType}
                            variant="outlined"
                          >
                            {nodeTypes.map((node) => (
                              <MenuItem key={node.value} value={node.value}>
                                {node.label}
                              </MenuItem>
                            ))}
                          </TextField>
                        </CardContent>
                        <CardContent>
                          <TextField
                            error={Boolean(
                              touched.numberOfNodes && errors.numberOfNodes
                            )}
                            fullWidth
                            helperText={
                              touched.numberOfNodes && errors.numberOfNodes
                            }
                            label="Number of nodes"
                            name="numberOfNodes"
                            onBlur={handleBlur}
                            onChange={handleChange}
                            value={values.numberOfNodes}
                            variant="outlined"
                          />
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader title="Organize" />
                        <CardContent>
                          <TextField
                            error={Boolean(
                              touched.SamlGroupName && errors.SamlGroupName
                            )}
                            helperText={
                              touched.SamlGroupName && errors.SamlGroupName
                            }
                            fullWidth
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
                          Create Warehouse
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
