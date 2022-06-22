import { Box, Grid } from '@mui/material';
import PropTypes from 'prop-types';
import ObjectBrief from '../../components/ObjectBrief';
import ObjectMetadata from '../../components/ObjectMetadata';
import PipelineCodeCommit from './PipelineCodeCommit';
import PipelineDatasets from './PipelineDatasets';

const PipelineOverview = (props) => {
  const { pipeline, ...other } = props;

  return (
    <Grid container spacing={3} {...other}>
      <Grid item lg={8} xl={9} xs={12}>
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
        <Box sx={{ sx: 3 }}>
          <PipelineCodeCommit pipeline={pipeline} />
        </Box>
      </Grid>
      <Grid item lg={4} xl={3} xs={12}>
        <Box sx={{ mb: 3 }}>
         <ObjectMetadata
           environment={pipeline.environment}
           region={pipeline.environment?.region}
           organization={pipeline.organization}
           owner={pipeline.owner}
           admins={pipeline.SamlGroupName || '-'}
           created={pipeline.created}
           status={pipeline.stack?.status}
         />
        </Box>
        <Box sx={{ sx: 3 }}>
          <PipelineDatasets pipeline={pipeline} />
        </Box>
      </Grid>
    </Grid>
  );
};

PipelineOverview.propTypes = {
  pipeline: PropTypes.object.isRequired
};

export default PipelineOverview;
