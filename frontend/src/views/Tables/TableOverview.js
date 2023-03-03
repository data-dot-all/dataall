import { Box, Grid } from '@mui/material';
import PropTypes from 'prop-types';
import ObjectBrief from '../../components/ObjectBrief';
import ObjectMetadata from '../../components/ObjectMetadata';
import LFTagBrief from '../../components/LFTagBrief';

const TableOverview = (props) => {
  const { table, ...other } = props;

  return (
    <Grid container spacing={3} {...other}>
      <Grid item lg={8} xl={9} xs={12}>
        <Box>
          <ObjectBrief
            title="Details"
            uri={table.tableUri || '-'}
            name={table.label || '-'}
            description={table.description || 'No description provided'}
            tags={table.tags && table.tags.length > 0 ? table.tags : ['-']}
            terms={
              table.terms && table.terms.nodes.length > 0
                ? table.terms.nodes
                : [{ label: '-', nodeUri: '-' }]
            }
          />
        </Box>
      </Grid>
      <Grid item lg={4} xl={3} xs={12}>
        <ObjectMetadata
          environment={table.dataset.environment}
          region={table.dataset.region}
          organization={table.dataset.organization}
          owner={table.owner}
          admins={table.dataset.SamlAdminGroupName || '-'}
          created={table.created}
          status={table.LastGlueTableStatus}
        />
      </Grid>
      <Grid item lg={12} xl={6} xs={12}>
        <LFTagBrief
          title="LF-Tags"
          lftagkeys={table.lfTagKey}
          lftagvalues={table.lfTagValue}
          objectType="table"
        />
      </Grid>
    </Grid>
  );
};

TableOverview.propTypes = {
  table: PropTypes.object.isRequired
};

export default TableOverview;
