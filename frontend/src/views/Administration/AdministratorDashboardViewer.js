import { createRef, useCallback, useEffect, useState } from 'react';
import * as Yup from 'yup';
import { Formik, useFormik } from 'formik';
import * as ReactIf from 'react-if';
import {
  Box,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Divider,
  TextField,
  Typography,
  Button,
  CircularProgress
} from '@mui/material';
import { FaCheckCircle } from 'react-icons/fa';
import { AddOutlined, CopyAllOutlined, ArrowLeft, ArrowRightAlt, ChevronRight } from '@mui/icons-material';
import { CopyToClipboard } from 'react-copy-to-clipboard/lib/Component';
import { LoadingButton } from '@mui/lab';
import getMonitoringDashboardId from '../../api/Tenant/getMonitoringDashboardId';
import getMonitoringVPCConnectionId from '../../api/Tenant/getMonitoringVPCConnectionId';
import updateSSMParameter from "../../api/Tenant/updateSSMParameter";
import getTrustAccount from '../../api/Environment/getTrustAccount';
import createQuicksightDataSourceSet from '../../api/Tenant/createQuicksightDataSourceSet';
import getPlatformAuthorSession from '../../api/Tenant/getPlatformAuthorSession';
import { useDispatch } from '../../store';
import useClient from '../../hooks/useClient';
import { SET_ERROR } from '../../store/errorReducer';
import {AwsRegions} from "../../constants";


const QuickSightEmbedding = require('amazon-quicksight-embedding-sdk');

