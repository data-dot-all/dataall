import {
  ForumOutlined,
  Info,
  ShareOutlined,
  ShowChart
} from '@mui/icons-material';
import {
  Box,
  Breadcrumbs,
  Button,
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
import { deleteDashboard, getDashboard } from '../services';
import {
  DashboardOverview,
  DashboardShares,
  DashboardViewer
} from '../components';

const DashboardView = () => {
  const dispatch = useDispatch();
  const { settings } = useSettings();
  const params = useParams();
  const client = useClient();
  const { enqueueSnackbar } = useSnackbar();
  const navigate = useNavigate();
  const [currentTab, setCurrentTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [isUpVoted, setIsUpVoted] = useState(false);
  const [upVotes, setUpvotes] = useState(null);
  const [isDeleteObjectModalOpen, setIsDeleteObjectModalOpen] = useState(false);
  const [dashboard, setDashboard] = useState({});
  const [openFeed, setOpenFeed] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);

  const getTabs = () => {
    const tabs = [
      {
        label: 'Viewer',
        value: 'viewer',
        icon: <ShowChart fontSize="small" />
      },
      { label: 'Overview', value: 'overview', icon: <Info fontSize="small" /> }
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

  const getUserDashboardVote = useCallback(
    async (dashboardUri) => {
      const response = await client.query(getVote(dashboardUri, 'dashboard'));
      if (!response.errors && response.data.getVote !== null) {
        setIsUpVoted(response.data.getVote.upvote);
      }
    },
    [client]
  );

  const reloadVotes = async () => {
    const response = await client.query(countUpVotes(params.uri, 'dashboard'));
    if (!response.errors && response.data.countUpVotes !== null) {
      setUpvotes(response.data.countUpVotes);
    } else {
      setUpvotes(0);
    }
  };

  const upVoteDashboard = async (dashboardUri) => {
    const response = await client.mutate(
      upVote({
        targetUri: dashboardUri,
        targetType: 'dashboard',
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
    const response = await client.query(getDashboard(params.uri));
    if (response.data.getDashboard !== null) {
      setDashboard(response.data.getDashboard);
      setUpvotes(response.data.getDashboard.upvotes);
      setIsAdmin(
        ['Admin', 'Creator'].indexOf(
          response.data.getDashboard.userRoleForDashboard
        ) !== -1
      );
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Dashboard not found';
      dispatch({ type: SET_ERROR, error });
    }
    setLoading(false);
  }, [client, dispatch, params.uri]);

  useEffect(() => {
    if (client) {
      getUserDashboardVote(params.uri).catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
      fetchItem().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client, dispatch, fetchItem, getUserDashboardVote, params.uri]);

  const handleTabsChange = (event, value) => {
    setCurrentTab(value);
  };
  const removeDashboard = async () => {
    const response = await client.mutate(
      deleteDashboard(dashboard.dashboardUri)
    );
    if (!response.errors) {
      handleDeleteObjectModalClose();
      enqueueSnackbar('Dashboard deleted', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      navigate('/console/dashboards');
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };

  if (loading) {
    return <CircularProgress />;
  }
  if (!dashboard) {
    return null;
  }

  return (
    <>
      <Helmet>
        <title>Dashboard: Dashboard Details | data.all</title>
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
                Dashboard {dashboard.label}
              </Typography>
              <Breadcrumbs
                aria-label="breadcrumb"
                separator={<ChevronRightIcon fontSize="small" />}
                sx={{ mt: 1 }}
              >
                <Link underline="hover" color="textPrimary" variant="subtitle2">
                  Play
                </Link>
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to="/console/dashboards"
                  variant="subtitle2"
                >
                  Dashboards
                </Link>
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to={`/console/dashboards/${dashboard.dashboardUri}`}
                  variant="subtitle2"
                >
                  {dashboard.label}
                </Link>
              </Breadcrumbs>
            </Grid>
            <Grid item>
              <Box sx={{ m: -1 }}>
                <UpVoteButton
                  upVoted={isUpVoted}
                  disabled={!isAdmin}
                  onClick={() => upVoteDashboard(dashboard.dashboardUri)}
                  upVotes={upVotes || 0}
                />
                {isAdmin && (
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
                )}
                <Button
                  color="primary"
                  component={RouterLink}
                  startIcon={<PencilAltIcon fontSize="small" />}
                  sx={{ mt: 1, mr: 1 }}
                  to={`/console/dashboards/${dashboard.dashboardUri}/edit`}
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
            {currentTab === 'viewer' && (
              <DashboardViewer dashboard={dashboard} />
            )}
            {currentTab === 'overview' && (
              <DashboardOverview dashboard={dashboard} />
            )}
            {isAdmin && currentTab === 'shares' && (
              <DashboardShares dashboard={dashboard} />
            )}
          </Box>
        </Container>
      </Box>
      <DeleteObjectWithFrictionModal
        objectName={dashboard.label}
        onApply={handleDeleteObjectModalClose}
        onClose={handleDeleteObjectModalClose}
        open={isDeleteObjectModalOpen}
        deleteFunction={removeDashboard}
        isAWSResource={false}
      />
      {openFeed && (
        <FeedComments
          objectOwner={dashboard.owner}
          targetType="Dashboard"
          targetUri={dashboard.dashboardUri}
          open={openFeed}
          onClose={() => setOpenFeed(false)}
        />
      )}
    </>
  );
};

export default DashboardView;
