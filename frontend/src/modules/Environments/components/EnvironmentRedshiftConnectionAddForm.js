import { GroupAddOutlined } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import {
  Box,
  CardContent,
  CircularProgress,
  Dialog,
  Divider,
  Grid,
  MenuItem,
  TextField,
  Typography
} from '@mui/material';
import { Formik } from 'formik';
import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
import React from 'react';
import * as Yup from 'yup';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient, useFetchGroups } from 'services';
import { createRedshiftConnection } from '../services';

export const EnvironmentRedshiftConnectionAddForm = (props) => {
  const { environment, onClose, open, reload, ...other } = props;
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const client = useClient();

  let { groupOptions, loadingGroups } = useFetchGroups(environment);

  const clusterOptions = [
    { value: 'serverless', label: 'Serverless' },
    { value: 'cluster', label: 'Provisioned Cluster' }
  ];

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = await client.mutate(
        createRedshiftConnection({
          connectionName: values.connectionName,
          SamlGroupName: values.SamlGroupName,
          environmentUri: environment.environmentUri,
          redshiftType: values.redshiftType,
          clusterId: values.clusterId,
          nameSpaceId: values.nameSpaceId,
          workgroupId: values.workgroupId,
          redshiftUser: values.redshiftUser,
          secretArn: values.secretArn
        })
      );
      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        enqueueSnackbar('Redshift connection added to environment', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        if (reload) {
          reload();
        }
        if (onClose) {
          onClose();
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

  if (!environment) {
    return null;
  }

  if (loadingGroups) {
    return <CircularProgress size={10} />;
  }

  return (
    <Dialog maxWidth="lg" fullWidth onClose={onClose} open={open} {...other}>
      <Box sx={{ p: 3 }}>
        <Typography
          align="center"
          color="textPrimary"
          gutterBottom
          variant="h4"
        >
          Add a Redshift connection to environment {environment.label}
        </Typography>
        <Typography align="center" color="textSecondary" variant="subtitle2">
          The Redshift connection is owned by the selected Team. It is used to
          import Redshift Datasets.
        </Typography>
        <Box sx={{ p: 3 }}>
          <Formik
            initialValues={{
              connectionName: '',
              SamlGroupName: '',
              redshiftType: '',
              clusterId: '',
              nameSpaceId: '',
              workgroupId: '',
              redshiftUser: '',
              secretArn: ''
            }}
            validationSchema={Yup.object().shape({
              SamlGroupName: Yup.string()
                .max(255)
                .required('*Owners Team is required'),
              connectionName: Yup.string()
                .max(255)
                .required('*Connection Name is required') // TODO: add other required rules
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
              handleChange,
              handleSubmit,
              isSubmitting,
              setFieldValue,
              touched,
              values
            }) => (
              <form onSubmit={handleSubmit}>
                <Box>
                  <CardContent>
                    <TextField
                      error={Boolean(
                        touched.connectionName && errors.connectionName
                      )}
                      fullWidth
                      helperText={
                        touched.connectionName && errors.connectionName
                      }
                      label="connection Name"
                      placeholder="Name to identify your Connection in data.all"
                      name="connectionName"
                      onChange={handleChange}
                      value={values.connectionName}
                      variant="outlined"
                    />
                  </CardContent>
                  <CardContent>
                    <TextField
                      fullWidth
                      error={Boolean(
                        touched.SamlGroupName && errors.SamlGroupName
                      )}
                      helperText={touched.SamlGroupName && errors.SamlGroupName}
                      label="Team"
                      name="SamlGroupName"
                      onChange={handleChange}
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
                </Box>
                <Grid container spacing={3}>
                  <Grid item lg={6} md={6} xs={12}>
                    <CardContent>
                      <TextField
                        fullWidth
                        error={Boolean(
                          touched.redshiftType && errors.redshiftType
                        )}
                        helperText={touched.redshiftType && errors.redshiftType}
                        label="Redshift type"
                        name="redshiftType"
                        onChange={handleChange}
                        select
                        value={values.redshiftType}
                        variant="outlined"
                      >
                        {clusterOptions.map((r) => (
                          <MenuItem key={r.value} value={r.value}>
                            {r.label}
                          </MenuItem>
                        ))}
                      </TextField>
                    </CardContent>
                  </Grid>
                  <Grid item lg={6} md={6} xs={12}>
                    {values.redshiftType === 'serverless' && (
                      <Box>
                        <CardContent>
                          <TextField
                            error={Boolean(
                              touched.nameSpaceId && errors.nameSpaceId
                            )}
                            fullWidth
                            helperText={
                              touched.nameSpaceId && errors.nameSpaceId
                            }
                            label="Namespace Id"
                            placeholder="Redshift Serverless Namespace Id"
                            name="nameSpaceId"
                            onChange={handleChange}
                            value={values.nameSpaceId}
                            variant="outlined"
                          />
                        </CardContent>
                        <CardContent>
                          <TextField
                            error={Boolean(
                              touched.workgroupId && errors.workgroupId
                            )}
                            fullWidth
                            helperText={
                              touched.workgroupId && errors.workgroupId
                            }
                            label="Workgroup Id"
                            placeholder="Redshift Serverless Workgroup"
                            name="workgroupId"
                            onChange={handleChange}
                            value={values.workgroupId}
                            variant="outlined"
                          />
                        </CardContent>
                      </Box>
                    )}
                    {values.redshiftType === 'cluster' && (
                      <Box>
                        <CardContent>
                          <TextField
                            error={Boolean(
                              touched.clusterId && errors.clusterId
                            )}
                            fullWidth
                            helperText={touched.clusterId && errors.clusterId}
                            label="Cluster Id"
                            placeholder="Redshift Provisioned Cluster Id"
                            name="clusterId"
                            onChange={handleChange}
                            value={values.clusterId}
                            variant="outlined"
                          />
                        </CardContent>
                      </Box>
                    )}
                  </Grid>
                </Grid>
                <CardContent>
                  <Typography color="textPrimary" variant="body2">
                    You can choose to provide a Redshift user or a Secret.
                  </Typography>
                </CardContent>
                <CardContent>
                  <TextField
                    error={Boolean(touched.redshiftUser && errors.redshiftUser)}
                    fullWidth
                    helperText={touched.redshiftUser && errors.redshiftUser}
                    label="Redshift User"
                    placeholder="Redshift User"
                    name="redshiftUser"
                    onChange={handleChange}
                    value={values.redshiftUser}
                    variant="outlined"
                  />
                </CardContent>
                <Divider>OR</Divider>
                <CardContent>
                  <TextField
                    error={Boolean(touched.secretArn && errors.secretArn)}
                    fullWidth
                    helperText={touched.secretArn && errors.secretArn}
                    label="Secrets Manager Secret Arn"
                    placeholder="Secrets Manager Secret Arn with credentials to Redshift"
                    name="secretArn"
                    onChange={handleChange}
                    value={values.secretArn}
                    variant="outlined"
                  />
                </CardContent>
                <Box>
                  <CardContent>
                    <LoadingButton
                      fullWidth
                      startIcon={<GroupAddOutlined fontSize="small" />}
                      color="primary"
                      disabled={isSubmitting}
                      type="submit"
                      variant="contained"
                    >
                      Add Connection
                    </LoadingButton>
                  </CardContent>
                </Box>
              </form>
            )}
          </Formik>
        </Box>
      </Box>
    </Dialog>
  );
};

EnvironmentRedshiftConnectionAddForm.propTypes = {
  environment: PropTypes.object.isRequired,
  onClose: PropTypes.func,
  open: PropTypes.bool.isRequired,
  reload: PropTypes.func
};
