import { LoadingButton } from '@mui/lab';
import {
  Autocomplete,
  Box,
  CardContent,
  CardHeader,
  Dialog,
  FormHelperText,
  Grid,
  TextField,
  Typography
} from '@mui/material';
import { Formik } from 'formik';
import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState } from 'react';
import * as Yup from 'yup';
import { ChipInput, Defaults } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { listEnvironmentGroups, useClient } from 'services';
import { createNetwork } from '../services';

export const NetworkCreateModal = (props) => {
  const { environment, onApply, onClose, open, reloadNetworks, ...other } =
    props;
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const client = useClient();
  const [groupOptions, setGroupOptions] = useState([]);

  const fetchGroups = useCallback(async () => {
    try {
      const response = await client.query(
        listEnvironmentGroups({
          filter: Defaults.selectListFilter,
          environmentUri: environment.environmentUri
        })
      );
      if (!response.errors) {
        setGroupOptions(
          response.data.listEnvironmentGroups.nodes.map((g) => ({
            value: g.groupUri,
            label: g.groupUri
          }))
        );
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    }
  }, [client, dispatch, environment]);

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = await client.mutate(
        createNetwork({
          environmentUri: environment.environmentUri,
          tags: values.tags,
          description: values.description,
          label: values.label,
          vpcId: values.vpcId,
          SamlGroupName: values.SamlAdminGroupName,
          privateSubnetIds: values.privateSubnetIds,
          publicSubnetIds: values.publicSubnetIds
        })
      );
      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        enqueueSnackbar('Network added', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        if (reloadNetworks) {
          reloadNetworks();
        }
        if (onApply) {
          onApply();
        }
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
      fetchGroups().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, dispatch, fetchGroups]);

  if (!environment) {
    return null;
  }

  return (
    <Dialog maxWidth="md" fullWidth onClose={onClose} open={open} {...other}>
      <Box sx={{ p: 3 }}>
        <Typography
          align="center"
          color="textPrimary"
          gutterBottom
          variant="h4"
        >
          Create a new network configuration
        </Typography>
        <Typography align="center" color="textSecondary" variant="subtitle2">
          Networks are VPC and subnets information required for AWS resources
          created under a VPC.
        </Typography>
        <Box sx={{ p: 3 }}>
          <Formik
            initialValues={{
              label: '',
              vpcId: '',
              SamlAdminGroupName: '',
              privateSubnetIds: [],
              publicSubnetIds: [],
              tags: []
            }}
            validationSchema={Yup.object().shape({
              label: Yup.string().max(255).required('*VPC name is required'),
              vpcId: Yup.string().max(255).required('*VPC ID is required'),
              SamlAdminGroupName: Yup.string()
                .max(255)
                .required('*Team is required'),
              privateSubnetIds: Yup.array().nullable(),
              publicSubnetIds: Yup.array().nullable(),
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
              <form onSubmit={handleSubmit}>
                <Grid container spacing={3}>
                  <Grid item lg={8} md={6} xs={12}>
                    <Box>
                      <CardHeader title="Details" />
                      <CardContent>
                        <TextField
                          error={Boolean(touched.label && errors.label)}
                          fullWidth
                          helperText={touched.label && errors.label}
                          label="VPC name"
                          name="label"
                          onBlur={handleBlur}
                          onChange={handleChange}
                          value={values.label}
                          variant="outlined"
                        />
                      </CardContent>
                      <CardContent>
                        <TextField
                          error={Boolean(touched.vpcId && errors.vpcId)}
                          fullWidth
                          helperText={touched.vpcId && errors.vpcId}
                          label="VPC ID"
                          name="vpcId"
                          onBlur={handleBlur}
                          onChange={handleChange}
                          value={values.vpcId}
                          variant="outlined"
                        />
                      </CardContent>
                      <CardContent>
                        <ChipInput
                          fullWidth
                          defaultValue={values.publicSubnetIds}
                          error={Boolean(
                            touched.publicSubnetIds && errors.publicSubnetIds
                          )}
                          helperText={
                            touched.publicSubnetIds && errors.publicSubnetIds
                          }
                          variant="outlined"
                          label="Public subnets"
                          placeholder="Hit enter after typing value"
                          onChange={(chip) => {
                            setFieldValue('publicSubnetIds', [...chip]);
                          }}
                        />
                      </CardContent>
                      <CardContent>
                        <ChipInput
                          fullWidth
                          defaultValue={values.privateSubnetIds}
                          error={Boolean(
                            touched.privateSubnetIds && errors.privateSubnetIds
                          )}
                          helperText={
                            touched.privateSubnetIds && errors.privateSubnetIds
                          }
                          variant="outlined"
                          label="Private subnets"
                          placeholder="Hit enter after typing value"
                          onChange={(chip) => {
                            setFieldValue('privateSubnetIds', [...chip]);
                          }}
                        />
                      </CardContent>
                    </Box>
                  </Grid>
                  <Grid item lg={4} md={6} xs={12}>
                    <Box>
                      <CardHeader title="Organize" />
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
                      <CardContent>
                        <ChipInput
                          error={Boolean(touched.tags && errors.tags)}
                          fullWidth
                          helperText={touched.tags && errors.tags}
                          variant="outlined"
                          label="Tags"
                          placeholder="Hit enter after typing value"
                          onChange={(chip) => {
                            setFieldValue('tags', [...chip]);
                          }}
                        />
                      </CardContent>
                    </Box>
                    {errors.submit && (
                      <Box sx={{ mt: 3 }}>
                        <FormHelperText error>{errors.submit}</FormHelperText>
                      </Box>
                    )}
                    <CardContent>
                      <LoadingButton
                        color="primary"
                        disabled={isSubmitting}
                        type="submit"
                        variant="contained"
                      >
                        Create
                      </LoadingButton>
                    </CardContent>
                  </Grid>
                </Grid>
              </form>
            )}
          </Formik>
        </Box>
      </Box>
    </Dialog>
  );
};

NetworkCreateModal.propTypes = {
  environment: PropTypes.object.isRequired,
  onApply: PropTypes.func,
  onClose: PropTypes.func,
  reloadNetworks: PropTypes.func,
  open: PropTypes.bool.isRequired
};
