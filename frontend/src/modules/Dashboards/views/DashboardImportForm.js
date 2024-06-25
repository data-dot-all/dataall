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
  Container,
  FormHelperText,
  Grid,
  Link,
  TextField,
  Typography
} from '@mui/material';
import { Formik } from 'formik';
import { useSnackbar } from 'notistack';
import { useCallback, useEffect, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import * as Yup from 'yup';
import {
  ArrowLeftIcon,
  ChevronRightIcon,
  ChipInput,
  Defaults,
  useSettings
} from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { searchGlossary, useClient } from 'services';
import { importDashboard } from '../services';
import { EnvironmentTeamDropdown } from 'modules/Shared';

const DashboardImportForm = (props) => {
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const client = useClient();
  const { settings } = useSettings();
  const [selectableTerms, setSelectableTerms] = useState([]);

  const fetchTerms = useCallback(async () => {
    const response = await client.query(
      searchGlossary(Defaults.selectListFilter)
    );
    if (!response.errors) {
      if (
        response.data.searchGlossary &&
        response.data.searchGlossary.nodes.length > 0
      ) {
        const selectables = response.data.searchGlossary.nodes.map((node) => ({
          label: node.label,
          value: node.nodeUri,
          nodeUri: node.nodeUri,
          disabled: node.__typename !== 'Term' /* eslint-disable-line*/,
          nodePath: node.path,
          nodeType: node.__typename /* eslint-disable-line*/
        }));
        setSelectableTerms(selectables);
      }
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  }, [client, dispatch]);
  useEffect(() => {
    if (client) {
      fetchTerms().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, fetchTerms, dispatch]);

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = await client.mutate(
        importDashboard({
          input: {
            label: values.label,
            dashboardId: values.dashboardId,
            environmentUri: values.environment.environmentUri,
            description: values.description,
            SamlGroupName: values.SamlAdminGroupName,
            tags: values.tags,
            terms: values.terms.nodes
              ? values.terms.nodes.map((t) => t.nodeUri)
              : values.terms.map((t) => t.nodeUri)
          }
        })
      );
      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        enqueueSnackbar('QuickSight dashboard imported', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        navigate(
          `/console/dashboards/${response.data.importDashboard.dashboardUri}`
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

  return (
    <>
      <Helmet>
        <title>Dashboards: Dashboard Create | data.all</title>
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
                Import a QuickSight dashboard
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
                  to="/console/dashboards"
                  variant="subtitle2"
                >
                  Dashboards
                </Link>
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to="/console/dashboards/new"
                  variant="subtitle2"
                >
                  Import
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
                  to="/console/dashboards"
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
                dashboardId: '',
                description: '',
                SamlAdminGroupName: '',
                environment: '',
                tags: [],
                terms: []
              }}
              validationSchema={Yup.object().shape({
                label: Yup.string()
                  .max(255)
                  .required('*Dashboard name is required'),
                dashboardId: Yup.string()
                  .max(255)
                  .required('*QuickSight dashboard identifier is required'),
                description: Yup.string().max(5000),
                SamlAdminGroupName: Yup.string()
                  .max(255)
                  .required('*Team is required'),
                environment: Yup.object().required('*Environment is required'),
                tags: Yup.array().nullable(),
                terms: Yup.array().nullable()
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
                            label="Dashboard name"
                            name="label"
                            onBlur={handleBlur}
                            onChange={handleChange}
                            value={values.label}
                            variant="outlined"
                          />
                        </CardContent>
                        <CardContent>
                          <TextField
                            error={Boolean(
                              touched.dashboardId && errors.dashboardId
                            )}
                            fullWidth
                            helperText={
                              touched.dashboardId && errors.dashboardId
                            }
                            label="QuickSight dashboard identifier"
                            name="dashboardId"
                            onBlur={handleBlur}
                            onChange={handleChange}
                            value={values.dashboardId}
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
                      <Card>
                        <CardHeader title="Organize" />
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
                          <Autocomplete
                            multiple
                            id="tags-filled"
                            options={selectableTerms}
                            getOptionLabel={(opt) => opt.label}
                            getOptionDisabled={(opt) => opt.disabled}
                            getOptionSelected={(option, value) =>
                              option.nodeUri === value.nodeUri
                            }
                            onChange={(event, value) => {
                              setFieldValue('terms', value);
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
                                fullWidth
                                variant="outlined"
                                label="Glossary Terms"
                              />
                            )}
                          />
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item lg={5} md={6} xs={12}>
                      <EnvironmentTeamDropdown
                        setFieldValue={setFieldValue}
                        handleChange={handleChange}
                        values={values}
                        touched={touched}
                        errors={errors}
                      />
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
                          Import Dashboard
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

export default DashboardImportForm;
