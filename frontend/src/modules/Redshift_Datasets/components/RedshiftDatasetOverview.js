import { Box, Grid } from '@mui/material';
import PropTypes from 'prop-types';
import { ObjectBrief, ObjectMetadata } from 'design';
import { DatasetGovernance } from 'modules/DatasetsBase/components/DatasetGovernance';
import { RedshiftDatasetAWSInfo } from './RedshiftDatasetAWSInfo';

export const RedshiftDatasetOverview = (props) => {
  const { dataset, isAdmin, ...other } = props;

  return (
    <Grid container spacing={2} {...other}>
      <Grid item lg={7} xl={7} xs={12}>
        <Box sx={{ mb: 3 }}>
          <ObjectBrief
            title="Details"
            uri={dataset.datasetUri || '-'}
            name={dataset.label || '-'}
            description={dataset.description || 'No description provided'}
          />
        </Box>
      </Grid>
      <Grid item lg={5} xl={5} xs={12}>
        <ObjectMetadata
          environment={dataset.environment}
          region={dataset.region}
          organization={dataset.environment.organization}
          owner={dataset.owner}
          created={dataset.created}
          status={dataset.stack?.status}
          objectType="dataset"
        />
      </Grid>
      <Grid item lg={7} xl={7} xs={12}>
        <Box sx={{ mb: 3 }}>
          <DatasetGovernance dataset={dataset} />
        </Box>
      </Grid>
      <Grid item lg={5} xl={5} xs={12}>
        <Box sx={{ mb: 3 }}>
          <RedshiftDatasetAWSInfo dataset={dataset} />
        </Box>
      </Grid>
    </Grid>
  );
};

RedshiftDatasetOverview.propTypes = {
  dataset: PropTypes.object.isRequired,
  isAdmin: PropTypes.bool.isRequired
};
