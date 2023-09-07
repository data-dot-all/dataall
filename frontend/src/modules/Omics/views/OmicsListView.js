import React, { useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { Box, Container, Divider, Tab, Tabs } from '@mui/material';
import { FaAws } from 'react-icons/fa';
import { Info } from '@mui/icons-material';
import { useSettings } from 'design';

import { OmicsRunList } from './OmicsRunsList';
import { OmicsWorkflowsList } from './OmicsWorkflowsList';
//TODO: mostly done, but review
const tabs = [
  { label: 'Workflows', value: 'workflows', icon: <Info fontSize="small" /> },
  { label: 'Runs', value: 'runs', icon: <FaAws size={20} /> }
];

const OmicsView = () => {
  const { settings } = useSettings();
  const [currentTab, setCurrentTab] = useState('workflows');

  const handleTabsChange = (event, value) => {
    setCurrentTab(value);
  };

  return (
    <>
      <Helmet>
        <title>Omics</title>
      </Helmet>
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
      <Box
        sx={{
          backgroundColor: 'background.default',
          minHeight: '100%',
          py: 8
        }}
      >
        <Container maxWidth={settings.compact ? 'xl' : false}>
          <Box sx={{ mt: 3 }}>
            {currentTab === 'workflows' && <OmicsWorkflowsList />}
            {currentTab === 'runs' && <OmicsRunList />}
          </Box>
        </Container>
      </Box>
    </>
  );
};

export default OmicsView;
