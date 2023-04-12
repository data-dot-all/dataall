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
import { ChipInput } from '../../components';
import { SET_ERROR, useDispatch } from '../../globalErrors';
import { useGroups, useSettings } from '../../hooks';
import { ChevronRightIcon } from '../../icons';
import { ArrowLeftIcon } from '../../icons/';
import { getRedshiftCluster, useClient } from '../../services';

const WarehouseEditForm = (props) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const params = useParams();
  const { enqueueSnackbar } = useSnackbar();
  const client = useClient();
  const groups = useGroups();
  const { settings } = useSettings();
  const [loading, setLoading] = useState(true);
  const [warehouse, setWarehouse] = useState(null);
  const groupOptions = groups
    ? groups.map((g) => ({ value: g, label: g }))
    : [];

  const fetchItem = useCallback(async () => {
    setLoading(true);
    const response = await client.query(getRedshiftCluster(params.uri));
    if (!response.errors && response.data.get !== null) {
      setWarehouse(response.data.getRedshiftCluster);
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Warehouse not found';
      dispatch({ type: SET_ERROR, error });
    }
    setLoading(false);
  }, [client, dispatch, params.uri]);

  useEffect(() => {
    if (client) {
      fetchItem().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client, fetchItem, dispatch]);

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = {};
      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        enqueueSnackbar('Warehouse updated', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        navigate(
          `/console/warehouse/${response.data.updateSqlWarehouse.clusterUri}`
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

  if (loading || !(warehouse && warehouse.environment)) {
    return <CircularProgress />;
  }

  return (
    <>
      <Helmet>
        <title>Dataset: Warehouse Update | data.all</title>
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
                Edit warehouse {warehouse.label}
              </Typography>
              <Breadcrumbs
                aria-label="breadcrumb"
                separator={<ChevronRightIcon fontSize="small" />}
                sx={{ mt: 1 }}
              >
                <Link underline="hover" color="textPrimary" variant="subtitle2">
                  Discover
                </Link>
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to="/console/datasets"
                  variant="subtitle2"
                >
                  Warehouses
                </Link>
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to={`/console/warehouse/${warehouse.clusterUri}`}
                  variant="subtitle2"
                >
                  {warehouse.label}
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
                  to={`/console/warehouse/${warehouse.clusterUri}`}
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
                label: warehouse.label,
                description: warehouse.description,
                SamlGroupName: warehouse.SamlAdminGroupName,
                tags: warehouse.tags
              }}
              validationSchema={Yup.object().shape({
                label: Yup.string()
                  .max(255)
                  .required('*Cluster name is required'),
                description: Yup.string().max(5000),
                SamlGroupName: Yup.string()
                  .max(255)
                  .required('*Team is required'),
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
                            label="Cluster name"
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
                              setFieldValue(
                                'SamlGroupName',
                                event.target.value
                              );
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
                          <Box>
                            <ChipInput
                              fullWidth
                              defaultValue={warehouse.tags}
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
                            value={warehouse.environment.label}
                            variant="outlined"
                          />
                        </CardContent>
                        <CardContent>
                          <TextField
                            disabled
                            fullWidth
                            label="Region"
                            name="region"
                            value={warehouse.environment.region}
                            variant="outlined"
                          />
                        </CardContent>
                        <CardContent>
                          <TextField
                            disabled
                            fullWidth
                            label="Organization"
                            name="organization"
                            value={warehouse.organization.label}
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

export default WarehouseEditForm;