const DashboardViewer = () => {
  const dispatch = useDispatch();
  const client = useClient();
  const [dashboardId, setDashboardId] = useState('');
  const [vpcConnectionId, setVpcConnectionId] = useState('');
  const [trustedAccount, setTrustedAccount] = useState(null);
  const [ready, setReady] = useState(false);
  const [readerSessionUrl, setReaderSessionUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isOpeningSession, setIsOpeningSession] = useState(false);

  const fetchTrustedAccount = useCallback(async () => {
    const response = await client.query(getTrustAccount());
    if (!response.errors) {
      setTrustedAccount(response.data.getTrustAccount);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  }, [client, dispatch]);

  const fetchMonitoringVPCConnectionId = useCallback( async () => {
    const response = await client.query(getMonitoringVPCConnectionId());
    if (!response.errors) {
      setVpcConnectionId(response.data.getMonitoringVPCConnectionId);
      console.log("fetch")
      console.log(response.data.getMonitoringVPCConnectionId)
      console.log(vpcConnectionId)
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  }, [client, dispatch]);

  const fetchMonitoringDashboardId = useCallback( async () => {
    const response = await client.query(getMonitoringDashboardId());
    if (!response.errors) {
      setDashboardId(response.data.getMonitoringDashboardId);
      console.log("fetch")
      console.log(dashboardId)
      if (response.data.getMonitoringDashboardId != "updateme"){
        setReady(true)
      }
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  }, [client, dispatch]);

  useEffect(() => {
    if (client) {
      fetchMonitoringDashboardId().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
      fetchMonitoringVPCConnectionId().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
      fetchTrustedAccount().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, dispatch,fetchMonitoringDashboardId, fetchMonitoringVPCConnectionId, fetchTrustedAccount]);

  async function submitVpc(values, setStatus, setSubmitting, setErrors){
    try {
      console.log("values")
      console.log(values);
      console.log(values.vpc)
      setVpcConnectionId(values.vpc)
      const response = await client.mutate(updateSSMParameter({name:"VPCConnectionId", value:values.vpc}));
      if (!response.errors) {
        setStatus({success: true});
        setSubmitting(false);
      }else{
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (err) {
      console.error(err);
      setStatus({ success: false });
      setErrors({ submit: err.message });
      setSubmitting(false);
      dispatch({ type: SET_ERROR, error: err.message });
    }
  };

  async function submitDash(values, setStatus, setSubmitting, setErrors){
    try {
      console.log("values")
      console.log(values);
      console.log(values.dash)
      setVpcConnectionId(values.dash)
      const response = await client.mutate(updateSSMParameter({name:"DashboardId", value:values.dash}));
      if (!response.errors) {
        setStatus({success: true});
        setSubmitting(false);
      }else{
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (err) {
      console.error(err);
      setStatus({ success: false });
      setErrors({ submit: err.message });
      setSubmitting(false);
      dispatch({ type: SET_ERROR, error: err.message });
    }
  };

  async function createQuicksightdata () {
    console.log("inside enableQuicksight")
    console.log(dashboardId)
    console.log(vpcConnectionId)
    setLoading(true)
    const response = await client.mutate(createQuicksightDataSourceSet({vpcConnectionId}));
    if (!response.errors) {
      setReady(true);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false)
  }


  const startQSSession = async () => {
    setIsOpeningSession(true);
    const response = await client.query(getPlatformAuthorSession(trustedAccount));
    if (response.errors) {
      window.open(response.data.getPlatformAuthorSession, '_blank');
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setIsOpeningSession(false);
  };

  if (loading) {
    return <CircularProgress />;
  }

  return (
    <Container maxWidth={settings.compact ? 'xl' : false}>
          <Grid container justifyContent="space-between" spacing={3}>
            <Grid item lg={12} md={6} xs={12}>
              <Card sx={{ mt: 3 }}>
                <CardHeader title="Prerequisites" />
                <Divider />
                <CardContent>
                  <Box>
                    <Typography color="textSecondary" variant="subtitle2">
                      1. Enable Quicksight Enterprise Edition in AWS Account = {trustedAccount}. Check the user guide for more details.
                    </Typography>
                  </Box>
                  <Box>
                    <Typography color="textSecondary" variant="subtitle2">
                      2. Create a VPC Connection between Quicksight and RDS VPC. Check the user guide for more details.
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            <Grid item lg={6} md={6} xs={12}>
              <Card sx={{ mt: 3 }}>
                <CardHeader title="Ingest the data into Quicksight" />
                <Divider />
                <CardContent>
                  <Box>
                    <Box mb={1}>
                      <Typography color="textSecondary" variant="subtitle2">
                        3. Introduce or Update the VPC Connection ID value in the following box:
                      </Typography>
                    </Box>
                    <Grid container justifyContent="space-between" spacing={6}>
                      <Grid item lg={4} xl={6} xs={6}>
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
                            await submitVpc(values, setStatus, setSubmitting, setErrors);
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
                             <TextField
                              error={Boolean(touched.vpc && errors.vpc)}
                              fullWidth
                              helperText={touched.vpc && errors.vpc}
                              label="VPC Connection Id"
                              name="vpc"
                              onBlur={handleBlur}
                              onChange={handleChange}
                              value={values.vpc}
                              variant="outlined"
                             />
                             <LoadingButton
                              color="primary"
                              loading={isSubmitting}
                              type="submit"
                              variant="contained"
                            >
                              Save
                            </LoadingButton>
                           </form>
                          )}
                        </Formik>
                      </Grid>
                    </Grid>
                  </Box>
                  <Box>
                    <Box>
                      <Typography color="textSecondary" variant="subtitle2">
                        4. Click on the button to automatically create the data source and data sets in Quicksight
                      </Typography>
                    </Box>
                    <Grid container justifyContent="space-between" spacing={3}>
                      <Grid item lg={6} xl={6} xs={6}>
                        <Button
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
                          Create Quicksight resources
                        </Button>
                      </Grid>
                    </Grid>
                  </Box>
                </CardContent>
              </Card>
              <Card sx={{ mt: 3 }}>
                <CardHeader title="Get insights in Quicksight" />
                <Divider />
                <CardContent>
                  <Box>
                    <Box>
                      <Typography color="textSecondary" variant="subtitle2">
                        5. Go to Quicksight to build your Analysis and publish a Dashboard
                      </Typography>
                    </Box>
                    <Grid container justifyContent="space-between" spacing={3}>
                      <Grid item lg={4} xl={6} xs={6}>
                        <LoadingButton
                          loading={isOpeningSession}
                          color="primary"
                          endIcon={<ArrowRightAlt fontSize="small" />}
                          variant="outlined"
                          onClick={startQSSession}
                          sx={{ mt: 1, mb: 2, ml: 2 }}
                        >
                          Start Quicksight session
                        </LoadingButton>
                      </Grid>
                    </Grid>
                  </Box>
                  <Box>
                    <Box mb={1}>
                      <Typography color="textSecondary" variant="subtitle2">
                        6. Import or update your Dashboard ID
                      </Typography>
                    </Box>
                    <Grid container justifyContent="space-between" spacing={6}>
                      <Grid item lg={6} xl={6} xs={6}>
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
                            await submitDash(values, setStatus, setSubmitting, setErrors);
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
                             <TextField
                              error={Boolean(touched.dash && errors.dash)}
                              fullWidth
                              helperText={touched.dash && errors.dash}
                              label="Dashboard Id"
                              name="dash"
                              onBlur={handleBlur}
                              onChange={handleChange}
                              value={values.dash}
                              variant="outlined"
                             />
                             <LoadingButton
                              color="primary"
                              loading={isSubmitting}
                              type="submit"
                              variant="contained"
                            >
                              Save
                            </LoadingButton>
                           </form>
                          )}
                        </Formik>
                      </Grid>
                    </Grid>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            <Grid item lg={6} md={6} xs={12}>
              <ReactIf.If condition={ready}>
                <ReactIf.Then>
                  <Box sx={{ mb: 3 }}>
                    <Button
                      color="primary"
                      component="a"
                      target="_blank"
                      rel="noreferrer"
                      startIcon={<FaCheckCircle size={15} />}
                      variant="outlined"
                    >
                      View in Quicksight
                    </Button>
                  </Box>
                </ReactIf.Then>
              </ReactIf.If>
            </Grid>
          </Grid>
    </Container>
  );
};

export default DashboardViewer;
