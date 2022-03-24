import React, { useEffect, useState } from 'react';
import { Link as RouterLink, useParams } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
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
} from '@material-ui/core';
import { FaAws, FaTrash } from 'react-icons/all';
import { useNavigate } from 'react-router';
import * as PropTypes from 'prop-types';
import { Folder, Info, LocalOffer, PauseOutlined, PlayArrowOutlined } from '@material-ui/icons';
import { useSnackbar } from 'notistack';
import { LoadingButton } from '@material-ui/lab';
import useSettings from '../../hooks/useSettings';
import useClient from '../../hooks/useClient';
import ChevronRightIcon from '../../icons/ChevronRight';
import Stack from '../Stack/Stack';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import WarehouseOverview from './WarehouseOverview';
import DeleteObjectWithFrictionModal from '../../components/DeleteObjectWithFrictionModal';
import deleteRedshiftCluster from '../../api/RedshiftCluster/deleteCluster';
import getCluster from '../../api/RedshiftCluster/getCluster';
import pauseRedshiftCluster from '../../api/RedshiftCluster/pauseCluster';
import resumeRedshiftCluster from '../../api/RedshiftCluster/resumeCluster';
import WarehouseDatasets from './WarehouseDatasets';
import StackStatus from '../Stack/StackStatus';
import KeyValueTagList from '../KeyValueTags/KeyValueTagList';

const tabs = [
  { label: 'Overview', value: 'overview', icon: <Info /> },
  { label: 'Datasets', value: 'datasets', icon: <Folder /> },
  { label: 'Tags', value: 'tags', icon: <LocalOffer /> },
  { label: 'Stack', value: 'stack', icon: <FaAws size={20} /> }
];
function WarehouseViewPageHeader({ warehouse, deleteCluster, pauseCluster, resumeCluster, resumeLoader, pauseLoader }) {
  return (
    <Grid
      container
      justifyContent="space-between"
      spacing={3}
    >
      <Grid item>
        <Typography
          color="textPrimary"
          variant="h5"
        >
          Warehouse
          {' '}
          {warehouse.label}
        </Typography>
        <Breadcrumbs
          aria-label="breadcrumb"
          separator={<ChevronRightIcon fontSize="small" />}
          sx={{ mt: 1 }}
        >
          <Typography
            color="textPrimary"
            variant="subtitle2"
          >
            Organize
          </Typography>
          <Link
            color="textPrimary"
            component={RouterLink}
            to="/console/environments"
            variant="subtitle2"
          >
            Environments
          </Link>
          <Link
            color="textPrimary"
            component={RouterLink}
            to={`/console/environments/${warehouse.environment.environmentUri}`}
            variant="subtitle2"
          >
            {warehouse.environment.label}
          </Link>
          <Link
            color="textPrimary"
            component={RouterLink}
            to={`/console/warehouse/${warehouse.clusterUri}`}
            variant="subtitle2"
          >
            {warehouse.label}
          </Link>
        </Breadcrumbs>
      </Grid>
      <Grid item>
        <Box sx={{ m: -1 }}>
          {resumeCluster && (
          <LoadingButton
            pending={resumeLoader}
            color="primary"
            startIcon={<PlayArrowOutlined size={15} />}
            sx={{ mt: 1, mr: 1 }}
            onClick={resumeCluster}
            type="button"
            variant="outlined"
          >
            Resume
          </LoadingButton>
          )}
          {pauseCluster && (
          <LoadingButton
            pending={pauseLoader}
            color="primary"
            startIcon={<PauseOutlined size={15} />}
            sx={{ mt: 1, mr: 1 }}
            onClick={pauseCluster}
            type="button"
            variant="outlined"
          >
            Pause
          </LoadingButton>
          )}
          <Button
            color="primary"
            startIcon={<FaTrash size={15} />}
            sx={{ mt: 1 }}
            onClick={deleteCluster}
            type="button"
            variant="outlined"
          >
            Delete
          </Button>
        </Box>
      </Grid>
    </Grid>
  );
}

