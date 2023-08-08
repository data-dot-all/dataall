import {
  Card,
  CardContent,
  CardHeader,
  Divider,
  List,
  ListItem,
  Typography
} from '@mui/material';
import PropTypes from 'prop-types';
import React from 'react';
import { Label } from 'design';

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
                color={
                  environment.parameters['dashboardsEnabled'] === 'true'
                    ? 'success'
                    : 'error'
                }
              >
                {environment.parameters['dashboardsEnabled'] === 'true'
                  ? 'Enabled'
                  : 'Disabled'}
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
              <Label
                color={
                  environment.parameters['notebooksEnabled'] === 'true'
                    ? 'success'
                    : 'error'
                }
              >
                {environment.parameters['notebooksEnabled'] === 'true'
                  ? 'Enabled'
                  : 'Disabled'}
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
              <Label
                color={
                  environment.parameters['mlStudiosEnabled'] === 'true'
                    ? 'success'
                    : 'error'
                }
              >
                {environment.parameters['mlStudiosEnabled'] === 'true'
                  ? 'Enabled'
                  : 'Disabled'}
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
        </List>
      </CardContent>
    </Card>
  );
};

EnvironmentFeatures.propTypes = {
  environment: PropTypes.object.isRequired
};

export default EnvironmentFeatures;
