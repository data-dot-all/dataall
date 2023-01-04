import React, { useCallback, useEffect, useState } from 'react';
import { Link as RouterLink, useParams } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import {
  Box,
  Breadcrumbs,
  Button,
  Card,
  CardContent,
  CardHeader,
  Container,
  Divider,
  Grid,
  IconButton,
  Link,
  List,
  ListItem,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Tooltip,
  Typography
} from '@mui/material';
import CircularProgress from '@mui/material/CircularProgress';
import {
  BlockOutlined,
  CheckCircleOutlined,
  DeleteOutlined,
  LockRounded,
  RefreshRounded
} from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import * as PropTypes from 'prop-types';
import { useSnackbar } from 'notistack';
import { useNavigate } from 'react-router';
import useSettings from '../../hooks/useSettings';
import ChevronRightIcon from '../../icons/ChevronRight';
import useClient from '../../hooks/useClient';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import getShareObject from '../../api/ShareObject/getShareObject';
import ShareStatus from '../../components/ShareStatus';
import TextAvatar from '../../components/TextAvatar';
import Pager from '../../components/Pager';
import Scrollbar from '../../components/Scrollbar';
import * as Defaults from '../../components/defaults';
import { PagedResponseDefault } from '../../components/defaults';
import removeSharedItem from '../../api/ShareObject/removeSharedItem';
import deleteShareObject from '../../api/ShareObject/deleteShareObject.js';
import PlusIcon from '../../icons/Plus';
import AddShareItemModal from './AddShareItemModal';
import approveShareObject from '../../api/ShareObject/approveShareObject';
import rejectShareObject from '../../api/ShareObject/rejectShareObject';
import submitApproval from '../../api/ShareObject/submitApproval';

