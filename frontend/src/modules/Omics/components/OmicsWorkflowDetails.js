import { Box, Grid } from '@mui/material';
import PropTypes from 'prop-types';
import { ObjectBrief } from 'design';

export const OmicsWorkflowDetails = (props) => {
  const { workflow, ...other } = props;

  return (
    <Grid container spacing={3} {...other}>
      <Grid item lg={7} xl={7} xs={12}>
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
      <Grid item lg={5} xl={5} xs={12}>
        <Box>
          <ObjectBrief
            title="Parameter template"
            parameterTemplate={workflow.parameterTemplate || '-'}
          />
        </Box>
      </Grid>
    </Grid>
  );
};

OmicsWorkflowDetails.propTypes = {
  workflow: PropTypes.object.isRequired
};
