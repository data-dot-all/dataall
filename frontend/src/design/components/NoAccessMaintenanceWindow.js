import { Box, Typography } from '@mui/material';
import React from 'react';
import config from '../../generated/config.json';
import { SanitizedHTML } from './SanitizedHTML';

export const NoAccessMaintenanceWindow = () => (
  <Box
    sx={{
      alignItems: 'center',
      backgroundColor: 'background.paper',
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      justifyContent: 'center',
      left: 0,
      p: 3,
      position: 'fixed',
      top: 0,
      width: '100%',
      zIndex: 2000
    }}
  >
    {config.modules.maintenance.custom_maintenance_text !== undefined ? (
      <Typography>
        <SanitizedHTML
          dirtyHTML={config.modules.maintenance.custom_maintenance_text}
        />
      </Typography>
    ) : (
      <Typography variant="subtitle2" align={'center'} fontSize={'20px'}>
        data.all is in maintenance mode. Please contact data.all administrators
        for any assistance.
      </Typography>
    )}
  </Box>
);
