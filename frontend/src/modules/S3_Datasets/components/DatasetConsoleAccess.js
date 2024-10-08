import PropTypes from 'prop-types';
import {
  Card,
  CardContent,
  CardHeader,
  Divider,
  Typography
} from '@mui/material';

export const DatasetConsoleAccess = (props) => {
  const { dataset } = props;

  return (
    <Card {...dataset}>
      <CardHeader title="AWS Information" />
      <Divider />
      <CardContent>
        <Typography color="textSecondary" variant="subtitle2">
          Account
        </Typography>
        <Typography color="textPrimary" variant="body2">
          {dataset.resourceDetails?.AwsAccountId}
        </Typography>
      </CardContent>
      <CardContent>
        <Typography color="textSecondary" variant="subtitle2">
          S3 bucket
        </Typography>
        <Typography color="textPrimary" variant="body2">
          arn:aws:s3:::
          {dataset.resourceDetails?.S3BucketName}
        </Typography>
      </CardContent>
      <CardContent>
        <Typography color="textSecondary" variant="subtitle2">
          Glue database
        </Typography>
        <Typography color="textPrimary" variant="body2">
          {`arn:aws:glue:${dataset.region}:${dataset.resourceDetails?.AwsAccountId}/database:${dataset.resourceDetails?.GlueDatabaseName}`}
        </Typography>
      </CardContent>
      <CardContent>
        <Typography color="textSecondary" variant="subtitle2">
          IAM role
        </Typography>
        <Typography color="textPrimary" variant="body2">
          {dataset.resourceDetails?.IAMDatasetAdminRoleArn}
        </Typography>
      </CardContent>
      {dataset.resourceDetails?.KmsAlias === 'SSE-S3' || dataset.resourceDetails?.KmsAlias === 'Undefined' ? (
        <CardContent>
          <Typography color="textSecondary" variant="subtitle2">
            S3 Encryption
          </Typography>
          <Typography color="textPrimary" variant="body2">
            {`${dataset.resourceDetails?.KmsAlias}`}
          </Typography>
        </CardContent>
      ) : (
        <CardContent>
          <Typography color="textSecondary" variant="subtitle2">
            S3 Encryption SSE-KMS
          </Typography>
          <Typography color="textPrimary" variant="body2">
            {`arn:aws:kms:${dataset.region}:${dataset.resourceDetails?.AwsAccountId}/alias:${dataset.resourceDetails?.KmsAlias}`}
          </Typography>
        </CardContent>
      )}
    </Card>
  );
};

DatasetConsoleAccess.propTypes = {
  dataset: PropTypes.object.isRequired
};
