import {
  Article,
  BlockOutlined,
  CheckCircleOutlined,
  DeleteOutlined,
  Warning,
  RefreshRounded
} from '@mui/icons-material';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import SecurityIcon from '@mui/icons-material/Security';
import { LoadingButton } from '@mui/lab';
import {
  Box,
  Breadcrumbs,
  Button,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Container,
  Divider,
  Dialog,
  DialogTitle,
  DialogActions,
  Grid,
  Link,
  List,
  ListItem,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Tooltip,
  Stack,
  Typography
} from '@mui/material';
import CircularProgress from '@mui/material/CircularProgress';
import FilterAltIcon from '@mui/icons-material/FilterAlt';
import { useSnackbar } from 'notistack';
import * as PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState, useRef } from 'react';
import { Helmet } from 'react-helmet-async';
import { useNavigate } from 'react-router';
import { Link as RouterLink, useParams } from 'react-router-dom';
import {
  ChevronRightIcon,
  Defaults,
  Pager,
  PencilAltIcon,
  Scrollbar,
  ShareStatus,
  ShareHealthStatus,
  TextAvatar,
  useSettings,
  Label,
  SanitizedHTML,
  UserModal
} from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import {
  approveShareObject,
  deleteShareObject,
  getShareObject,
  rejectShareObject,
  removeSharedItem,
  submitShareObject,
  revokeItemsShareObject,
  verifyItemsShareObject,
  reApplyItemsShareObject,
  getShareItemDataFilters,
  approveShareExtension,
  cancelShareExtension
} from '../services';
import {
  AddShareItemModal,
  S3ConsumptionData,
  ShareItemsSelectorModal,
  ShareRejectModal,
  UpdateRejectReason,
  UpdateRequestReason,
  ShareItemFilterModal
} from '../components';
import { generateShareItemLabel, createLinkMarkup } from 'utils';
import { ShareLogs } from '../components/ShareLogs';
import { ShareSubmitModal } from '../components/ShareSubmitModal';
import { useTheme } from '@mui/styles';
import { UpdateExtensionReason } from '../components/ShareUpdateExtension';
import CancelIcon from '@mui/icons-material/Close';

const isReadOnlyShare = (share) => share.permissions.every((p) => p === 'Read');

