import {
  Alert,
  Box,
  Button,
  CardContent,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Tooltip,
  TextField,
  Typography,
  Collapse,
  FormControlLabel,
  FormGroup
} from '@mui/material';
import {
  ArrowRightIcon,
  Defaults,
  Label,
  Pager,
  ShareHealthStatus,
  ShareStatus
} from 'design';
import SendIcon from '@mui/icons-material/Send';
import React, { useCallback, useEffect, useState } from 'react';
import {
  addSharedItem,
  getShareObject,
  removeSharedItem,
  revokeItemsShareObject,
  submitShareObject,
  updateShareRequestReason,
  updateShareExpirationPeriod,
  submitExtension
} from '../../Shares/services';
import { SET_ERROR } from 'globalErrors';
import { DeleteOutlined } from '@mui/icons-material';
import PropTypes from 'prop-types';
import { useNavigate, useLocation } from 'react-router-dom';
import EditIcon from '@mui/icons-material/Edit';
import Checkbox from '@mui/material/Checkbox';

const ItemRow = (props) => {
  const {
    share,
    shareStatus,
    item,
    onAction,
    onLoadingStart,
    onLoadingEnd,
    enqueueSnackbar,
    dispatch,
    client
  } = props;

  const whatToDo = () => {
    if (!item.status && shareStatus !== 'Revoked') return 'Request';
    if (
      item.status === 'Revoke_Succeeded' ||
      item.status === 'PendingApproval' ||
      item.status === 'Share_Rejected' ||
      item.status === 'Share_Failed'
    )
      return 'Delete';
    if (
      (item.status === 'Share_Succeeded' || item.status === 'Revoke_Failed') &&
      item.healthStatus !== 'PendingReApply'
    )
      return 'Revoke';
    return 'Nothing';
  };

  const possibleAction = whatToDo();

  const removeShareItem = async () => {
    onLoadingStart();
    const response = await client.mutate(
      removeSharedItem({ shareItemUri: item.shareItemUri })
    );
    onLoadingEnd();
    if (!response.errors) {
      enqueueSnackbar('Item removed', {
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
    onLoadingStart();
    const response = await client.mutate(
      revokeItemsShareObject({
        input: {
          shareUri: share.shareUri,
          itemUris: [item.shareItemUri]
        }
      })
    );
    onLoadingEnd();
    if (!response.errors) {
      enqueueSnackbar('Item revoked', {
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
    onLoadingStart();
    const response = await client.mutate(
      addSharedItem({
        shareUri: share.shareUri,
        input: {
          itemUri: item.itemUri,
          itemType: item.itemType
        }
      })
    );
    onLoadingEnd();
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
      <TableCell>
        {item.status ? (
          <ShareHealthStatus
            status={item.status}
            healthStatus={item.healthStatus}
            lastVerificationTime={item.lastVerificationTime}
          />
        ) : (
          'Not requested'
        )}
      </TableCell>
      {(shareStatus === 'Draft' ||
        shareStatus === 'Processed' ||
        shareStatus === 'Rejected' ||
        shareStatus === 'Revoked' ||
        shareStatus === 'Submitted' ||
        shareStatus === 'Extension_Rejected') && (
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
              Include
            </Button>
          )}
          {possibleAction === 'Nothing' && (
            <Typography color="textSecondary" variant="subtitle2">
              Wait until this item is processed and/or re-apply task is complete
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

export const ShareEditForm = (props) => {
  const {
    share,
    alreadyExisted,
    dispatch,
    enqueueSnackbar,
    client,
    onApply,
    onCancel,
    showViewShare
  } = props;
  const navigate = useNavigate();
  const location = useLocation();
  const [sharedItems, setSharedItems] = useState(Defaults.pagedResponse);
  const [shareStatus, setShareStatus] = useState('');
  const [filter, setFilter] = useState(Defaults.filter);
  const [loading, setLoading] = useState(false);
  const [requestPurpose, setRequestPurpose] = useState('');
  const [smthChanged, setSmthChanged] = useState(false);
  const [editShareExpiration, setEditShareExpiration] = useState(false);
  const [editShareExtension, setEditShareExtension] = useState(false);
  const [shareExpiration, setShareExpiration] = useState(0);
  const [shareExtensionReason, setShareExtensionReason] = useState('');
  const [requestNonExpirableShare, setNonExpirableShare] = useState(
    share.nonExpirable
  );

  const canUpdateRequestPurpose = () => {
    return (
      (share.userRoleForShareObject === 'Requesters' ||
        share.userRoleForShareObject === 'ApproversAndRequesters') &&
      (share.status === 'Draft' ||
        share.status === 'Processed' ||
        share.status === 'Rejected' ||
        share.status === 'Submitted')
    );
  };

  const handlePageChange = async (event, value) => {
    if (value <= sharedItems.pages && value !== sharedItems.page) {
      await setFilter({ ...filter, page: value });
    }
  };

  const beforeClose = async () => {
    if (requestPurpose !== share.requestPurpose) {
      await updateRequestPurpose();
    }

    const isExpirationUpdated =
      (shareExpiration &&
        shareExpiration !== 0 &&
        share.shareExpirationPeriod !== shareExpiration) ||
      share.nonExpirable !== requestNonExpirableShare;

    if (isExpirationUpdated) {
      await updateShareExpiration();
    }
    if (
      smthChanged ||
      requestPurpose !== share.requestPurpose ||
      (shareExpiration && shareExpiration !== 0)
    ) {
      onApply();
    } else {
      onCancel();
    }
  };

  const sendRequest = async () => {
    if (requestPurpose !== share.requestPurpose) {
      await updateRequestPurpose();
    }

    const isExpirationUpdated =
      (shareExpiration &&
        shareExpiration !== 0 &&
        share.shareExpirationPeriod !== shareExpiration) ||
      share.nonExpirable !== requestNonExpirableShare;

    if (isExpirationUpdated) {
      await updateShareExpiration();
    }

    setLoading(true);
    const response = await client.mutate(
      submitShareObject({
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
    const targetPath = `/console/shares/${share.shareUri}`;
    if (location.pathname !== targetPath) {
      navigate(targetPath);
    }
  };

  const sendShareExtensionRequest = async () => {
    setLoading(true);
    const response = await client.mutate(
      submitExtension({
        shareUri: share.shareUri,
        expiration: shareExpiration,
        extensionReason: shareExtensionReason,
        nonExpirable: requestNonExpirableShare
      })
    );

    if (!response.errors) {
      enqueueSnackbar('Share extension request submitted', {
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
    if (requestPurpose !== share.requestPurpose) {
      await updateRequestPurpose();
    }

    const isExpirationUpdated =
      (shareExpiration &&
        shareExpiration !== 0 &&
        share.shareExpirationPeriod !== shareExpiration) ||
      share.nonExpirable !== requestNonExpirableShare;

    if (isExpirationUpdated) {
      await updateShareExpiration();
    }
    if (onApply) {
      onApply();
    }
    navigate(`/console/shares/${share.shareUri}`);
  };

  const getExplanation = (status) => {
    const track_progress_str = showViewShare
      ? ' Track its progress in the Shares menu on the left or click the "View share" button.'
      : '';
    const more_info_str = showViewShare
      ? ' For more information, click the "View share" button.'
      : '';

    const descriptions = {
      Draft:
        'The request for the selected principal is currently in draft status. You can edit and submit the request for approval.',
      Approved:
        'The request for the selected principal has already been approved by the data owner. You can make changes after the request is processed.' +
        track_progress_str,
      Rejected:
        'The request for the selected principal has already been rejected by the data owner. You can make changes and submit the request again.' +
        more_info_str,
      Submitted:
        'The request for the selected principal has already been submitted for approval. You can edit the request.' +
        more_info_str,
      Processed:
        'Request for the selected principal was already created and processed. You can make changes and submit request again. For more information click the button "View share".',
      Revoked:
        'The access for the selected principal has been revoked. A request to revoke access is currently in progress.' +
        track_progress_str,
      Revoke_In_Progress:
        'The access for the selected principal has been revoked. A request to revoke access is currently in progress.' +
        track_progress_str,
      Share_In_Progress:
        'A request to share data with the selected principal is currently in progress. ' +
        track_progress_str
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

  const updateShareExpiration = async () => {
    try {
      const response = await client.mutate(
        updateShareExpirationPeriod({
          shareUri: share.shareUri,
          expiration: shareExpiration,
          nonExpirable: requestNonExpirableShare
        })
      );
      if (!response.errors) {
        enqueueSnackbar('Share Expiration updated', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e });
    }
  };

  const fetchShareItems = useCallback(async () => {
    setLoading(true);

    const response = await client.query(
      getShareObject({
        shareUri: share.shareUri,
        filter: {
          ...filter,
          pageSize: 5
        }
      })
    );
    if (!response.errors) {
      setSharedItems({ ...response.data.getShareObject.items });
      setShareStatus(response.data.getShareObject.status);
      if (
        response.data.getShareObject.items.nodes.filter(
          (node) => node.status === 'PendingApproval'
        ).length > 0
      ) {
        setEditShareExpiration(false);
      }
      if (response.data.getShareObject.extensionReason) {
        setShareExtensionReason(response.data.getShareObject.extensionReason);
      }
      setSmthChanged(true);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [client, filter, dispatch]);

  useEffect(() => {
    if (client) {
      fetchShareItems()
        .then((resp) => {
          setSmthChanged(false);
        })
        .catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
      setShareStatus(share.status);
      setShareExpiration(share.shareExpirationPeriod);
      setRequestPurpose(share.requestPurpose);
    }
  }, [client, fetchShareItems, dispatch, share]);

  const handleOpenEditCollapsableWindow = async (extension = false) => {
    if (extension) {
      setEditShareExtension(!editShareExtension);
    }
    setEditShareExpiration(!editShareExpiration);
  };

  const checkPendingShareItemsStateForEditExpiration = (sharedItems) => {
    const numberOfPendingApprovalShareItems = sharedItems.nodes.filter(
      (node) => node.status === 'PendingApproval'
    ).length;

    const numberOfSharedItems = sharedItems.nodes.length;

    const numberOfItemWithPendingActionsOrCompletedShares =
      sharedItems.nodes.filter(
        (node) =>
          node.status === 'Share_Succeeded' ||
          node.status === 'Share_In_Progress' ||
          node.status === 'Revoke_In_Progress'
      ).length;

    const numberOfPendingExtensionShareItems = sharedItems.nodes.filter(
      (node) => node.status === 'PendingExtension'
    ).length;

    if (numberOfPendingExtensionShareItems === numberOfSharedItems) return true;

    if (numberOfItemWithPendingActionsOrCompletedShares > 0) return false;

    if (
      numberOfPendingApprovalShareItems > 0 &&
      numberOfItemWithPendingActionsOrCompletedShares === 0
    )
      return true;
  };

  if (loading) {
    return (
      <Box sx={{ p: 3, minHeight: 800 }}>
        <CircularProgress sx={{ mt: '25%', ml: '40%' }} size={140} />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3, minHeight: 800 }}>
      <Typography align="center" color="textPrimary" gutterBottom variant="h4">
        Share status: {shareStatus}
      </Typography>
      {alreadyExisted && (
        <Typography align="center" color="red" variant="subtitle2">
          Share object for the selected principal and target already exists.
        </Typography>
      )}
      <Typography align="center" color="textSecondary" variant="subtitle2">
        {getExplanation(shareStatus)}
      </Typography>
      <Box>
        <Box sx={{ p: 1 }}>
          {sharedItems.nodes.find((item) => item.itemType === 'S3Bucket') && (
            <Alert severity="warning" gutterBottom sx={{ mr: 1 }}>
              Sharing S3Bucket gives Requestor read access to{' '}
              <b>the entire S3 Bucket</b> superseding Folder shares and
              providing potential workarounds for Table access
            </Alert>
          )}
        </Box>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Type</TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Health Status</TableCell>
              {(shareStatus === 'Draft' ||
                shareStatus === 'Processed' ||
                shareStatus === 'Rejected' ||
                shareStatus === 'Submitted' ||
                shareStatus === 'Extension_Rejected') && (
                <TableCell>Action</TableCell>
              )}
            </TableRow>
          </TableHead>
          <TableBody>
            {sharedItems.nodes.length > 0 ? (
              sharedItems.nodes.map((sharedItem) => (
                <ItemRow
                  share={share}
                  shareStatus={shareStatus}
                  item={sharedItem}
                  dispatch={dispatch}
                  enqueueSnackbar={enqueueSnackbar}
                  onAction={fetchShareItems}
                  onLoadingStart={() => {
                    setLoading(true);
                  }}
                  onLoadingEnd={() => {
                    setLoading(false);
                  }}
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
              rows={3}
              disabled={!canUpdateRequestPurpose()}
              value={requestPurpose}
              variant="outlined"
              onChange={(event) => {
                setRequestPurpose(event.target.value);
              }}
            />
          </CardContent>
          {share.dataset.enableExpiration && (
            <CardContent>
              <Box display="flex" alignItems="center">
                {share.expiryDate != null && (
                  <Typography
                    sx={{ flexGrow: 1 }}
                    color="red"
                    variant="subtitle2"
                  >
                    Current Share Expiration Date :{' '}
                    <Label color={'primary'}>
                      {new Date(share.expiryDate).toDateString()}
                    </Label>
                  </Typography>
                )}
                {share.requestedExpiryDate != null && (
                  <Typography
                    sx={{ flexGrow: 1 }}
                    color="red"
                    variant="subtitle2"
                  >
                    Requested Share Expiration Date :{' '}
                    <Label color={'warning'}>
                      {new Date(share.requestedExpiryDate).toDateString()}
                    </Label>
                  </Typography>
                )}

                {(share.status === 'Submitted' ||
                  share.status === 'Draft' ||
                  share.status === 'Submitted_For_Extension' ||
                  share.status === 'Rejected') &&
                  checkPendingShareItemsStateForEditExpiration(sharedItems) && (
                    <Button
                      color="primary"
                      startIcon={<EditIcon fontSize="small" />}
                      variant="outlined"
                      onClick={() => {
                        handleOpenEditCollapsableWindow(false);
                      }}
                    >
                      Edit Share Expiration
                    </Button>
                  )}
                {(share.status === 'Draft' ||
                  share.status === 'Processed' ||
                  share.status === 'Extension_Rejected' ||
                  share.status === 'Rejected') &&
                  sharedItems.nodes.filter(
                    (node) => node.status === 'PendingApproval'
                  ).length === 0 &&
                  sharedItems.nodes.filter(
                    (node) => node.status === 'Share_Succeeded'
                  ).length > 0 && (
                    <Button
                      color="primary"
                      startIcon={<ArrowRightIcon fontSize="small" />}
                      variant="outlined"
                      onClick={() => {
                        handleOpenEditCollapsableWindow(true);
                      }}
                    >
                      {share.nonExpirable
                        ? 'Change Expiration'
                        : 'Extend Share Request'}
                    </Button>
                  )}
              </Box>
              <Collapse in={editShareExpiration}>
                <Box sx={{ mt: 2 }}>
                  <TextField
                    fullWidth
                    label={`Share Expiration Period - Request access for dataset in ${
                      share.dataset.expirySetting === 'Monthly'
                        ? 'month(s)'
                        : 'quarter(s)'
                    }`}
                    variant="outlined"
                    inputProps={{ type: 'number' }}
                    onChange={(event) => {
                      setShareExpiration(parseInt(event.target.value));
                    }}
                    disabled={requestNonExpirableShare}
                    value={shareExpiration}
                  />
                </Box>
                <Box sx={{ m: 1 }}>
                  <FormGroup>
                    <FormControlLabel
                      variant="outlined"
                      label={'Request non-expiring share for this dataset'}
                      control={
                        <Checkbox
                          defaultChecked={share.nonExpirable}
                          onChange={(event, value) => {
                            setNonExpirableShare(value);
                          }}
                        />
                      }
                    />
                  </FormGroup>
                </Box>
                {(share.status === 'Draft' ||
                  share.status === 'Processed' ||
                  share.status === 'Extension_Rejected' ||
                  share.status === 'Rejected') &&
                  sharedItems.nodes.filter(
                    (node) => node.status === 'PendingApproval'
                  ).length === 0 &&
                  sharedItems.nodes.filter(
                    (node) => node.status === 'Share_Succeeded'
                  ).length > 0 && (
                    <Box sx={{ mt: 2 }}>
                      <TextField
                        FormHelperTextProps={{
                          sx: {
                            textAlign: 'right',
                            mr: 0
                          }
                        }}
                        fullWidth
                        helperText={`${
                          200 - shareExtensionReason.length
                        } characters left`}
                        label="Extension reason"
                        name="extensionReason"
                        multiline
                        rows={3}
                        value={shareExtensionReason}
                        variant="outlined"
                        onChange={(event) => {
                          setShareExtensionReason(event.target.value);
                        }}
                      />
                      <Button
                        onClick={sendShareExtensionRequest}
                        fullWidth
                        startIcon={<SendIcon fontSize="small" />}
                        color="primary"
                        variant="contained"
                      >
                        Submit Extension Request
                      </Button>
                    </Box>
                  )}
              </Collapse>
            </CardContent>
          )}
        </Box>
      </Box>
      {shareStatus.toUpperCase() === 'DRAFT' &&
        (share.userRoleForShareObject === 'Requesters' ||
          share.userRoleForShareObject === 'ApproversAndRequesters') &&
        !editShareExtension && (
          <CardContent>
            <Tooltip
              title={
                sharedItems.nodes.filter((item) => item.status).length === 0
                  ? 'There is no items added into the request.'
                  : ''
              }
            >
              <span>
                <Button
                  onClick={sendRequest}
                  fullWidth
                  startIcon={<SendIcon fontSize="small" />}
                  color="primary"
                  variant="contained"
                  disabled={
                    sharedItems.nodes.filter((item) => item.status).length === 0
                  }
                >
                  Submit request
                </Button>
              </span>
            </Tooltip>
          </CardContent>
        )}
      {shareStatus.toUpperCase() === 'DRAFT' && (
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
      {shareStatus.toUpperCase() !== 'DRAFT' && showViewShare && (
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

      {shareStatus.toUpperCase() !== 'DRAFT' && (
        <CardContent>
          <Button
            onClick={beforeClose}
            fullWidth
            color="primary"
            variant="outlined"
          >
            Save & Close
          </Button>
        </CardContent>
      )}
    </Box>
  );
};