function ShareViewHeader(props) {
  const {
    share,
    client,
    dispatch,
    enqueueSnackbar,
    navigate,
    fetchItem,
    fetchItems,
    loading
  } = props;
  const [accepting, setAccepting] = useState(false);
  const [rejecting, setRejecting] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [removing, setRemoving] = useState(false);
  const submit = async () => {
    setSubmitting(true);
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
      await fetchItem();
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setSubmitting(false);
  };
  const remove = async () => {
    setRemoving(true);
    const response = await client.mutate(
      deleteShareObject({
        shareUri: share.shareUri
      })
    );
    if (!response.errors) {
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
    setRemoving(false);
  };
  const accept = async () => {
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

  const reject = async () => {
    setRejecting(true);
    const response = await client.mutate(
      rejectShareObject({
        shareUri: share.shareUri
      })
    );
    if (!response.errors) {
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
    <Grid container justifyContent="space-between" spacing={3}>
      <Grid item>
        <Typography color="textPrimary" variant="h5">
          Share object for {share.dataset?.datasetName}
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
            to={`/console/datasets/${share.dataset?.datasetUri}`}
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
            <Button
              color="primary"
              startIcon={<DeleteOutlined fontSize="small" />}
              sx={{ m: 1 }}
              variant="outlined"
              onClick={remove}
            >
              Delete
            </Button>
            {share.userRoleForShareObject === 'Approvers' ? (
              <>
                {share.status === 'PendingApproval' && (
                  <>
                    <LoadingButton
                      loading={accepting}
                      color="success"
                      startIcon={<CheckCircleOutlined />}
                      sx={{ m: 1 }}
                      onClick={accept}
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
                      onClick={reject}
                      type="button"
                      variant="outlined"
                    >
                      Reject
                    </LoadingButton>
                  </>
                )}
                {share.status === 'Approved' && (
                  <LoadingButton
                    loading={rejecting}
                    color="primary"
                    startIcon={<LockRounded />}
                    sx={{ m: 1 }}
                    onClick={reject}
                    type="button"
                    variant="outlined"
                  >
                    Revoke
                  </LoadingButton>
                )}
              </>
            ) : (
              <>
                {(share.status === 'Draft' || share.status === 'Rejected') && (
                  <LoadingButton
                    loading={submitting}
                    color="primary"
                    startIcon={<CheckCircleOutlined />}
                    sx={{ m: 1 }}
                    onClick={submit}
                    type="button"
                    variant="contained"
                  >
                    Submit
                  </LoadingButton>
                )}
              </>
            )}
          </Box>
        )}
      </Grid>
    </Grid>
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

function SharedItem(props) {
  const {
    item,
    client,
    dispatch,
    enqueueSnackbar,
    fetchShareItems,
    fetchItem
  } = props;
  const [isRemovingItem, setIsRemovingItem] = useState(false);
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
      <TableCell>{item.itemType === 'Table' ? 'Table' : 'Folder'}</TableCell>
      <TableCell>{item.itemName}</TableCell>
      <TableCell>
        <ShareStatus status={item.status} />
      </TableCell>
      <TableCell>
        {isRemovingItem ? (
          <CircularProgress size={15} />
        ) : (
          <IconButton onClick={removeItemFromShareObject}>
            <DeleteOutlined fontSize="small" />
          </IconButton>
        )}
      </TableCell>
    </TableRow>
  );
}

SharedItem.propTypes = {
  item: PropTypes.any,
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
  const [filter, setFilter] = useState(Defaults.DefaultFilter);
  const [sharedItems, setSharedItems] = useState(PagedResponseDefault);
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const params = useParams();
  const client = useClient();
  const [loading, setLoading] = useState(true);
  const [loadingShareItems, setLoadingShareItems] = useState(false);
  const [isAddItemModalOpen, setIsAddItemModalOpen] = useState(false);
  const handleAddItemModalOpen = () => {
    setIsAddItemModalOpen(true);
  };

  const handleAddItemModalClose = () => {
    setIsAddItemModalOpen(false);
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

  const handlePageChange = async (event, value) => {
    if (value <= sharedItems.pages && value !== sharedItems.page) {
      await setFilter({ ...filter, isShared: true, page: value });
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
              <Grid container spacing={3}>
                <Grid item md={5} xl={5} xs={12}>
                  <Box sx={{ mb: 3 }}>
                    <Card {...share} sx={{ width: 1 }}>
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
                              Dataset
                            </Typography>
                            <Typography color="textPrimary" variant="subtitle2">
                              {share.dataset.datasetName}
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
                                {share.dataset.SamlAdminGroupName || '-'}
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
                        </Box>
                      </CardContent>
                    </Card>
                  </Box>
                </Grid>
                <Grid item md={7} xl={7} xs={12}>
                  <Card {...share} style={{ height: '92%' }}>
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
                          divider
                          sx={{
                            justifyContent: 'space-between',
                            padding: 2
                          }}
                        >
                          <Typography color="textSecondary" variant="subtitle2">
                            Principal
                          </Typography>
                          <Typography
                            color="textPrimary"
                            variant="body2"
                            sx={{
                              width: '500px',
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
                          <Typography color="textSecondary" variant="subtitle2">
                            Requester Team
                          </Typography>
                          <Typography color="textPrimary" variant="body2">
                            {share.principal.SamlGroupName || '-'}
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
                          <Typography color="textSecondary" variant="subtitle2">
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
                          <Typography color="textSecondary" variant="subtitle2">
                            Creation time
                          </Typography>
                          <Typography color="textPrimary" variant="body2">
                            {share.created}
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
                          <Typography color="textSecondary" variant="subtitle2">
                            Status
                          </Typography>
                          <Typography color="textPrimary" variant="body2">
                            <ShareStatus status={share.status} />
                          </Typography>
                        </ListItem>
                      </List>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
              <Card>
                <CardHeader
                  title="Shared Items"
                  action={
                    <LoadingButton
                      color="primary"
                      onClick={handleAddItemModalOpen}
                      startIcon={<PlusIcon fontSize="small" />}
                      sx={{ m: 1 }}
                      variant="outlined"
                    >
                      Add Item
                    </LoadingButton>
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
                          <TableCell>Action</TableCell>
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
      </Box>
    </>
  );
};

export default ShareView;
