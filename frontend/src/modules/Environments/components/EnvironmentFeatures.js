import React from 'react';
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
import { Label } from 'design';
import { ModuleNames, isModuleEnabled } from 'utils';

export const EnvironmentFeatures = (props) => {
  const { environment, ...other } = props;

  const features = [
    {
      title: 'Dashboards',
      enabledEnvVariableName: 'dashboardsEnabled',
      active: isModuleEnabled(ModuleNames.DASHBOARDS)
    },
    {
      title: 'Notebooks',
      enabledEnvVariableName: 'notebooksEnabled',
      active: isModuleEnabled(ModuleNames.NOTEBOOKS)
    },
    {
      title: 'ML Studio',
      enabledEnvVariableName: 'mlStudiosEnabled',
      active: isModuleEnabled(ModuleNames.MLSTUDIO)
    },
    {
      title: 'Pipelines',
      enabledEnvVariableName: 'pipelinesEnabled',
      active: isModuleEnabled(ModuleNames.DATAPIPELINES)
    },
    {
      title: 'Omics',
      enabledEnvVariableName: 'omicsEnabled',
      active: isModuleEnabled(ModuleNames.OMICS)
    }
  ];

  // Filter the features based on the 'active' attribute
  const activeFeatures = features.filter((feature) => feature.active);

  if (activeFeatures.length === 0) {
    return <></>;
  } else {
    return (
      <Card {...other}>
        <CardHeader title="Features" />
        <Divider />
        <CardContent sx={{ pt: 0 }}>
          <List>
            {activeFeatures.map((feature) => (
              <ListItem
                key={feature.title}
                disableGutters
                divider
                sx={{
                  justifyContent: 'space-between',
                  padding: 2
                }}
              >
                <Typography color="textSecondary" variant="subtitle2">
                  {feature.title}
                </Typography>
                <Typography color="textPrimary" variant="body2">
                  <Label
                    color={
                      environment.parameters[feature.enabledEnvVariableName] ===
                      'true'
                        ? 'success'
                        : 'error'
                    }
                  >
                    {environment.parameters[feature.enabledEnvVariableName] ===
                    'true'
                      ? 'Enabled'
                      : 'Disabled'}
                  </Label>
                </Typography>
              </ListItem>
            ))}
          </List>
        </CardContent>
      </Card>
    );
  }
};

EnvironmentFeatures.propTypes = {
  environment: PropTypes.object.isRequired
};
