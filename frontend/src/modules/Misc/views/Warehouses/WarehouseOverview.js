import { Box, Grid } from '@mui/material';
import PropTypes from 'prop-types';
import { ObjectBrief, ObjectMetadata } from '../../../../design';
import WarehouseConnection from './WarehouseConnection';
import WarehouseCredentials from './WarehouseCredentials';

const WarehouseOverview = (props) => {
  const { warehouse, ...other } = props;

  return (
    <Grid container spacing={3} {...other}>
      <Grid item lg={8} xl={9} xs={12}>
        <Box sx={{ mb: 2 }}>
          <ObjectBrief
            title="Details"
            uri={warehouse.clusterUri || '-'}
            name={warehouse.label || '-'}
            description={warehouse.description || 'No description provided'}
            tags={
              warehouse.tags && warehouse.tags.length > 0
                ? warehouse.tags
                : ['-']
            }
          />
        </Box>
        <Box sx={{ mb: 2 }}>
          <WarehouseConnection warehouse={warehouse} />
        </Box>
      </Grid>
      <Grid item lg={4} xl={3} xs={12}>
        {' '}
        <Box sx={{ mb: 2 }}>
          <ObjectMetadata
            environment={warehouse.environment}
            region={warehouse.region}
            organization={warehouse.organization}
            owner={warehouse.owner}
            admins={warehouse.SamlGroupName || '-'}
            created={warehouse.created}
            status={warehouse.status}
          />
        </Box>
        <Box sx={{ mb: 2 }}>
          <WarehouseCredentials warehouse={warehouse} />
        </Box>
      </Grid>
    </Grid>
  );
};

WarehouseOverview.propTypes = {
  warehouse: PropTypes.object.isRequired
};

export default WarehouseOverview;
