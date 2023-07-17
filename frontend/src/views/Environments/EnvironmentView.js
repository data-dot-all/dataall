import React, { useCallback, useEffect, useState } from 'react';
import { Link as RouterLink, useParams } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
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
import {
  FolderOpen,
  Info,
  LocalOffer,
  NotificationsActive,
  SupervisedUserCircleRounded,
  Warning
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import { useNavigate } from 'react-router';
import { FaAws, FaNetworkWired, FaTrash } from 'react-icons/fa';
import { GoDatabase } from 'react-icons/go';
import useSettings from '../../hooks/useSettings';
import getEnvironment from '../../api/Environment/getEnvironment';
import useClient from '../../hooks/useClient';
import ChevronRightIcon from '../../icons/ChevronRight';
import EnvironmentOverview from './EnvironmentOverview';
import EnvironmentDatasets from './EnvironmentDatasets';
import EnvironmentWarehouses from './EnvironmentWarehouses';
import Stack from '../Stack/Stack';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import archiveEnvironment from '../../api/Environment/archiveEnvironment';
import PencilAltIcon from '../../icons/PencilAlt';
import EnvironmentSubscriptions from './EnvironmentSubscriptions';
import EnvironmentTeams from './EnvironmentTeams';
import EnvironmentNetworks from '../Networks/NetworkList';
import DeleteObjectWithFrictionModal from '../../components/DeleteObjectWithFrictionModal';
import StackStatus from '../Stack/StackStatus';
import KeyValueTagList from '../KeyValueTags/KeyValueTagList';

const tabs = [
  { label: 'Overview', value: 'overview', icon: <Info fontSize="small" /> },
  {
    label: 'Teams',
    value: 'teams',
    icon: <SupervisedUserCircleRounded fontSize="small" />
  },
  {
    label: 'Datasets',
    value: 'datasets',
    icon: <FolderOpen fontSize="small" />
  },
  { label: 'Networks', value: 'networks', icon: <FaNetworkWired size={20} /> },
  /*{ label: 'Warehouses', value: 'warehouses', icon: <GoDatabase size={20} /> },*/
  {
    label: 'Subscriptions',
    value: 'subscriptions',
    icon: <NotificationsActive fontSize="small" />
  },
  { label: 'Tags', value: 'tags', icon: <LocalOffer fontSize="small" /> },
  { label: 'Stack', value: 'stack', icon: <FaAws size={20} /> }
];

const EnvironmentView = () => {
  const dispatch = useDispatch();
  const { settings } = useSettings();
  const { enqueueSnackbar } = useSnackbar();
  const navigate = useNavigate();
  const params = useParams();
  const client = useClient();
  const [currentTab, setCurrentTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [env, setEnv] = useState(null);
  const [stack, setStack] = useState(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [isArchiveObjectModalOpen, setIsArchiveObjectModalOpen] =
    useState(false);
  const handleArchiveObjectModalOpen = () => {
    setIsArchiveObjectModalOpen(true);
  };

  const handleArchiveObjectModalClose = () => {
    setIsArchiveObjectModalOpen(false);
  };
  const handleTabsChange = (event, value) => {
    setCurrentTab(value);
  };

  const archiveEnv = async () => {
    const response = await client.mutate(
      archiveEnvironment({
        environmentUri: env.environmentUri,
        deleteFromAWS: true
      })
    );
    if (!response.errors) {
      handleArchiveObjectModalClose();
      enqueueSnackbar('Environment deleted', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      navigate('/console/environments');
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };

  const fetchItem = useCallback(async () => {
    const response = await client.query(
      getEnvironment({ environmentUri: params.uri })
    );
    if (!response.errors && response.data.getEnvironment) {
      setEnv(response.data.getEnvironment);
      setStack(response.data.getEnvironment.stack);
      setIsAdmin(
        ['Admin', 'Owner'].indexOf(
          response.data.getEnvironment.userRoleInEnvironment
        ) !== -1
      );
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Environment not found';
      dispatch({ type: SET_ERROR, error });
    }
    setLoading(false);
  }, [client, dispatch, params.uri]);
  useEffect(() => {
    if (client) {
      fetchItem().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client, dispatch, fetchItem]);

  if (loading) {
    return <CircularProgress />;
  }
  if (!env) {
    return null;
  }

  return (
    <>
      <Helmet>
        <title>Environments: Environment Details | data.all</title>
      </Helmet>
      <StackStatus
        stack={stack}
        setStack={setStack}
        environmentUri={env.environmentUri}
      />
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
                Environment {env.label}
              </Typography>
              <Breadcrumbs
                aria-label="breadcrumb"
                separator={<ChevronRightIcon fontSize="small" />}
                sx={{ mt: 1 }}
              >
                <Link underline="hover" color="textPrimary" variant="subtitle2">
                  Organize
                </Link>
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to="/console/environments"
                  variant="subtitle2"
                >
                  Environments
                </Link>
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to={`/console/environments/${env.environmentUri}`}
                  variant="subtitle2"
                >
                  {env.label}
                </Link>
              </Breadcrumbs>
            </Grid>
            <Grid item>
              <Box sx={{ m: -1 }}>
                <Button
                  color="primary"
                  component={RouterLink}
                  startIcon={<PencilAltIcon fontSize="small" />}
                  sx={{ m: 1 }}
                  variant="outlined"
                  to={`/console/environments/${env.environmentUri}/edit`}
                >
                  Edit
                </Button>
                <Button
                  color="primary"
                  startIcon={<FaTrash size={15} />}
                  sx={{ m: 1 }}
                  onClick={handleArchiveObjectModalOpen}
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
              <EnvironmentOverview environment={env} />
            )}
            {currentTab === 'teams' && <EnvironmentTeams environment={env} />}
            {currentTab === 'datasets' && (
              <EnvironmentDatasets environment={env} />
            )}
            {currentTab === 'networks' && (
              <EnvironmentNetworks environment={env} />
            )}
            {currentTab === 'warehouses' && (
              <EnvironmentWarehouses environment={env} />
            )}
            {currentTab === 'subscriptions' && (
              <EnvironmentSubscriptions
                environment={env}
                fetchItem={fetchItem}
              />
            )}
            {isAdmin && currentTab === 'tags' && (
              <KeyValueTagList
                targetUri={env.environmentUri}
                targetType="environment"
              />
            )}
            {isAdmin && currentTab === 'stack' && (
              <Stack
                environmentUri={env.environmentUri}
                stackUri={env.stack.stackUri}
                targetUri={env.environmentUri}
                targetType="environment"
              />
            )}
          </Box>
        </Container>
      </Box>
      {isArchiveObjectModalOpen && (
        <DeleteObjectWithFrictionModal
          objectName={env.label}
          onApply={handleArchiveObjectModalClose}
          onClose={handleArchiveObjectModalClose}
          open={isArchiveObjectModalOpen}
          deleteFunction={archiveEnv}
          isAWSResource
          deleteMessage={
            <Card variant="outlined" sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="subtitle2" color="error">
                  <Warning sx={{ mr: 1 }} /> Remove all environment related
                  objects before proceeding with the deletion !
                </Typography>
              </CardContent>
            </Card>
          }
        />
      )}
    </>
  );
};

export default EnvironmentView;
