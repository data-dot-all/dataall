// TODO completely
import React, { useCallback, useEffect, useState } from 'react';
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
} from '@mui/material';
import { FaAws, FaTrash } from 'react-icons/fa';
import { SiJupyter } from 'react-icons/si';
import { useNavigate } from 'react-router';
import { LoadingButton } from '@mui/lab';
import { useSnackbar } from 'notistack';
import { Info } from '@mui/icons-material';
import {
  StackStatus,
  Stack
} from 'modules/Shared';
import { useClient } from 'services';
import {
  ChevronRightIcon,
  DeleteObjectWithFrictionModal,
  useSettings
} from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';


// TODO getOmicsRun does not exist
import {
  //getOmicsRun,
  deleteOmicsRun
} from '../services';
import {
  OmicsWorkflowsListItem,
  OmicsWorkflowDetails
} from '../components';


const tabs = [
  { label: 'Overview', value: 'overview', icon: <Info fontSize="small" /> },
  { label: 'Stack', value: 'stack', icon: <FaAws size={20} /> }
];

const OmicsWorkflowView = () => {
  const dispatch = useDispatch();
  const { settings } = useSettings();
  const { enqueueSnackbar } = useSnackbar();
  const params = useParams();
  const client = useClient();
  const navigate = useNavigate();
  const [currentTab, setCurrentTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [isDeleteObjectModalOpen, setIsDeleteObjectModalOpen] = useState(false);
  const [omicsRun, setOmicsRun] = useState(null);
  const [stack, setStack] = useState(null);
  //const [isOpeningOmicsRun, setIsOpeningOmicsRun] = useState(false);

  const handleDeleteObjectModalOpen = () => {
    setIsDeleteObjectModalOpen(true);
  };

  const handleDeleteObjectModalClose = () => {
    setIsDeleteObjectModalOpen(false);
  };

  const fetchItem = useCallback(async () => {
    setLoading(true);
    const response = await client.query(getOmicsRun(params.uri));
    if (!response.errors) {
      setOmicsRun(response.data.getOmicsRun);
      if (stack) {
        setStack(response.data.getOmicsRun.stack);
      }
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Omics Run not found';
      dispatch({ type: SET_ERROR, error });
    }
    setLoading(false);
  }, [client, dispatch, params.uri, stack]);

  // const getMLStudioPresignedUrl = async () => {
  //   setIsOpeningSagemakerStudio(true);
  //   const response = await client.query(
  //     getSagemakerStudioUserPresignedUrl(mlstudio.sagemakerStudioUserUri)
  //   );
  //   if (!response.errors) {
  //     window.open(response.data.getSagemakerStudioUserPresignedUrl);
  //   } else {
  //     dispatch({ type: SET_ERROR, error: response.errors[0].message });
  //   }
  //   setIsOpeningSagemakerStudio(false);
  // };

  useEffect(() => {
    if (client) {
      fetchItem().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client, dispatch, fetchItem]);

  const handleTabsChange = (event, value) => {
    setCurrentTab(value);
  };
  const removeOmicsRun = async (deleteFromAWS = false) => {
    const response = await client.mutate(
      deleteOmicsRun(omicsRun.omicsRun, deleteFromAWS)
    );
    if (!response.errors) {
      handleDeleteObjectModalClose();
      enqueueSnackbar('Omics Run deleted', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      navigate('/console/omics');
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };

  if (loading) {
    return <CircularProgress />;
  }
  if (!omicsRun) {
    return null;
  }

  return (
    <>
      <Helmet>
        <title>Omics: Run Details</title>
      </Helmet>
      <StackStatus
        stack={stack}
        setStack={setStack}
        environmentUri={omicsRun.environment?.environmentUri}
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
                Omics Run {omicsRun.label}
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
                  Workflows
                </Link>
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to={`/console/omics/${omicsRun.omicsRunrUri}`}
                  variant="subtitle2"
                >
                  {omicsRun.label}
                </Link>
              </Breadcrumbs>
            </Grid>
            <Grid item>
              <Box sx={{ m: -1 }}>
                <LoadingButton
                  //loading={isOpeningOmicsRun}
                  color="primary"
                  startIcon={<SiJupyter size={15} />}
                  sx={{ m: 1 }}
                  //onClick={getOmicsRunPresignedUrl}
                  type="button"
                  variant="outlined"
                >
                  Open Omics Run
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
              <OmicsWorkflowDetails omicsRun={omicsRun} />
            )}
            {currentTab === 'stack' && (
              <Stack
                environmentUri={omicsRun.environment.environmentUri}
                stackUri={omicsRun.stack.stackUri}
                targetUri={omicsRun.omicsRunUri}
                targetType="omics"
              />
            )}
          </Box>
        </Container>
      </Box>
      <DeleteObjectWithFrictionModal
        objectName={omicsRun.label}
        onApply={handleDeleteObjectModalClose}
        onClose={handleDeleteObjectModalClose}
        open={isDeleteObjectModalOpen}
        deleteFunction={removeOmicsRun}
        isAWSResource
      />
    </>
  );
};

export default OmicsWorkflowView;
