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
  TextField,
  Typography
} from '@mui/material';
import { Helmet } from 'react-helmet-async';
import { LoadingButton } from '@mui/lab';
import { useCallback, useEffect, useState } from 'react';
import useClient from '../../hooks/useClient';
import ChevronRightIcon from '../../icons/ChevronRight';
import ArrowLeftIcon from '../../icons/ArrowLeft';
import useSettings from '../../hooks/useSettings';
import listEnvironments from '../../api/Environment/listEnvironments';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import ChipInput from '../../components/TagsInput';
import createDataPipeline from '../../api/DataPipeline/createDataPipeline';
import listEnvironmentGroups from '../../api/Environment/listEnvironmentGroups';
import * as Defaults from '../../components/defaults';
import listDatasetsOwnedByEnvGroup from "../../api/Environment/listDatasetsOwnedByEnvGroup";
import listDataItemsSharedWithEnvGroup from "../../api/Environment/listDataItemsSharedWithEnvGroup";

const PipelineCrateForm = (props) => {
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const client = useClient();
  const { settings } = useSettings();
  const [loading, setLoading] = useState(true);
  const [currentEnv, setCurrentEnv] = useState('');
  const [groupOptions, setGroupOptions] = useState([]);
  const [environmentOptions, setEnvironmentOptions] = useState([]);
  const [datasetOptions, setDatasetOptions] = useState([]);
  const devOptions =[{value:"trunk", label:"Trunk-based"},{value:"gitflow", label:"Gitflow"}];

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
    setCurrentEnv(environmentUri)
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
    let sharedWithDatasets = [];
    try {
      const response = await client.query(
        listDatasetsOwnedByEnvGroup({
          filter: Defaults.SelectListFilter,
          environmentUri: currentEnv,
          groupUri: groupUri,
        })
      );
      if (!response.errors) {
        ownedDatasets =
          response.data.listDatasetsOwnedByEnvGroup.nodes?.map((dataset) => ({
            value: dataset.datasetUri,
            label: dataset.label
          }))
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    }
    try {
      const response = await client.query(
        listDataItemsSharedWithEnvGroup({
          filter: {
            page: 1,
            pageSize: 10000,
            term: '',
            itemTypes: 'DatasetTable'
          },
          environmentUri: currentEnv,
          groupUri: groupUri,
        })
      );
      if (!response.errors) {
        sharedWithDatasets =
          response.data.listDataItemsSharedWithEnvGroup.nodes?.map((dataset) => ({
            value: dataset.datasetUri,
            label: dataset.label
          }))
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    }
    setDatasetOptions(ownedDatasets.concat(sharedWithDatasets));
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
        createDataPipeline({
          input: {
            label: values.label,
            environmentUri: values.environment.environmentUri,
            description: values.description,
            SamlGroupName: values.SamlGroupName,
            tags: values.tags,
            devStrategy: values.devStrategy,
            devStages: values.devStages,
            inputDatasetUri: values.inputDatasetUri,
            outputDatasetUri: values.outputDatasetUri,
            template: values.template,
          }
        })
      );
      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        enqueueSnackbar('Pipeline creation started', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        navigate(
          `/console/pipelines/${response.data.createDataPipeline.DataPipelineUri}`
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
        <title>Pipelines: Pipeline Create | data.all</title>
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
                Create a new pipeline
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
                  to="/console/pipelines"
                  variant="subtitle2"
                >
                  Pipelines
                </Link>
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to="/console/pipelines/new"
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
                  to="/console/pipelines"
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
                SamlGroupName: '',
                environment: '',
                tags: [],
                devStages: [],
                devStrategy: '',
                inputDatasetUri: '',
                outputDatasetUri: '',
                template: ''
              }}
              validationSchema={Yup.object().shape({
                label: Yup.string()
                  .max(255)
                  .required('*Pipeline name is required'),
                description: Yup.string().max(5000),
                SamlGroupName: Yup.string()
                  .max(255)
                  .required('*Team is required'),
                environment: Yup.object().required('*Environment is required'),
                devStages: Yup.array().required('*At least ONE stage is required'),
                devStrategy: Yup.string().required('*A development strategy is required'),
                tags: Yup.array().nullable(),
                inputDatasetUri: Yup.string().nullable(),
                outputDatasetUri: Yup.string().nullable(),
                template: Yup.string().nullable()
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
                            label="Pipeline name"
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
                              placeholder="Hit enter after typing value"
                              onChange={(chip) => {
                                setFieldValue('tags', [...chip]);
                              }}
                            />
                          </Box>
                        </CardContent>
                      </Card>
                      <Card sx={{ mb: 3 }}>
                        <CardHeader title="Parameters" />
                        <CardContent>
                          <TextField
                            fullWidth
                            error={Boolean(
                              touched.inputDatasetUri && errors.inputDatasetUri
                            )}
                            helperText={
                              touched.inputDatasetUri && errors.inputDatasetUri
                            }
                            label="Input Dataset"
                            name="inputDatasetUri"
                            onChange={handleChange}
                            select
                            value={values.inputDatasetUri}
                            variant="outlined"
                          >
                            {datasetOptions.map((dataset) => (
                              <MenuItem key={dataset.value} value={dataset.value}>
                                {dataset.label}
                              </MenuItem>
                            ))}
                          </TextField>
                        </CardContent>
                        <CardContent>
                          <TextField
                            fullWidth
                            error={Boolean(
                              touched.outputDatasetUri && errors.outputDatasetUri
                            )}
                            helperText={
                              touched.outputDatasetUri && errors.outputDatasetUri
                            }
                            label="Output Dataset"
                            name="outputDatasetUri"
                            onChange={handleChange}
                            select
                            value={values.outputDatasetUri}
                            variant="outlined"
                          >
                            {datasetOptions.map((dataset) => (
                              <MenuItem key={dataset.value} value={dataset.value}>
                                {dataset.label}
                              </MenuItem>
                            ))}
                          </TextField>
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
                              setFieldValue('inputDatasetUri', '');
                              setFieldValue('outputDatasetUri', '');
                              fetchDatasets(
                                event.target.value
                              ).catch((e) =>
                                dispatch({ type: SET_ERROR, error: e.message })
                              );
                              setFieldValue('SamlGroupName', event.target.value);
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
                          <TextField
                            fullWidth
                            error={Boolean(
                              touched.devStrategy && errors.devStrategy
                            )}
                            helperText={
                              touched.devStrategy && errors.devStrategy
                            }
                            label="Development strategy"
                            name="devStrategy"
                            onChange={handleChange}
                            select
                            value={values.devStrategy}
                            variant="outlined"
                          >
                            {devOptions.map((dev) => (
                              <MenuItem key={dev.value} value={dev.value}>
                                {dev.label}
                              </MenuItem>
                            ))}
                          </TextField>
                        </CardContent>
                        <CardContent>
                          <Box>
                            <ChipInput
                              fullWidth
                              error={Boolean(touched.devStages && errors.devStages)}
                              helperText={touched.devStages && errors.devStages}
                              variant="outlined"
                              label="Development stages (dev,test,prod..)"
                              placeholder="Hit enter after typing the value of each stage"
                              onChange={(chip) => {
                                setFieldValue('devStages', [...chip]);
                              }}
                            />
                          </Box>
                        </CardContent>
                        <CardContent>
                          <TextField
                            error={Boolean(touched.template && errors.template)}
                            fullWidth
                            helperText={touched.template && errors.template}
                            label="URL to a git repository (ddk init --template)"
                            name="template"
                            onBlur={handleBlur}
                            onChange={handleChange}
                            value={values.template}
                            variant="outlined"
                          />
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
                          Create Pipeline
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

export default PipelineCrateForm;
