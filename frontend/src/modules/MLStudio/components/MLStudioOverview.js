import { Box, Grid } from '@mui/material';
import PropTypes from 'prop-types';
import { ObjectBrief, ObjectMetadata } from 'design';

export const MLStudioOverview = (props) => {
  const { mlstudiouser, ...other } = props;

  return (
    <Grid container spacing={3} {...other}>
      <Grid item lg={8} xl={9} xs={12}>
        <Box>
          <ObjectBrief
            title="Details"
            uri={mlstudiouser.sagemakerStudioUserUri || '-'}
            name={mlstudiouser.label || '-'}
            description={mlstudiouser.description || 'No description provided'}
            tags={
              mlstudiouser.tags && mlstudiouser.tags.length > 0
                ? mlstudiouser.tags
                : ['-']
            }
          />
        </Box>
      </Grid>
      <Grid item lg={4} xl={3} xs={12}>
        <ObjectMetadata
          environment={mlstudiouser.environment}
          region={mlstudiouser.region}
          organization={mlstudiouser.organization}
          owner={mlstudiouser.owner}
          admins={mlstudiouser.SamlAdminGroupName || '-'}
          created={mlstudiouser.created}
          status={mlstudiouser.sagemakerStudioUserStatus}
        />
      </Grid>
    </Grid>
  );
};

MLStudioOverview.propTypes = {
  mlstudiouser: PropTypes.object.isRequired
};
