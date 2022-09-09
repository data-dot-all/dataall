import { Box, Grid } from '@mui/material';
import PropTypes from 'prop-types';
import ObjectBrief from '../../components/ObjectBrief';
import ObjectMetadata from '../../components/ObjectMetadata';
import PipelineCICD from './PipelineCICD';
import PipelineDatasets from './PipelineDatasets';
import PipelineEnvironments from './PipelineEnvironments';

const PipelineOverview = (props) => {
  const { pipeline, ...other } = props;

  return (
    <Grid container spacing={3} {...other}>
      <Grid item lg={12} xl={6} xs={12}
          <Grid item lg={7} xl={9} xs={12}>
            <Box sx={{ mb: 3 }}>
              <ObjectBrief
                title="Details"
                uri={pipeline.DataPipelineUri || '-'}
                name={pipeline.label || '-'}
                description={pipeline.description || 'No description provided'}
                tags={
                  pipeline.tags && pipeline.tags.length > 0 ? pipeline.tags : ['-']
                }
              />
            </Box>
          </Grid>
          <Grid item lg={5} xl={3} xs={12}>
            <Box sx={{ mb: 3 }}>
             <ObjectMetadata
               owner={pipeline.owner}
               admins={pipeline.SamlGroupName || '-'}
               created={pipeline.created}
               status={pipeline.stack?.status}
             />
            </Box>
          </Grid>
      </Grid>
      <Grid item lg={12} xl={6} xs={12} >
          <Grid item lg={6} xl={9} xs={12}>
              <Box sx={{ sx: 3 }}>
              <PipelineCICD pipeline={pipeline} />
              </Box>
          </Grid>
          <Grid item lg={6} xl={9} xs={12}>
              <Box sx={{ mb: 3 }}>
                <PipelineEnvironments
                  pipeline={pipeline}
                />
              </Box>
          </Grid>
      </Grid>
    </Grid>
  );
};

PipelineOverview.propTypes = {
  pipeline: PropTypes.object.isRequired
};

export default PipelineOverview;
