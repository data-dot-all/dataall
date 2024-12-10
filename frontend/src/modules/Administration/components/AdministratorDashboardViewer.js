import { AddOutlined } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Container,
  Divider,
  Grid,
  TextField,
  Typography
} from '@mui/material';
import { Formik } from 'formik';
import { createRef, useCallback, useEffect, useState } from 'react';
import * as ReactIf from 'react-if';
import * as Yup from 'yup';
import { useSettings } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import {
  createQuicksightDataSourceSet,
  getMonitoringDashboardId,
  getMonitoringVPCConnectionId,
  getPlatformReaderSession,
  updateSSMParameter
} from '../services';

const QuickSightEmbedding = require('amazon-quicksight-embedding-sdk');

export const DashboardViewer = () => {
  const dispatch = useDispatch();
  const client = useClient();
  const { settings } = useSettings();
  const [dashboardId, setDashboardId] = useState('');
  const [vpcConnectionId, setVpcConnectionId] = useState('');
  const [dashboardRef] = useState(createRef());
  const [sessionUrl, setSessionUrl] = useState(null);
  const [isCreatingDataSource, setIsCreatingDataSource] = useState(false);

  const fetchMonitoringVPCConnectionId = useCallback(async () => {
    const response = await client.query(getMonitoringVPCConnectionId());
    if (!response.errors) {
      setVpcConnectionId(response.data.getMonitoringVPCConnectionId);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  }, [client, dispatch]);

  const fetchMonitoringDashboardId = useCallback(async () => {
    const response = await client.query(getMonitoringDashboardId());
    if (!response.errors) {
      setDashboardId(response.data.getMonitoringDashboardId);
      if (response.data.getMonitoringDashboardId !== 'updateme') {
        const resp = await client.query(
          getPlatformReaderSession(response.data.getMonitoringDashboardId)
        );
        if (!resp.errors) {
          setSessionUrl(resp.data.getPlatformReaderSession);
          const options = {
            url: resp.data.getPlatformReaderSession,
            scrolling: 'no',
            height: '700px',
            width: '100%',
            locale: 'en-US',
            footerPaddingEnabled: true,
            sheetTabsDisabled: false,
            printEnabled: false,
            maximize: true,
            container: dashboardRef.current
          };
          QuickSightEmbedding.embedDashboard(options);
        } else {
          dispatch({ type: SET_ERROR, error: resp.errors[0].message });
        }
      }
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  }, [client, dispatch, dashboardRef]);

  useEffect(() => {
    if (client) {
      fetchMonitoringDashboardId().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
      fetchMonitoringVPCConnectionId().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [
    client,
    dispatch,
    fetchMonitoringDashboardId,
    fetchMonitoringVPCConnectionId
  ]);

  async function submitVpc(values, setStatus, setSubmitting, setErrors) {
    try {
      setVpcConnectionId(values.vpc);
      const response = await client.mutate(
        updateSSMParameter({ name: 'VPCConnectionId', value: values.vpc })
      );
      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
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

  async function submitDash(values, setStatus, setSubmitting, setErrors) {
    try {
      setDashboardId(values.dash);
      const response = await client.mutate(
        updateSSMParameter({ name: 'DashboardId', value: values.dash })
      );
      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        const resp = await client.query(getPlatformReaderSession(values.dash));
        if (!resp.errors) {
          setSessionUrl(resp.data.getPlatformReaderSession);
          const options = {
            url: resp.data.getPlatformReaderSession,
            scrolling: 'no',
            height: '700px',
            width: '100%',
            locale: 'en-US',
            footerPaddingEnabled: true,
            sheetTabsDisabled: false,
            printEnabled: false,
            maximize: true,
            container: dashboardRef.current
          };
          QuickSightEmbedding.embedDashboard(options);
        } else {
          dispatch({ type: SET_ERROR, error: resp.errors[0].message });
        }
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

  async function createQuicksightdata() {
    setIsCreatingDataSource(true);
    const response = await client.mutate(
      createQuicksightDataSourceSet({ vpcConnectionId })
    );
    if (response.errors) {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setIsCreatingDataSource(false);
  }

  return (
    <Container maxWidth={settings.compact ? 'xl' : false}>
      <Grid container justifyContent="space-between" spacing={3}>
        <Grid item lg={12} md={12} sm={12} xs={12}>
          <Card sx={{ mt: 3 }}>
            <CardHeader title="Prerequisites" />
            <Divider />
            <CardContent>
              <Box>
                <Typography color="textSecondary" variant="subtitle2">
                  1. Enable Quicksight Enterprise Edition in the infrastructure
                  data.all central account. Check the user guide for more
                  details.
                </Typography>
              </Box>
              <Box>
                <Typography color="textSecondary" variant="subtitle2">
                  2. Create a VPC Connection between Quicksight and RDS VPC.
                  Check the user guide for more details.
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item lg={6} md={6} sm={12} xs={12}>
          <Card sx={{ mt: 3 }}>
            <CardHeader title="Create the RDS data source in Quicksight" />
            <Divider />
            <CardContent>
              <Box mb={1}>
                <Box mb={1}>
                  <Typography color="textSecondary" variant="subtitle2">
                    3. Introduce or Update the VPC Connection ID value in the
                    following box:
                  </Typography>
                </Box>
                <Grid container justifyContent="space-between" spacing={6}>
                  <Grid item lg={12} xl={12} xs={12}>
                    <Formik
                      initialValues={{
                        vpc: vpcConnectionId
                      }}
                      validationSchema={Yup.object().shape({
                        vpc: Yup.string()
                          .max(255)
                          .required('*Value is required')
                      })}
                      onSubmit={async (
                        values,
                        { setErrors, setStatus, setSubmitting }
                      ) => {
                        await submitVpc(
                          values,
                          setStatus,
                          setSubmitting,
                          setErrors
                        );
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
                          <Grid
                            container
                            justifyContent="space-between"
                            spacing={3}
                          >
                            <Grid item lg={8} md={8} xs={8}>
                              <TextField
                                error={Boolean(touched.vpc && errors.vpc)}
                                fullWidth
                                helperText={touched.vpc && errors.vpc}
                                defaultValue={vpcConnectionId}
                                name="vpc"
                                onBlur={handleBlur}
                                onChange={handleChange}
                                value={
                                  values.vpc ? values.vpc : vpcConnectionId
                                }
                                variant="outlined"
                              />
                            </Grid>
                            <Grid item lg={4} md={4} xs={4}>
                              <LoadingButton
                                color="primary"
                                loading={isSubmitting}
                                type="submit"
                                variant="contained"
                              >
                                Save
                              </LoadingButton>
                            </Grid>
                          </Grid>
                        </form>
                      )}
                    </Formik>
                  </Grid>
                </Grid>
              </Box>
              <Box>
                <Box>
                  <Typography color="textSecondary" variant="subtitle2">
                    4. Click on the button to automatically create the data
                    source connecting our RDS Aurora database with Quicksight
                  </Typography>
                </Box>
                <Grid container justifyContent="space-between" spacing={3}>
                  <Grid item lg={6} xl={6} xs={6}>
                    <LoadingButton
                      loading={isCreatingDataSource}
                      color="primary"
                      endIcon={<AddOutlined fontSize="small" />}
                      sx={{ mt: 1, mb: 2, ml: 2 }}
                      variant="outlined"
                      onClick={() => {
                        createQuicksightdata().catch((e) =>
                          dispatch({ type: SET_ERROR, error: e.message })
                        );
                      }}
                    >
                      Create Quicksight data source
                    </LoadingButton>
                  </Grid>
                </Grid>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item lg={6} md={6} sm={12} xs={12}>
          <Card sx={{ mt: 3 }}>
            <CardHeader title="Get insights in Quicksight" />
            <Divider />
            <CardContent>
              <Box>
                <Box>
                  <Typography color="textSecondary" variant="subtitle2">
                    5. Go to Quicksight to build your Analysis and publish a
                    Dashboard. Check the user guide for more details.
                  </Typography>
                </Box>
              </Box>
              <Box>
                <Box mb={1}>
                  <Typography color="textSecondary" variant="subtitle2">
                    6. Introduce or update your Dashboard ID
                  </Typography>
                </Box>
                <Grid container justifyContent="space-between" spacing={6}>
                  <Grid item lg={12} xl={12} xs={12}>
                    <Formik
                      initialValues={{
                        dash: dashboardId
                      }}
                      validationSchema={Yup.object().shape({
                        dash: Yup.string()
                          .max(255)
                          .required('*Value is required')
                      })}
                      onSubmit={async (
                        values,
                        { setErrors, setStatus, setSubmitting }
                      ) => {
                        await submitDash(
                          values,
                          setStatus,
                          setSubmitting,
                          setErrors
                        );
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
                          <Grid
                            container
                            justifyContent="space-between"
                            spacing={3}
                          >
                            <Grid item lg={8} md={8} xs={8}>
                              <TextField
                                error={Boolean(touched.dash && errors.dash)}
                                fullWidth
                                helperText={touched.dash && errors.dash}
                                defaultValue={dashboardId}
                                name="dash"
                                onBlur={handleBlur}
                                onChange={handleChange}
                                value={values.dash ? values.dash : dashboardId}
                                variant="outlined"
                              />
                            </Grid>
                            <Grid item lg={4} md={4} xs={4}>
                              <LoadingButton
                                color="primary"
                                loading={isSubmitting}
                                type="submit"
                                variant="contained"
                              >
                                Save
                              </LoadingButton>
                            </Grid>
                          </Grid>
                        </form>
                      )}
                    </Formik>
                  </Grid>
                </Grid>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item lg={12} md={12} sm={12} xs={12}>
          <ReactIf.If condition={sessionUrl}>
            <ReactIf.Then>
              <div ref={dashboardRef} />
            </ReactIf.Then>
          </ReactIf.If>
        </Grid>
      </Grid>
    </Container>
  );
};
