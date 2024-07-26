import SendIcon from '@mui/icons-material/Send';
import { LoadingButton } from '@mui/lab';
import {
  Box,
  Button,
  CardContent,
  CircularProgress,
  Dialog,
  TextField,
  Typography
} from '@mui/material';
import { Formik } from 'formik';
import PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState } from 'react';
import { Defaults } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { listValidEnvironments, useClient } from 'services';
import Autocomplete from '@mui/lab/Autocomplete';

export const CreateMetadataFormModal = (props) => {
  const { onApply, onClose, open, stopLoader, ...other } = props;
  const dispatch = useDispatch();
  const client = useClient();
  const [loadingEnvs, setLoadingEnvs] = useState(false);
  const [environmentOptions, setEnvironmentOptions] = useState([]);
  const [visibilityOptions, setVisibilityOptions] = useState([]);

  const fetchEnvironments = useCallback(async () => {
    setLoadingEnvs(true);
    try {
      const response = await client.query(
        listValidEnvironments({
          filter: Defaults.selectListFilter
        })
      );
      if (!response.errors) {
        setEnvironmentOptions(
          response.data.listValidEnvironments.nodes.map((e) => ({
            ...e,
            value: e.environmentUri,
            label: e.label
          }))
        );
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    } finally {
      setLoadingEnvs(false);
      stopLoader();
    }
  }, [client, dispatch]);

  const fetchVisibilityOptions = useCallback(async () => {
    setVisibilityOptions([{ name: 'Test', description: 'Also Test' }]);
  }, [client, dispatch]);

  useEffect(() => {
    if (client && open) {
      fetchEnvironments().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
      fetchVisibilityOptions().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, open, fetchEnvironments, dispatch]);

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
    } catch (err) {
      console.error(err);
      setStatus({ success: false });
      setErrors({ submit: err.message });
      setSubmitting(false);
      dispatch({ type: SET_ERROR, error: err.message });
    }
  }

  if (loadingEnvs) {
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
          Create Metadata Form
        </Typography>
        <Formik
          initialValues={{
            name: '',
            description: ''
          }}
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
            setFieldValue,
            touched,
            values
          }) => (
            <form onSubmit={handleSubmit}>
              <Box>
                <CardContent>
                  <TextField
                    fullWidth
                    label="Form name"
                    name="name"
                    value={values.name}
                    variant="outlined"
                  />
                </CardContent>
                <CardContent>
                  <TextField
                    FormHelperTextProps={{
                      sx: {
                        textAlign: 'right',
                        mr: 0
                      }
                    }}
                    fullWidth
                    helperText={`${
                      200 - values.description.length
                    } characters left`}
                    label="Description"
                    name="description"
                    multiline
                    rows={3}
                    value={values.description}
                    variant="outlined"
                  />
                </CardContent>
                <CardContent>
                  <Autocomplete
                    id="visibility"
                    disablePortal
                    options={visibilityOptions.map(
                      (option) => option.description
                    )}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        fullWidth
                        label="Visibility"
                        onChange={handleChange}
                        variant="outlined"
                      />
                    )}
                  />
                </CardContent>
                <CardContent>
                  <Autocomplete
                    id="environment"
                    disablePortal
                    options={environmentOptions.map((option) => option)}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        fullWidth
                        error={Boolean(
                          touched.environmentUri && errors.environmentUri
                        )}
                        helperText={
                          touched.environmentUri && errors.environmentUri
                        }
                        label="Environment"
                        onChange={handleChange}
                        variant="outlined"
                      />
                    )}
                  />
                </CardContent>
              </Box>
              {isSubmitting ? (
                <CardContent>
                  <CircularProgress sx={{ ml: '45%' }} size={50} />
                </CardContent>
              ) : (
                <CardContent>
                  <LoadingButton
                    fullWidth
                    startIcon={<SendIcon fontSize="small" />}
                    color="primary"
                    disabled={isSubmitting}
                    type="submit"
                    variant="contained"
                  >
                    Create
                  </LoadingButton>

                  <Button
                    sx={{ mt: 2 }}
                    onClick={onApply}
                    fullWidth
                    color="primary"
                    variant="outlined"
                    disabled={isSubmitting}
                  >
                    Cancel
                  </Button>
                </CardContent>
              )}
            </form>
          )}
        </Formik>
      </Box>
    </Dialog>
  );
};

CreateMetadataFormModal.propTypes = {
  onApply: PropTypes.func,
  onClose: PropTypes.func,
  open: PropTypes.bool.isRequired,
  stopLoader: PropTypes.func
};
