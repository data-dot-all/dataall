import { LoadingButton } from '@mui/lab';
import {
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
import * as Yup from 'yup';
import { ChipInput } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import { createMLStudioDomain } from '../services';

export const MLStudioDomainCreateModal = (props) => {
  const { environment, onApply, onClose, open, reloadStudioDomains, ...other } =
    props;
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const client = useClient();

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = await client.mutate(
        createMLStudioDomain({
          environmentUri: environment.environmentUri,
          label: values.label,
          vpcId: values.mlStudioVPCId,
          subnetIds: values.mlStudioSubnetIds
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
        if (reloadStudioDomains) {
          reloadStudioDomains();
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
          Create a SageMaker ML Studio Domain for your Environment
        </Typography>
        <Box sx={{ p: 3 }}>
          <Formik
            initialValues={{
              label: '',
              mlStudioVPCId: '',
              mlStudioSubnetIds: []
            }}
            validationSchema={Yup.object().shape({
              label: Yup.string()
                .max(255)
                .required('*ML Studio Domain Name is required'),
              mlStudioVPCId: Yup.string().nullable(),
              mlStudioSubnetIds: Yup.array().when('mlStudioVPCId', {
                is: (value) => !!value,
                then: Yup.array()
                  .min(1)
                  .required('At least 1 Subnet Id required if VPC Id specified')
              })
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
                          label="ML Studio Domain Name"
                          name="label"
                          onBlur={handleBlur}
                          onChange={handleChange}
                          value={values.label}
                          variant="outlined"
                        />
                      </CardContent>
                      <CardContent>
                        <TextField
                          label="(Optional) ML Studio VPC ID"
                          placeholder="(Optional) Bring your own VPC - Specify VPC ID"
                          name="mlStudioVPCId"
                          fullWidth
                          error={Boolean(
                            touched.mlStudioVPCId && errors.mlStudioVPCId
                          )}
                          helperText={
                            touched.mlStudioVPCId && errors.mlStudioVPCId
                          }
                          onBlur={handleBlur}
                          onChange={handleChange}
                          value={values.mlStudioVPCId}
                          variant="outlined"
                        />
                      </CardContent>
                      <CardContent>
                        <ChipInput
                          fullWidth
                          error={Boolean(
                            touched.mlStudioSubnetIds &&
                              errors.mlStudioSubnetIds
                          )}
                          helperText={
                            touched.mlStudioSubnetIds &&
                            errors.mlStudioSubnetIds
                          }
                          variant="outlined"
                          label="(Optional) ML Studio Subnet ID(s)"
                          placeholder="(Optional) Bring your own VPC - Specify Subnet ID (Hit enter after typing value)"
                          onChange={(chip) => {
                            setFieldValue('mlStudioSubnetIds', [...chip]);
                          }}
                        />
                      </CardContent>
                    </Box>
                  </Grid>
                  <Grid item lg={4} md={6} xs={12}>
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

MLStudioDomainCreateModal.propTypes = {
  environment: PropTypes.object.isRequired,
  onApply: PropTypes.func,
  onClose: PropTypes.func,
  reloadStudioDomains: PropTypes.func,
  open: PropTypes.bool.isRequired
};
