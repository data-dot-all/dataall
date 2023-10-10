// TODO completely
import React, { useCallback, useEffect, useState } from 'react';
import { Link as RouterLink, useParams } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import {
  Box,
  Button,
  Breadcrumbs,
  CircularProgress,
  Container,
  Divider,
  Grid,
  Link,
  Tab,
  Tabs,
  Typography
} from '@mui/material';
import { Info } from '@mui/icons-material';
import { useClient } from 'services';
import { ChevronRightIcon, useSettings, PlusIcon } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';

import { getOmicsWorkflow } from '../services';
// import { OmicsWorkflowsListItem, OmicsWorkflowDetails } from '../components';
import { OmicsWorkflowDetails } from '../components';

const tabs = [
  { label: 'Overview', value: 'overview', icon: <Info fontSize="small" /> }
];

const OmicsWorkflowView = () => {
  const dispatch = useDispatch();
  const { settings } = useSettings();
  // const { enqueueSnackbar } = useSnackbar();
  const params = useParams();
  const client = useClient();
  // const navigate = useNavigate();
  const [currentTab, setCurrentTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [omicsWorkflow, setOmicsWorkflow] = useState(null);

  const fetchItem = useCallback(async () => {
    setLoading(true);
    const response = await client.query(getOmicsWorkflow(params.uri));
    if (!response.errors) {
      setOmicsWorkflow(response.data.getOmicsWorkflow);
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Omics Workflownot found';
      dispatch({ type: SET_ERROR, error });
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
  if (!omicsWorkflow) {
    return null;
  }

  return (
    <>
      <Helmet>
        <title>Omics: Workflow Details</title>
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
                Omics Workflow {omicsWorkflow.name}
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
                  to={`/console/omics/workflows/${omicsWorkflow.id}`}
                  variant="subtitle2"
                >
                  {omicsWorkflow.name}
                </Link>
              </Breadcrumbs>
            </Grid>
          </Grid>

          <Grid>
            <Box sx={{ m: -1 }}>
              <Button
                color="primary"
                component={RouterLink}
                startIcon={<PlusIcon fontSize="small" />}
                sx={{ m: 1 }}
                to={`/console/omics/runs/new/${omicsWorkflow.id}`}
                variant="contained"
              >
                Create Run
              </Button>
            </Box>
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
              <OmicsWorkflowDetails workflow={omicsWorkflow} />
            )}
          </Box>
        </Container>
      </Box>
    </>
  );
};

export default OmicsWorkflowView;
