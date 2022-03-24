import PropTypes from 'prop-types';
import { Card, CardContent, CardHeader, Divider, Typography } from '@material-ui/core';

const DatasetConsoleAccess = (props) => {
  const { dataset } = props;

  return (
    <Card {...dataset}>
      <CardHeader title="AWS Information" />
      <Divider />
      <CardContent>
        <Typography
          color="textSecondary"
          variant="subtitle2"
        >
          Account
        </Typography>
        <Typography
          color="textPrimary"
          variant="body2"
        >
          {dataset.AwsAccountId}
        </Typography>
      </CardContent>
      <CardContent>
        <Typography
          color="textSecondary"
          variant="subtitle2"
        >
          S3 bucket
        </Typography>
        <Typography
          color="textPrimary"
          variant="body2"
        >
          arn:aws:s3:::
          {dataset.S3BucketName}
        </Typography>
      </CardContent>
      <CardContent>
        <Typography
          color="textSecondary"
          variant="subtitle2"
        >
          Glue database
        </Typography>
        <Typography
          color="textPrimary"
          variant="body2"
        >
          {`arn:aws:glue:${dataset.region}:${dataset.AwsAccountId}/database:${dataset.GlueDatabaseName}`}
        </Typography>
      </CardContent>
      <CardContent>
        <Typography
          color="textSecondary"
          variant="subtitle2"
        >
          IAM role
        </Typography>
        <Typography
          color="textPrimary"
          variant="body2"
        >
          {dataset.IAMDatasetAdminRoleArn}
        </Typography>
      </CardContent>
      {!dataset.imported && (
      <CardContent>
        <Typography
          color="textSecondary"
          variant="subtitle2"
        >
          KMS alias
        </Typography>
        <Typography
          color="textPrimary"
          variant="body2"
        >
          {`arn:aws:kms:${dataset.region}:${dataset.AwsAccountId}/alias:${dataset.KmsAlias}`}
        </Typography>
      </CardContent>
      )}
    </Card>
  );
};

DatasetConsoleAccess.propTypes = {
  dataset: PropTypes.object.isRequired
};

export default DatasetConsoleAccess;
