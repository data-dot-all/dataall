import SendIcon from '@mui/icons-material/Send';
import { LoadingButton } from '@mui/lab';
import {
  Box,
  Button,
  CardContent,
  CircularProgress,
  Dialog,
  FormControlLabel,
  FormHelperText,
  MenuItem,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography
} from '@mui/material';
import { Formik } from 'formik';
import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState } from 'react';
import * as Yup from 'yup';
import { Defaults, Pager, ShareStatus } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import {
  createShareObject,
  listEnvironmentConsumptionRoles,
  listEnvironmentGroups,
  listValidEnvironments,
  requestDashboardShare,
  getConsumptionRolePolicies,
  useClient
} from 'services';
import { useNavigate } from 'react-router-dom';
import {
  addSharedItem,
  getShareObject,
  removeSharedItem,
  revokeItemsShareObject,
  submitApproval,
  updateShareRequestReason
} from '../../Shares/services';
import { DeleteOutlined } from '@mui/icons-material';

const ItemRow = (props) => {
  const { share, item, onAction, enqueueSnackbar, dispatch, client } = props;

  const whatToDo = () => {
    if (!item.status) return 'Request';
    if (item.status === 'Revoke_Succeeded' || item.status === 'PendingApproval')
      return 'Delete';
    if (item.status === 'Share_Succeeded' || item.status === 'Revoke_Failed')
      return 'Revoke';
    return 'Nothing';
  };

  const possibleAction = whatToDo();

  const removeShareItem = async () => {
    const response = await client.mutate(
      removeSharedItem({ shareItemUri: item.shareItemUri })
    );
    if (!response.errors) {
      enqueueSnackbar('Item added', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      await onAction();
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };

  const revokeShareItem = async () => {
    const response = await client.mutate(
      revokeItemsShareObject({
        input: {
          shareUri: share.shareUri,
          itemUris: [item.itemUri]
        }
      })
    );

    if (!response.errors) {
      enqueueSnackbar('Item added', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      await onAction();
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };

  const addShareItem = async () => {
    const response = await client.mutate(
      addSharedItem({
        shareUri: share.shareUri,
        input: {
          itemUri: item.itemUri,
          itemType: item.itemType
        }
      })
    );

    if (!response.errors) {
      enqueueSnackbar('Item added', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      await onAction();
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };

  return (
    <TableRow>
      <TableCell>{item.itemType}</TableCell>
      <TableCell>{item.itemName}</TableCell>
      <TableCell>
        {item.status ? <ShareStatus status={item.status} /> : 'Not requested'}
      </TableCell>
      {(share.status === 'Draft' ||
        share.status === 'Processed' ||
        share.status === 'Rejected' ||
        share.status === 'Submitted') && (
        <TableCell>
          {possibleAction === 'Delete' && (
            <Button
              color="primary"
              startIcon={<DeleteOutlined fontSize="small" />}
              sx={{ m: 1 }}
              variant="outlined"
              onClick={removeShareItem}
            >
              Delete
            </Button>
          )}
          {possibleAction === 'Revoke' && (
            <Button
              variant="contained"
              onClick={revokeShareItem}
              startIcon={<SendIcon fontSize="small" />}
              color="primary"
            >
              Revoke
            </Button>
          )}
          {possibleAction === 'Request' && (
            <Button
              variant="contained"
              onClick={addShareItem}
              startIcon={<SendIcon fontSize="small" />}
              color="primary"
            >
              Request
            </Button>
          )}
          {possibleAction === 'Nothing' && (
            <Typography color="textSecondary" variant="subtitle2">
              Wait until this item is processed
            </Typography>
          )}
        </TableCell>
      )}
    </TableRow>
  );
};

ItemRow.propTypes = {
  item: PropTypes.object,
  onAction: PropTypes.func
};

export const RequestAccessModal = (props) => {
  const { hit, onApply, onClose, open, stopLoader, ...other } = props;
  const { enqueueSnackbar } = useSnackbar();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const client = useClient();
  const [environmentOptions, setEnvironmentOptions] = useState([]);
  const [loadingGroups, setLoadingGroups] = useState(false);
  const [loadingEnvs, setLoadingEnvs] = useState(false);
  const [groupOptions, setGroupOptions] = useState([]);
  const [loadingRoles, setLoadingRoles] = useState(false);
  const [roleOptions, setRoleOptions] = useState([]);
  const [isSharePolicyAttached, setIsSharePolicyAttached] = useState(true);
  const [policyName, setPolicyName] = useState('');

  const [step, setStep] = useState(0);
  const [share, setShare] = useState({});
  const [sharedItems, setSharedItems] = useState(Defaults.pagedResponse);
  const [filter, setFilter] = useState(Defaults.filter);
  const [loading, setLoading] = useState(false);
  const [requestPurpose, setRequestPurpose] = useState('');

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

  const fetchGroups = async (environmentUri) => {
    setLoadingGroups(true);
    try {
      const response = await client.query(
        listEnvironmentGroups({
          filter: Defaults.selectListFilter,
          environmentUri
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

  const fetchRoles = async (environmentUri, groupUri) => {
    setLoadingRoles(true);
    try {
      const response = await client.query(
        listEnvironmentConsumptionRoles({
          filter: { ...Defaults.selectListFilter, groupUri: groupUri },
          environmentUri
        })
      );
      if (!response.errors) {
        setRoleOptions(
          response.data.listEnvironmentConsumptionRoles.nodes.map((g) => ({
            value: g.consumptionRoleUri,
            label: [g.consumptionRoleName, ' [', g.IAMRoleArn, ']'].join(''),
            IAMRoleName: g.IAMRoleName,
            dataallManaged: g.dataallManaged
          }))
        );
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    } finally {
      setLoadingRoles(false);
    }
  };

  const fetchRolePolicies = async (environmentUri, IAMRoleName) => {
    setLoadingRoles(true);
    try {
      const response = await client.query(
        getConsumptionRolePolicies({
          environmentUri,
          IAMRoleName
        })
      );
      if (!response.errors) {
        var isSharePolicyAttached =
          response.data.getConsumptionRolePolicies.find(
            (policy) => policy.policy_type === 'SharePolicy'
          ).attached;
        setIsSharePolicyAttached(isSharePolicyAttached);
        var policyName = response.data.getConsumptionRolePolicies.find(
          (policy) => policy.policy_type === 'SharePolicy'
        ).policy_name;
        setPolicyName(policyName);
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    } finally {
      setLoadingRoles(false);
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
    let types = {
      table: 'DatasetTable',
      folder: 'DatasetStorageLocation'
    };
    return {
      datasetUri: hit.datasetUri,
      itemUri: hit._id,
      itemType: types[hit.resourceKind],
      input: inputObject
    };
  };

  const formRequestObject = (values) => {
    let type = values.consumptionRole ? 'ConsumptionRole' : 'Group';
    let principal = values.consumptionRole
      ? values.consumptionRole
      : values.groupUri;

    let inputObject = {
      environmentUri: values.environment.environmentUri,
      groupUri: values.groupUri,
      principalId: principal,
      principalType: type,
      requestPurpose: values.comment,
      attachMissingPolicies: values.attachMissingPolicies
    };

    if (hit.resourceKind === 'dataset') {
      return formDatasetRequestObject(inputObject);
    }
    if (hit.resourceKind === 'table' || hit.resourceKind === 'folder') {
      return formItemRequestObject(inputObject);
    }
  };

  const fetchShareObject = async (shareUri) => {
    setLoading(true);
    const response = await client.query(getShareObject({ shareUri: shareUri }));
    if (!response.errors) {
      setShare(response.data.getShareObject);
      setSharedItems({ ...response.data.getShareObject.items });
      setRequestPurpose(response.data.getShareObject.requestPurpose);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  };

  const sendRequest = async () => {
    setStep(0);
    if (requestPurpose !== share.requestPurpose) {
      await updateRequestPurpose();
    }
    setLoading(true);
    const response = await client.mutate(
      submitApproval({
        shareUri: share.shareUri
      })
    );

    if (!response.errors) {
      enqueueSnackbar('Share request submitted', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);

    if (onApply) {
      onApply();
    }
  };

  const draftRequest = async () => {
    setStep(0);
    if (requestPurpose !== share.requestPurpose) {
      await updateRequestPurpose();
    }
    if (onApply) {
      onApply();
    }
    navigate(`/console/shares/${share.shareUri}`);
  };

  const getExplanation = (status) => {
    const descriptions = {
      Draft:
        'The request for the selected principal is currently in draft status. You can edit and submit the request for approval.',
      Approved:
        'The request for the selected principal has already been approved by the data owner. You can make changes after the request is processed. Track its progress in the Shares menu on the left or click the "View share" button.',
      Rejected:
        'The request for the selected principal has already been rejected by the data owner. You can make changes and submit the request again. For more information, click the "View share" button.',
      Submitted:
        'The request for the selected principal has already been submitted for approval. You can edit the request. For more information, click the "View share" button.',
      Processed:
        'Request for the selected principal was already created and processed. You can make changes and submit request again. For more information click the button "View share".',
      Revoked:
        'The access for the selected principal has been revoked. A request to revoke access is currently in progress.  Track its progress in the Shares menu on the left or click the "View share" button.',
      Revoke_In_Progress:
        'The access for the selected principal has been revoked. A request to revoke access is currently in progress. Track its progress in the Shares menu on the left or click the "View share" button.',
      Share_In_Progress:
        'A request to share data with the selected principal is currently in progress. Track its progress in the Shares menu on the left or click the "View share" button.'
    };
    return descriptions[status];
  };
  const updateRequestPurpose = async () => {
    const response = await client.mutate(
      updateShareRequestReason({
        shareUri: share.shareUri,
        requestPurpose: requestPurpose
      })
    );
    if (!response.errors) {
      enqueueSnackbar('Share request reason updated', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };

  const fetchShareItems = async () => {
    setLoading(true);

    const response = await client.query(
      getShareObject({
        shareUri: share.shareUri,
        filter: {
          ...filter
        }
      })
    );
    if (!response.errors) {
      setShare(response.data.getShareObject);
      setSharedItems({ ...response.data.getShareObject.items });
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  };

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      let response;

      if (hit.resourceKind === 'dashboard') {
        response = await client.mutate(
          requestDashboardShare(hit._id, values.groupUri)
        );
      } else {
        response = await client.mutate(
          createShareObject(formRequestObject(values))
        );
      }

      if (response && !response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        enqueueSnackbar('Draft share request created', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        fetchShareObject(response.data.createShareObject.shareUri);
        setStep(1);
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

  if (!hit || loadingEnvs) {
    return null;
  }

  const handlePageChange = async (event, value) => {
    if (value <= sharedItems.pages && value !== sharedItems.page) {
      await setFilter({ ...filter, isShared: true, page: value });
    }
  };

  return (
    <Dialog maxWidth="md" fullWidth onClose={onClose} open={open} {...other}>
      {step === 0 && !loading && (
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
            Data access is requested for the whole requester Team or for the
            selected Consumption role. The request will be submitted to the data
            owners, track its progress in the Shares menu on the left.
          </Typography>
          <Box sx={{ p: 3 }}>
            <Formik
              initialValues={{
                environment: '',
                comment: '',
                attachMissingPolicies: false
              }}
              validationSchema={Yup.object().shape({
                environment: Yup.object().required('*Environment is required'),
                groupUri: Yup.string().required('*Team is required'),
                consumptionRole: Yup.string(),
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
                      {hit.resourceKind === 'table' && (
                        <TextField
                          fullWidth
                          disabled
                          label="Table name"
                          name="table"
                          value={hit.label}
                          variant="outlined"
                        />
                      )}
                      {hit.resourceKind === 'folder' && (
                        <TextField
                          fullWidth
                          disabled
                          label="Folder name"
                          name="folder"
                          value={hit.label}
                          variant="outlined"
                        />
                      )}
                      {hit.resourceKind === 'dataset' && (
                        <TextField
                          fullWidth
                          disabled
                          label="Dataset name"
                          name="dataset"
                          value={hit.label}
                          variant="outlined"
                        />
                      )}
                      {hit.resourceKind === 'dashboard' && (
                        <TextField
                          fullWidth
                          disabled
                          label="Dashboard name"
                          name="dashboard"
                          value={hit.label}
                          variant="outlined"
                        />
                      )}
                    </CardContent>
                    {hit.resourceKind !== 'dashboard' && (
                      <Box>
                        <CardContent>
                          <TextField
                            fullWidth
                            error={Boolean(
                              touched.environment && errors.environment
                            )}
                            helperText={
                              touched.environment && errors.environment
                            }
                            label="Environment"
                            name="environment"
                            onChange={(event) => {
                              setFieldValue('groupUri', '');
                              setFieldValue('consumptionRole', '');
                              fetchGroups(
                                event.target.value.environmentUri
                              ).catch((e) =>
                                dispatch({ type: SET_ERROR, error: e.message })
                              );
                              setFieldValue('environment', event.target.value);
                            }}
                            select
                            value={values.environment}
                            variant="outlined"
                          >
                            {environmentOptions.map((environment) => (
                              <MenuItem
                                key={environment.environmentUri}
                                value={environment}
                              >
                                {environment.label}
                              </MenuItem>
                            ))}
                          </TextField>
                        </CardContent>
                        <CardContent>
                          {loadingGroups ? (
                            <CircularProgress size={10} />
                          ) : (
                            <Box>
                              {groupOptions.length > 0 ? (
                                <TextField
                                  error={Boolean(
                                    touched.groupUri && errors.groupUri
                                  )}
                                  helperText={
                                    touched.groupUri && errors.groupUri
                                  }
                                  fullWidth
                                  label="Requesters Team"
                                  name="groupUri"
                                  onChange={(event) => {
                                    setFieldValue('consumptionRole', '');
                                    fetchRoles(
                                      values.environment.environmentUri,
                                      event.target.value
                                    ).catch((e) =>
                                      dispatch({
                                        type: SET_ERROR,
                                        error: e.message
                                      })
                                    );
                                    setFieldValue(
                                      'groupUri',
                                      event.target.value
                                    );
                                  }}
                                  select
                                  value={values.groupUri}
                                  variant="outlined"
                                >
                                  {groupOptions.map((group) => (
                                    <MenuItem
                                      key={group.value}
                                      value={group.value}
                                    >
                                      {group.label}
                                    </MenuItem>
                                  ))}
                                </TextField>
                              ) : (
                                <TextField
                                  error={Boolean(
                                    touched.groupUri && errors.groupUri
                                  )}
                                  helperText={
                                    touched.groupUri && errors.groupUri
                                  }
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
                          {loadingRoles ? (
                            <CircularProgress size={10} />
                          ) : (
                            <Box>
                              {roleOptions.length > 0 ? (
                                <TextField
                                  error={Boolean(
                                    touched.consumptionRole &&
                                      errors.consumptionRole
                                  )}
                                  helperText={
                                    touched.consumptionRole &&
                                    errors.consumptionRole
                                  }
                                  fullWidth
                                  label="Consumption Role (optional)"
                                  name="consumptionRole"
                                  onChange={(event) => {
                                    setFieldValue(
                                      'consumptionRole',
                                      event.target.value.value
                                    );
                                    setFieldValue(
                                      'consumptionRoleObj',
                                      event.target.value
                                    );
                                    fetchRolePolicies(
                                      values.environment.environmentUri,
                                      event.target.value.IAMRoleName
                                    ).catch((e) =>
                                      dispatch({
                                        type: SET_ERROR,
                                        error: e.message
                                      })
                                    );
                                  }}
                                  select
                                  value={values.consumptionRoleObj}
                                  variant="outlined"
                                >
                                  {roleOptions.map((role) => (
                                    <MenuItem key={role.value} value={role}>
                                      {role.label}
                                    </MenuItem>
                                  ))}
                                </TextField>
                              ) : (
                                <TextField
                                  error={Boolean(
                                    touched.consumptionRole &&
                                      errors.consumptionRole
                                  )}
                                  helperText={
                                    touched.consumptionRole &&
                                    errors.consumptionRole
                                  }
                                  fullWidth
                                  disabled
                                  label="Consumption Role (optional)"
                                  value="No additional consumption roles owned by this Team in this Environment."
                                  variant="outlined"
                                />
                              )}
                            </Box>
                          )}
                        </CardContent>
                      </Box>
                    )}
                    {!values.consumptionRole ||
                    values.consumptionRoleObj.dataallManaged ||
                    isSharePolicyAttached ? (
                      <Box />
                    ) : (
                      <CardContent sx={{ ml: 2 }}>
                        <FormControlLabel
                          control={
                            <Switch
                              checked={values.attachMissingPolicies}
                              onChange={handleChange}
                              color="primary"
                              edge="start"
                              name="attachMissingPolicies"
                            />
                          }
                          label={
                            <div>
                              Let Data.All attach policies to this role
                              <Typography
                                color="textSecondary"
                                component="p"
                                variant="caption"
                              ></Typography>
                              {values.consumptionRoleObj &&
                              !(
                                values.consumptionRoleObj.dataallManaged ||
                                isSharePolicyAttached ||
                                values.attachMissingPolicies
                              ) ? (
                                <FormHelperText error>
                                  Selected consumption role is managed by
                                  customer, but the share policy{' '}
                                  <strong>{policyName}</strong> is not attached.
                                  <br />
                                  Please attach it or let Data.all attach it for
                                  you.
                                </FormHelperText>
                              ) : (
                                ''
                              )}
                            </div>
                          }
                        />
                      </CardContent>
                    )}
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
                          200 - values.comment.length
                        } characters left`}
                        label="Request purpose"
                        name="comment"
                        multiline
                        onBlur={handleBlur}
                        onChange={handleChange}
                        rows={3}
                        value={values.comment}
                        variant="outlined"
                      />
                      {touched.comment && errors.comment && (
                        <Box sx={{ mt: 2 }}>
                          <FormHelperText error>
                            {errors.comment}
                          </FormHelperText>
                        </Box>
                      )}
                    </CardContent>
                  </Box>
                  <CardContent>
                    <LoadingButton
                      fullWidth
                      startIcon={<SendIcon fontSize="small" />}
                      color="primary"
                      disabled={
                        isSubmitting ||
                        (values.consumptionRoleObj &&
                          !(
                            values.consumptionRoleObj.dataallManaged ||
                            isSharePolicyAttached ||
                            values.attachMissingPolicies
                          ))
                      }
                      type="submit"
                      variant="contained"
                    >
                      Create Request
                    </LoadingButton>

                    <Button
                      sx={{ mt: 2 }}
                      onClick={onApply}
                      fullWidth
                      color="primary"
                      variant="outlined"
                    >
                      Cancel
                    </Button>
                  </CardContent>
                </form>
              )}
            </Formik>
          </Box>
        </Box>
      )}
      {step === 1 && !loading && (
        <Box sx={{ p: 3, minHeight: 800 }}>
          <Typography
            align="center"
            color="textPrimary"
            gutterBottom
            variant="h4"
          >
            Share status: {share.status}
          </Typography>
          <Typography align="center" color="textSecondary" variant="subtitle2">
            {getExplanation(share.status)}
          </Typography>
          <Box>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Type</TableCell>
                  <TableCell>Name</TableCell>
                  <TableCell>Status</TableCell>
                  {(share.status === 'Draft' ||
                    share.status === 'Processed' ||
                    share.status === 'Rejected' ||
                    share.status === 'Submitted') && (
                    <TableCell>Action</TableCell>
                  )}
                </TableRow>
              </TableHead>
              <TableBody>
                {sharedItems.nodes.length > 0 ? (
                  sharedItems.nodes.map((sharedItem) => (
                    <ItemRow
                      share={share}
                      item={sharedItem}
                      dispatch={dispatch}
                      enqueueSnackbar={enqueueSnackbar}
                      onAction={fetchShareItems}
                      client={client}
                    ></ItemRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell>No items added.</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
            {sharedItems.nodes.length > 0 && (
              <Pager
                mgTop={2}
                mgBottom={2}
                items={sharedItems}
                onChange={handlePageChange}
              />
            )}
            <Box>
              <CardContent>
                <TextField
                  FormHelperTextProps={{
                    sx: {
                      textAlign: 'right',
                      mr: 0
                    }
                  }}
                  fullWidth
                  helperText={`${200 - requestPurpose.length} characters left`}
                  label="Request purpose"
                  name="requestPurpose"
                  multiline
                  rows={5}
                  disabled={
                    share.status !== 'Draft' &&
                    share.status !== 'Processed' &&
                    share.status !== 'Rejected' &&
                    share.status !== 'Submitted'
                  }
                  value={requestPurpose}
                  variant="outlined"
                  onChange={(event) => {
                    setRequestPurpose(event.target.value);
                  }}
                />
              </CardContent>
            </Box>
          </Box>
          {share.status.toUpperCase() === 'DRAFT' && (
            <CardContent>
              <Button
                onClick={sendRequest}
                fullWidth
                startIcon={<SendIcon fontSize="small" />}
                color="primary"
                variant="contained"
              >
                Submit request
              </Button>
            </CardContent>
          )}
          {share.status.toUpperCase() === 'DRAFT' && (
            <CardContent>
              <Button
                onClick={draftRequest}
                fullWidth
                color="primary"
                variant="outlined"
              >
                Draft request
              </Button>
            </CardContent>
          )}
          {share.status.toUpperCase() !== 'DRAFT' && (
            <CardContent>
              <Button
                onClick={draftRequest}
                fullWidth
                color="primary"
                variant="contained"
              >
                View share
              </Button>
            </CardContent>
          )}
          {share.status.toUpperCase() !== 'DRAFT' && (
            <CardContent>
              <Button
                onClick={onApply}
                fullWidth
                color="primary"
                variant="outlined"
              >
                Cancel
              </Button>
            </CardContent>
          )}
        </Box>
      )}
      {loading && (
        <Box sx={{ p: 3, minHeight: 800 }}>
          <CircularProgress sx={{ mt: '25%', ml: '40%' }} size={140} />
        </Box>
      )}
    </Dialog>
  );
};

RequestAccessModal.propTypes = {
  hit: PropTypes.object.isRequired,
  onApply: PropTypes.func,
  onClose: PropTypes.func,
  open: PropTypes.bool.isRequired,
  stopLoader: PropTypes.func
};
