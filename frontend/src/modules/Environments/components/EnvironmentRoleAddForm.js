import { GroupAddOutlined } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import {
  Box,
  CardContent,
  CircularProgress,
  Dialog,
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
import { useClient } from 'services';
import { addConsumptionRoleToEnvironment } from '../services';
import { useFetchGroups } from '../../../utils/api';

export const EnvironmentRoleAddForm = (props) => {
  const { environment, onClose, open, reloadRoles, ...other } = props;
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const client = useClient();

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = await client.mutate(
        addConsumptionRoleToEnvironment({
          groupUri: values.groupUri,
          consumptionRoleName: values.consumptionRoleName,
          IAMRoleArn: values.IAMRoleArn,
          environmentUri: environment.environmentUri
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
              groupUri: ''
            }}
            validationSchema={Yup.object().shape({
              groupUri: Yup.string()
                .max(255)
                .required('*Owners Team is required'),
              consumptionRoleName: Yup.string()
                .max(255)
                .required('*Consumption Role Name is required'),
              IAMRoleArn: Yup.string().required('*IAM Role Arn is required')
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
                  <TextField
                    fullWidth
                    error={Boolean(touched.groupUri && errors.groupUri)}
                    helperText={touched.groupUri && errors.groupUri}
                    label="Owners"
                    name="groupUri"
                    onChange={handleChange}
                    select
                    value={values.groupUri}
                    variant="outlined"
                  >
                    {groupOptions.map((group) => (
                      <MenuItem key={group.value} value={group.value}>
                        {group.label}
                      </MenuItem>
                    ))}
                  </TextField>
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
