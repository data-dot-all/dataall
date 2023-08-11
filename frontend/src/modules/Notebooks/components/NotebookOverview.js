import { Box, Grid } from '@mui/material';
import PropTypes from 'prop-types';
import { ObjectBrief, ObjectMetadata } from 'design';
import { NotebookInstanceProperties } from './NotebookInstanceProperties';

/**
 * @description NotebookOverview view.
 * @param {NotebookOverview.propTypes} props
 * @return {JSX.Element}
 */
export const NotebookOverview = (props) => {
  const { notebook, ...other } = props;

  return (
    <Grid container spacing={3} {...other}>
      <Grid item lg={8} xl={9} xs={12}>
        <Box>
          <ObjectBrief
            title="Details"
            uri={notebook.notebookUri}
            name={notebook.label || '-'}
            description={notebook.description || 'No description provided'}
            tags={
              notebook.tags && notebook.tags.length > 0 ? notebook.tags : ['-']
            }
          />
        </Box>
        <Box sx={{ mt: 3 }}>
          <NotebookInstanceProperties notebook={notebook} />
        </Box>
      </Grid>
      <Grid item lg={4} xl={3} xs={12}>
        <ObjectMetadata
          environment={notebook.environment}
          region={notebook.region}
          organization={notebook.organization}
          owner={notebook.owner}
          admins={notebook.SamlAdminGroupName || '-'}
          created={notebook.created}
          status={notebook.NotebookInstanceStatus}
        />
      </Grid>
    </Grid>
  );
};

NotebookOverview.propTypes = {
  notebook: PropTypes.object.isRequired
};
