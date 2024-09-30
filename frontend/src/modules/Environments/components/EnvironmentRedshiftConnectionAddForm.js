import { GroupAddOutlined } from '@mui/icons-material';
import InfoIcon from '@mui/icons-material/Info';
import { LoadingButton } from '@mui/lab';
import { styled } from '@mui/material/styles';
import {
  Autocomplete,
  Box,
  CardContent,
  CircularProgress,
  Dialog,
  Divider,
  Grid,
  MenuItem,
  TextField,
  Tooltip,
  TooltipProps,
  tooltipClasses,
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

  const CustomWidthTooltip = styled(({ className, ...props }: TooltipProps) => (
    <Tooltip {...props} classes={{ popper: className }} />
  ))({
    [`& .${tooltipClasses.tooltip}`]: {
      maxWidth: 500
    }
  });

  let { groupOptions, loadingGroups } = useFetchGroups(environment);

  const connectionOptions = [
    {
      value: 'DATA_USER',
      label: 'Data User',
      info: 'Data users connections are required to import Redshift Datasets. The Redshift user for the connection should have Redshift READ permissions to the tables that will be imported in data.all'
    },
    {
      value: 'ADMIN',
      label: 'Admin',
      info: 'Admin connections are used by data.all backend to manage data sharing requests. To create a share request between 2 namespaces, an ADMIN connection in the source and in the target namespaces are required. The Redshift user for the connection should have enough permissions to MANAGE DATASHARES in the namespace.'
    }
  ];

  const clusterOptions = [
    { value: 'serverless', label: 'Serverless' },
    { value: 'cluster', label: 'Provisioned Cluster' }
  ];

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = await client.mutate(
        createRedshiftConnection({
          connectionName: values.connectionName,
          SamlGroupName: values.SamlAdminGroupName,
          environmentUri: environment.environmentUri,
          redshiftType: values.redshiftType,
          clusterId: values.clusterId,
          nameSpaceId: values.nameSpaceId,
          workgroup: values.workgroup,
          database: values.database,
          redshiftUser: values.redshiftUser,
          secretArn: values.secretArn,
          connectionType: values.connectionType
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
          The Redshift connection contains the metadata to connect to Redshift
          with a particular user.
        </Typography>
      </Box>
      <Box sx={{ p: 3 }}>
        <Formik
          initialValues={{
            connectionName: '',
            SamlAdminGroupName: '',
            redshiftType: '',
            clusterId: '',
            nameSpaceId: '',
            workgroup: '',
            database: '',
            redshiftUser: '',
            secretArn: '',
            connectionType: ''
          }}
          validationSchema={Yup.object().shape({
            connectionName: Yup.string()
              .max(255)
              .required('*Connection Name is required'),
            SamlAdminGroupName: Yup.string()
              .max(255)
              .required('*Owners Team is required'),
            redshiftType: Yup.string()
              .max(255)
              .required('*Redshift type is required'),
            clusterId: Yup.string().max(255),
            nameSpaceId: Yup.string().max(255),
            workgroup: Yup.string().max(255),
            database: Yup.string().max(255).required('*Database is required'),
            redshiftUser: Yup.string().max(255),
            secretArn: Yup.string().max(255),
            connectionType: Yup.string()
              .max(255)
              .required('*ConnectionType is required')
          })}
          onSubmit={async (values, { setErrors, setStatus, setSubmitting }) => {
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
                    helperText={touched.connectionName && errors.connectionName}
                    label="connection Name"
                    placeholder="Name to identify your Connection in data.all"
                    name="connectionName"
                    onChange={handleChange}
                    value={values.connectionName}
                    variant="outlined"
                  />
                </CardContent>
                <CardContent>
                  <Autocomplete
                    id="SamlAdminGroupName"
                    disablePortal
                    options={groupOptions.map((option) => option)}
                    noOptionsText="No teams found for this environment"
                    onChange={(event, value) => {
                      if (value && value.value) {
                        setFieldValue('SamlAdminGroupName', value.value);
                      } else {
                        setFieldValue('SamlAdminGroupName', '');
                      }
                    }}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        fullWidth
                        error={Boolean(
                          touched.SamlAdminGroupName &&
                            errors.SamlAdminGroupName
                        )}
                        helperText={
                          touched.SamlAdminGroupName &&
                          errors.SamlAdminGroupName
                        }
                        label="Team"
                        name="SamlAdminGroupName"
                        variant="outlined"
                        value={values.SamlAdminGroupName}
                      />
                    )}
                  />
                </CardContent>
              </Box>
              <Grid container spacing={3}>
                <Grid item lg={6} md={6} xs={12}>
                  <CardContent>
                    <TextField
                      fullWidth
                      error={Boolean(
                        touched.connectionType && errors.connectionType
                      )}
                      helperText={
                        touched.connectionType && errors.connectionType
                      }
                      label="Connection type"
                      name="connectionType"
                      onChange={handleChange}
                      select
                      value={values.connectionType}
                      variant="outlined"
                    >
                      {connectionOptions.map((r) => (
                        <MenuItem key={r.value} value={r.value}>
                          <CustomWidthTooltip
                            title={r.info}
                            placement="right-end"
                          >
                            <Box display="flex" alignItems="center">
                              <div>{r.label}</div>
                              <InfoIcon
                                fontSize="small"
                                style={{ marginLeft: '8px' }}
                              />
                            </Box>
                          </CustomWidthTooltip>
                        </MenuItem>
                      ))}
                    </TextField>
                  </CardContent>
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
                          helperText={touched.nameSpaceId && errors.nameSpaceId}
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
                          error={Boolean(touched.workgroup && errors.workgroup)}
                          fullWidth
                          helperText={touched.workgroup && errors.workgroup}
                          label="Workgroup"
                          placeholder="Redshift Serverless Workgroup"
                          name="workgroup"
                          onChange={handleChange}
                          value={values.workgroup}
                          variant="outlined"
                        />
                      </CardContent>
                    </Box>
                  )}
                  {values.redshiftType === 'cluster' && (
                    <Box>
                      <CardContent>
                        <TextField
                          error={Boolean(touched.clusterId && errors.clusterId)}
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
                <TextField
                  error={Boolean(touched.database && errors.database)}
                  fullWidth
                  helperText={touched.database && errors.database}
                  label="database"
                  placeholder="Redshift database you will be connecting to"
                  name="database"
                  onChange={handleChange}
                  value={values.database}
                  variant="outlined"
                />
              </CardContent>
              <CardContent>
                <Typography color="textPrimary" variant="body2">
                  You can choose to provide a Redshift user (for Provisioned
                  Cluster) or a Secrets Manager secret.
                </Typography>
              </CardContent>
              {values.redshiftType !== 'serverless' && (
                <Box>
                  <CardContent>
                    <TextField
                      error={Boolean(
                        touched.redshiftUser && errors.redshiftUser
                      )}
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
                </Box>
              )}
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
    </Dialog>
  );
};

EnvironmentRedshiftConnectionAddForm.propTypes = {
  environment: PropTypes.object.isRequired,
  onClose: PropTypes.func,
  open: PropTypes.bool.isRequired,
  reload: PropTypes.func
};
