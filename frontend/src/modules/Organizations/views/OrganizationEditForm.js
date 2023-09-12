import { LoadingButton } from '@mui/lab';
import {
  Box,
  Breadcrumbs,
  Button,
  Card,
  CardContent,
  CardHeader,
  Container,
  FormHelperText,
  Grid,
  Link,
  TextField,
  Typography
} from '@mui/material';
import CircularProgress from '@mui/material/CircularProgress';
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
  useSettings
} from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { getOrganization, useClient } from 'services';
import { updateOrganization } from '../services';

const OrganizationEditForm = (props) => {
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const client = useClient();
  const { settings } = useSettings();
  const params = useParams();
  const [organization, setOrganization] = useState({});
  const [loading, setLoading] = useState(true);
  const fetchItem = useCallback(async () => {
    const response = await client.query(getOrganization(params.uri));
    if (!response.errors) {
      setOrganization(response.data.getOrganization);
      setLoading(false);
    }
    setLoading(false);
  }, [client, params.uri]);

  useEffect(() => {
    if (client) {
      fetchItem().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client, fetchItem, dispatch]);

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = await client.mutate(
        updateOrganization({
          organizationUri: organization.organizationUri,
          input: {
            label: values.label,
            description: values.description,
            tags: values.tags
          }
        })
      );
      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        enqueueSnackbar('Organization Updated', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        navigate(
          `/console/organizations/${response.data.updateOrganization.organizationUri}`
        );
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

  return (
    <>
      <Helmet>
        <title>Organizations: Organization Edit | data.all</title>
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
                Organization Edit
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
                  to="/console/organizations"
                  variant="subtitle2"
                >
                  Organizations
                </Link>
                <Typography color="textSecondary" variant="subtitle2">
                  Edit
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
                  to="/console/organizations"
                  variant="outlined"
                >
                  Cancel
                </Button>
              </Box>
            </Grid>
          </Grid>
          {loading ? (
            <CircularProgress />
          ) : (
            <Box sx={{ mt: 3 }}>
              <Formik
                initialValues={{
                  label: organization.label || '',
                  description: organization.description || '',
                  SamlGroupName: organization.SamlGroupName || '',
                  tags: organization.tags || []
                }}
                validationSchema={Yup.object().shape({
                  label: Yup.string().max(255).required(),
                  description: Yup.string().max(5000),
                  tags: Yup.array()
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
                      <Grid item lg={8} md={6} xs={12}>
                        <Card>
                          <CardHeader title="Details" />
                          <CardContent>
                            <Box sx={{ mb: 2 }}>
                              <TextField
                                error={Boolean(touched.label && errors.label)}
                                fullWidth
                                helperText={touched.label && errors.label}
                                label="Organization Name"
                                name="label"
                                onBlur={handleBlur}
                                onChange={handleChange}
                                value={values.label}
                                variant="outlined"
                              />
                            </Box>
                            <Box sx={{ mt: 3 }}>
                              <TextField
                                autoFocus
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
                            </Box>
                          </CardContent>
                        </Card>
                      </Grid>
                      <Grid item lg={4} md={6} xs={12}>
                        <Card>
                          <CardHeader title="Organize" />
                          <CardContent>
                            <TextField
                              fullWidth
                              label="Team"
                              name="SamlGroupName"
                              value={values.SamlGroupName}
                              variant="outlined"
                              disabled
                            />
                          </CardContent>
                          <CardContent>
                            <CardContent>
                              <Box>
                                <ChipInput
                                  fullWidth
                                  defaultValue={organization.tags}
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
                          </CardContent>
                        </Card>
                        {errors.submit && (
                          <Box sx={{ mt: 3 }}>
                            <FormHelperText error>
                              {errors.submit}
                            </FormHelperText>
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
                            disabled={isSubmitting}
                            type="submit"
                            variant="contained"
                          >
                            Update Organization
                          </LoadingButton>
                        </Box>
                      </Grid>
                    </Grid>
                  </form>
                )}
              </Formik>
            </Box>
          )}
        </Container>
      </Box>
    </>
  );
};

export default OrganizationEditForm;
