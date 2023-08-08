import { LoadingButton } from '@mui/lab';
import {
  Box,
  Card,
  CardContent,
  CircularProgress,
  FormHelperText,
  TextField
} from '@mui/material';
import { Formik } from 'formik';
import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
import { useEffect, useState } from 'react';
import * as Yup from 'yup';
import { SET_ERROR, useDispatch } from 'globalErrors';
import {
  deleteCategory,
  deleteTerm,
  updateCategory,
  updateGlossary,
  updateTerm
} from '../services';

export const GlossaryNodeForm = ({ client, data, refresh, isAdmin }) => {
  const dispatch = useDispatch();
  const [formData, setFormData] = useState(data);
  const [deleting, setDeleting] = useState(false);
  const { enqueueSnackbar } = useSnackbar();
  useEffect(() => {
    setFormData(data);
  }, [data]);

  const deleteGlossaryNode = async () => {
    setDeleting(true);
    let mutation;
    if (data.__typename === 'Term') {
      mutation = deleteTerm;
    } else if (data.__typename === 'Category') {
      mutation = deleteCategory;
    }
    const response = await client.mutate(mutation(data.nodeUri));
    if (!response.errors) {
      refresh();
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setDeleting(false);
  };

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      let mutation;
      if (data.__typename === 'Term') {
        mutation = updateTerm;
      } else if (data.__typename === 'Category') {
        mutation = updateCategory;
      } else {
        mutation = updateGlossary;
      }
      const response = await client.mutate(
        mutation({
          nodeUri: data.nodeUri,
          input: {
            label: values.label,
            readme: values.readme
          }
        })
      );
      if (!response.errors) {
        enqueueSnackbar('Glossary updated', {
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
    <>
      <Box sx={{ p: 3 }}>
        <Formik
          enableReinitialize
          initialValues={{
            label: formData.label,
            readme: formData.readme
          }}
          validationSchema={Yup.object().shape({
            label: Yup.string().max(255).required('*Name is required'),
            readme: Yup.string().max(5000).required('*Description is required')
          })}
          onSubmit={async (values, { setErrors, setStatus, setSubmitting }) => {
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
              <Card>
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
                {isAdmin && (
                  <Box
                    sx={{
                      display: 'flex',
                      justifyContent: 'flex-end',
                      mt: 3,
                      mr: 3,
                      mb: 2
                    }}
                  >
                    <LoadingButton
                      color="primary"
                      sx={{ m: 1 }}
                      loading={isSubmitting}
                      type="submit"
                      variant="contained"
                    >
                      Save
                    </LoadingButton>
                    {/* eslint-disable-next-line react/prop-types */}
                    {data.__typename !== 'Glossary' && (
                      <LoadingButton
                        sx={{ m: 1 }}
                        color="primary"
                        loading={deleting}
                        onClick={deleteGlossaryNode}
                        variant="contained"
                      >
                        Delete
                      </LoadingButton>
                    )}
                  </Box>
                )}
              </Card>
            </form>
          )}
        </Formik>
      </Box>
    </>
  );
};
GlossaryNodeForm.propTypes = {
  data: PropTypes.object.isRequired,
  isAdmin: PropTypes.bool.isRequired,
  client: PropTypes.func.isRequired,
  refresh: PropTypes.func.isRequired
};