function ShareViewHeader(props) {
  const {
    share,
    sharedItems,
    client,
    dispatch,
    enqueueSnackbar,
    navigate,
    fetchItem,
    fetchItems,
    loading
  } = props;
  const [accepting, setAccepting] = useState(false);
  const [acceptingWarning, setAcceptingWarning] = useState(false);
  const [rejecting, setRejecting] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [cancellingExtension, setCancellingExtension] = useState(false);
  const [isRejectShareModalOpen, setIsRejectShareModalOpen] = useState(false);
  const [openLogsModal, setOpenLogsModal] = useState(null);
  const anchorRef = useRef(null);

  const [isSubmitShareModalOpen, setIsSubmitShareModalOpen] = useState(false);

  const datasetTypeLink =
    share.dataset.datasetType === 'DatasetTypes.S3'
      ? `s3-datasets`
      : share.dataset.datasetType === 'DatasetTypes.Redshift'
      ? `redshift-datasets`
      : '-';

  const submit = async () => {
    setSubmitting(true);
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
      await fetchItem();
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setSubmitting(false);
  };

  const remove = async () => {
    const response = await client.mutate(
      deleteShareObject({
        shareUri: share.shareUri
      })
    );

    if (!response.errors) {
      handleSubmitShareModalClose();
      enqueueSnackbar('Share request deleted', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      navigate('/console/shares');
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };

  const handleOpenLogsModal = () => {
    setOpenLogsModal(true);
  };
  const handleCloseOpenLogs = () => {
    setOpenLogsModal(false);
  };

  const handleRejectShareModalOpen = () => {
    setIsRejectShareModalOpen(true);
  };

  const handleRejectShareModalClose = () => {
    setIsRejectShareModalOpen(false);
  };

  const handleSubmitShareModalOpen = () => {
    setIsSubmitShareModalOpen(true);
  };

  const handleSubmitShareModalApplied = () => {
    setIsSubmitShareModalOpen(false);
    fetchItem();
    fetchItems();
  };

  const handleSubmitShareModalClose = () => {
    setIsSubmitShareModalOpen(false);
  };

  const handleApproveExtensionShare = async () => {
    setAccepting(true);
    const response = await client.mutate(
      approveShareExtension({
        shareUri: share.shareUri
      })
    );

    if (!response.errors) {
      enqueueSnackbar('Share Extension request approved', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      await fetchItems();
      await fetchItem();
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setAccepting(false);
  };

  const handleCancelShareExtensionRequest = async () => {
    setCancellingExtension(true);
    const response = await client.mutate(
      cancelShareExtension({
        shareUri: share.shareUri
      })
    );

    if (!response.errors) {
      enqueueSnackbar('Share Extension request cancelled', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      await fetchItems();
      await fetchItem();
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setCancellingExtension(false);
  };

  const handleApproveShare = async () => {
    setAccepting(true);
    const response = await client.mutate(
      approveShareObject({
        shareUri: share.shareUri
      })
    );

    if (!response.errors) {
      enqueueSnackbar('Share request approved', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      await fetchItems();
      await fetchItem();
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setAccepting(false);
  };

  const handleRejectShare = async (rejectPurpose) => {
    setRejecting(true);
    const response = await client.mutate(
      rejectShareObject({
        shareUri: share.shareUri,
        rejectPurpose: rejectPurpose
      })
    );

    if (!response.errors) {
      handleRejectShareModalClose();
      enqueueSnackbar('Share request rejected', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      await fetchItems();
      await fetchItem();
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setRejecting(false);
  };

  return (
    <>
      <Grid container justifyContent="space-between" spacing={3}>
        <Grid item>
          <Typography color="textPrimary" variant="h5">
            Share object for {share.dataset?.datasetName}{' '}
            {share.status === 'Draft' ? '(DRAFT)' : ''}
          </Typography>
          <Breadcrumbs
            aria-label="breadcrumb"
            separator={<ChevronRightIcon fontSize="small" />}
            sx={{ mt: 1 }}
          >
            <Link
              underline="hover"
              color="textPrimary"
              component={RouterLink}
              to="/console/shares"
              variant="subtitle2"
            >
              Shares
            </Link>
            <Link
              underline="hover"
              color="textPrimary"
              component={RouterLink}
              to="/console/shares"
              variant="subtitle2"
            >
              Shares
            </Link>
            <Typography
              color="textSecondary"
              variant="subtitle2"
              component={RouterLink}
              to={`/console/${datasetTypeLink}/${share.dataset?.datasetUri}`}
            >
              {share.dataset?.datasetName}
            </Typography>
          </Breadcrumbs>
        </Grid>
        <Grid item>
          {!loading && (
            <Box sx={{ m: -1 }}>
              <Button
                color="primary"
                startIcon={<RefreshRounded fontSize="small" />}
                sx={{ m: 1 }}
                variant="outlined"
                onClick={() => {
                  fetchItem();
                  fetchItems();
                }}
              >
                Refresh
              </Button>
              {share.canViewLogs && (
                <Button
                  color="primary"
                  startIcon={<Article fontSize="small" />}
                  sx={{ m: 1 }}
                  variant="outlined"
                  onClick={handleOpenLogsModal}
                >
                  Logs
                </Button>
              )}
              {(share.userRoleForShareObject === 'Approvers' ||
                share.userRoleForShareObject === 'ApproversAndRequesters') && (
                <>
                  {share.status === 'Submitted' && (
                    <>
                      <LoadingButton
                        loading={accepting}
                        color="success"
                        startIcon={<CheckCircleOutlined />}
                        sx={{ m: 1 }}
                        onClick={async () =>
                          isReadOnlyShare(share)
                            ? handleApproveShare()
                            : setAcceptingWarning(true)
                        }
                        ref={anchorRef}
                        type="button"
                        variant="outlined"
                      >
                        Approve
                      </LoadingButton>
                      <LoadingButton
                        loading={rejecting}
                        color="error"
                        sx={{ m: 1 }}
                        startIcon={<BlockOutlined />}
                        onClick={handleRejectShareModalOpen}
                        type="button"
                        variant="outlined"
                      >
                        Reject
                      </LoadingButton>
                      <Dialog
                        open={acceptingWarning}
                        onClose={async () => setAcceptingWarning(false)}
                      >
                        <DialogTitle>
                          Write or Modify permissions requested, do you want to
                          proceed with the Approval?
                        </DialogTitle>
                        <DialogActions>
                          <Button
                            onClick={async () => {
                              setAcceptingWarning(false);
                              handleApproveShare();
                            }}
                          >
                            Yes
                          </Button>
                          <Button
                            onClick={async () => setAcceptingWarning(false)}
                            autoFocus
                          >
                            No
                          </Button>
                        </DialogActions>
                      </Dialog>
                    </>
                  )}
                  {share.status === 'Submitted_For_Extension' && (
                    <>
                      <LoadingButton
                        loading={accepting}
                        color="success"
                        startIcon={<CheckCircleOutlined />}
                        sx={{ m: 1 }}
                        onClick={handleApproveExtensionShare}
                        type="button"
                        variant="outlined"
                      >
                        Approve Extension
                      </LoadingButton>
                      <LoadingButton
                        loading={rejecting}
                        color="error"
                        sx={{ m: 1 }}
                        startIcon={<BlockOutlined />}
                        onClick={handleRejectShareModalOpen}
                        type="button"
                        variant="outlined"
                      >
                        Reject Extension
                      </LoadingButton>
                    </>
                  )}
                </>
              )}
              <LoadingButton
                loading={submitting}
                color="primary"
                startIcon={<PencilAltIcon />}
                sx={{ m: 1 }}
                onClick={handleSubmitShareModalOpen}
                type="button"
                variant="outlined"
              >
                Edit
              </LoadingButton>
              {(share.userRoleForShareObject === 'Requesters' ||
                share.userRoleForShareObject === 'ApproversAndRequesters') && (
                <>
                  {share.status === 'Submitted_For_Extension' && (
                    <LoadingButton
                      loading={cancellingExtension}
                      color="primary"
                      startIcon={<CancelIcon />}
                      sx={{ m: 1 }}
                      onClick={handleCancelShareExtensionRequest}
                      type="button"
                      variant="outlined"
                    >
                      Cancel Extension
                    </LoadingButton>
                  )}
                </>
              )}
              {(share.userRoleForShareObject === 'Requesters' ||
                share.userRoleForShareObject === 'ApproversAndRequesters') && (
                <>
                  {(share.status === 'Draft' ||
                    share.status === 'Rejected') && (
                    <Tooltip
                      title={
                        sharedItems.nodes.length === 0
                          ? 'There is no items added into the request.'
                          : ''
                      }
                    >
                      <span>
                        <LoadingButton
                          loading={submitting}
                          color="primary"
                          startIcon={<CheckCircleOutlined />}
                          sx={{ m: 1 }}
                          onClick={submit}
                          type="button"
                          variant="contained"
                          disabled={sharedItems.nodes.length === 0}
                        >
                          Submit
                        </LoadingButton>
                      </span>
                    </Tooltip>
                  )}
                </>
              )}
              <Button
                color="primary"
                startIcon={<DeleteOutlined fontSize="small" />}
                sx={{ m: 1 }}
                variant="outlined"
                onClick={remove}
              >
                Delete
              </Button>
            </Box>
          )}
        </Grid>
      </Grid>
      {isRejectShareModalOpen && (
        <ShareRejectModal
          share={share}
          onApply={handleRejectShareModalClose}
          onClose={handleRejectShareModalClose}
          open={isRejectShareModalOpen}
          rejectFunction={handleRejectShare}
        />
      )}
      {isSubmitShareModalOpen && (
        <ShareSubmitModal
          share={share}
          onApply={handleSubmitShareModalApplied}
          onClose={handleSubmitShareModalClose}
          open={isSubmitShareModalOpen}
          submitFunction={submit}
          client={client}
          dispatch={dispatch}
          enqueueSnackbar={enqueueSnackbar}
          fetchItem={fetchItem}
          sharedItems={sharedItems}
        />
      )}
      {share.canViewLogs && (
        <ShareLogs
          shareUri={share.shareUri}
          onClose={handleCloseOpenLogs}
          open={openLogsModal && share.canViewLogs}
        />
      )}
    </>
  );
}

ShareViewHeader.propTypes = {
  share: PropTypes.any,
  client: PropTypes.any,
  dispatch: PropTypes.any,
  enqueueSnackbar: PropTypes.any,
  navigate: PropTypes.any,
  fetchItem: PropTypes.func,
  fetchItems: PropTypes.func,
  loading: PropTypes.bool
};

export function SharedItem(props) {
  const {
    item,
    share,
    client,
    dispatch,
    enqueueSnackbar,
    fetchShareItems,
    fetchItem
  } = props;
  const [isRemovingItem, setIsRemovingItem] = useState(false);
  const [isFilterModalOpenUri, setIsFilterModalOpenUri] = useState(0);
  const [isLoadingFilters, setIsLoadingFilters] = useState(false);
  const [itemDataFilter, setItemDataFilter] = useState(null);
  const [isAssignedFilterModalOpen, setIsAssignedFilterModalOpen] =
    useState('');

  const getItemDataFilters = async (attachedDataFilterUri) => {
    setIsLoadingFilters(true);
    try {
      const response = await client.query(
        getShareItemDataFilters({
          attachedDataFilterUri: attachedDataFilterUri
        })
      );
      if (!response.errors) {
        if (response.data && response.data.getShareItemDataFilters) {
          setItemDataFilter(response.data.getShareItemDataFilters);
        }
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    } finally {
      setIsLoadingFilters(false);
    }
  };

  useEffect(() => {
    if (client && item.itemType === 'Table' && item.attachedDataFilterUri) {
      getItemDataFilters(item.attachedDataFilterUri);
    }
  }, [client, item, dispatch]);

  const handleFilterModalClose = () => {
    setIsFilterModalOpenUri(0);
  };

  const handleFilterModalOpen = (uri) => {
    setIsFilterModalOpenUri(uri);
  };

  const handleAssignedFilterModalOpen = (label) => {
    setIsAssignedFilterModalOpen(label);
  };
  const handleAssignedFilterModalClose = () => {
    setIsAssignedFilterModalOpen('');
  };

  const removeItemFromShareObject = async () => {
    setIsRemovingItem(true);
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
      await fetchShareItems();
      await fetchItem();
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setIsRemovingItem(false);
  };

  return (
    <TableRow hover>
      <TableCell>{generateShareItemLabel(item.itemType)}</TableCell>
      <TableCell>{item.itemName}</TableCell>
      <TableCell>
        <ShareStatus status={item.status} />
      </TableCell>
      <TableCell>
        {isLoadingFilters ? (
          <CircularProgress size={15} />
        ) : (
          <>
            {itemDataFilter &&
              itemDataFilter?.dataFilterNames &&
              itemDataFilter?.dataFilterNames.length > 0 && (
                <Button
                  color="primary"
                  startIcon={<OpenInNewIcon fontSize="small" />}
                  sx={{ mr: 1 }}
                  variant="outlined"
                  onClick={() => {
                    handleAssignedFilterModalOpen(itemDataFilter.label);
                  }}
                >
                  {itemDataFilter?.label}
                </Button>
              )}
            {isAssignedFilterModalOpen === itemDataFilter?.label && (
              <ShareItemFilterModal
                item={item}
                shareUri={share.shareUri}
                itemDataFilter={itemDataFilter}
                onApply={() => handleAssignedFilterModalClose()}
                onClose={() => handleAssignedFilterModalClose()}
                open={isAssignedFilterModalOpen === itemDataFilter?.label}
                viewOnly={true}
              />
            )}
          </>
        )}
      </TableCell>
      <TableCell>
        {isRemovingItem ? (
          <CircularProgress size={15} />
        ) : (
          <>
            {item.status === 'Share_Succeeded' ||
            item.status === 'Revoke_Failed' ? (
              <Typography color="textSecondary" variant="subtitle2">
                Revoke access to this item before deleting
              </Typography>
            ) : item.status === 'Share_Approved' ||
              item.status === 'Revoke_Approved' ||
              item.status === 'Revoke_In_Progress' ||
              item.status === 'Share_In_Progress' ? (
              <Typography color="textSecondary" variant="subtitle2">
                Wait until this item is processed
              </Typography>
            ) : (
              <Button
                color="primary"
                startIcon={<DeleteOutlined fontSize="small" />}
                sx={{ m: 1 }}
                variant="outlined"
                onClick={removeItemFromShareObject}
              >
                Delete
              </Button>
            )}
            {/* If item status is PENDINGAPPROVAL and is of type table then have a button the is 'Assign Filters' */}
            {item.status === 'PendingApproval' &&
              item.itemType === 'Table' &&
              (share.userRoleForShareObject === 'Approvers' ||
                share.userRoleForShareObject === 'ApproversAndRequesters') && (
                <Button
                  color="primary"
                  startIcon={<FilterAltIcon fontSize="small" />}
                  sx={{ m: 1 }}
                  variant="outlined"
                  onClick={() => {
                    handleFilterModalOpen(item.shareItemUri);
                  }}
                >
                  Edit Filters
                </Button>
              )}
            {isFilterModalOpenUri === item.shareItemUri && (
              <ShareItemFilterModal
                item={item}
                shareUri={share.shareUri}
                itemDataFilter={itemDataFilter}
                onApply={() => handleFilterModalClose()}
                onClose={() => handleFilterModalClose()}
                reloadItems={fetchShareItems}
                open={isFilterModalOpenUri === item.shareItemUri}
              />
            )}
          </>
        )}
      </TableCell>
      <TableCell>
        <ShareHealthStatus
          status={item.status}
          healthStatus={item.healthStatus}
          lastVerificationTime={item.lastVerificationTime}
        />
      </TableCell>
      <TableCell>
        {item.healthMessage ? (
          <List dense>
            {item.healthMessage.split('|').map((err_msg, i) => (
              <ListItem key={i}>{err_msg}</ListItem>
            ))}
          </List>
        ) : (
          '-'
        )}
      </TableCell>
    </TableRow>
  );
}

SharedItem.propTypes = {
  item: PropTypes.any,
  share: PropTypes.any,
  client: PropTypes.any,
  dispatch: PropTypes.any,
  enqueueSnackbar: PropTypes.any,
  fetchShareItems: PropTypes.func,
  fetchItem: PropTypes.func
};

const ShareView = () => {
  const { settings } = useSettings();
  const { enqueueSnackbar } = useSnackbar();
  const [share, setShare] = useState(null);
  const [filter, setFilter] = useState(Defaults.filter);
  const [sharedItems, setSharedItems] = useState(Defaults.pagedResponse);
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const params = useParams();
  const client = useClient();
  const theme = useTheme();
  const linkColor = theme.palette.primary.main;
  const [loading, setLoading] = useState(true);
  const [loadingShareItems, setLoadingShareItems] = useState(false);
  const [isAddItemModalOpen, setIsAddItemModalOpen] = useState(false);
  const [isRevokeItemsModalOpen, setIsRevokeItemsModalOpen] = useState(false);
  const [isVerifyItemsModalOpen, setIsVerifyItemsModalOpen] = useState(false);
  const [isReApplyShareItemModalOpen, setIsReApplyShareItemModalOpen] =
    useState(false);

  const [modalOpen, setIsModalOpen] = useState(false);
  const handleOpenModal = () => setIsModalOpen(true);
  const handleCloseModal = () => setIsModalOpen(false);

  const [requestTeamModalOpen, setIsRequestTeamModalOpen] = useState(false);
  const handleRequestTeamOpenModal = () => {
    setIsRequestTeamModalOpen(true);
  };
  const handleCloseRequestTeamModal = () => {
    setIsRequestTeamModalOpen(false);
  };

  const handleAddItemModalClose = () => {
    setIsAddItemModalOpen(false);
  };

  const handleRevokeItemModalClose = () => {
    setIsRevokeItemsModalOpen(false);
  };

  const handleVerifyItemModalOpen = () => {
    setIsVerifyItemsModalOpen(true);
  };
  const handleVerifyItemModalClose = () => {
    setIsVerifyItemsModalOpen(false);
  };

  const handleReApplyShareItemModalOpen = () => {
    setIsReApplyShareItemModalOpen(true);
  };
  const handleReApplyShareItemModalClose = () => {
    setIsReApplyShareItemModalOpen(false);
  };

  const handlePageChange = async (event, value) => {
    if (value <= sharedItems.pages && value !== sharedItems.page) {
      await setFilter({ ...filter, isShared: true, page: value });
    }
  };

  const fetchItem = useCallback(async () => {
    setLoading(true);
    const response = await client.query(
      getShareObject({ shareUri: params.uri })
    );
    if (!response.errors) {
      setShare(response.data.getShareObject);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [client, dispatch, params.uri]);
  const fetchShareItems = useCallback(
    async (isAddingItem = false) => {
      setLoadingShareItems(true);
      const response = await client.query(
        getShareObject({
          shareUri: params.uri,
          filter: {
            ...filter,
            isShared: true
          }
        })
      );
      if (!response.errors) {
        if (isAddingItem) {
          await fetchItem();
        }
        setSharedItems({ ...response.data.getShareObject.items });
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
      setLoadingShareItems(false);
    },
    [client, dispatch, filter, fetchItem, params.uri]
  );

  const revoke = async (shareUri, selectionModel) => {
    const response = await client.mutate(
      revokeItemsShareObject({
        input: {
          shareUri: share.shareUri,
          itemUris: selectionModel
        }
      })
    );
    if (!response.errors) {
      enqueueSnackbar('Items revoked', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      handleRevokeItemModalClose();
      await fetchShareItems();
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };

  const verify = async (shareUri, selectionModel) => {
    const response = await client.mutate(
      verifyItemsShareObject({
        input: {
          shareUri: shareUri,
          itemUris: selectionModel
        }
      })
    );
    if (!response.errors) {
      enqueueSnackbar('Share Item Verification Started.', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      handleVerifyItemModalClose();
      await fetchShareItems();
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };

  const reapply = async (shareUri, selectionModel) => {
    const response = await client.mutate(
      reApplyItemsShareObject({
        input: {
          shareUri: shareUri,
          itemUris: selectionModel
        }
      })
    );
    if (!response.errors) {
      enqueueSnackbar('Share Item Re-Apply Started.', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      handleReApplyShareItemModalClose();
      await fetchShareItems();
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };

  useEffect(() => {
    if (client) {
      fetchItem().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
      fetchShareItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, fetchShareItems, fetchItem, dispatch]);

  if (!share) {
    return null;
  }

  return (
    <>
      <Helmet>
        <title>Shares: Share Details | data.all</title>
      </Helmet>
      <Box
        sx={{
          backgroundColor: 'background.default',
          minHeight: '100%',
          py: 8
        }}
      >
        <Container maxWidth={settings.compact ? 'xl' : false}>
          <ShareViewHeader
            share={share}
            sharedItems={sharedItems}
            client={client}
            dispatch={dispatch}
            navigate={navigate}
            enqueueSnackbar={enqueueSnackbar}
            fetchItem={fetchItem}
            fetchItems={fetchShareItems}
            loading={loadingShareItems}
          />
          {loading ? (
            <CircularProgress />
          ) : (
            <Box sx={{ mt: 3 }}>
              <Box sx={{ mb: 3 }}>
                <Grid container spacing={3}>
                  <Grid item md={4} xl={4} xs={8}>
                    <Card {...share} sx={{ width: 1, height: '100%' }}>
                      <Box>
                        <CardHeader title="Requested Dataset Details" />
                        <Divider />
                      </Box>
                      <CardContent>
                        <Box>
                          <Box>
                            <Typography
                              color="textSecondary"
                              variant="subtitle2"
                            >
                              Dataset {share.dataset.datasetName}
                            </Typography>
                            <Typography
                              color="textPrimary"
                              variant="subtitle2"
                              sx={{
                                mt: 1,
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                display: '-webkit-box',
                                WebkitLineClamp: '3',
                                WebkitBoxOrient: 'vertical'
                              }}
                            >
                              <SanitizedHTML
                                dirtyHTML={createLinkMarkup(
                                  share?.dataset?.description || '',
                                  linkColor
                                )}
                              />
                            </Typography>
                          </Box>
                          <Box sx={{ mt: 3 }}>
                            <Typography
                              color="textSecondary"
                              variant="subtitle2"
                            >
                              Dataset Owners
                            </Typography>
                            <Box sx={{ mt: 1 }}>
                              <Typography
                                color="textPrimary"
                                variant="subtitle2"
                              >
                                <Box
                                  sx={{ cursor: 'pointer' }}
                                  onClick={handleOpenModal}
                                >
                                  {share.dataset.SamlAdminGroupName || '-'}
                                </Box>
                                <UserModal
                                  team={share.dataset.SamlAdminGroupName}
                                  open={modalOpen}
                                  onClose={handleCloseModal}
                                />
                              </Typography>
                            </Box>
                          </Box>
                          <Box sx={{ mt: 3 }}>
                            <Typography
                              color="textSecondary"
                              variant="subtitle2"
                            >
                              Dataset Environment
                            </Typography>
                            <Box sx={{ mt: 1 }}>
                              <Typography
                                color="textPrimary"
                                variant="subtitle2"
                              >
                                {share.dataset.environmentName || '-'}
                              </Typography>
                            </Box>
                          </Box>
                          <Box sx={{ mt: 3 }}>
                            <Typography
                              color="textSecondary"
                              variant="subtitle2"
                            >
                              Your role for this request
                            </Typography>
                            <Box sx={{ mt: 1 }}>
                              <Typography
                                color="textPrimary"
                                variant="subtitle2"
                              >
                                {share.userRoleForShareObject}
                              </Typography>
                            </Box>
                          </Box>
                          {share.dataset.enableExpiration && (
                            <Box sx={{ mt: 3 }}>
                              <Tooltip
                                title={
                                  'Please submit an extension share request before this date to avoid losing access data. For submitting a share request, click on edit'
                                }
                              >
                                <Typography
                                  color="textSecondary"
                                  variant="subtitle2"
                                >
                                  Share Expiration Date
                                </Typography>
                              </Tooltip>
                              <Box sx={{ mt: 1 }}>
                                <Typography
                                  color="textPrimary"
                                  variant="subtitle2"
                                >
                                  {' '}
                                  {share.nonExpirable &&
                                  [
                                    'Processed',
                                    'Extension_Failed',
                                    'Extension_Rejected'
                                  ].some((item) =>
                                    share.status.includes(item)
                                  ) ? (
                                    <Label color={'warning'}>
                                      Non-expiring share
                                    </Label>
                                  ) : share.expiryDate != null ? (
                                    <Label color={'primary'}>
                                      {new Date(
                                        share.expiryDate
                                      ).toDateString()}
                                    </Label>
                                  ) : (
                                    'Share expiration date not set'
                                  )}
                                </Typography>
                              </Box>
                            </Box>
                          )}
                          {share.dataset.enableExpiration &&
                            (share.status === 'Submitted_For_Extension' ||
                              share.status === 'Draft' ||
                              share.status === 'Submitted') && (
                              <Box sx={{ mt: 3 }}>
                                <Tooltip
                                  title={
                                    'Please submit an extension share request before this date to avoid losing access data. For submitting a share request, click on edit'
                                  }
                                >
                                  <Typography
                                    color="textSecondary"
                                    variant="subtitle2"
                                  >
                                    Requested Share Expiration Date
                                  </Typography>
                                </Tooltip>
                                <Box sx={{ mt: 1 }}>
                                  <Typography
                                    color="textPrimary"
                                    variant="subtitle2"
                                  >
                                    {share.requestedExpiryDate != null ? (
                                      <Label color={'primary'}>
                                        {new Date(
                                          share.requestedExpiryDate
                                        ).toDateString()}
                                      </Label>
                                    ) : !share.nonExpirable ? (
                                      'Requested expiration date not available'
                                    ) : (
                                      <Label color={'warning'}>
                                        Non-expiring share
                                      </Label>
                                    )}
                                  </Typography>
                                </Box>
                              </Box>
                            )}
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item md={4} xl={4} xs={8}>
                    <Card {...share} sx={{ height: '100%' }}>
                      <Box>
                        <CardHeader title="Comments" />
                        <Divider />
                      </Box>
                      <CardContent>
                        <Box sx={{ paddingX: 2 }}>
                          <Grid container spacing={3}>
                            <Grid item md={11} xl={11} xs={22}>
                              <Typography
                                color="textSecondary"
                                variant="subtitle2"
                              >
                                Request Purpose
                              </Typography>
                            </Grid>
                            <Grid item md={1} xl={1} xs={2}>
                              {(share.userRoleForShareObject === 'Requesters' ||
                                share.userRoleForShareObject ===
                                  'ApproversAndRequesters') &&
                                (share.status === 'Draft' ||
                                  share.status === 'Processed' ||
                                  share.status === 'Rejected' ||
                                  share.status === 'Submitted') && (
                                  <UpdateRequestReason
                                    share={share}
                                    client={client}
                                    dispatch={dispatch}
                                    enqueueSnackbar={enqueueSnackbar}
                                    fetchItem={fetchItem}
                                  />
                                )}
                            </Grid>
                          </Grid>

                          <Box sx={{ mt: 1 }}>
                            <Typography
                              color="textPrimary"
                              variant="subtitle2"
                              sx={{ wordBreak: 'break-word' }}
                            >
                              {share.requestPurpose || '-'}
                            </Typography>
                          </Box>
                          <Divider sx={{ mt: 2, mb: 2 }} />
                          <Grid container spacing={3}>
                            <Grid item md={11} xl={11} xs={22}>
                              <Typography
                                color="textSecondary"
                                variant="subtitle2"
                              >
                                Reject Purpose
                              </Typography>
                            </Grid>
                            <Grid item md={1} xl={1} xs={2}>
                              {(share.userRoleForShareObject === 'Approvers' ||
                                share.userRoleForShareObject ===
                                  'ApproversAndRequesters') &&
                                (share.status === 'Submitted' ||
                                  share.status === 'Draft') && (
                                  <UpdateRejectReason
                                    share={share}
                                    client={client}
                                    dispatch={dispatch}
                                    enqueueSnackbar={enqueueSnackbar}
                                    fetchItem={fetchItem}
                                  />
                                )}
                            </Grid>
                          </Grid>

                          <Box sx={{ mt: 1 }}>
                            <Typography
                              color="textPrimary"
                              variant="subtitle2"
                              sx={{ wordBreak: 'break-word' }}
                            >
                              {share.rejectPurpose || '-'}
                            </Typography>
                          </Box>

                          {share.dataset.enableExpiration && (
                            <div>
                              <Divider sx={{ mt: 2, mb: 2 }} />
                              <Grid container spacing={3}>
                                <Grid item md={11} xl={11} xs={22}>
                                  <Tooltip
                                    title={
                                      'Extension Reason for when the share was last extended'
                                    }
                                  >
                                    <Typography
                                      color="textSecondary"
                                      variant="subtitle2"
                                    >
                                      Extension Purpose
                                    </Typography>
                                  </Tooltip>
                                </Grid>
                                <Grid item md={1} xl={1} xs={2}>
                                  {(share.userRoleForShareObject ===
                                    'Requesters' ||
                                    share.userRoleForShareObject ===
                                      'ApproversAndRequesters') &&
                                    (share.status === 'Submitted' ||
                                      share.status ===
                                        'Submitted_For_Extension' ||
                                      share.status === 'Draft') &&
                                    share.submittedForExtension && (
                                      <UpdateExtensionReason
                                        share={share}
                                        client={client}
                                        dispatch={dispatch}
                                        enqueueSnackbar={enqueueSnackbar}
                                        fetchItem={fetchItem}
                                      />
                                    )}
                                </Grid>
                              </Grid>
                              <Box sx={{ mt: 1 }}>
                                <Typography
                                  color="textPrimary"
                                  variant="subtitle2"
                                  sx={{ wordBreak: 'break-word' }}
                                >
                                  {share.extensionReason || '-'}
                                </Typography>
                              </Box>
                            </div>
                          )}
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item md={4} xl={4} xs={8}>
                    <Card {...share} style={{ height: '100%' }}>
                      <CardHeader
                        avatar={<TextAvatar name={share.owner} />}
                        disableTypography
                        subheader={
                          <Link
                            underline="hover"
                            color="textPrimary"
                            component={RouterLink}
                            to="#"
                            variant="subtitle2"
                          >
                            {share.owner}
                          </Link>
                        }
                        style={{ paddingBottom: 0 }}
                        title={
                          <Typography
                            color="textPrimary"
                            display="block"
                            variant="overline"
                          >
                            Request created by
                          </Typography>
                        }
                      />
                      <CardContent sx={{ pt: 0 }}>
                        <List>
                          <ListItem
                            disableGutters
                            sx={{
                              paddingX: 2,
                              paddingTop: 2,
                              paddingBottom: 0
                            }}
                          >
                            <Typography
                              color="textSecondary"
                              variant="subtitle2"
                            >
                              Principal
                            </Typography>
                          </ListItem>
                          <ListItem
                            disableGutters
                            divider
                            sx={{
                              justifyContent: 'space-between',
                              paddingX: 2,
                              paddingTop: 1,
                              paddingBottom: 2
                            }}
                          >
                            <Typography
                              color="textPrimary"
                              variant="body2"
                              sx={{
                                whiteSpace: 'nowrap',
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                WebkitBoxOrient: 'vertical',
                                WebkitLineClamp: 2
                              }}
                            >
                              <Tooltip
                                title={share.principal.principalName || '-'}
                              >
                                <span>
                                  {share.principal.principalName || '-'}
                                </span>
                              </Tooltip>
                            </Typography>
                          </ListItem>
                          <ListItem
                            disableGutters
                            divider
                            sx={{
                              justifyContent: 'space-between',
                              padding: 2
                            }}
                          >
                            <Typography
                              color="textSecondary"
                              variant="subtitle2"
                            >
                              Requester Team
                            </Typography>
                            <Typography color="textPrimary" variant="body2">
                              <Box
                                sx={{ cursor: 'pointer' }}
                                onClick={handleRequestTeamOpenModal}
                              >
                                {share.principal.SamlGroupName || '-'}
                              </Box>
                              <UserModal
                                team={share.principal.SamlGroupName}
                                open={requestTeamModalOpen}
                                onClose={handleCloseRequestTeamModal}
                              />
                            </Typography>
                          </ListItem>
                          <ListItem
                            disableGutters
                            divider
                            sx={{
                              justifyContent: 'space-between',
                              padding: 2
                            }}
                          >
                            <Typography
                              color="textSecondary"
                              variant="subtitle2"
                            >
                              Requester Environment
                            </Typography>
                            <Typography color="textPrimary" variant="body2">
                              {share.principal.environmentName || '-'}
                            </Typography>
                          </ListItem>
                          <ListItem
                            disableGutters
                            divider
                            sx={{
                              justifyContent: 'space-between',
                              padding: 2
                            }}
                          >
                            <Stack
                              spacing={1}
                              alignItems="center"
                              direction="row"
                            >
                              <Typography
                                color="textSecondary"
                                variant="subtitle2"
                              >
                                Permissions
                              </Typography>
                              {!isReadOnlyShare(share) && (
                                <Tooltip
                                  title="non-readonly share request"
                                  arrow
                                >
                                  <Warning color="warning" />
                                </Tooltip>
                              )}
                            </Stack>
                            <Typography color="textPrimary" variant="body2">
                              {share.permissions.map((perm) => (
                                <Chip label={perm} sx={{ marginRight: 1 }} />
                              ))}
                            </Typography>
                          </ListItem>
                          <ListItem
                            disableGutters
                            divider
                            sx={{
                              justifyContent: 'space-between',
                              padding: 2
                            }}
                          >
                            <Typography
                              color="textSecondary"
                              variant="subtitle2"
                            >
                              Creation time
                            </Typography>
                            <Typography color="textPrimary" variant="body2">
                              {share.created}
                            </Typography>
                          </ListItem>
                          <ListItem
                            disableGutters
                            sx={{
                              justifyContent: 'space-between',
                              padding: 2
                            }}
                          >
                            <Typography
                              color="textSecondary"
                              variant="subtitle2"
                            >
                              Status
                            </Typography>
                            {share.status === 'Draft' &&
                              (share.userRoleForShareObject === 'Requesters' ||
                                share.userRoleForShareObject ===
                                  'ApproversAndRequesters') && (
                                <Typography color="red" variant="body2">
                                  Don't forget to submit the request!
                                </Typography>
                              )}
                            <Typography color="textPrimary" variant="body2">
                              <ShareStatus status={share.status} />
                            </Typography>
                          </ListItem>
                        </List>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </Box>

              <Box sx={{ mb: 3 }}>
                <Card>
                  <CardHeader
                    title="Shared Items"
                    action={
                      <Box>
                        <LoadingButton
                          color="info"
                          startIcon={<SecurityIcon />}
                          sx={{ m: 1 }}
                          onClick={handleVerifyItemModalOpen}
                          type="button"
                          variant="outlined"
                        >
                          Verify Item(s) Health Status
                        </LoadingButton>
                        {(share.userRoleForShareObject === 'Approvers' ||
                          share.userRoleForShareObject ===
                            'ApproversAndRequesters') && (
                          <LoadingButton
                            color="info"
                            startIcon={<SecurityIcon />}
                            sx={{ m: 1 }}
                            onClick={handleReApplyShareItemModalOpen}
                            type="button"
                            variant="outlined"
                          >
                            Re-Apply Share
                          </LoadingButton>
                        )}
                      </Box>
                    }
                  />
                  <Divider />
                  <Scrollbar>
                    <Box sx={{ minWidth: 600 }}>
                      <Table>
                        <TableHead>
                          <TableRow>
                            <TableCell>Type</TableCell>
                            <TableCell>Name</TableCell>
                            <TableCell>Status</TableCell>
                            <TableCell>Data Filters</TableCell>
                            <TableCell>Action</TableCell>
                            <TableCell>Health Status</TableCell>
                            <TableCell>Health Message</TableCell>
                          </TableRow>
                        </TableHead>
                        {loadingShareItems ? (
                          <CircularProgress sx={{ mt: 1 }} size={20} />
                        ) : (
                          <TableBody>
                            {sharedItems.nodes.length > 0 ? (
                              sharedItems.nodes.map((sharedItem) => (
                                <SharedItem
                                  key={sharedItem.itemUri}
                                  item={sharedItem}
                                  share={share}
                                  client={client}
                                  dispatch={dispatch}
                                  enqueueSnackbar={enqueueSnackbar}
                                  fetchShareItems={fetchShareItems}
                                  fetchItem={fetchItem}
                                />
                              ))
                            ) : (
                              <TableRow>
                                <TableCell>No items added.</TableCell>
                              </TableRow>
                            )}
                          </TableBody>
                        )}
                      </Table>
                      {sharedItems.nodes.length > 0 && (
                        <Pager
                          mgTop={2}
                          mgBottom={2}
                          items={sharedItems}
                          onChange={handlePageChange}
                        />
                      )}
                    </Box>
                  </Scrollbar>
                </Card>
              </Box>
              {share.dataset.datasetType === 'DatasetTypes.S3' && (
                <S3ConsumptionData share={share}></S3ConsumptionData>
              )}
            </Box>
          )}
        </Container>
        {isAddItemModalOpen && (
          <AddShareItemModal
            share={share}
            onApply={handleAddItemModalClose}
            onClose={handleAddItemModalClose}
            reloadSharedItems={fetchShareItems}
            open={isAddItemModalOpen}
          />
        )}
        {isRevokeItemsModalOpen && (
          <ShareItemsSelectorModal
            share={share}
            onApply={handleRevokeItemModalClose}
            onClose={handleRevokeItemModalClose}
            open={isRevokeItemsModalOpen}
            submit={revoke}
            name={'Revoke'}
            filter={{
              ...Defaults.filter,
              pageSize: 1000,
              isShared: true,
              isRevokable: true
            }}
          />
        )}
        {isVerifyItemsModalOpen && (
          <ShareItemsSelectorModal
            share={share}
            onApply={handleVerifyItemModalClose}
            onClose={handleVerifyItemModalClose}
            open={isVerifyItemsModalOpen}
            submit={verify}
            name={'Verify'}
            filter={{
              ...Defaults.filter,
              pageSize: 1000,
              isShared: true,
              isRevokable: true
            }}
          />
        )}
        {isReApplyShareItemModalOpen && (
          <ShareItemsSelectorModal
            share={share}
            onApply={handleReApplyShareItemModalClose}
            onClose={handleReApplyShareItemModalClose}
            open={isReApplyShareItemModalOpen}
            submit={reapply}
            name={'Re-Apply Share'}
            filter={{
              ...Defaults.filter,
              pageSize: 1000,
              isShared: true,
              isRevokable: true,
              isHealthy: false
            }}
          />
        )}
      </Box>
    </>
  );
};

export default ShareView;
