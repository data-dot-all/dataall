import {
  Card,
  CardContent,
  CardHeader,
  Divider,
  Typography
} from '@mui/material';
import PropTypes from 'prop-types';
import React from 'react';

export const NotebookInstanceProperties = ({ notebook }) => (
  <Card>
    <CardHeader title="Instance Properties" />
    <Divider />
    <CardContent>
      <Typography color="textSecondary" variant="subtitle2">
        Instance type
      </Typography>
      <Typography color="textPrimary" variant="body2">
        {notebook.InstanceType || '-'}
      </Typography>
    </CardContent>
    <CardContent>
      <Typography color="textSecondary" variant="subtitle2">
        Volume size
      </Typography>
      <Typography color="textPrimary" variant="body2">
        {`${notebook.VolumeSizeInGB} Go` || '-'}
      </Typography>
    </CardContent>
    <CardContent>
      <Typography color="textSecondary" variant="subtitle2">
        VPC
      </Typography>
      <Typography color="textPrimary" variant="body2">
        {notebook.VpcId || '-'}
      </Typography>
    </CardContent>
    <CardContent>
      <Typography color="textSecondary" variant="subtitle2">
        Subnet
      </Typography>
      <Typography color="textPrimary" variant="body2">
        {notebook.SubnetId || '-'}
      </Typography>
    </CardContent>
    <CardContent>
      <Typography color="textSecondary" variant="subtitle2">
        Instance Profile
      </Typography>
      <Typography color="textPrimary" variant="body2">
        {notebook.RoleArn}
      </Typography>
    </CardContent>
  </Card>
);
NotebookInstanceProperties.propTypes = {
  notebook: PropTypes.object.isRequired
};
