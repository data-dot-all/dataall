import { Box, Grid } from '@mui/material';
import PropTypes from 'prop-types';
import { ObjectBrief, ObjectMetadata } from '../../components';

const OrganizationOverview = (props) => {
  const { organization, ...other } = props;

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
          admins={organization.SamlGroupName || '-'}
          created={organization.created}
        />
      </Grid>
    </Grid>
  );
};

OrganizationOverview.propTypes = {
  organization: PropTypes.object.isRequired
};

export default OrganizationOverview;
