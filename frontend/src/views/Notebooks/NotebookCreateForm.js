import { Link as RouterLink, useNavigate } from 'react-router-dom';
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
  Slider,
  TextField,
  Typography
} from '@mui/material';
import { Helmet } from 'react-helmet-async';
import { Autocomplete, LoadingButton } from '@mui/lab';
import { useCallback, useEffect, useState } from 'react';
import useClient from '../../hooks/useClient';
import ChevronRightIcon from '../../icons/ChevronRight';
import ArrowLeftIcon from '../../icons/ArrowLeft';
import useSettings from '../../hooks/useSettings';
import createSagemakerNotebook from '../../api/SagemakerNotebook/createSagemakerNotebook';
import listEnvironments from '../../api/Environment/listEnvironments';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import ChipInput from '../../components/TagsInput';
import listEnvironmentGroups from '../../api/Environment/listEnvironmentGroups';
import * as Defaults from '../../components/defaults';

const NotebookCreateForm = (props) => {
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const client = useClient();
  const { settings } = useSettings();
  const [loading, setLoading] = useState(true);
  const [groupOptions, setGroupOptions] = useState([]);
  const [environmentOptions, setEnvironmentOptions] = useState([]);
  const [vpcOptions, setVpcOptions] = useState([]);
  const [subnetOptions, setSubnetOptions] = useState([]);
  const marks = [
    {
      value: 32,
      label: '32'
    },
    {
      value: 64,
      label: '64'
    },
    {
      value: 128,
      label: '128'
    },
    {
      value: 256,
      label: '256'
    }
  ];
  const instanceTypes = [
    { label: 'ml.t3.medium', value: 'ml.t3.medium' },
    { label: 'ml.t3.large', value: 'ml.t3.large' },
    { label: 'ml.m5.xlarge', value: 'ml.m5.xlarge' }
  ];

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
    }
  }, [client, dispatch, fetchEnvironments]);

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = await client.mutate(
        createSagemakerNotebook({
          label: values.label,
          environmentUri: values.environment.environmentUri,
          description: values.description,
          SamlAdminGroupName: values.SamlAdminGroupName,
          tags: values.tags,
          VpcId: values.VpcId,
          SubnetId: values.SubnetId,
          VolumeSizeInGB: values.VolumeSizeInGB,
          InstanceType: values.InstanceType
        })
      );
      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        enqueueSnackbar('Sagemaker instance creation started', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        navigate(
          `/console/notebooks/${response.data.createSagemakerNotebook.notebookUri}`
        );
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (err) {
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
        <title>Notebooks: Notebook Create | data.all</title>
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
                Create a new notebook
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
                  to="/console/notebooks"
                  variant="subtitle2"
                >
                  Notebooks
                </Link>
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to="/console/notebooks/new"
                  variant="subtitle2"
                >
                  Create
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
                  to="/console/notebooks"
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
                SamlAdminGroupName: '',
                VpcId: '',
                SubnetId: '',
                VolumeSizeInGB: 32,
                InstanceType: '',
                environment: '',
                tags: []
              }}
              validationSchema={Yup.object().shape({
                label: Yup.string()
                  .max(255)
                  .required('*Notebook name is required'),
                description: Yup.string().max(5000),
                SamlAdminGroupName: Yup.string()
                  .max(255)
                  .required('*Team is required'),
                environment: Yup.object().required('*Environment is required'),
                tags: Yup.array().nullable(),
                VpcId: Yup.string().min(1).required('*VPC ID is required'),
                SubnetId: Yup.string().min(1).required('*Subnet ID is required'),
                InstanceType: Yup.string()
                  .min(1)
                  .required('*Instance type is required'),
                VolumeSizeInGB: Yup.number()
                  .min(32)
                  .max(256)
                  .required('*Volume size in GB is required')
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
                            label="Sagemaker instance name"
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
                        <CardContent>
                          <Box>
                            <ChipInput
                              fullWidth
                              error={Boolean(touched.tags && errors.tags)}
                              helperText={touched.tags && errors.tags}
                              variant="outlined"
                              label="Tags"
                              onChange={(chip) => {
                                setFieldValue('tags', [...chip]);
                              }}
                            />
                          </Box>
                        </CardContent>
                      </Card>
                      <Card sx={{ mb: 3 }}>
                        <CardHeader title="Instance Properties" />
                        <CardContent>
                          <TextField
                            id="InstanceType"
                            fullWidth
                            error={Boolean(
                              touched.InstanceType && errors.InstanceType
                            )}
                            helperText={
                              touched.InstanceType && errors.InstanceType
                            }
                            label="Instance type"
                            name="InstanceType"
                            onChange={handleChange}
                            select
                            value={values.InstanceType}
                            variant="outlined"
                          >
                            {instanceTypes.map((i) => (
                              <MenuItem key={i.value} value={i.value}>
                                {i.label}
                              </MenuItem>
                            ))}
                          </TextField>
                        </CardContent>
                        <CardContent>
                          <Box sx={{ p: 1 }}>
                            <Typography color="textSecondary" gutterBottom>
                              Volume size
                            </Typography>
                            <Slider
                              defaultValue={32}
                              aria-labelledby="discrete-slider"
                              valueLabelDisplay="auto"
                              marks={marks}
                              min={32}
                              max={256}
                              onChange={(event, value) => {
                                setFieldValue('VolumeSizeInGB', value);
                              }}
                            />
                            {touched.VolumeSizeInGB && errors.VolumeSizeInGB && (
                              <Box sx={{ mt: 2 }}>
                                <FormHelperText error>
                                  {errors.VolumeSizeInGB}
                                </FormHelperText>
                              </Box>
                            )}
                          </Box>
                        </CardContent>
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
                            onChange={(event) => {
                              setFieldValue('SamlAdminGroupName', '');
                              fetchGroups(
                                event.target.value.environmentUri
                              ).catch((e) =>
                                dispatch({ type: SET_ERROR, error: e.message })
                              );
                              setFieldValue('environment', event.target.value);
                              setVpcOptions(
                                event.target.value.networks.map((v) => ({
                                  ...v,
                                  value: v,
                                  label: v.VpcId
                                }))
                              );
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
                              touched.SamlAdminGroupName &&
                                errors.SamlAdminGroupName
                            )}
                            helperText={
                              touched.SamlAdminGroupName &&
                              errors.SamlAdminGroupName
                            }
                            label="Team"
                            name="SamlAdminGroupName"
                            onChange={handleChange}
                            select
                            value={values.SamlAdminGroupName}
                            variant="outlined"
                          >
                            {groupOptions.map((group) => (
                              <MenuItem key={group.value} value={group.value}>
                                {group.label}
                              </MenuItem>
                            ))}
                          </TextField>
                        </CardContent>
                      </Card>
                      <Card sx={{ mt: 3 }}>
                        <CardHeader title="Networking" />
                        <Box sx={{ p: 2 }}>
                          <Box>
                            <Autocomplete
                              id="VpcId"
                              freeSolo
                              options={vpcOptions.map((option) => option.label)}
                              onChange={(event, value) => {
                                setSubnetOptions([]);
                                const filteredVpc = vpcOptions.filter(
                                  (v) => v.VpcId === value
                                );
                                if (
                                  value &&
                                  vpcOptions &&
                                  filteredVpc.length === 1
                                ) {
                                  setSubnetOptions(
                                    filteredVpc[0].privateSubnetIds.concat(
                                      filteredVpc[0].publicSubnetIds
                                    )
                                  );
                                  setFieldValue('VpcId', value);
                                } else {
                                  setFieldValue('VpcId', value);
                                }
                              }}
                              renderInput={(params) => (
                                <TextField
                                  {...params}
                                  label="VPC ID"
                                  margin="normal"
                                  error={Boolean(touched.VpcId && errors.VpcId)}
                                  helperText={touched.VpcId && errors.VpcId}
                                  onChange={handleChange}
                                  value={values.SubnetId}
                                  variant="outlined"
                                />
                              )}
                            />
                          </Box>
                          <Box sx={{ mt: 1 }}>
                            <Autocomplete
                              id="SubnetId"
                              freeSolo
                              options={subnetOptions.map((option) => option)}
                              onChange={(event, value) => {
                                setFieldValue('SubnetId', value);
                              }}
                              renderInput={(params) => (
                                <TextField
                                  {...params}
                                  label="Subnet ID"
                                  margin="normal"
                                  error={Boolean(
                                    touched.SubnetId && errors.SubnetId
                                  )}
                                  helperText={
                                    touched.SubnetId && errors.SubnetId
                                  }
                                  onChange={handleChange}
                                  value={values.SubnetId}
                                  variant="outlined"
                                />
                              )}
                            />
                          </Box>
                        </Box>
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
                          Create Notebook
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

export default NotebookCreateForm;
