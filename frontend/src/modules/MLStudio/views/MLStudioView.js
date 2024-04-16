import { Info } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
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
import { FaAws, FaTrash } from 'react-icons/fa';
import { SiJupyter } from 'react-icons/si';
import { useNavigate } from 'react-router';
import { Link as RouterLink, useParams } from 'react-router-dom';
import {
  ChevronRightIcon,
  DeleteObjectWithFrictionModal,
  useSettings
} from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import {
  deleteSagemakerStudioUser,
  getSagemakerStudioUser,
  getSagemakerStudioUserPresignedUrl
} from '../services';
import { useClient } from 'services';
import { Stack } from 'modules/Shared';
import { MLStudioOverview } from '../components';

const tabs = [
  { label: 'Overview', value: 'overview', icon: <Info fontSize="small" /> },
  { label: 'Stack', value: 'stack', icon: <FaAws size={20} /> }
];

const MLStudioView = () => {
  const dispatch = useDispatch();
  const { settings } = useSettings();
  const { enqueueSnackbar } = useSnackbar();
  const params = useParams();
  const client = useClient();
  const navigate = useNavigate();
  const [currentTab, setCurrentTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [isDeleteObjectModalOpen, setIsDeleteObjectModalOpen] = useState(false);
  const [mlstudio, setMLStudio] = useState(null);
  const [isOpeningSagemakerStudio, setIsOpeningSagemakerStudio] =
    useState(false);

  const handleDeleteObjectModalOpen = () => {
    setIsDeleteObjectModalOpen(true);
  };

  const handleDeleteObjectModalClose = () => {
    setIsDeleteObjectModalOpen(false);
  };

  const fetchItem = useCallback(async () => {
    setLoading(true);
    const response = await client.query(getSagemakerStudioUser(params.uri));
    if (!response.errors) {
      setMLStudio(response.data.getSagemakerStudioUser);
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'ML Studio User not found';
      dispatch({ type: SET_ERROR, error });
    }
    setLoading(false);
  }, [client, dispatch, params.uri]);

  const getMLStudioPresignedUrl = async () => {
    setIsOpeningSagemakerStudio(true);
    const response = await client.query(
      getSagemakerStudioUserPresignedUrl(mlstudio.sagemakerStudioUserUri)
    );
    if (!response.errors) {
      window.open(response.data.getSagemakerStudioUserPresignedUrl);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setIsOpeningSagemakerStudio(false);
  };

  useEffect(() => {
    if (client) {
      fetchItem().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client, dispatch, fetchItem]);

  const handleTabsChange = (event, value) => {
    setCurrentTab(value);
  };
  const removeMLStudio = async (deleteFromAWS = false) => {
    const response = await client.mutate(
      deleteSagemakerStudioUser(mlstudio.sagemakerStudioUserUri, deleteFromAWS)
    );
    if (!response.errors) {
      handleDeleteObjectModalClose();
      enqueueSnackbar('ML Studio User deleted', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      navigate('/console/mlstudio');
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };

  if (loading) {
    return <CircularProgress />;
  }
  if (!mlstudio) {
    return null;
  }

  return (
    <>
      <Helmet>
        <title>ML Studio: User Details | DataStudio</title>
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
                ML Studio User {mlstudio.label}
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
                  to="/console/mlstudio"
                  variant="subtitle2"
                >
                  ML Studio
                </Link>
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to={`/console/mlstudio/${mlstudio.sagemakerStudioUserUri}`}
                  variant="subtitle2"
                >
                  {mlstudio.label}
                </Link>
              </Breadcrumbs>
            </Grid>
            <Grid item>
              <Box sx={{ m: -1 }}>
                <LoadingButton
                  loading={isOpeningSagemakerStudio}
                  color="primary"
                  startIcon={<SiJupyter size={15} />}
                  sx={{ m: 1 }}
                  onClick={getMLStudioPresignedUrl}
                  type="button"
                  variant="outlined"
                >
                  Open ML Studio
                </LoadingButton>
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
              <MLStudioOverview mlstudiouser={mlstudio} />
            )}
            {currentTab === 'stack' && (
              <Stack
                environmentUri={mlstudio.environment.environmentUri}
                stackUri={mlstudio.stack.stackUri}
                targetUri={mlstudio.sagemakerStudioUserUri}
                targetType="mlstudio"
              />
            )}
          </Box>
        </Container>
      </Box>
      <DeleteObjectWithFrictionModal
        objectName={mlstudio.label}
        onApply={handleDeleteObjectModalClose}
        onClose={handleDeleteObjectModalClose}
        open={isDeleteObjectModalOpen}
        deleteFunction={removeMLStudio}
        isAWSResource
      />
    </>
  );
};

export default MLStudioView;
