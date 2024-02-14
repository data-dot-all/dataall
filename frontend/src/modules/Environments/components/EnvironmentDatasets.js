import PropTypes from 'prop-types';
import { Box } from '@mui/material';
import { EnvironmentSharedDatasets } from 'modules/Environments/components/EnvironmentSharedDatasets';
import { EnvironmentOwnedDatasets } from 'modules/Environments/components/EnvironmentOwnedDatasets';

export const EnvironmentDatasets = ({ environment }) => (
  <Box>
    <Box>
      <EnvironmentOwnedDatasets environment={environment} />
    </Box>
    <Box sx={{ mt: 3 }}>
      <EnvironmentSharedDatasets environment={environment} />
    </Box>
  </Box>
);

EnvironmentDatasets.propTypes = {
  environment: PropTypes.object.isRequired
};
