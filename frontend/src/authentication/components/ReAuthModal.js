// import SendIcon from '@mui/icons-material/Send';
// import { LoadingButton } from '@mui/lab';
import {
  Box,
  // CardContent,
  Dialog,
  // TextField,
  Typography,
  Button
} from '@mui/material';
// import { Formik } from 'formik';
// import PropTypes from 'prop-types';
// import * as Yup from 'yup';
import { useAuth } from 'authentication';
// import { createReAuthSession } from 'authentication/contexts/services';
// import { useClient } from 'services';

export const ReAuthModal = () => {
  // const { onApply, onClose, open, ...other } = props;
  // When State is REAUTH --> LOAD
  const { reAuthStatus, reauth } = useAuth();

  // async function submit(values, setStatus, setSubmitting, setErrors) {
  //   try {
  //     setStatus({ success: true });
  //     setSubmitting(false);
  //     await reauth();
  //     // await client.query(createReAuthSession());
  //     // enqueueSnackbar('ReAuth Confirmed', {
  //     //   anchorOrigin: {
  //     //     horizontal: 'right',
  //     //     vertical: 'top'
  //     //   },
  //     //   variant: 'success'
  //     // });
  //     // if (onApply) {
  //     //   onApply();
  //     // }

  //     // TODO: QUERY TO CREATE REAUTH SESSION
  //   } catch (err) {
  //     console.error(err);
  //     setStatus({ success: false });
  //     setErrors({ submit: err.message });
  //     setSubmitting(false);
  //     // dispatch({ type: SET_ERROR, error: err.message });
  //   }
  // }

  return (
    <Dialog maxWidth="md" fullWidth open={reAuthStatus}>
      <Box sx={{ p: 3 }}>
        <Typography
          align="center"
          color="textPrimary"
          gutterBottom
          variant="h4"
        >
          ReAuth Credentials
        </Typography>
        
        <Box sx={{ p: 3 }}>
        <CardContent>
          <Typography color="textSecondary" variant="subtitle2">
            In order to perform this action you are required to log in again to the data.all UI.
            Click the below button to be redirected to log back in before proceeding further or Click
            away to continue with other data.all operations.
          </Typography>
          <Button
            color="primary"
            fullWidth
            size="large"
            type="submit"
            variant="contained"
            onClick={reauth}
          >
            Re-Authenticate
          </Button>
        </CardContent>
          {/* <Formik
            initialValues={{
              username: '',
              password: ''
            }}
            validationSchema={Yup.object().shape({
              username: Yup.object().required('*Username is required'),
              password: Yup.string().required('*Password is required')
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
              isSubmitting,
              handleSubmit,
              setFieldValue,
              touched,
              values
            }) => (
              <form onSubmit={handleSubmit}>
                <Box>
                  <CardContent>
                    <TextField
                      fullWidth
                      error={Boolean(touched.environment && errors.environment)}
                      helperText={touched.environment && errors.environment}
                      label="Username"
                      name="username"
                      onBlur={handleBlur}
                      onChange={handleChange}
                      value={values.username}
                      variant="outlined"
                    />
                  </CardContent>
                  <CardContent>
                    <TextField
                      fullWidth
                      error={Boolean(touched.environment && errors.environment)}
                      helperText={touched.environment && errors.environment}
                      label="Password"
                      name="password"
                      onBlur={handleBlur}
                      onChange={handleChange}
                      value={values.password}
                      variant="outlined"
                    />
                  </CardContent>
                </Box>
                <CardContent>
                  <LoadingButton
                    fullWidth
                    startIcon={<SendIcon fontSize="small" />}
                    color="primary"
                    disabled={isSubmitting}
                    type="submit"
                    variant="contained"
                  >
                    ReAuth Button
                  </LoadingButton>
                </CardContent>
              </form>
            )}
          </Formik> */}
        </Box>
      </Box>
    </Dialog>
  );
};
