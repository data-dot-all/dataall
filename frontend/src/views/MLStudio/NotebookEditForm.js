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
import getSagemakerStudioUserProfile from '../../api/SagemakerStudio/getSagemakerStudioUserProfile';
import updateUserProfile from '../../api/UserProfile/updateUserProfile';

const PipelineEditForm = (props) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const params = useParams();
  const { enqueueSnackbar } = useSnackbar();
  const client = useClient();
  const { settings } = useSettings();
  const [loading, setLoading] = useState(true);
  const [notebook, setNotebook] = useState(null);

  const fetchItem = useCallback(async () => {
    setLoading(true);
    const response = await client.query(
      getSagemakerStudioUserProfile(params.uri)
    );
    if (
      !response.errors &&
      response.data.getSagemakerStudioUserProfile !== null
    ) {
      setNotebook(response.data.getSagemakerStudioUserProfile);
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Notebook not found';
      dispatch({ type: SET_ERROR, error });
    }
    setLoading(false);
  }, [client, dispatch, params.uri]);

  useEffect(() => {
    if (client) {
      fetchItem().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client, dispatch, fetchItem]);

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = await client.mutate(
        updateUserProfile({
          input: {
            sagemakerStudioUserProfileUri:
              notebook.sagemakerStudioUserProfileUri,
            description: values.description,
            label: values.label,
            tags: values.tags
          }
        })
      );
      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        enqueueSnackbar('Notebook updated', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        navigate(
          `/console/mlstudio/${response.data.updateUserProfile.sagemakerStudioUserProfileUri}`
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

  if (loading || !(notebook && notebook.environment)) {
    return <CircularProgress />;
  }

  return (
    <>
      <Helmet>
        <title>Dataset: Notebook Update | data.all</title>
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
                Edit notebook {notebook.label}
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
                  to="/console/datasets"
                  variant="subtitle2"
                >
                  ML Studio
                </Link>
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to={`/console/mlstudio/${notebook.sagemakerStudioUserProfileUri}`}
                  variant="subtitle2"
                >
                  {notebook.label}
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
                  to={`/console/mlstudio/${notebook.sagemakerStudioUserProfileUri}`}
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
                label: notebook.label,
                description: notebook.description,
                SamlGroupName: notebook.SamlAdminGroupName,
                tags: notebook.tags
              }}
              validationSchema={Yup.object().shape({
                label: Yup.string()
                  .max(255)
                  .required('*Dataset name is required'),
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
                        <CardHeader title="Organize" />
                        <CardContent>
                          <TextField
                            disabled
                            fullWidth
                            label="Team"
                            name="SamlGroupName"
                            onBlur={handleBlur}
                            onChange={handleChange}
                            variant="outlined"
                            value={notebook.SamlGroupName}
                          />
                        </CardContent>
                        <CardContent>
                          <Box>
                            <ChipInput
                              fullWidth
                              defaultValue={notebook.tags}
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
                            value={notebook.environment.label}
                            variant="outlined"
                          />
                        </CardContent>
                        <CardContent>
                          <TextField
                            disabled
                            fullWidth
                            label="Region"
                            name="region"
                            value={notebook.environment.region}
                            variant="outlined"
                          />
                        </CardContent>
                        <CardContent>
                          <TextField
                            disabled
                            fullWidth
                            label="Organization"
                            name="organization"
                            value={notebook.organization.label}
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

export default PipelineEditForm;