WarehouseViewPageHeader.propTypes = {
  warehouse: PropTypes.object.isRequired,
  deleteCluster: PropTypes.func.isRequired,
  pauseCluster: PropTypes.func.isRequired,
  resumeCluster: PropTypes.func.isRequired,
  resumeLoader: PropTypes.bool.isRequired,
  pauseLoader: PropTypes.bool.isRequired
};
const WarehouseView = () => {
  const dispatch = useDispatch();
  const { settings } = useSettings();
  const { enqueueSnackbar } = useSnackbar();
  const params = useParams();
  const client = useClient();
  const navigate = useNavigate();
  const [currentTab, setCurrentTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [warehouse, setWarehouse] = useState(null);
  const [stack, setStack] = useState(null);
  const [showResumeCluster, setShowResumeCluster] = useState(false);
  const [showPauseCluster, setShowPauseCluster] = useState(false);
  const [isDeleteObjectModalOpen, setIsDeleteObjectModalOpen] = useState(false);
  const handleDeleteObjectModalOpen = () => {
    setIsDeleteObjectModalOpen(true);
  };

  const handleDeleteObjectModalClose = () => {
    setIsDeleteObjectModalOpen(false);
  };

  const fetchItem = async () => {
    setLoading(true);
    const response = await client.query(getCluster(params.uri));
    if (!response.errors && response.data.getRedshiftCluster !== null) {
      setWarehouse(response.data.getRedshiftCluster);
      if (stack) {
        setStack(response.data.getRedshiftCluster.stack);
      }
    } else {
      const error = response.errors ? response.errors[0].message : 'Warehouse not found';
      dispatch({ type: SET_ERROR, error });
    }
    setLoading(false);
  };
  useEffect(() => {
    if (client) {
      fetchItem().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client]);

  const handleTabsChange = (event, value) => {
    setCurrentTab(value);
  };

  const deleteCluster = async (deleteFromAWS = false) => {
    const response = await client.mutate(deleteRedshiftCluster(warehouse.clusterUri, deleteFromAWS));
    if (!response.errors) {
      handleDeleteObjectModalClose();
      navigate(`/console/environments/${warehouse.environment.environmentUri}`);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };

  const pauseCluster = async () => {
    const response = await client.mutate(pauseRedshiftCluster(warehouse.clusterUri));
    if (!response.errors) {
      enqueueSnackbar('Amazon Redshift cluster pause started', {
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
    setShowPauseCluster(false);
  };
  const resumeCluster = async () => {
    const response = await client.mutate(resumeRedshiftCluster(warehouse.clusterUri));
    if (!response.errors) {
      enqueueSnackbar('Amazon Redshift cluster resume started', {
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
    setShowResumeCluster(false);
  };

  if (loading) {
    return <CircularProgress />;
  }
  if (!warehouse) {
    return null;
  }

  return (
    <>
      <Helmet>
        <title>Warehouses: Warehouse Details | data.all</title>
      </Helmet>
      <StackStatus
        stack={stack}
        setStack={setStack}
        environmentUri={warehouse.environment?.environmentUri}
      />
      <Box
        sx={{
          backgroundColor: 'background.default',
          minHeight: '100%',
          py: 8
        }}
      >
        <Container maxWidth={settings.compact ? 'xl' : false}>
          <WarehouseViewPageHeader
            warehouse={warehouse}
            deleteCluster={handleDeleteObjectModalOpen}
            resumeCluster={warehouse.status === 'paused' ? resumeCluster : null}
            resumeLoader={showResumeCluster}
            pauseLoader={showPauseCluster}
            pauseCluster={warehouse.status === 'available' ? pauseCluster : null}
          />
          <Box sx={{ mt: 3 }}>
            <Tabs
              indicatorColor="primary"
              onChange={handleTabsChange}
              scrollButtons="auto"
              textColor="primary"
              value={currentTab}
              variant="scrollable"
            >
              {tabs.map((tab) => (
                <Tab
                  key={tab.value}
                  label={tab.label}
                  value={tab.value}
                  icon={settings.tabIcons ? tab.icon : null}
                />
              ))}
            </Tabs>
          </Box>
          <Divider />
          <Box sx={{ mt: 3 }}>
            {currentTab === 'overview'
            && <WarehouseOverview warehouse={warehouse} />}
            {currentTab === 'datasets'
            && (
            <WarehouseDatasets warehouse={warehouse} />
            )}
            {currentTab === 'tags'
            && (
            <KeyValueTagList
              targetUri={warehouse.clusterUri}
              targetType="redshift"
            />
            )}
            {currentTab === 'stack'
            && (
            <Stack
              environmentUri={warehouse.environment.environmentUri}
              stackUri={warehouse.stack.stackUri}
              targetUri={warehouse.clusterUri}
              targetType="redshift"
            />
            )}
          </Box>
        </Container>
      </Box>
      <DeleteObjectWithFrictionModal
        objectName={warehouse.label}
        onApply={handleDeleteObjectModalClose}
        onClose={handleDeleteObjectModalClose}
        open={isDeleteObjectModalOpen}
        deleteFunction={deleteCluster}
        isAWSResource
      />
    </>
  );
};

export default WarehouseView;
