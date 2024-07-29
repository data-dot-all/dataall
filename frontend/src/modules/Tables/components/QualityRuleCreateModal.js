import {
  Box,
  CardContent,
  CardHeader,
  Dialog,
  Grid,
  TextField,
  Typography
} from '@mui/material';
import { Formik } from 'formik';
// import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState } from 'react';
import * as Yup from 'yup';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
//TODO: import { createDataQualityRule } from '../services';

export const QualityRuleCreateModal = (props) => {
  const { table, onApply, onClose, open, ...other } = props;
  //const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const client = useClient();
  const [ruleOptions, setRuleOptions] = useState([]);

  const fetchRules = useCallback(async () => {
    try {
      // const response = await client.query(
      //   listGlueDataQualityRules()
      // );
      // if (!response.errors) {
      //   setRuleOptions(response.data.listGlueDataQualityRules);
      // } else {
      //   dispatch({ type: SET_ERROR, error: response.errors[0].message });
      // }
      setRuleOptions(ruleOptions);
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    }
  }, [client, dispatch]);

  async function submit(values, setStatus, setSubmitting, setErrors) {
    // try {
    //   const response = await client.mutate(
    //     createDataQualityRule({
    //       tableuri: table.tableuri,
    //       //TODO: rest of input
    //     })
    //   );
    //   if (!response.errors) {
    //     setStatus({ success: true });
    //     setSubmitting(false);
    //     enqueueSnackbar('Network added', {
    //       anchorOrigin: {
    //         horizontal: 'right',
    //         vertical: 'top'
    //       },
    //       variant: 'success'
    //     });
    //     if (reloadNetworks) {
    //       reloadNetworks();
    //     }
    //     if (onApply) {
    //       onApply();
    //     }
    //   } else {
    //     dispatch({ type: SET_ERROR, error: response.errors[0].message });
    //   }
    // } catch (err) {
    //   setStatus({ success: false });
    //   setErrors({ submit: err.message });
    //   setSubmitting(false);
    //   dispatch({ type: SET_ERROR, error: err.message });
    // }
  }

  useEffect(() => {
    if (client) {
      fetchRules().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, dispatch, fetchRules]);

  if (!table) {
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
          Create a new Glue Data Quality rule
        </Typography>
        <Typography align="center" color="textSecondary" variant="subtitle2">
          Networks are VPC and subnets information required for AWS resources
          created under a VPC.
        </Typography>
        <Box sx={{ p: 3 }}>
          <Formik
            initialValues={{
              label: ''
            }}
            validationSchema={Yup.object().shape({
              label: Yup.string().max(255).required('*Rule name is required')
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
                          label="Rule name"
                          name="label"
                          onBlur={handleBlur}
                          onChange={handleChange}
                          value={values.label}
                          variant="outlined"
                        />
                      </CardContent>
                    </Box>
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

QualityRuleCreateModal.propTypes = {
  table: PropTypes.object.isRequired,
  onApply: PropTypes.func,
  onClose: PropTypes.func,
  open: PropTypes.bool.isRequired
};
