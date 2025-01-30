import { Box, Grid } from '@mui/material';
import PropTypes from 'prop-types';
import { ObjectBrief, ObjectMetadata } from 'design';
import { DatasetConsoleAccess } from './DatasetConsoleAccess';
import { DatasetGovernance } from 'modules/DatasetsBase/components/DatasetGovernance';

export const DatasetOverview = (props) => {
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
          organization={dataset.environment?.organization}
          owner={dataset.owner}
          created={dataset.created}
          status={dataset.stack?.status}
          objectType="dataset"
        />
        <Box sx={{ mt: 2 }}>
          {isAdmin && dataset.restricted && (
            <DatasetConsoleAccess dataset={dataset} />
          )}
        </Box>
      </Grid>
    </Grid>
  );
};

DatasetOverview.propTypes = {
  dataset: PropTypes.object.isRequired,
  isAdmin: PropTypes.bool.isRequired
};
