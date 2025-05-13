import { GroupAddOutlined } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import {
  Alert,
  Autocomplete,
  Box,
  CardContent,
  CircularProgress,
  Dialog,
  TextField,
  Typography
} from '@mui/material';
import { Formik } from 'formik';
import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
import * as Yup from 'yup';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient, useFetchGroups } from 'services';
import { addConsumptionPrincipalToEnvironment } from '../services';
import { policyManagementInfoMap } from '../../constants';
import { InfoIconWithToolTip } from '../../../design';

export const EnvironmentPrincipalAddForm = (props) => {
  const {
    environment,
    onClose,
    open,
    reloadPrincipals,
    policyManagementOptions,
    ...other
  } = props;
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const client = useClient();

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = await client.mutate(
        addConsumptionPrincipalToEnvironment({
          groupUri: values.groupUri,
          consumptionPrincipalName: values.consumptionPrincipalName,
          IAMPrincipalArn: values.IAMPrincipalArn,
          environmentUri: environment.environmentUri,
          dataallManaged: values.dataallManaged
        })
      );
      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        enqueueSnackbar('IAM principal added to the environment', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        if (reloadPrincipals) {
          reloadPrincipals();
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

  let { groupOptions, loadingGroups } = useFetchGroups(environment);

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
          Add Consumption IAM Principal to environment {environment.label}
        </Typography>
        <Typography align="center" color="textSecondary" variant="subtitle2">
          An IAM Consumption Principal - an IAM Role/User - is owned by the selected Team. The owners team
          request access on behalf of this IAM Principal, which can be used by
          downstream applications.
        </Typography>
        <Box sx={{ p: 3 }}>
          <Formik
            initialValues={{
              groupUri: '',
              dataallManaged: ''
            }}
            validationSchema={Yup.object().shape({
              groupUri: Yup.string()
                .max(255)
                .required('*Owners Team is required'),
              consumptionPrincipalName: Yup.string()
                .max(255)
                .required('*Consumption Principal Name is required'),
              IAMPrincipalArn: Yup.string().required(
                '*IAM Principal Arn is required'
              ),
              dataallManaged: Yup.string()
                .required(
                  'Policy Management option required. Please select a valid option'
                )
                .oneOf(policyManagementOptions.map((obj) => obj.key))
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
                <CardContent>
                  <TextField
                    error={Boolean(
                      touched.consumptionPrincipalName &&
                        errors.consumptionPrincipalName
                    )}
                    fullWidth
                    helperText={
                      touched.consumptionPrincipalName &&
                      errors.consumptionPrincipalName
                    }
                    label="Consumption Principal Name"
                    placeholder="Name to identify your IAM Principal in data.all"
                    name="consumptionPrincipalName"
                    onChange={handleChange}
                    value={values.consumptionPrincipalName}
                    variant="outlined"
                  />
                </CardContent>
                <CardContent>
                  <TextField
                    error={Boolean(
                      touched.IAMPrincipalArn && errors.IAMPrincipalArn
                    )}
                    fullWidth
                    helperText={
                      touched.IAMPrincipalArn && errors.IAMPrincipalArn
                    }
                    label="IAM Principal ARN"
                    placeholder="IAM Principal ARN"
                    name="IAMPrincipalArn"
                    onChange={handleChange}
                    value={values.IAMPrincipalArn}
                    variant="outlined"
                  />
                </CardContent>
                <CardContent>
                  <Autocomplete
                    id="SamlAdminGroupName"
                    disablePortal
                    options={groupOptions.map((option) => option)}
                    onChange={(event, value) => {
                      if (value && value.value) {
                        setFieldValue('groupUri', value.value);
                      } else {
                        setFieldValue('groupUri', '');
                      }
                    }}
                    noOptionsText="No teams found for this environment"
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        fullWidth
                        error={Boolean(touched.groupUri && errors.groupUri)}
                        helperText={touched.groupUri && errors.groupUri}
                        label="Owners"
                        name="groupUri"
                        variant="outlined"
                        value={values.groupUri}
                      />
                    )}
                  />
                </CardContent>
                <CardContent>
                  <Autocomplete
                    id="PolicyManagement"
                    disablePortal
                    options={policyManagementOptions}
                    onChange={(event, value) => {
                      if (value && value.key) {
                        setFieldValue('dataallManaged', value.key);
                      } else {
                        setFieldValue('dataallManaged', '');
                      }
                    }}
                    renderOption={(props, option) => {
                      const { key, ...propOptions } = props;
                      return (
                        <Box key={key} {...propOptions}>
                          {option.label}
                          <InfoIconWithToolTip
                            title={
                              <span style={{ fontSize: 'small' }}>
                                {policyManagementInfoMap[option.key] != null
                                  ? policyManagementInfoMap[option.key]
                                  : 'Invalid Option for policy management.'}
                              </span>
                            }
                            placement={'right-start'}
                            size={1}
                          />
                        </Box>
                      );
                    }}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        fullWidth
                        error={Boolean(
                          touched.dataallManaged && errors.dataallManaged
                        )}
                        helperText={
                          touched.dataallManaged && errors.dataallManaged
                        }
                        label="Policy Management"
                        name="dataallManaged"
                        variant="outlined"
                        value={values.dataallManaged}
                      />
                    )}
                  />
                </CardContent>
                {values.dataallManaged === 'EXTERNALLY_MANAGED' ? (
                  <CardContent>
                    <Alert severity="error" sx={{ mr: 1 }}>
                      With "Externally-Managed" policy management, you are
                      completely responsible for attaching / giving your
                      consumption principal (IAM Role/User) appropriate permissions. Please select
                      "Externally-Managed" if you know that your consumption principal has some
                      super-user permissions or if you are completely managing
                      the principal and its policies.
                    </Alert>
                  </CardContent>
                ) : (
                  <div></div>
                )}
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
                      Add Consumption Principal
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

EnvironmentPrincipalAddForm.propTypes = {
  environment: PropTypes.object.isRequired,
  onClose: PropTypes.func,
  open: PropTypes.bool.isRequired,
  reloadPrincipals: PropTypes.func
};
