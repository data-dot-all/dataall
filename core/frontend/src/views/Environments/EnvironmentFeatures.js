import PropTypes from 'prop-types';
import {
  Card,
  CardContent,
  CardHeader,
  Divider,
  List,
  ListItem,
  Typography
} from '@mui/material';
import React from 'react';
import Label from '../../components/Label';

const EnvironmentFeatures = (props) => {
  const { environment, ...other } = props;

  return (
    <Card {...other}>
      <CardHeader title="Features" />
      <Divider />
      <CardContent sx={{ pt: 0 }}>
        <List>
          <ListItem
            disableGutters
            divider
            sx={{
              justifyContent: 'space-between',
              padding: 2
            }}
          >
            <Typography color="textSecondary" variant="subtitle2">
              Dashboards
            </Typography>
            <Typography color="textPrimary" variant="body2">
              <Label
                color={environment.dashboardsEnabled ? 'success' : 'error'}
              >
                {environment.dashboardsEnabled ? 'Enabled' : 'Disabled'}
              </Label>
            </Typography>
          </ListItem>
          <ListItem
            disableGutters
            divider
            sx={{
              justifyContent: 'space-between',
              padding: 2
            }}
          >
            <Typography color="textSecondary" variant="subtitle2">
              Notebooks
            </Typography>
            <Typography color="textPrimary" variant="body2">
              <Label color={environment.notebooksEnabled ? 'success' : 'error'}>
                {environment.notebooksEnabled ? 'Enabled' : 'Disabled'}
              </Label>
            </Typography>
          </ListItem>
          <ListItem
            disableGutters
            divider
            sx={{
              justifyContent: 'space-between',
              padding: 2
            }}
          >
            <Typography color="textSecondary" variant="subtitle2">
              ML Studio
            </Typography>
            <Typography color="textPrimary" variant="body2">
              <Label color={environment.mlStudiosEnabled ? 'success' : 'error'}>
                {environment.mlStudiosEnabled ? 'Enabled' : 'Disabled'}
              </Label>
            </Typography>
          </ListItem>
          <ListItem
            disableGutters
            divider
            sx={{
              justifyContent: 'space-between',
              padding: 2
            }}
          >
            <Typography color="textSecondary" variant="subtitle2">
              Pipelines
            </Typography>
            <Typography color="textPrimary" variant="body2">
              <Label color={environment.pipelinesEnabled ? 'success' : 'error'}>
                {environment.pipelinesEnabled ? 'Enabled' : 'Disabled'}
              </Label>
            </Typography>
          </ListItem>
{/*          <ListItem
            disableGutters
            divider
            sx={{
              justifyContent: 'space-between',
              padding: 2
            }}
          >
            <Typography color="textSecondary" variant="subtitle2">
              Warehouses
            </Typography>
            <Typography color="textPrimary" variant="body2">
              <Label
                color={environment.warehousesEnabled ? 'success' : 'error'}
              >
                {environment.warehousesEnabled ? 'Enabled' : 'Disabled'}
              </Label>
            </Typography>
          </ListItem>*/}
        </List>
      </CardContent>
    </Card>
  );
};

EnvironmentFeatures.propTypes = {
  environment: PropTypes.object.isRequired
};

export default EnvironmentFeatures;
