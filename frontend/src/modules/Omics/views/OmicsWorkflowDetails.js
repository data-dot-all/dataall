import { Box, Grid } from '@mui/material';
import PropTypes from 'prop-types';
import ObjectBrief from '../../components/ObjectBrief';
import ObjectMetadata from '../../components/ObjectMetadata';

const OmicsWorkflowDetails = (props) => {
  const { workflow, ...other } = props;

  return (
    <Grid container spacing={3} {...other}>
      <Grid item lg={8} xl={9} xs={12}>
        <Box>
          <ObjectBrief
            title="Details"
            uri={workflow.workflowUri || '-'}
            name={workflow.label || '-'}
            description={workflow.description || 'No description provided'}
            tags={
              workflow.tags && workflow.tags.length > 0 ? workflow.tags : ['-']
            }
          />
        </Box>
      </Grid>
      <Grid item lg={4} xl={3} xs={12}>
        <ObjectMetadata
          name={workflow.name}
          publisher={workflow.publisher}
          version={workflow.version}
          language={workflow.language}
          runTime={workflow.runTime || '-'}
          listPrice={workflow.listPrice}
          description={workflow.description}
        />
      </Grid>
    </Grid>
  );
};

OmicsWorkflowDetails.propTypes = {
  workflow: PropTypes.object.isRequired
};

export default OmicsWorkflowDetails;
