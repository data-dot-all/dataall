import { Box, Grid } from '@mui/material';
import PropTypes from 'prop-types';
import { ObjectBrief, ObjectMetadata } from 'design';

export const DashboardOverview = (props) => {
  const { dashboard, ...other } = props;

  return (
    <Grid container spacing={3} {...other}>
      <Grid item lg={8} xl={9} xs={12}>
        <Box>
          <ObjectBrief
            title="Details"
            uri={dashboard.dashboardUri}
            name={dashboard.label || '-'}
            description={dashboard.description || 'No description provided'}
            tags={
              dashboard.tags && dashboard.tags.length > 0
                ? dashboard.tags
                : ['-']
            }
            terms={
              dashboard.terms && dashboard.terms.nodes.length > 0
                ? dashboard.terms.nodes
                : [{ label: '-', nodeUri: '-' }]
            }
          />
        </Box>
      </Grid>
      <Grid item lg={4} xl={3} xs={12}>
        <ObjectMetadata
          environment={dashboard.environment}
          region={dashboard.restricted?.region}
          organization={dashboard.environment.organization}
          owner={dashboard.owner}
          admins={dashboard.SamlGroupName || '-'}
          created={dashboard.created}
        />
      </Grid>
    </Grid>
  );
};

DashboardOverview.propTypes = {
  dashboard: PropTypes.object.isRequired
};
