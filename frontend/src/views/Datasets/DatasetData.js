import PropTypes from 'prop-types';
import React from 'react';
import { Box } from '@mui/material';
import DatasetTables from './DatasetTables';
import DatasetFolders from './DatasetFolders';
import config from '../../generated/config.json';

const DatasetData = ({ dataset, isAdmin }) => (
  <Box>
    <Box>
      <DatasetTables dataset={dataset} isAdmin={isAdmin} />
    </Box>
    {config.modules.datasets.features.file_actions === true && (
      <Box sx={{ mt: 3 }}>
        <DatasetFolders dataset={dataset} isAdmin={isAdmin} />
      </Box>
    )}
  </Box>
);

DatasetData.propTypes = {
  dataset: PropTypes.object.isRequired,
  isAdmin: PropTypes.bool.isRequired
};

export default DatasetData;
