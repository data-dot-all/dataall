import {
  Alert,
  Box,
  Breadcrumbs,
  Card,
  CardHeader,
  CardContent,
  Container,
  Divider,
  Grid,
  Link,
  Tab,
  Tabs,
  Typography
} from '@mui/material';
import { useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { Link as RouterLink } from 'react-router-dom';
import { ChevronRightIcon, LoadingScreen, useSettings } from 'design';
import { AdministrationTeams, DashboardViewer } from '../components';
import { MaintenanceViewer } from '../../Maintenance/components/MaintenanceViewer';
import { isModuleEnabled, ModuleNames, isTenantUser } from 'utils';
import config from '../../../generated/config.json';
import { useGroups } from 'services';

const tabs = [{ label: 'Teams', value: 'teams' }];

if (config.core.features.enable_quicksight_monitoring) {
  tabs.push({ label: 'Monitoring', value: 'dashboard' });
}

if (isModuleEnabled(ModuleNames.MAINTENANCE)) {
  tabs.push({ label: 'Maintenance', value: 'maintenance' });
}

const AdministrationView = () => {
  const { settings } = useSettings();
  const groups = useGroups();
  const [currentTab, setCurrentTab] = useState('teams');

  const handleTabsChange = (event, value) => {
    setCurrentTab(value);
  };

  if (!groups) {
    return <LoadingScreen />;
  }

  return !isTenantUser(groups) ? (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        backgroundColor: 'background.default'
      }}
    >
      <Card sx={{ maxWidth: 400 }}>
        <CardHeader
          title="Unauthorized Access"
          sx={{ bgcolor: 'error.main', color: 'error.contrastText' }}
        />
        <CardContent>
          <Alert severity="error">
            You do not have permission to view this page. Please contact an
            administrator if you believe this is an error.
          </Alert>
        </CardContent>
      </Card>
    </Box>
  ) : (
    <>
      <Helmet>
        <title>Administration: Settings | data.all</title>
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
                Settings
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
                  to="/console/administration"
                  variant="subtitle2"
                >
                  Administration
                </Link>
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to="/console/administration"
                  variant="subtitle2"
                >
                  Settings
                </Link>
              </Breadcrumbs>
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
                <Tab key={tab.value} label={tab.label} value={tab.value} />
              ))}
            </Tabs>
          </Box>
          <Divider />
          <Box sx={{ mt: 3 }}>
            {currentTab === 'teams' && <AdministrationTeams />}
            {currentTab === 'dashboard' && <DashboardViewer />}
            {currentTab === 'maintenance' && <MaintenanceViewer />}
          </Box>
        </Container>
      </Box>
    </>
  );
};

export default AdministrationView;
