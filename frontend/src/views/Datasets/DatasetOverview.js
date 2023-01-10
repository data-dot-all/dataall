import { Box, Grid } from '@mui/material';
import PropTypes from 'prop-types';
import LFTagBrief from '../../components/LFTagBrief';
import ObjectBrief from '../../components/ObjectBrief';
import ObjectMetadata from '../../components/ObjectMetadata';
import DatasetConsoleAccess from './DatasetConsoleAccess';
import DatasetGovernance from './DatasetGovernance';

const DatasetOverview = (props) => {
  const { dataset, isAdmin, ...other } = props;

  return (
    <Grid container spacing={2} {...other}>
      <Grid item lg={7} xl={9} xs={12}>
        <Box sx={{ mb: 3 }}>
          <ObjectBrief
            title="Details"
            uri={dataset.datasetUri || '-'}
            name={dataset.label || '-'}
            description={dataset.description || 'No description provided'}
          />
        </Box>
        <Box sx={{ mb: 3 }}>
          <DatasetGovernance dataset={dataset} />
        </Box>
      </Grid>
      <Grid item lg={5} xl={3} xs={12}>
        <ObjectMetadata
          environment={dataset.environment}
          region={dataset.region}
          organization={dataset.organization}
          owner={dataset.owner}
          created={dataset.created}
          status={dataset.stack?.status}
          objectType="dataset"
        />
        <Box sx={{ mt: 2 }}>
          {isAdmin && <DatasetConsoleAccess dataset={dataset} />}
        </Box>
      </Grid>
      <Grid item lg={12} xl={6} xs={12}>
        <LFTagBrief
          title="LF-Tags"
          lftagkeys={dataset.lfTagKey}
          lftagvalues={dataset.lfTagValue}
          objectType="dataset"
        />
      </Grid>
    </Grid>
  );
};

DatasetOverview.propTypes = {
  dataset: PropTypes.object.isRequired,
  isAdmin: PropTypes.bool.isRequired
};

export default DatasetOverview;
