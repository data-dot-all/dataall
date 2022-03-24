import PropTypes from 'prop-types';
import { Box } from '@material-ui/core';
import EnvironmentSharedDatasets from './EnvironmentSharedDatasets';
import EnvironmentOwnedDatasets from './EnvironmentOwnedDatasets';

const EnvironmentDatasets = ({ environment }) => (
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

export default EnvironmentDatasets;
