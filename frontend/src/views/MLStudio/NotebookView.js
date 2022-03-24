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
import { FaAws, FaTrash, SiJupyter } from 'react-icons/all';
import { useNavigate } from 'react-router';
import { LoadingButton } from '@material-ui/lab';
import { useSnackbar } from 'notistack';
import { Info } from '@material-ui/icons';
import useSettings from '../../hooks/useSettings';
import useClient from '../../hooks/useClient';
import ChevronRightIcon from '../../icons/ChevronRight';
import Stack from '../Stack/Stack';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import DeleteObjectWithFrictionModal from '../../components/DeleteObjectWithFrictionModal';
import getSagemakerStudioUserProfile from '../../api/SagemakerStudio/getSagemakerStudioUserProfile';
import deleteSagemakerStudioUserProfile from '../../api/SagemakerStudio/deleteSagemakerStudioUserProfile';
import NotebookOverview from './NotebookOverview';
import getSagemakerStudioUserProfilePresignedUrl from '../../api/SagemakerStudio/getSagemakerStudioUserProfilePresignedUrl';
import StackStatus from '../Stack/StackStatus';

const tabs = [
  { label: 'Overview', value: 'overview', icon: <Info fontSize="small" /> },
  { label: 'Stack', value: 'stack', icon: <FaAws size={20} /> }
];

const NotebookView = () => {
  const dispatch = useDispatch();
  const { settings } = useSettings();
  const { enqueueSnackbar } = useSnackbar();
  const params = useParams();
  const client = useClient();
  const navigate = useNavigate();
  const [currentTab, setCurrentTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [isDeleteObjectModalOpen, setIsDeleteObjectModalOpen] = useState(false);
  const [notebook, setNotebook] = useState(null);
  const [stack, setStack] = useState(null);
  const [isOpeningSagemakerStudio, setIsOpeningSagemakerStudio] = useState(false);

  const handleDeleteObjectModalOpen = () => {
    setIsDeleteObjectModalOpen(true);
  };

  const handleDeleteObjectModalClose = () => {
    setIsDeleteObjectModalOpen(false);
  };

  const fetchItem = async () => {
    setLoading(true);
    const response = await client.query(getSagemakerStudioUserProfile(params.uri));
    if (!response.errors) {
      setNotebook(response.data.getSagemakerStudioUserProfile);
      if (stack) {
        setStack(response.data.getSagemakerStudioUserProfile.stack);
      }
    } else {
      const error = response.errors ? response.errors[0].message : 'Notebook not found';
      dispatch({ type: SET_ERROR, error });
    }
    setLoading(false);
  };

  const getNotebookPresignedUrl = async () => {
    setIsOpeningSagemakerStudio(true);
    const response = await client.query(getSagemakerStudioUserProfilePresignedUrl(notebook.sagemakerStudioUserProfileUri));
    if (!response.errors) {
      window.open(response.data.getSagemakerStudioUserProfilePresignedUrl);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setIsOpeningSagemakerStudio(false);
  };

  useEffect(() => {
    if (client) {
      fetchItem().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client]);

  const handleTabsChange = (event, value) => {
    setCurrentTab(value);
  };
  const removeNotebook = async (deleteFromAWS = false) => {
    const response = await client.mutate(deleteSagemakerStudioUserProfile(notebook.sagemakerStudioUserProfileUri, deleteFromAWS));
    if (!response.errors) {
      handleDeleteObjectModalClose();
      enqueueSnackbar('Notebook deleted', {
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
  if (!notebook) {
    return null;
  }

  return (
    <>
      <Helmet>
        <title>ML Studio: Notebook Details | data.all</title>
      </Helmet>
      <StackStatus
        stack={stack}
        setStack={setStack}
        environmentUri={notebook.environment?.environmentUri}
      />
      <Box
        sx={{
          backgroundColor: 'background.default',
          minHeight: '100%',
          py: 8
        }}
      >
        <Container maxWidth={settings.compact ? 'xl' : false}>
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
                Notebook
                {' '}
                {notebook.label}
              </Typography>
              <Breadcrumbs
                aria-label="breadcrumb"
                separator={<ChevronRightIcon fontSize="small" />}
                sx={{ mt: 1 }}
              >
                <Link
                  color="textPrimary"
                  variant="subtitle2"
                >
                  Play
                </Link>
                <Link
                  color="textPrimary"
                  component={RouterLink}
                  to="/console/mlstudio"
                  variant="subtitle2"
                >
                  ML Studio
                </Link>
                <Link
                  color="textPrimary"
                  component={RouterLink}
                  to={`/console/mlstudio/${notebook.sagemakerStudioUserProfileUri}`}
                  variant="subtitle2"
                >
                  {notebook.label}
                </Link>
              </Breadcrumbs>
            </Grid>
            <Grid item>
              <Box sx={{ m: -1 }}>
                <LoadingButton
                  pending={isOpeningSagemakerStudio}
                  color="primary"
                  startIcon={<SiJupyter size={15} />}
                  sx={{ m: 1 }}
                  onClick={getNotebookPresignedUrl}
                  type="button"
                  variant="outlined"
                >
                  Open Notebook
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
            && <NotebookOverview notebook={notebook} />}
            {currentTab === 'stack'
                      && (
                      <Stack
                        environmentUri={notebook.environment.environmentUri}
                        stackUri={notebook.stack.stackUri}
                        targetUri={notebook.sagemakerStudioUserProfileUri}
                        targetType="mlstudio"
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
        isAWSResource
      />
    </>
  );
};

export default NotebookView;
