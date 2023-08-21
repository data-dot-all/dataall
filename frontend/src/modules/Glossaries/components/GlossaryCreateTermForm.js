import { LoadingButton } from '@mui/lab';
import {
  Box,
  CardContent,
  CircularProgress,
  Dialog,
  FormHelperText,
  TextField,
  Typography
} from '@mui/material';
import { Formik } from 'formik';
import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
import { useEffect, useState } from 'react';
import * as Yup from 'yup';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { createTerm } from '../services';

export const GlossaryCreateTermForm = ({
  client,
  data,
  refresh,
  isAdmin,
  onApply,
  onClose,
  open
}) => {
  const dispatch = useDispatch();
  const [formData, setFormData] = useState(data);
  const { enqueueSnackbar } = useSnackbar();
  useEffect(() => {
    setFormData(data);
  }, [data]);

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = await client.mutate(
        createTerm({
          parentUri: data.nodeUri,
          input: {
            label: values.label,
            readme: values.readme
          }
        })
      );
      if (!response.errors) {
        enqueueSnackbar('Category created', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
      refresh();
      if (onApply) {
        onApply();
      }
    } catch (err) {
      console.error(err);
      setStatus({ success: false });
      setErrors({ submit: err.message });
      setSubmitting(false);
      dispatch({ type: SET_ERROR, error: err.message });
    }
  }
  if (!formData) {
    return <CircularProgress />;
  }
  return (
    <Dialog maxWidth="md" fullWidth onClose={onClose} open={open}>
      <Box sx={{ p: 3 }}>
        <Typography
          align="center"
          color="textPrimary"
          gutterBottom
          variant="h4"
        >
          Add a new term
        </Typography>
        <Box sx={{ p: 3 }}>
          <Formik
            enableReinitialize
            initialValues={{
              label: '',
              readme: ''
            }}
            validationSchema={Yup.object().shape({
              label: Yup.string().max(255).required('*Name is required'),
              readme: Yup.string()
                .max(5000)
                .required('*Description is required')
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
              touched,
              values
            }) => (
              <form onSubmit={handleSubmit}>
                <CardContent>
                  <TextField
                    disabled
                    label="Parent"
                    fullWidth
                    value={data.label}
                    variant="outlined"
                  />
                </CardContent>
                <CardContent>
                  <TextField
                    disabled={!isAdmin}
                    enableReinitialize
                    error={Boolean(touched.label && errors.label)}
                    fullWidth
                    helperText={touched.label && errors.label}
                    label="Name"
                    name="label"
                    onBlur={handleBlur}
                    onChange={handleChange}
                    value={values.label}
                    variant="outlined"
                  />
                </CardContent>
                <CardContent>
                  <TextField
                    disabled={!isAdmin}
                    enableReinitialize
                    FormHelperTextProps={{
                      sx: {
                        textAlign: 'right',
                        mr: 0
                      }
                    }}
                    fullWidth
                    error={Boolean(touched.readme && errors.readme)}
                    helperText={`${200 - values.readme.length} characters left`}
                    label="Description"
                    name="readme"
                    multiline
                    onBlur={handleBlur}
                    onChange={handleChange}
                    rows={5}
                    value={values.readme}
                    variant="outlined"
                  />
                  {touched.readme && errors.readme && (
                    <Box>
                      <FormHelperText error>{errors.readme}</FormHelperText>
                    </Box>
                  )}
                </CardContent>
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'flex-end',
                    mt: 3,
                    mr: 3,
                    mb: 2
                  }}
                >
                  {isAdmin && (
                    <LoadingButton
                      color="primary"
                      loading={isSubmitting}
                      type="submit"
                      variant="contained"
                    >
                      Save
                    </LoadingButton>
                  )}
                </Box>
              </form>
            )}
          </Formik>
        </Box>
      </Box>
    </Dialog>
  );
};
GlossaryCreateTermForm.propTypes = {
  data: PropTypes.object.isRequired,
  isAdmin: PropTypes.bool.isRequired,
  client: PropTypes.func.isRequired,
  refresh: PropTypes.func.isRequired,
  onApply: PropTypes.func.isRequired,
  onClose: PropTypes.func.isRequired,
  open: PropTypes.bool.isRequired
};
