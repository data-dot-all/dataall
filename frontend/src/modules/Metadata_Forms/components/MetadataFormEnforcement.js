import PropTypes from 'prop-types';
import EngineeringOutlinedIcon from '@mui/icons-material/EngineeringOutlined';
import { Box, Typography } from '@mui/material';

export const MetadataFormEnforcement = (props) => {
  return (
    <Box
      sx={{
        alignContent: 'center',
        justifyContent: 'center'
      }}
    >
      <EngineeringOutlinedIcon
        sx={{ ml: 15, fontSize: 80, color: '#65748B' }}
      />
      <Typography color="textSecondary" sx={{ fontSize: 30 }}>
        This tab is under construction.
      </Typography>
    </Box>
  );
};

MetadataFormEnforcement.propTypes = {
  metadataForm: PropTypes.any.isRequired
};
