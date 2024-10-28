import React, { useState } from 'react';
import { Box, Grid } from '@mui/material';
import PropTypes from 'prop-types';
import { ObjectBrief, ObjectMetadata, UserModal } from 'design';

export const OrganizationOverview = (props) => {
  const { organization, ...other } = props;

  const [modalOpen, setIsModalOpen] = useState(false);
  const handleOpenModal = () => setIsModalOpen(true);
  const handleCloseModal = () => setIsModalOpen(false);

  return (
    <Grid container spacing={3} {...other}>
      <Grid item lg={8} xl={9} xs={12}>
        <Box>
          <ObjectBrief
            uri={organization.organizationUri}
            name={organization.label || '-'}
            description={organization.description || 'No description provided'}
            tags={organization.tags.length > 0 ? organization.tags : ['-']}
          />
        </Box>
      </Grid>
      <Grid item lg={4} xl={3} xs={12}>
        <ObjectMetadata
          owner={organization.owner}
          admins={
            <div onClick={handleOpenModal} style={{ cursor: 'pointer' }}>
              {organization.SamlGroupName || '-'}
            </div>
          }
          created={organization.created}
        />
        <UserModal
          team={organization.SamlGroupName}
          open={modalOpen}
          onClose={handleCloseModal}
        />
      </Grid>
    </Grid>
  );
};

OrganizationOverview.propTypes = {
  organization: PropTypes.object.isRequired
};
