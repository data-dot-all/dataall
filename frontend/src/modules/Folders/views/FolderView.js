import { ForumOutlined, Warning } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import {
  Box,
  Breadcrumbs,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Container,
  Divider,
  Grid,
  Link,
  Tab,
  Tabs,
  Typography
} from '@mui/material';
import { useSnackbar } from 'notistack';
import * as PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { FaExternalLinkAlt, FaTrash } from 'react-icons/fa';
import { useNavigate } from 'react-router';
import { Link as RouterLink, useParams } from 'react-router-dom';
import {
  ChevronRightIcon,
  DeleteObjectModal,
  PencilAltIcon,
  useSettings
} from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import {
  useClient,
  deleteDatasetStorageLocation,
  getDatasetAssumeRoleUrl,
  getDatasetSharedAssumeRoleUrl
} from 'services';
import { getDatasetStorageLocation } from '../services';

import { FeedComments } from 'modules/Shared';
import { FolderOverview } from '../components';
import { isFeatureEnabled } from 'utils';

const tabs = [{ label: 'Overview', value: 'overview' }];

function FolderPageHeader(props) {
  const { folder, handleDeleteObjectModalOpen, isAdmin } = props;
  const client = useClient();
  const dispatch = useDispatch();
  const [isLoadingUI, setIsLoadingUI] = useState(false);
  const [openFeed, setOpenFeed] = useState(false);

  const goToS3Console = async () => {
    setIsLoadingUI(true);
    if (isAdmin) {
      const response = await client.query(
        getDatasetAssumeRoleUrl(folder.dataset.datasetUri)
      );
      if (!response.errors) {
        window.open(response.data.getDatasetAssumeRoleUrl, '_blank');
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } else {
      const response = await client.query(
        getDatasetSharedAssumeRoleUrl(folder.dataset.datasetUri)
      );
      if (!response.errors) {
        window.open(response.data.getDatasetSharedAssumeRoleUrl, '_blank');
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    }
    setIsLoadingUI(false);
  };
  return (
    <Grid container justifyContent="space-between" spacing={3}>
      <Grid item>
        <Typography color="textPrimary" variant="h5">
          Folder {folder.label}
        </Typography>
        <Breadcrumbs
          aria-label="breadcrumb"
          separator={<ChevronRightIcon fontSize="small" />}
          sx={{ mt: 1 }}
        >
          <Link
            underline="hover"
            component={RouterLink}
            color="textPrimary"
            variant="subtitle2"
            to="/console/catalog"
          >
            Discover
          </Link>
          <Link
            underline="hover"
            color="textPrimary"
            component={RouterLink}
            to="/console/datasets"
            variant="subtitle2"
          >
            Datasets
          </Link>
          <Link
            underline="hover"
            color="textPrimary"
            component={RouterLink}
            to={`/console/s3-datasets/${folder?.dataset?.datasetUri}`}
            variant="subtitle2"
          >
            {folder?.dataset?.name}
          </Link>
          <Link
            underline="hover"
            color="textPrimary"
            component={RouterLink}
            to={`/console/s3-datasets/folder/${folder.locationUri}`}
            variant="subtitle2"
          >
            {folder.label}
          </Link>
        </Breadcrumbs>
      </Grid>
      <Grid item>
        <Box sx={{ m: -1 }}>
          {isAdmin && (
            <Button
              color="primary"
              startIcon={<ForumOutlined fontSize="small" />}
              sx={{ m: 1 }}
              onClick={() => setOpenFeed(true)}
              type="button"
              variant="outlined"
            >
              Chat
            </Button>
          )}
          {isFeatureEnabled('s3_datasets', 'aws_actions') && (
            <LoadingButton
              loading={isLoadingUI}
              startIcon={<FaExternalLinkAlt size={15} />}
              variant="outlined"
              color="primary"
              sx={{ m: 1 }}
              onClick={goToS3Console}
            >
              S3 Bucket
            </LoadingButton>
          )}
          {isAdmin && (
            <Button
              color="primary"
              component={RouterLink}
              startIcon={<PencilAltIcon fontSize="small" />}
              sx={{ m: 1 }}
              to={`/console/s3-datasets/folder/${folder.locationUri}/edit`}
              variant="outlined"
            >
              Edit
            </Button>
          )}
          {isAdmin && (
            <Button
              color="primary"
              startIcon={<FaTrash size={15} />}
              sx={{ m: 1 }}
              onClick={handleDeleteObjectModalOpen}
              type="button"
              variant="outlined"
            >
              Delete
            </Button>
          )}
        </Box>
      </Grid>
      {openFeed && (
        <FeedComments
          objectOwner={folder.dataset.owner}
          targetType="DatasetStorageLocation"
          targetUri={folder.locationUri}
          open={openFeed}
          onClose={() => setOpenFeed(false)}
        />
      )}
    </Grid>
  );
}

FolderPageHeader.propTypes = {
  folder: PropTypes.object.isRequired,
  handleDeleteObjectModalOpen: PropTypes.func.isRequired,
  isAdmin: PropTypes.bool.isRequired
};
const FolderView = () => {
  const dispatch = useDispatch();
  const { settings } = useSettings();
  const params = useParams();
  const client = useClient();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const [folder, setFolder] = useState(null);
  const [currentTab, setCurrentTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [isDeleteObjectModalOpen, setIsDeleteObjectModalOpen] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);

  const handleDeleteObjectModalOpen = () => {
    setIsDeleteObjectModalOpen(true);
  };
  const handleDeleteObjectModalClose = () => {
    setIsDeleteObjectModalOpen(false);
  };

  const deleteFolder = async () => {
    const response = await client.mutate(
      deleteDatasetStorageLocation({ locationUri: folder.locationUri })
    );
    if (!response.errors) {
      enqueueSnackbar('Folder deleted', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      navigate(`/console/s3-datasets/${folder.dataset.datasetUri}`);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };

  const fetchItem = useCallback(async () => {
    setLoading(true);
    const response = await client.query(getDatasetStorageLocation(params.uri));
    if (response.data.getDatasetStorageLocation !== null) {
      setFolder(response.data.getDatasetStorageLocation);
      setIsAdmin(
        ['Creator', 'Admin', 'Owner'].indexOf(
          response.data.getDatasetStorageLocation.dataset?.userRoleForDataset
        ) !== -1
      );
    } else {
      setFolder(null);
      response.errors.forEach((err) =>
        dispatch({ type: SET_ERROR, error: err.message })
      );
    }
    setLoading(false);
  }, [client, dispatch, params.uri]);
  useEffect(() => {
    if (client) {
      fetchItem().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client, dispatch, fetchItem]);

  const handleTabsChange = (event, value) => {
    setCurrentTab(value);
  };

  if (loading) {
    return <CircularProgress />;
  }
  if (!folder) {
    return null;
  }

  return (
    <>
      <Helmet>
        <title>Folders: Folder Details | data.all</title>
      </Helmet>
      <Box
        sx={{
          backgroundColor: 'background.default',
          minHeight: '100%',
          py: 8
        }}
      >
        <Container maxWidth={settings.compact ? 'xl' : false}>
          <FolderPageHeader
            folder={folder}
            handleDeleteObjectModalOpen={handleDeleteObjectModalOpen}
            isAdmin={isAdmin}
          />
          <Box sx={{ mt: 3 }}>
            <Tabs
              indicatorColor="primary"
              onChange={handleTabsChange}
              scrollButtons="auto"
              textColor="primary"
              value={currentTab}
              variant="fullWidth"
            >
              {tabs.map((tab) => (
                <Tab
                  key={tab.value}
                  label={tab.label}
                  value={tab.value}
                  icon={settings.tabIcons ? tab.icon : null}
                  iconPosition="start"
                />
              ))}
            </Tabs>
          </Box>
          <Divider />
          <Box sx={{ mt: 3 }}>
            {currentTab === 'overview' && (
              <FolderOverview folder={folder} isAdmin={isAdmin} />
            )}
          </Box>
        </Container>
      </Box>
      {isAdmin && (
        <DeleteObjectModal
          objectName={folder.label}
          onApply={handleDeleteObjectModalClose}
          onClose={handleDeleteObjectModalClose}
          open={isDeleteObjectModalOpen}
          deleteFunction={deleteFolder}
          deleteMessage={
            <Card>
              <CardContent>
                <Typography gutterBottom variant="body2">
                  <Warning /> Folder will be deleted from data.all catalog, but
                  will still be available on Amazon S3.
                </Typography>
              </CardContent>
            </Card>
          }
        />
      )}
    </>
  );
};

export default FolderView;
