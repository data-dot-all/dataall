import SendIcon from '@mui/icons-material/Send';
import { LoadingButton } from '@mui/lab';
import Autocomplete from '@mui/lab/Autocomplete';
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
import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState } from 'react';
import * as Yup from 'yup';
import { Defaults } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import {
  createShareObject,
  listEnvironmentRedshiftConnections,
  listEnvironmentGroups,
  listValidEnvironments,
  useClient
} from 'services';
import { ShareEditForm } from '../../Shared/Shares/ShareEditForm';
import { getShareObject } from '../../Shares/services';

export const RequestRedshiftAccessModal = (props) => {
  const { hit, onApply, onClose, open, stopLoader, ...other } = props;
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const client = useClient();
  const [environmentOptions, setEnvironmentOptions] = useState([]);
  const [loadingGroups, setLoadingGroups] = useState(false);
  const [loadingEnvs, setLoadingEnvs] = useState(false);
  const [groupOptions, setGroupOptions] = useState([]);
  const [loadingNamespaces, setLoadingNamespaces] = useState(false);
  const [namespaceOptions, setNamespaceOptions] = useState([]);

  const [step, setStep] = useState(0);
  const [share, setShare] = useState(false);
  const [loading, setLoading] = useState(false);
  const [alreadyExisted, setAlreadyExisted] = useState(false);

  const fetchEnvironments = useCallback(async () => {
    setStep(0);
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

  const fetchShareObject = async (shareUri) => {
    const response = await client.query(getShareObject({ shareUri: shareUri }));
    if (!response.errors) {
      setShare(response.data.getShareObject);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };

  const fetchGroups = async (environmentUri) => {
    setLoadingGroups(true);
    try {
      const response = await client.query(
        listEnvironmentGroups({
          filter: Defaults.selectListFilter,
          environmentUri: environmentUri
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
    } finally {
      setLoadingGroups(false);
    }
  };

  const fetchNamespaces = async (environmentUri, groupUri) => {
    setLoadingNamespaces(true);
    try {
      const response = await client.query(
        listEnvironmentRedshiftConnections({
          filter: {
            ...Defaults.selectListFilter,
            environmentUri: environmentUri,
            groupUri: groupUri,
            connectionType: 'ADMIN'
          }
        })
      );
      if (!response.errors) {
        setNamespaceOptions(
          response.data.listEnvironmentRedshiftConnections.nodes.map(
            (item) => ({
              value: item.connectionUri,
              label: `${item.nameSpaceId} [CONNECTION: ${item.name}] [DATABASE: ${item.database}]`
            })
          )
        );
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    } finally {
      setLoadingNamespaces(false);
    }
  };

  useEffect(() => {
    if (client && open) {
      fetchEnvironments().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, open, fetchEnvironments, dispatch]);

  const formDatasetRequestObject = (inputObject) => {
    return {
      datasetUri: hit._id,
      input: inputObject
    };
  };

  const formItemRequestObject = (inputObject) => {
    return {
      datasetUri: hit.datasetUri,
      itemUri: hit._id,
      itemType: 'RedshiftTable',
      input: inputObject
    };
  };

  const formRequestObject = (values) => {
    let inputObject = {
      environmentUri: values.environmentUri,
      groupUri: values.groupUri,
      principalId: values.connection,
      principalRoleName: values.rsRole,
      principalType: 'RedshiftRole',
      requestPurpose: values.comment,
      permissions: ['Read']
    };

    if (hit.resourceKind === 'redshiftdataset') {
      return formDatasetRequestObject(inputObject);
    }
    if (hit.resourceKind === 'redshifttable') {
      return formItemRequestObject(inputObject);
    }
  };

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = await client.mutate(
        createShareObject(formRequestObject(values))
      );

      if (response && !response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        setLoading(true);
        setAlreadyExisted(response.data.createShareObject.alreadyExisted);
        await fetchShareObject(response.data.createShareObject.shareUri);
        setStep(1);
        setLoading(false);
        const message = response.data.createShareObject.alreadyExisted
          ? 'Redirecting to the existing share'
          : 'Draft share request created';
        enqueueSnackbar(message, {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
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

  const beforeApply = () => {
    setStep(0);
    onApply();
  };

  if (!hit || loadingEnvs) {
    return null;
  }

  return (
    <Dialog maxWidth="md" fullWidth onClose={onClose} open={open} {...other}>
      {step === 0 && (
        <Box sx={{ p: 3, minHeight: 800 }}>
          <Typography
            align="center"
            color="textPrimary"
            gutterBottom
            variant="h4"
          >
            Request Access
          </Typography>
          <Typography align="center" color="textSecondary" variant="subtitle2">
            Data access is requested on behalf of the requester team for the
            selected namespace and redshift role. The request will be submitted
            to the data owners, track its progress in the Shares menu on the
            left.
          </Typography>
          <Box sx={{ p: 3 }}>
            <Formik
              initialValues={{
                environmentUri: '',
                comment: '',
                attachMissingPolicies: false
              }}
              validationSchema={Yup.object().shape({
                environmentUri: Yup.string().required(
                  '*Environment is required'
                ),
                groupUri: Yup.string().required('*Team is required'),
                connection: Yup.string().required(
                  '*Redshift Namespace is required'
                ),
                rsRole: Yup.string().required('*Redshift role is required'),
                comment: Yup.string().max(5000)
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
                  <Box>
                    <CardContent>
                      {hit.resourceKind === 'redshifttable' && (
                        <TextField
                          fullWidth
                          disabled
                          label="Redshift Table name"
                          name="redshifttable"
                          value={hit.label}
                          variant="outlined"
                        />
                      )}
                      {hit.resourceKind === 'redshiftdataset' && (
                        <TextField
                          fullWidth
                          disabled
                          label="Redshift Dataset name"
                          name="redshiftdataset"
                          value={hit.label}
                          variant="outlined"
                        />
                      )}
                    </CardContent>
                    <CardContent>
                      <Autocomplete
                        id="environment"
                        disablePortal
                        options={environmentOptions.map((option) => option)}
                        onChange={(event, value) => {
                          setFieldValue('groupUri', '');
                          setFieldValue('connection', '');
                          if (value && value.environmentUri) {
                            setFieldValue(
                              'environmentUri',
                              value.environmentUri
                            );
                            fetchGroups(value.environmentUri).catch((e) =>
                              dispatch({
                                type: SET_ERROR,
                                error: e.message
                              })
                            );
                          } else {
                            setFieldValue('environmentUri', '');
                            setGroupOptions([]);
                            setNamespaceOptions([]);
                          }
                        }}
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
                    <CardContent>
                      {loadingGroups ? (
                        <CircularProgress size={10} />
                      ) : (
                        <Box>
                          {groupOptions.length > 0 ? (
                            <Autocomplete
                              id="group"
                              disablePortal
                              options={groupOptions.map((option) => option)}
                              onChange={(event, value) => {
                                setFieldValue('connection', '');
                                if (value && value.value) {
                                  setFieldValue('groupUri', value.value);
                                  fetchNamespaces(
                                    values.environmentUri,
                                    value.value
                                  ).catch((e) =>
                                    dispatch({
                                      type: SET_ERROR,
                                      error: e.message
                                    })
                                  );
                                } else {
                                  setFieldValue('groupUri', '');
                                  setNamespaceOptions([]);
                                }
                              }}
                              renderInput={(params) => (
                                <TextField
                                  {...params}
                                  fullWidth
                                  error={Boolean(
                                    touched.groupUri && errors.groupUri
                                  )}
                                  helperText={
                                    touched.groupUri && errors.groupUri
                                  }
                                  label="Team"
                                  onChange={handleChange}
                                  variant="outlined"
                                />
                              )}
                            />
                          ) : (
                            <TextField
                              error={Boolean(
                                touched.groupUri && errors.groupUri
                              )}
                              helperText={touched.groupUri && errors.groupUri}
                              fullWidth
                              disabled
                              label="Team"
                              value="No teams found for this environment"
                              variant="outlined"
                            />
                          )}
                        </Box>
                      )}
                    </CardContent>
                    <CardContent>
                      {loadingNamespaces ? (
                        <CircularProgress size={10} />
                      ) : (
                        <Box>
                          {namespaceOptions.length > 0 ? (
                            <Autocomplete
                              id="connection"
                              disablePortal
                              options={namespaceOptions.map((option) => option)}
                              getOptionLabel={(option) => option.label}
                              onChange={(event, value) => {
                                if (value && value.value) {
                                  setFieldValue('connection', value.value);
                                } else {
                                  setFieldValue('connection', '');
                                }
                              }}
                              renderInput={(params) => (
                                <TextField
                                  {...params}
                                  fullWidth
                                  error={Boolean(
                                    touched.connection && errors.connection
                                  )}
                                  helperText={
                                    touched.connection && errors.connection
                                  }
                                  label="Redshift Namespace"
                                  onChange={handleChange}
                                  variant="outlined"
                                />
                              )}
                            />
                          ) : (
                            <TextField
                              error={Boolean(
                                touched.connection && errors.connection
                              )}
                              helperText={
                                touched.connection && errors.connection
                              }
                              fullWidth
                              disabled
                              label="Redshift Namespace"
                              value="This team cannot access any Redshift Namespace in this Environment."
                              variant="outlined"
                            />
                          )}
                        </Box>
                      )}
                    </CardContent>
                    <CardContent>
                      <TextField
                        error={Boolean(touched.rsRole && errors.rsRole)}
                        fullWidth
                        helperText={touched.rsRole && errors.rsRole}
                        label="Redshift Role"
                        name="rsRole"
                        onBlur={handleBlur}
                        onChange={handleChange}
                        value={values.rsRole}
                        variant="outlined"
                      />
                    </CardContent>
                  </Box>
                  {isSubmitting || loading ? (
                    <CardContent>
                      <CircularProgress sx={{ ml: '45%' }} size={50} />
                    </CardContent>
                  ) : (
                    <CardContent>
                      <LoadingButton
                        fullWidth
                        startIcon={<SendIcon fontSize="small" />}
                        color="primary"
                        disabled={isSubmitting || loading}
                        type="submit"
                        variant="contained"
                      >
                        Create Draft Request
                      </LoadingButton>

                      <Button
                        sx={{ mt: 2 }}
                        onClick={onApply}
                        fullWidth
                        color="primary"
                        variant="outlined"
                        disabled={isSubmitting || loading}
                      >
                        Cancel
                      </Button>
                    </CardContent>
                  )}
                </form>
              )}
            </Formik>
          </Box>
        </Box>
      )}
      {step === 1 && (
        <ShareEditForm
          share={share}
          alreadyExisted={alreadyExisted}
          dispatch={dispatch}
          enqueueSnackbar={enqueueSnackbar}
          client={client}
          onApply={beforeApply}
          onCancel={beforeApply}
          showViewShare={true}
        ></ShareEditForm>
      )}
    </Dialog>
  );
};

RequestRedshiftAccessModal.propTypes = {
  hit: PropTypes.object.isRequired,
  onApply: PropTypes.func,
  onClose: PropTypes.func,
  open: PropTypes.bool.isRequired,
  stopLoader: PropTypes.func
};
