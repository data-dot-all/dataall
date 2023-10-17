import { Box, Grid } from '@mui/material';
import PropTypes from 'prop-types';
import { ObjectBrief } from 'design';

const OmicsRunDetails = (props) => {
  const { omicsRun, ...other } = props;

  return (
    <Grid container spacing={3} {...other}>
      <Grid item lg={8} xl={9} xs={12}>
        <Box>
          <ObjectBrief
            title="Details"
            uri={omicsRun.runUri || '-'}
            name={omicsRun.label || '-'}
            description={omicsRun.description || 'No description provided'}
            tags={
              omicsRun.tags && omicsRun.tags.length > 0 ? omicsRun.tags : ['-']
            }
            parameterTemplate={omicsRun.parameterTemplate || '-'}
            outputUri={omicsRun.outputUri}
          />
        </Box>
      </Grid>
    </Grid>
  );
};

OmicsRunDetails.propTypes = {
  omicsRun: PropTypes.object.isRequired
};

export default OmicsRunDetails;
