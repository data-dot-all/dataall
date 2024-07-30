import SendIcon from '@mui/icons-material/Send';
import { LoadingButton } from '@mui/lab';
import {
  Box,
  Button,
  CardContent,
  CircularProgress,
  Dialog,
  TextField,
  Typography,
  Autocomplete
} from '@mui/material';
import { Formik } from 'formik';
import PropTypes from 'prop-types';
import React, { useEffect, useState } from 'react';
import { Defaults } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import {
  fetchOneEnum,
  listGroups,
  listValidEnvironments,
  useClient
} from 'services';
import { listOrganizations } from '../../Organizations/services';

export const CreateMetadataFormModal = (props) => {
  const { onApply, onClose, open, stopLoader, ...other } = props;
  const dispatch = useDispatch();
  const client = useClient();
  const [loading, setLoading] = useState(false);
  const [groupOptions, setGroupOptions] = useState([]);
  const [environmentOptions, setEnvironmentOptions] = useState([]);
  const [organizationOptions, setOrganizationOptions] = useState([]);
  const [visibilityOptions, setVisibilityOptions] = useState([]);
  const [visibilityDict, setVisibilityDict] = useState({});

  const fetchGroups = async () => {
    setLoading(true);
    try {
      const response = await client.query(listGroups({ filter: {} }));
      if (!response.errors) {
        setGroupOptions(
          response.data.listGroups.map((e) => ({
            ...e,
            value: e.groupName,
            label: e.groupName
          }))
        );
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    } finally {
      setLoading(false);
      stopLoader();
    }
  };
  const fetchOrganizations = async () => {
    setLoading(true);
    try {
      const response = await client.query(
        listOrganizations({
          filter: Defaults.selectListFilter
        })
      );
      if (!response.errors) {
        setOrganizationOptions(
          response.data.listOrganizations.nodes.map((e) => ({
            ...e,
            value: e.organizationUri,
            label: e.label
          }))
        );
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    } finally {
      setLoading(false);
      stopLoader();
    }
  };
  const fetchEnvironments = async () => {
    setLoading(true);
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
      setLoading(false);
      stopLoader();
    }
  };
  const fetchVisibilityOptions = async () => {
    try {
      const enumVisibilityOptions = await fetchOneEnum(
        client,
        'MetadataFormVisibility'
      );
      if (enumVisibilityOptions.length > 0) {
        setVisibilityOptions(enumVisibilityOptions);
        setVisibilityDict(
          Object.assign(
            {},
            ...enumVisibilityOptions.map((x) => ({ [x.name]: x.value }))
          )
        );
      } else {
        const error = 'Could not fetch visibility options';
        dispatch({ type: SET_ERROR, error });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    }
  };

  useEffect(() => {
    if (client && open) {
      fetchEnvironments().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
      fetchVisibilityOptions().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
      fetchOrganizations().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
      fetchGroups().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, open, dispatch]);

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

  if (loading) {
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
            description: '',
            visibility: visibilityDict.Global
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
                    onChange={handleChange}
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
                    onChange={handleChange}
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
                    value={values.visibility}
                    options={visibilityOptions.map((option) => option.value)}
                    onChange={(event, value) => {
                      setFieldValue('visibility', value);
                    }}
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
                {values.visibility === visibilityDict.Organization && (
                  <CardContent>
                    <Autocomplete
                      id="organization"
                      disablePortal
                      visibility={
                        values.visibility === visibilityDict['Organization']
                      }
                      onChange={(event, value) => {
                        setFieldValue('organization', value.value);
                      }}
                      options={organizationOptions.map((option) => option)}
                      renderInput={(params) => (
                        <TextField
                          {...params}
                          fullWidth
                          error={Boolean(
                            touched.organizationUri && errors.organizationUri
                          )}
                          helperText={
                            touched.organizationUri && errors.organizationUri
                          }
                          label="Organization"
                          onChange={handleChange}
                          variant="outlined"
                        />
                      )}
                    />
                  </CardContent>
                )}
                {values.visibility === visibilityDict.Environment && (
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
                )}
                {values.visibility === visibilityDict.Team && (
                  <CardContent>
                    <Autocomplete
                      id="group"
                      disablePortal
                      options={groupOptions.map((option) => option)}
                      renderInput={(params) => (
                        <TextField
                          {...params}
                          fullWidth
                          error={Boolean(touched.groupName && errors.groupName)}
                          helperText={touched.groupName && errors.groupName}
                          label="Team"
                          onChange={handleChange}
                          variant="outlined"
                        />
                      )}
                    />
                  </CardContent>
                )}
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
