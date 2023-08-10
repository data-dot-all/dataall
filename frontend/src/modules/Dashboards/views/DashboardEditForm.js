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
import CircularProgress from '@mui/material/CircularProgress';
import { Formik } from 'formik';
import { useSnackbar } from 'notistack';
import * as PropTypes from 'prop-types';
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
} from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { searchGlossary, useClient } from 'services';
import { getDashboard, updateDashboard } from '../services';

function DashboardEditHeader(props) {
  const { dashboard } = props;
  return (
    <Grid container justifyContent="space-between" spacing={3}>
      <Grid item>
        <Typography color="textPrimary" variant="h5">
          {`Update Dashboard: ${dashboard.label}`}
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
            to="/console/dashboards"
            variant="subtitle2"
          >
            Dashboards
          </Link>
          <Link
            underline="hover"
            color="textPrimary"
            component={RouterLink}
            to={`/console/dashboards/${dashboard.dashboardUri}`}
            variant="subtitle2"
          >
            {dashboard.label}
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
            to={`/console/dashboards/${dashboard.dashboardUri}`}
            variant="outlined"
          >
            Cancel
          </Button>
        </Box>
      </Grid>
    </Grid>
  );
}

DashboardEditHeader.propTypes = { dashboard: PropTypes.object.isRequired };

const DashboardEditForm = () => {
  const dispatch = useDispatch();
  const { settings } = useSettings();
  const params = useParams();
  const client = useClient();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const [dashboard, setDashboard] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectableTerms, setSelectableTerms] = useState([]);
  const [dashboardTerms, setDashboardTerms] = useState([]);
  const fetchItem = useCallback(async () => {
    setLoading(true);
    let response = await client.query(getDashboard(params.uri));
    let fetchedTerms = [];
    if (!response.errors && response.data.getDashboard !== null) {
      setDashboard(response.data.getDashboard);
      if (
        response.data.getDashboard.terms &&
        response.data.getDashboard.terms.nodes.length > 0
      ) {
        fetchedTerms = response.data.getDashboard.terms.nodes.map((node) => ({
          label: node.label,
          value: node.nodeUri,
          nodeUri: node.nodeUri,
          disabled: node.__typename !== 'Term' /*eslint-disable-line*/,
          nodePath: node.path,
          nodeType: node.__typename /*eslint-disable-line*/
        }));
      }
      setDashboardTerms(fetchedTerms);
      response = client.query(searchGlossary(Defaults.selectListFilter));
      response.then((result) => {
        if (
          result.data.searchGlossary &&
          result.data.searchGlossary.nodes.length > 0
        ) {
          const selectables = result.data.searchGlossary.nodes.map((node) => ({
            label: node.label,
            value: node.nodeUri,
            nodeUri: node.nodeUri,
            disabled: node.__typename !== 'Term' /* eslint-disable-line*/,
            nodePath: node.path,
            nodeType: node.__typename /* eslint-disable-line*/
          }));
          setSelectableTerms(selectables);
        }
      });
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Dashboard not found';
      dispatch({ type: SET_ERROR, error });
    }
    setLoading(false);
  }, [client, dispatch, params.uri]);

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = await client.mutate(
        updateDashboard({
          dashboardUri: dashboard.dashboardUri,
          label: values.label,
          description: values.description,
          terms: values.terms.nodes
            ? values.terms.nodes.map((t) => t.nodeUri)
            : values.terms.map((t) => t.nodeUri),
          tags: values.tags
        })
      );
      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        enqueueSnackbar('Dashboard updated', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        navigate(`/console/dashboards/${dashboard.dashboardUri}`);
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (err) {
      setStatus({ success: false });
      setErrors({ submit: err.message });
      setSubmitting(false);
      dispatch({ type: SET_ERROR, error: err.message });
    }
  }

  useEffect(() => {
    if (client) {
      fetchItem().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client, dispatch, fetchItem]);

  if (loading) {
    return <CircularProgress />;
  }
  if (!dashboard) {
    return null;
  }

  return (
    <>
      <Helmet>
        <title>Dashboard: Dashboard Update | data.all</title>
      </Helmet>
      <Box
        sx={{
          backgroundColor: 'background.default',
          minHeight: '100%',
          py: 8
        }}
      >
        <Container maxWidth={settings.compact ? 'xl' : false}>
          <DashboardEditHeader dashboard={dashboard} />
          <Box sx={{ mt: 3 }}>
            <Formik
              initialValues={{
                label: dashboard.label,
                prefix: dashboard.S3Prefix,
                description: dashboard.description || '',
                tags: dashboard.tags || [],
                terms: dashboard.terms || []
              }}
              validationSchema={Yup.object().shape({
                label: Yup.string()
                  .max(255)
                  .required('*Dashboard name is required'),
                description: Yup.string().max(5000),
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
                <form onSubmit={handleSubmit}>
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
                              onBlur={handleBlur}
                              onChange={handleChange}
                              label="Dashboard name"
                              name="label"
                              value={values.label}
                              variant="outlined"
                            />
                          </Box>
                          <Box sx={{ mb: 2 }}>
                            <TextField
                              disabled
                              fullWidth
                              onBlur={handleBlur}
                              onChange={handleChange}
                              label="Dashboard ID"
                              name="DashboardId"
                              value={dashboard.DashboardId}
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
                          <Box sx={{ mt: 3 }}>
                            <ChipInput
                              fullWidth
                              variant="outlined"
                              defaultValue={dashboard.tags}
                              label="Tags"
                              placeholder="Hit enter after typing value"
                              onChange={(chip) => {
                                setFieldValue('tags', [...chip]);
                              }}
                            />
                          </Box>
                          <Box sx={{ mt: 3 }}>
                            {dashboard && (
                              <Autocomplete
                                multiple
                                id="tags-filled"
                                options={selectableTerms}
                                defaultValue={dashboardTerms.map((node) => ({
                                  label: node.label,
                                  nodeUri: node.nodeUri
                                }))}
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
                                    variant="outlined"
                                    label="Glossary Terms"
                                  />
                                )}
                              />
                            )}
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
                          disabled={isSubmitting}
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

export default DashboardEditForm;
