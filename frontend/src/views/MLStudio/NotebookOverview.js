import { Box, Grid } from '@material-ui/core';
import PropTypes from 'prop-types';
import ObjectBrief from '../../components/ObjectBrief';
import ObjectMetadata from '../../components/ObjectMetadata';

const NotebookOverview = (props) => {
  const { notebook, ...other } = props;

  return (
    <Grid
      container
      spacing={3}
      {...other}
    >
      <Grid
        item
        lg={8}
        xl={9}
        xs={12}
      >
        <Box>
          <ObjectBrief
            title="Details"
            uri={notebook.sagemakerStudioUserProfileUri || '-'}
            name={notebook.label || '-'}
            description={notebook.description || 'No description provided'}
            tags={notebook.tags && notebook.tags.length > 0 ? notebook.tags : ['-']}
          />
        </Box>
      </Grid>
      <Grid
        item
        lg={4}
        xl={3}
        xs={12}
      >
        <ObjectMetadata
          environment={notebook.environment}
          region={notebook.region}
          organization={notebook.organization}
          owner={notebook.owner}
          admins={notebook.SamlAdminGroupName || '-'}
          created={notebook.created}
          status={notebook.sagemakerStudioUserProfileStatus}
        />
      </Grid>
    </Grid>
  );
};

NotebookOverview.propTypes = {
  notebook: PropTypes.object.isRequired
};

export default NotebookOverview;
