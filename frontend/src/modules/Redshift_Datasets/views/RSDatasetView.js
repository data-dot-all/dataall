import {
  ForumOutlined,
  Info,
  ShareOutlined,
  ViewArrayOutlined,
  Warning
} from '@mui/icons-material';
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
import React, { useCallback, useEffect, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { FaTrash } from 'react-icons/fa';
import { useNavigate } from 'react-router';
import { Link as RouterLink, useParams } from 'react-router-dom';
import {
  ChevronRightIcon,
  DeleteObjectWithFrictionModal,
  PencilAltIcon,
  UpVoteButton,
  useSettings
} from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { countUpVotes, getVote, upVote, useClient } from 'services';
import { FeedComments } from 'modules/Shared';
import { ShareBoxList } from 'modules/Shares';
import { deleteRedshiftDataset, getRedshiftDataset } from '../services';
import { RedshiftDatasetTables, RedshiftDatasetOverview } from '../components';

const RSDatasetView = () => {
  const dispatch = useDispatch();
  const { settings } = useSettings();
  const { enqueueSnackbar } = useSnackbar();
  const params = useParams();
  const client = useClient();
  const navigate = useNavigate();
  const [currentTab, setCurrentTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [dataset, setDataset] = useState(null);
  const [isDeleteObjectModalOpen, setIsDeleteObjectModalOpen] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [isUpVoted, setIsUpVoted] = useState(false);
  const [upVotes, setUpvotes] = useState(null);
  const [openFeed, setOpenFeed] = useState(false);
  const getTabs = () => {
    const tabs = [
      { label: 'Overview', value: 'overview', icon: <Info fontSize="small" /> },
      {
        label: 'Data',
        value: 'data',
        icon: <ViewArrayOutlined fontSize="small" />
      }
    ];
    if (isAdmin) {
      tabs.push({
        label: 'Shares',
        value: 'shares',
        icon: <ShareOutlined fontSize="small" />
      });
    }
    return tabs;
  };

  const handleDeleteObjectModalOpen = () => {
    setIsDeleteObjectModalOpen(true);
  };

  const handleDeleteObjectModalClose = () => {
    setIsDeleteObjectModalOpen(false);
  };

  const getUserDatasetVote = useCallback(
    async (datasetUri) => {
      const response = await client.query(
        getVote(datasetUri, 'redshiftdataset')
      );
      if (!response.errors && response.data.getVote !== null) {
        setIsUpVoted(response.data.getVote.upvote);
      }
    },
    [client]
  );

  const reloadVotes = async () => {
    const response = await client.query(
      countUpVotes(params.uri, 'redshiftdataset')
    );
    if (!response.errors && response.data.countUpVotes !== null) {
      setUpvotes(response.data.countUpVotes);
    } else {
      setUpvotes(0);
    }
  };

  const upVoteDataset = async (datasetUri) => {
    const response = await client.mutate(
      upVote({
        targetUri: datasetUri,
        targetType: 'redshiftdataset',
        upvote: !isUpVoted
      })
    );
    if (!response.errors && response.data.upVote !== null) {
      setIsUpVoted(response.data.upVote.upvote);
    }
    reloadVotes().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
  };

  const fetchItem = useCallback(async () => {
    setLoading(true);
    const response = await client.query(getRedshiftDataset(params.uri));
    if (!response.errors && response.data.getRedshiftDataset !== null) {
      setDataset(response.data.getRedshiftDataset);
      setIsAdmin(
        ['BusinessOwner', 'Admin', 'DataSteward', 'Creator'].indexOf(
          response.data.getRedshiftDataset.userRoleForDataset
        ) !== -1
      );
      setUpvotes(response.data.getRedshiftDataset.upvotes);
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Dataset not found';
      dispatch({ type: SET_ERROR, error });
    }
    setLoading(false);
  }, [client, dispatch, params.uri]);

  useEffect(() => {
    if (client) {
      getUserDatasetVote(params.uri).catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
      fetchItem().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client, fetchItem, getUserDatasetVote, dispatch, params.uri]);

  const handleTabsChange = (event, value) => {
    setCurrentTab(value);
  };

  const removeDataset = async (deleteFromAWS = false) => {
    const response = await client.mutate(
      deleteRedshiftDataset(dataset.datasetUri, deleteFromAWS)
    );
    if (!response.errors) {
      handleDeleteObjectModalClose();
      enqueueSnackbar('Dataset deleted', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      navigate('/console/datasets');
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };

  if (loading) {
    return <CircularProgress />;
  }
  if (!dataset) {
    return null;
  }

  return (
    <>
      <Helmet>
        <title>Datasets: Dataset Details | data.all</title>
      </Helmet>
      <Box
        sx={{
          backgroundColor: 'background.default',
          minHeight: '100%',
          py: 8
        }}
      >
        <Container maxWidth={settings.compact ? 'xl' : false}>
          <Grid container justifyContent="space-between" spacing={3}>
            <Grid item>
              <Typography color="textPrimary" variant="h5">
                Redshift Dataset {dataset.label}
              </Typography>
              <Breadcrumbs
                aria-label="breadcrumb"
                separator={<ChevronRightIcon fontSize="small" />}
                sx={{ mt: 1 }}
              >
                <Typography color="textPrimary" variant="subtitle2">
                  Contribute
                </Typography>
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
                  to={`/console/redshift-datasets/${dataset.datasetUri}`}
                  variant="subtitle2"
                >
                  {dataset.label}
                </Link>
              </Breadcrumbs>
            </Grid>
            <Grid item>
              <Box sx={{ m: -1 }}>
                <UpVoteButton
                  upVoted={isUpVoted}
                  disabled={!isAdmin}
                  onClick={() => upVoteDataset(dataset.datasetUri)}
                  upVotes={upVotes}
                />
                {isAdmin && (
                  <span>
                    <Button
                      color="primary"
                      startIcon={<ForumOutlined fontSize="small" />}
                      sx={{ mt: 1, mr: 1 }}
                      onClick={() => setOpenFeed(true)}
                      type="button"
                      variant="outlined"
                    >
                      Chat
                    </Button>
                    <Button
                      color="primary"
                      component={RouterLink}
                      startIcon={<PencilAltIcon fontSize="small" />}
                      sx={{ mt: 1, mr: 1 }}
                      to={`/console/redshift-datasets/${dataset.datasetUri}/edit`}
                      variant="outlined"
                    >
                      Edit
                    </Button>
                    <Button
                      color="primary"
                      startIcon={<FaTrash size={15} />}
                      sx={{ mt: 1 }}
                      onClick={handleDeleteObjectModalOpen}
                      type="button"
                      variant="outlined"
                    >
                      Delete
                    </Button>
                  </span>
                )}
              </Box>
            </Grid>
          </Grid>
          <Box sx={{ mt: 3 }}>
            <Tabs
              indicatorColor="primary"
              onChange={handleTabsChange}
              scrollButtons="auto"
              textColor="primary"
              value={currentTab}
              variant="fullWidth"
            >
              {getTabs().map((tab) => (
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
            {currentTab === 'data' && (
              <RedshiftDatasetTables dataset={dataset} isAdmin={isAdmin} />
            )}
            {currentTab === 'overview' && (
              <RedshiftDatasetOverview dataset={dataset} isAdmin={isAdmin} />
            )}
            {isAdmin && currentTab === 'shares' && (
              <ShareBoxList tab={'inbox'} dataset={dataset} />
            )}
          </Box>
        </Container>
      </Box>
      {isAdmin && (
        <DeleteObjectWithFrictionModal
          objectName={dataset.label}
          onApply={handleDeleteObjectModalClose}
          onClose={handleDeleteObjectModalClose}
          open={isDeleteObjectModalOpen}
          deleteFunction={removeDataset}
          deleteMessage={
            <Card>
              <CardContent>
                <Typography gutterBottom variant="body2">
                  <Warning /> Redshift Dataset will be deleted from data.all
                  catalog, but its tables and schema will still be available in
                  Amazon Redshift.
                </Typography>
              </CardContent>
            </Card>
          }
          isAWSResource={false}
        />
      )}
      {openFeed && (
        <FeedComments
          objectOwner={dataset.owner}
          targetType="RedshiftDataset"
          targetUri={dataset.datasetUri}
          open={openFeed}
          onClose={() => setOpenFeed(false)}
        />
      )}
    </>
  );
};

export default RSDatasetView;
