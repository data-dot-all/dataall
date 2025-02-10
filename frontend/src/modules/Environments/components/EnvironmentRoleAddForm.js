import { GroupAddOutlined } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import {
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
import React, { useEffect, useState } from 'react';
import * as Yup from 'yup';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { fetchEnums, useClient, useFetchGroups } from 'services';
import { addConsumptionRoleToEnvironment } from '../services';
import { policyManagementInfoMap } from '../../constants';
import { InfoIconWithToolTip } from '../../../design';

export const EnvironmentRoleAddForm = (props) => {
  const { environment, onClose, open, reloadRoles, ...other } = props;
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const client = useClient();
  const [policyManagementOptions, setPolicyManagementOptions] = useState([]);

  useEffect(() => {
    const fetchPolicyManagementOptions = async () => {
      const response = await fetchEnums(client, ['PolicyManagementOptions']);
      if (response['PolicyManagementOptions'].length > 0) {
        setPolicyManagementOptions(
          response['PolicyManagementOptions'].map((elem) => {
            return {
              label: elem.value,
              key: elem.name
            };
          })
        );
      } else {
        dispatch({
          type: SET_ERROR,
          error: 'Could not fetch consumption role policy management options'
        });
      }
    };

    if (client)
      fetchPolicyManagementOptions().catch((e) =>
        dispatch({ type: SET_ERROR, e })
      );
  }, [client, dispatch]);

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = await client.mutate(
        addConsumptionRoleToEnvironment({
          groupUri: values.groupUri,
          consumptionRoleName: values.consumptionRoleName,
          IAMRoleArn: values.IAMRoleArn,
          environmentUri: environment.environmentUri,
          dataallManaged: values.dataallManaged
        })
      );
      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        enqueueSnackbar('IAM role added to environment', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        if (reloadRoles) {
          reloadRoles();
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
          Add a consumption IAM role to environment {environment.label}
        </Typography>
        <Typography align="center" color="textSecondary" variant="subtitle2">
          An IAM consumption role is owned by the selected Team. The owners team
          request access on behalf of this IAM role, which can be used by
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
              consumptionRoleName: Yup.string()
                .max(255)
                .required('*Consumption Role Name is required'),
              IAMRoleArn: Yup.string().required('*IAM Role Arn is required'),
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
                      touched.consumptionRoleName && errors.consumptionRoleName
                    )}
                    fullWidth
                    helperText={
                      touched.consumptionRoleName && errors.consumptionRoleName
                    }
                    label="Consumption Role Name"
                    placeholder="Name to identify your IAM role in data.all"
                    name="consumptionRoleName"
                    onChange={handleChange}
                    value={values.consumptionRoleName}
                    variant="outlined"
                  />
                </CardContent>
                <CardContent>
                  <TextField
                    error={Boolean(touched.IAMRoleArn && errors.IAMRoleArn)}
                    fullWidth
                    helperText={touched.IAMRoleArn && errors.IAMRoleArn}
                    label="IAM Role ARN"
                    placeholder="IAM Role ARN"
                    name="IAMRoleArn"
                    onChange={handleChange}
                    value={values.IAMRoleArn}
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
                      Add Consumption Role
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

EnvironmentRoleAddForm.propTypes = {
  environment: PropTypes.object.isRequired,
  onClose: PropTypes.func,
  open: PropTypes.bool.isRequired,
  reloadRoles: PropTypes.func
};
