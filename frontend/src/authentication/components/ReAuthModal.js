import SendIcon from '@mui/icons-material/Send';
import { LoadingButton } from '@mui/lab';
import {
  Box,
  CardContent,
  Dialog,
  TextField,
  Typography
} from '@mui/material';
import { Formik } from 'formik';
import PropTypes from 'prop-types';
import * as Yup from 'yup';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { Auth } from 'aws-amplify';



// async function loginUser(credentials) {
//   return fetch(process.env.REACT_APP_GRAPHQL_API, {
//     method: 'POST',
//     headers: {
//       'Content-Type': 'application/json'
//     },
//     body: JSON.stringify(credentials)
//   })
//     .then(data => data.json())
//  } 

  export const ReAuthModal = (props) => {
  const { onApply, onClose, open, ...other } = props;
  const { logout, login } = useAuth();
  // const handleSubmit = async e => {
  //   e.preventDefault();
  //   const token = await loginUser({
  //     username,
  //     password
  //   });
  //   setToken(token);
  // }

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      await logout();
      await Auth.signIn(values.username, values.password);
      // await this.props.SetAuthState(AuthState.SignedIn)
      setStatus({ success: true });
      setSubmitting(false);
      enqueueSnackbar('ReAuth Confirmed', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      if (onApply) {
        onApply();
      }

      // TODO: QUERY TO CREATE REAUTH SESSION

    } catch (err) {
      console.error(err);
      setStatus({ success: false });
      setErrors({ submit: err.message });
      setSubmitting(false);
      dispatch({ type: SET_ERROR, error: err.message });
    }
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
          ReAuth Credentials
        </Typography>
          <form>
            <p>Username</p>
            <input type="username" />
            <p>Password</p>
            <input type="password" />
            <div>
              <button type="button" onClick={login}>
                {" "}
                Login{" "}
              </button>
            </div>
          </form>
        <Box sx={{ p: 3 }}>
          <Formik
            initialValues={{
              username: '',
              password: ''
            }}
            validationSchema={Yup.object().shape({
              username: Yup.object().required('*Usernmae is required'),
              password: Yup.string().required('*Password is required'),
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
              setFieldValue,
              touched,
              values
            }) => (
              <form onSubmit={handleSubmit}>
                <Box>
                  <CardContent>
                    <TextField
                      fullWidth
                      disabled
                      label="Username"
                      name="username"
                      onBlur={handleBlur}
                      onChange={handleChange}
                      value={username}
                      variant="outlined"
                    />
                  </CardContent>
                  <CardContent>
                    <TextField
                      fullWidth
                      disabled
                      label="Password"
                      name="password"
                      onBlur={handleBlur}
                      onChange={handleChange}
                      value={password}
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
          </Formik>
        </Box>
      </Box>
    </Dialog>
  );
};

ReAuthModal.propTypes = {
  onApply: PropTypes.func,
  onClose: PropTypes.func,
  open: PropTypes.bool.isRequired,
};
