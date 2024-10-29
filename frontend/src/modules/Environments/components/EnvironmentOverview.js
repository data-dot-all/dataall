import React, { useState } from 'react';
import { Box, Grid } from '@mui/material';
import PropTypes from 'prop-types';
import { ObjectBrief, ObjectMetadata, UserModal } from 'design';
import { EnvironmentConsoleAccess } from './EnvironmentConsoleAccess';
import { EnvironmentFeatures } from './EnvironmentFeatures';

export const EnvironmentOverview = (props) => {
  const { environment, ...other } = props;

  const [modalOpen, setIsModalOpen] = useState(false);
  const handleOpenModal = () => setIsModalOpen(true);
  const handleCloseModal = () => setIsModalOpen(false);

  return (
    <Grid container spacing={3} {...other}>
      <Grid item lg={8} xl={9} xs={12}>
        <Box>
          <ObjectBrief
            uri={environment.environmentUri || '-'}
            name={environment.label || '-'}
            description={environment.description || 'No description provided'}
            tags={environment.tags.length > 0 ? environment.tags : ['-']}
          />
        </Box>
        <Box sx={{ mt: 3 }}>
          <EnvironmentConsoleAccess environment={environment} />
        </Box>
      </Grid>
      <Grid item lg={4} xl={3} xs={12}>
        <ObjectMetadata
          accountId={environment.AwsAccountId}
          region={environment.region}
          organization={environment.organization}
          owner={environment.owner}
          admins={
            <div onClick={handleOpenModal} style={{ cursor: 'pointer' }}>
              {environment.SamlGroupName || '-'}
            </div>
          }
          created={environment.created}
          status={environment.stack?.status}
        />
        <UserModal
          team={environment.SamlGroupName}
          open={modalOpen}
          onClose={handleCloseModal}
        />
        <Box sx={{ mt: 3 }}>
          <EnvironmentFeatures environment={environment} />
        </Box>
      </Grid>
    </Grid>
  );
};

EnvironmentOverview.propTypes = {
  environment: PropTypes.object.isRequired
};
