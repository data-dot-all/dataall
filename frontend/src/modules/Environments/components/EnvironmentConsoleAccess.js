import PropTypes from 'prop-types';
import {
  Card,
  CardContent,
  CardHeader,
  Divider,
  Typography
} from '@mui/material';

export const EnvironmentConsoleAccess = ({ environment }) => {
  return (
    <Card>
      <CardHeader title="AWS Information" />
      <Divider />
      <CardContent>
        <Typography color="textSecondary" variant="subtitle2">
          Account
        </Typography>
        <Typography color="textPrimary" variant="body2">
          {environment.AwsAccountId}
        </Typography>
      </CardContent>
      <CardContent>
        <Typography color="textSecondary" variant="subtitle2">
          S3 bucket
        </Typography>
        <Typography color="textPrimary" variant="body2">
          arn:aws:s3:::
          {environment.EnvironmentDefaultBucketName}
        </Typography>
      </CardContent>
      <CardContent>
        <Typography color="textSecondary" variant="subtitle2">
          Admin Team IAM role
        </Typography>
        <Typography color="textPrimary" variant="body2">
          {environment.EnvironmentDefaultIAMRoleArn}
        </Typography>
      </CardContent>
    </Card>
  );
};
EnvironmentConsoleAccess.propTypes = {
  environment: PropTypes.object.isRequired
};
