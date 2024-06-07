import {
  Box,
  Button,
  CardContent,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography
} from '@mui/material';
import { Defaults, Pager, ShareStatus } from '../../../design';
import SendIcon from '@mui/icons-material/Send';
import React, { useCallback, useEffect, useState } from 'react';
import {
  addSharedItem,
  getShareObject,
  removeSharedItem,
  revokeItemsShareObject,
  submitApproval,
  updateShareRequestReason
} from '../../Shares/services';
import { SET_ERROR } from '../../../globalErrors';
import { DeleteOutlined } from '@mui/icons-material';
import PropTypes from 'prop-types';
import { useNavigate } from 'react-router-dom';

const ItemRow = (props) => {
  const {
    share,
    shareStatus,
    item,
    onAction,
    enqueueSnackbar,
    dispatch,
    client
  } = props;

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
    const response = await client.mutate(
      revokeItemsShareObject({
        input: {
          shareUri: share.shareUri,
          itemUris: [item.shareItemUri]
        }
      })
    );

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
      {(shareStatus === 'Draft' ||
        shareStatus === 'Processed' ||
        shareStatus === 'Rejected' ||
        shareStatus === 'Submitted') && (
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

export const ShareEditForm = (props) => {
  const {
    share,
    dispatch,
    enqueueSnackbar,
    client,
    onApply,
    onCancel,
    showViewShare
  } = props;
  const navigate = useNavigate();
  const [sharedItems, setSharedItems] = useState(Defaults.pagedResponse);
  const [shareStatus, setShareStatus] = useState('');
  const [filter, setFilter] = useState(Defaults.filter);
  const [loading, setLoading] = useState(false);
  const [requestPurpose, setRequestPurpose] = useState('');

  const handlePageChange = async (event, value) => {
    if (value <= sharedItems.pages && value !== sharedItems.page) {
      await setFilter({ ...filter, isShared: true, page: value });
    }
  };

  const sendRequest = async () => {
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
    if (requestPurpose !== share.requestPurpose) {
      await updateRequestPurpose();
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

  const fetchShareItems = useCallback(async () => {
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
      setSharedItems({ ...response.data.getShareObject.items });
      setShareStatus(response.data.getShareObject.status);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [client, share, dispatch]);

  useEffect(() => {
    if (client) {
      fetchShareItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
      setShareStatus(share.status);
      setRequestPurpose(share.requestPurpose);
    }
  }, [client, fetchShareItems, dispatch, share]);

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
      <Typography align="center" color="textSecondary" variant="subtitle2">
        {getExplanation(shareStatus)}
      </Typography>
      <Box>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Type</TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Status</TableCell>
              {(shareStatus === 'Draft' ||
                shareStatus === 'Processed' ||
                shareStatus === 'Rejected' ||
                shareStatus === 'Submitted') && <TableCell>Action</TableCell>}
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
              disabled={
                shareStatus !== 'Draft' &&
                shareStatus !== 'Processed' &&
                shareStatus !== 'Rejected' &&
                shareStatus !== 'Submitted'
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
      {shareStatus.toUpperCase() === 'DRAFT' && (
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
            onClick={onCancel}
            fullWidth
            color="primary"
            variant="outlined"
          >
            Close
          </Button>
        </CardContent>
      )}
    </Box>
  );
};