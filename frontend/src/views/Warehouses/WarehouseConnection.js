import { LoadingButton } from '@mui/lab';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Divider,
  Typography
} from '@mui/material';
import PropTypes from 'prop-types';
import { useState } from 'react';
import { FaExternalLinkAlt } from 'react-icons/fa';
import { getRedshiftClusterConsoleAccess } from '../../api';
import { SET_ERROR, useDispatch } from '../../globalErrors';
import { useClient } from '../../hooks';

const WarehouseConnection = (props) => {
  const { warehouse } = props;
  const client = useClient();
  const dispatch = useDispatch();
  const [openingQueryEditor, setOpeningQueryEditor] = useState(false);
  const jdbc = warehouse.endpoint
    ? `jdbc:redshift://${warehouse.endpoint}:${warehouse.port}/${warehouse.databaseName}`
    : '-';
  const odbc = warehouse.endpoint
    ? `Driver={Amazon Redshift (x64)}; Server=${
        warehouse.endpoint || '-'
      }; Database=${warehouse.databaseName}`
    : '-';
  const goToQueryEditor = async () => {
    setOpeningQueryEditor(true);
    const response = await client.query(
      getRedshiftClusterConsoleAccess(warehouse.clusterUri)
    );
    if (!response.errors) {
      window.open(response.data.getRedshiftClusterConsoleAccess, '_blank');
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setOpeningQueryEditor(false);
  };

  return (
    <Card {...warehouse}>
      <CardHeader title="Connection" />
      <Divider />

      <CardContent>
        <Box sx={{ mb: 3 }}>
          <Typography color="textSecondary" variant="subtitle2">
            Endpoint
          </Typography>
          <Typography color="textPrimary" variant="subtitle2">
            {warehouse.endpoint}
          </Typography>
        </Box>
        <Box sx={{ mb: 3 }}>
          <Typography color="textSecondary" variant="subtitle2">
            Port
          </Typography>
          <Typography color="textPrimary" variant="subtitle2">
            {warehouse.port}
          </Typography>
        </Box>
        <Box sx={{ mb: 3 }}>
          <Typography color="textSecondary" variant="subtitle2">
            JDBC URL
          </Typography>
          <Typography color="textPrimary" variant="subtitle2">
            {jdbc}
          </Typography>
        </Box>
        <Box sx={{ mb: 3 }}>
          <Typography color="textSecondary" variant="subtitle2">
            ODBC URL
          </Typography>
          <Typography color="textPrimary" variant="subtitle2">
            {odbc}
          </Typography>
        </Box>
        <Box sx={{ mt: 4 }}>
          <LoadingButton
            disabled={warehouse.status !== 'available'}
            loading={openingQueryEditor}
            color="primary"
            startIcon={<FaExternalLinkAlt size={15} />}
            sx={{ mr: 1 }}
            variant="contained"
            onClick={goToQueryEditor}
          >
            Redshift Query Editor
          </LoadingButton>
        </Box>
      </CardContent>
    </Card>
  );
};

WarehouseConnection.propTypes = {
  warehouse: PropTypes.object.isRequired
};

export default WarehouseConnection;
