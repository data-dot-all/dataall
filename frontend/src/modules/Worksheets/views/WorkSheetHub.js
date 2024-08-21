import React, { useState } from 'react';
import { Box, Tabs, Tab } from '@mui/material';
import WorksheetView from './WorksheetView';
import AISQLGenerator from './AISQLGen';
import DocumentSummarizer from './UnstructuredView';
import { isFeatureEnabled } from 'utils';

const WorksheetHub = () => {
  const [currentTab, setCurrentTab] = useState('Structured');

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
  };

  const getTabs = () => {
    const tabs = [];

    tabs.push({
      label: 'Structured Data',
      value: 'Structured',
      component: <WorksheetView />
    });
    if (isFeatureEnabled('worksheets', 'nlq')) {
      tabs.push({
        label: 'AI SQL Generator',
        value: '"AISQLGen"',
        component: <AISQLGenerator />
      });
      tabs.push({
        label: 'Document Summarizer',
        value: 'Unstructured',
        component: <DocumentSummarizer />
      });
    }

    return tabs;
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={currentTab} onChange={handleTabChange}>
          {getTabs().map(
            (tab) =>
              (tab.key === 'StructuredData' ||
                isFeatureEnabled('worksheets', 'nlq')) && (
                <Tab key={tab.value} value={tab.value} label={tab.label} />
              )
          )}
        </Tabs>
      </Box>
      {getTabs().map(
        (tab) =>
          currentTab === tab.value &&
          (tab.value === 'StructuredData' ||
            isFeatureEnabled('worksheets', 'nlq')) && (
            <Box key={tab.value}>{tab.component}</Box>
          )
      )}
    </Box>
  );
};

export default WorksheetHub;
