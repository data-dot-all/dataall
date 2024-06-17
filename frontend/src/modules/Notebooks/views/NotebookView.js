import { Info, LocalOffer, RefreshRounded } from '@mui/icons-material';
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
import { BiStopCircle } from 'react-icons/bi';
import { FaAws, FaTrash } from 'react-icons/fa';
import { SiJupyter } from 'react-icons/si';
import { VscDebugStart } from 'react-icons/vsc';
import { useNavigate } from 'react-router';
import { Link as RouterLink, useParams } from 'react-router-dom';
import {
  ChevronRightIcon,
  DeleteObjectWithFrictionModal,
  useSettings
} from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import { KeyValueTagList, Stack } from 'modules/Shared';
import { NotebookOverview } from '../components';
import {
  deleteSagemakerNotebook,
  getSagemakerNotebook,
  getSagemakerNotebookPresignedUrl,
  startSagemakerNotebook,
  stopSagemakerNotebook
} from '../services';

/**
 * @description NotebookView component.
 * @returns {JSX.Element|null}
 */
const NotebookView = () => {
  const getTabs = (isAdvancedMode) =>
    isAdvancedMode
      ? [
          {
            label: 'Overview',
            value: 'overview',
            icon: <Info fontSize="small" />
          },
          {
            label: 'Tags',
            value: 'tags',
            icon: <LocalOffer fontSize="small" />
          },
          { label: 'Stack', value: 'stack', icon: <FaAws size={20} /> }
        ]
      : [];
  const dispatch = useDispatch();
  const { settings } = useSettings();
  const { enqueueSnackbar } = useSnackbar();
  const params = useParams();
  const client = useClient();
  const navigate = useNavigate();
  const [currentTab, setCurrentTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [isStoppingNotebook, setIsStoppingNotebook] = useState(false);
  const [isStartingNotebook, setIsStartingNotebook] = useState(false);
  const [isRefreshingNotebook, setIsRefreshingNotebook] = useState(false);
  const [notebook, setNotebook] = useState(null);
  const [isOpeningSagemakerNotebook, setIsOpeningSagemakerNotebook] =
    useState(false);
  const [isStoppedInstance, setIsStoppedInstance] = useState({});
  const [isNotFoundInstance, setNotFoundInstance] = useState({});
  const [isDeleteObjectModalOpen, setIsDeleteObjectModalOpen] = useState(false);
  const [tabs, setTabs] = useState(getTabs(settings.isAdvancedMode));

  useEffect(
    () => setTabs(getTabs(settings.isAdvancedMode)),
    [settings.isAdvancedMode]
  );

  const handleDeleteObjectModalOpen = () => {
    setIsDeleteObjectModalOpen(true);
  };

  const handleDeleteObjectModalClose = () => {
    setIsDeleteObjectModalOpen(false);
  };

  const getNotebookInstance = useCallback(async () => {
    const response = await client.query(getSagemakerNotebook(params.uri));
    if (!response.errors) {
      setNotebook(response.data.getSagemakerNotebook);
      const status = response.data.getSagemakerNotebook.NotebookInstanceStatus;
      if (status === 'Stopped' || status === 'Stopping') {
        setIsStoppedInstance(true);
      } else {
        setIsStoppedInstance(false);
      }
      if (status === 'NotFound' || status === 'Pending') {
        setNotFoundInstance(true);
      } else {
        setNotFoundInstance(false);
      }
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Notebook not found';
      dispatch({ type: SET_ERROR, error });
    }
  }, [params.uri, client, dispatch]);

  const refreshInstance = async () => {
    setIsRefreshingNotebook(true);
    await getNotebookInstance();
    enqueueSnackbar('Notebook instance reloaded', {
      anchorOrigin: {
        horizontal: 'right',
        vertical: 'top'
      },
      variant: 'success'
    });
    setIsRefreshingNotebook(false);
  };

  const fetchItem = useCallback(async () => {
    setLoading(true);
    await getNotebookInstance();
    setLoading(false);
  }, [getNotebookInstance]);

  const removeNotebook = async (deleteFromAWS = false) => {
    const response = await client.mutate(
      deleteSagemakerNotebook(notebook.notebookUri, deleteFromAWS)
    );
    if (!response.errors) {
      handleDeleteObjectModalClose();
      enqueueSnackbar('Notebook deleted', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      navigate('/console/notebooks');
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };
  const getNotebookPresignedUrl = async () => {
    setIsOpeningSagemakerNotebook(true);
    const response = await client.query(
      getSagemakerNotebookPresignedUrl(notebook.notebookUri)
    );
    if (!response.errors) {
      window.open(response.data.getSagemakerNotebookPresignedUrl);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setIsOpeningSagemakerNotebook(false);
  };

  useEffect(() => {
    if (client) {
      fetchItem().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client, fetchItem, dispatch]);

  const handleTabsChange = (event, value) => {
    setCurrentTab(value);
  };
  const stopNotebook = async () => {
    setIsStoppingNotebook(true);
    const response = await client.mutate(
      stopSagemakerNotebook(notebook.notebookUri)
    );
    if (!response.errors) {
      enqueueSnackbar('Notebook instance is stopping', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      setIsStoppingNotebook(false);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };

  const startNotebook = async () => {
    setIsStartingNotebook(true);
    const response = await client.mutate(
      startSagemakerNotebook(notebook.notebookUri)
    );
    if (!response.errors) {
      enqueueSnackbar('Notebook instance starting', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      setIsStartingNotebook(false);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };

  if (loading) {
    return <CircularProgress />;
  }
  if (!notebook) {
    return null;
  }

  /**
   * @description Tab header.
   * @type {JSX.Element}
   */
  const tabHeader = (
    <>
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
    </>
  );

  return (
    <>
      <Helmet>
        <title>Notebooks: Notebook Details | data.all</title>
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
                Notebook {notebook.label}
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
                  to="/console/notebooks"
                  variant="subtitle2"
                >
                  Notebooks
                </Link>
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to={`/console/notebooks/${notebook.notebookUri}`}
                  variant="subtitle2"
                >
                  {notebook.label}
                </Link>
              </Breadcrumbs>
            </Grid>
            <Grid item>
              <Box sx={{ m: -1 }}>
                <LoadingButton
                  disabled={isStoppedInstance || isNotFoundInstance}
                  loading={isOpeningSagemakerNotebook}
                  color="primary"
                  startIcon={<SiJupyter size={15} />}
                  sx={{ m: 1 }}
                  onClick={getNotebookPresignedUrl}
                  type="button"
                  variant="outlined"
                >
                  Open JupyterLab
                </LoadingButton>
                <LoadingButton
                  disabled={isStoppedInstance || isNotFoundInstance}
                  loading={isStoppingNotebook}
                  color="primary"
                  startIcon={<BiStopCircle size={15} />}
                  sx={{ m: 1 }}
                  onClick={stopNotebook}
                  type="button"
                  variant="outlined"
                >
                  Stop Instance
                </LoadingButton>
                <LoadingButton
                  disabled={!isStoppedInstance || isNotFoundInstance}
                  loading={isStartingNotebook}
                  color="primary"
                  startIcon={<VscDebugStart size={15} />}
                  sx={{ m: 1 }}
                  onClick={startNotebook}
                  type="button"
                  variant="outlined"
                >
                  Start Instance
                </LoadingButton>
                <LoadingButton
                  color="primary"
                  loading={isRefreshingNotebook}
                  startIcon={<RefreshRounded fontSize="small" />}
                  sx={{ m: 1 }}
                  variant="outlined"
                  onClick={refreshInstance}
                >
                  Refresh
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
          {settings.isAdvancedMode && tabHeader}
          <Box sx={{ mt: 3 }}>
            {currentTab === 'overview' && (
              <NotebookOverview notebook={notebook} />
            )}
            {currentTab === 'tags' && (
              <KeyValueTagList
                targetUri={notebook.notebookUri}
                targetType="notebook"
              />
            )}
            {currentTab === 'stack' && (
              <Stack
                environmentUri={notebook.environment.environmentUri}
                stackUri={notebook.stack.stackUri}
                targetUri={notebook.notebookUri}
                targetType="notebook"
              />
            )}
          </Box>
        </Container>
      </Box>
      <DeleteObjectWithFrictionModal
        objectName={notebook.label}
        onApply={handleDeleteObjectModalClose}
        onClose={handleDeleteObjectModalClose}
        open={isDeleteObjectModalOpen}
        deleteFunction={removeNotebook}
      />
    </>
  );
};

export default NotebookView;
