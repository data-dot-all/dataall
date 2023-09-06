import { Box, Grid } from '@mui/material';
import PropTypes from 'prop-types';
import {
    ObjectBrief,
    ObjectMetadata
} from 'design';

const OmicsWorkflowDetails = (props) => {
  const { workflow, ...other } = props;

  return (
    <Grid container spacing={3} {...other}>
      <Grid item lg={8} xl={9} xs={12}>
        <Box>
          <ObjectBrief
            title="Parameters"
            uri={workflow.workflowUri || '-'}
            name={workflow.label || '-'}
            description={workflow.description || 'No description provided'}
            tags={
              workflow.tags && workflow.tags.length > 0
                ? workflow.tags
                : ['-']
            }
          />
        </Box>
      </Grid>
      <Grid item lg={4} xl={3} xs={12}>
        <ObjectMetadata
          inputParameters={workflow.inputParameters}
          downloadParameterTemplateFile={workflow.downloadParameterTemplateFile}
          inputParameterJsonTemplate={workflow.inputParameterJsonTemplate}
          downloadTestAndExampleParameterFiles={workflow.downloadTestAndExampleParameterFiles}
          fixedValues={workflow.fixedValues}
        />
      </Grid>
    </Grid>
  );
};

OmicsWorkflowDetails.propTypes = {
  workflow: PropTypes.object.isRequired
};

export default OmicsWorkflowDetails;
