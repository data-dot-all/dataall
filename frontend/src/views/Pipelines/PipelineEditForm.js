import { useCallback, useEffect, useState } from 'react';
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
  TextField,
  Typography
} from '@mui/material';
import { Helmet } from 'react-helmet-async';
import { LoadingButton } from '@mui/lab';
import useClient from '../../hooks/useClient';
import ChevronRightIcon from '../../icons/ChevronRight';
import ArrowLeftIcon from '../../icons/ArrowLeft';
import useSettings from '../../hooks/useSettings';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import ChipInput from '../../components/TagsInput';
import getDataPipeline from '../../api/DataPipeline/getDataPipeline';
import updateDataPipeline from '../../api/DataPipeline/updateDataPipeline';
import listEnvironments from '../../api/Environment/listEnvironments';
import PipelineEnvironmentEditForm from "./PipelineEnvironmentEditForm";
import * as Defaults from '../../components/defaults';


const PipelineEditForm = (props) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const params = useParams();
  const { enqueueSnackbar } = useSnackbar();
  const client = useClient();
  const { settings } = useSettings();
  const [loadingPipeline, setLoadingPipeline] = useState(true);
  const [loadingEnvs, setLoadingEnvs] = useState(true);
  const [pipeline, setPipeline] = useState(null);
  const [environmentOptions, setEnvironmentOptions] = useState([]);
  const [triggerEnvSubmit, setTriggerEnvSubmit] = useState(false);
  const [countEnvironmentsValid, setCountEnvironmentsValid] = useState(false);

  const handleCountEnvironmentValid = state => {
    setCountEnvironmentsValid(state);
      };

  const fetchItem = useCallback(async () => {
    setLoadingPipeline(true);
    const response = await client.query(getDataPipeline(params.uri));
    if (!response.errors && response.data.getDataPipeline !== null) {
      setPipeline(response.data.getDataPipeline);
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Pipeline not found';
      dispatch({ type: SET_ERROR, error });
    }
    setLoadingPipeline(false);
  }, [client, dispatch, params.uri]);

  useEffect(() => {
    if (client) {
      fetchItem().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client, dispatch, fetchItem]);

  const fetchEnvironments = useCallback(async () => {
    setLoadingEnvs(true);
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
    setLoadingEnvs(false);
  }, [client, dispatch]);

  useEffect(() => {
    if (client) {
      fetchEnvironments().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, dispatch, fetchEnvironments]);

  async function submit(values, setStatus, setSubmitting, setErrors) {
    if (!countEnvironmentsValid){
      dispatch({ type: SET_ERROR, error: "At least one deployment environment is required" })
    } else{
        try {
          const response = await client.mutate(
            updateDataPipeline({
              DataPipelineUri: pipeline.DataPipelineUri,
              input: {
                description: values.description,
                label: values.label,
                tags: values.tags
              }
            })
          );
          if (!response.errors) {
            setStatus({ success: true });
            setTriggerEnvSubmit(true);
            setSubmitting(false);
            enqueueSnackbar('Pipeline updated', {
              anchorOrigin: {
                horizontal: 'right',
                vertical: 'top'
              },
              variant: 'success'
            });
            navigate(
              `/console/pipelines/${response.data.updateDataPipeline.DataPipelineUri}`
            );
          } else {
            setTriggerEnvSubmit(false);
            dispatch({ type: SET_ERROR, error: response.errors[0].message });
          }
        } catch (err) {
          setStatus({ success: false });
          setTriggerEnvSubmit(false);
          setErrors({ submit: err.message });
          setSubmitting(false);
          dispatch({ type: SET_ERROR, error: err.message });
        }
      }
    }

  if ((loadingPipeline || loadingEnvs) || (!pipeline && pipeline.environment)) {
    return <CircularProgress />;
  }

  return (
    <>
      <Helmet>
        <title>Pipelines: Pipeline Update | data.all</title>
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
                Edit pipeline {pipeline.label}
              </Typography>
              <Breadcrumbs
                aria-label="breadcrumb"
                separator={<ChevronRightIcon fontSize="small" />}
                sx={{ mt: 1 }}
              >
                <Link underline="hover" color="textPrimary" variant="subtitle2">
                  Play
                </Link>
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
                  to={`/console/pipelines/${pipeline.DataPipelineUri}`}
                  variant="subtitle2"
                >
                  {pipeline.label}
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
                  to={`/console/pipelines/${pipeline.DataPipelineUri}`}
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
                label: pipeline.label,
                description: pipeline.description,
                SamlGroupName: pipeline.SamlAdminGroupName,
                tags: pipeline.tags
              }}
              validationSchema={Yup.object().shape({
                label: Yup.string()
                  .max(255)
                  .required('*Pipeline name is required'),
                description: Yup.string().max(5000),
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
                    <Grid item lg={7} md={7} xs={12}>
                      <Card>
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
                        <CardContent>
                          <TextField
                            disabled
                            fullWidth
                            label="Team"
                            name="SamlGroupName"
                            onBlur={handleBlur}
                            onChange={handleChange}
                            variant="outlined"
                            value={pipeline.SamlGroupName}
                          />
                        </CardContent>
                        <CardContent>
                          <TextField
                            disabled
                            fullWidth
                            label="Development Strategy"
                            name="devStrategy"
                            onBlur={handleBlur}
                            onChange={handleChange}
                            variant="outlined"
                            value={pipeline.devStrategy}
                          />
                        </CardContent>
                        <CardContent>
                          <Box>
                            <ChipInput
                              fullWidth
                              defaultValue={pipeline.tags}
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
                    </Grid>
                    <Grid item lg={5} md={5} xs={12}>
                      <Card sx={{ mb: 3 }}>
                        <CardHeader title="Deployment" />
                        <CardContent>
                          <TextField
                            disabled
                            fullWidth
                            label="Environment"
                            name="environment"
                            value={pipeline.environment.label}
                            variant="outlined"
                          />
                        </CardContent>
                        <CardContent>
                          <TextField
                            disabled
                            fullWidth
                            label="Region"
                            name="region"
                            value={pipeline.environment.region}
                            variant="outlined"
                          />
                        </CardContent>
                        <CardContent>
                          <TextField
                            disabled
                            fullWidth
                            label="Organization"
                            name="organization"
                            value={pipeline.organization.label}
                            variant="outlined"
                          />
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item lg={12} md={6} xs={12}>
                      <Box sx={{ mt: 3 }}>
                        <PipelineEnvironmentEditForm
                          environmentOptions={environmentOptions}
                          triggerEnvSubmit={triggerEnvSubmit}
                          pipelineUri={pipeline.DataPipelineUri}
                          pipeline={pipeline}
                          handleCountEnvironmentValid={handleCountEnvironmentValid}
                        />
                      </Box>
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
                          Update Pipeline
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

export default PipelineEditForm;
