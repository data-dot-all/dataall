import PropTypes from 'prop-types';
import React from 'react';
import { Box } from '@mui/material';
import { DatasetTables } from './DatasetTables';
import { DatasetFolders } from './DatasetFolders';
import { isFeatureEnabled } from 'utils';

export const DatasetData = (props) => {
  const { dataset, isAdmin } = props;

  return (
    <Box>
      <Box>
        <DatasetTables dataset={dataset} isAdmin={isAdmin} />
      </Box>
      {isFeatureEnabled('s3_datasets', 'file_actions') && (
        <Box sx={{ mt: 3 }}>
          <DatasetFolders dataset={dataset} isAdmin={isAdmin} />
        </Box>
      )}
    </Box>
  );
};

DatasetData.propTypes = {
  dataset: PropTypes.object.isRequired,
  isAdmin: PropTypes.bool.isRequired
};
