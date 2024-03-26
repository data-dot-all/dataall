import { Box, Grid } from '@mui/material';
import PropTypes from 'prop-types';
import { ObjectBrief } from 'design';

export const OmicsWorkflowDetails = (props) => {
  const { workflow, ...other } = props;

  return (
    <Grid container spacing={3} {...other}>
      <Grid item lg={6} xl={6} xs={12}>
        <Box>
          <ObjectBrief
            title="Details"
            uri={workflow.id || '-'}
            name={workflow.name || '-'}
            description={workflow.description || '-'}
            tags={
              workflow.tags && workflow.tags.length > 0 ? workflow.tags : ['-']
            }
          />
        </Box>
      </Grid>
      <Grid item lg={6} xl={6} xs={12}>
        <Box>
          <ObjectBrief
            title="Parameter template"
            parameterTemplate={JSON.stringify(
              JSON.parse(workflow.parameterTemplate) || '{}',
              null,
              2
            )}
          />
        </Box>
      </Grid>
    </Grid>
  );
};

OmicsWorkflowDetails.propTypes = {
  workflow: PropTypes.object.isRequired
};
