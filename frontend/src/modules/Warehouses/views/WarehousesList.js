import React, { useState } from 'react';
import { Helmet } from 'react-helmet-async';
import {
  Box,
  Container,
  Divider,
  Grid,
  Tab,
  Tabs,
  Typography
} from '@mui/material';
import { FaDna, FaGear } from 'react-icons/fa6';
import { useSettings } from 'design';

import { ConnectionsList, ConsumersList } from '../components';

const tabs = [
  {
    label: 'Producer Connections',
    value: 'connections',
    icon: <FaDna size={20} />
  },
  { label: 'Consumers', value: 'consumers', icon: <FaGear size={20} /> }
];

const WarehouseList = () => {
  const { settings } = useSettings();
  const [currentTab, setCurrentTab] = useState('connections');

  const handleTabsChange = (event, value) => {
    setCurrentTab(value);
  };

  return (
    <>
      <Helmet>
        <title>Warehouses | data.all</title>
      </Helmet>
      <Box
        sx={{
          backgroundColor: 'background.default',
          minHeight: '100%',
          py: 5
        }}
      >
        <Container maxWidth={settings.compact ? 'xl' : false}>
          <Grid container justifyContent="space-between" spacing={3}>
            <Grid item>
              <Typography color="textPrimary" variant="h5">
                Warehouses
              </Typography>
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
              centered
            >
              {tabs.map((tab) => (
                <Tab
                  key={tab.value}
                  label={tab.label}
                  value={tab.value}
                  icon={tab.icon}
                />
              ))}
            </Tabs>
          </Box>
          <Divider />
          <Box sx={{ mt: 3 }}>
            {currentTab === 'connections' && <ConnectionsList />}
            {currentTab === 'consumers' && <ConsumersList />}
          </Box>
        </Container>
      </Box>
    </>
  );
};

export default WarehouseList;
