import PropTypes from 'prop-types';
import {
  Card,
  CardContent,
  CardHeader,
  Divider,
  Typography
} from '@mui/material';

export const FolderS3Properties = (props) => {
  const { folder } = props;

  return (
    <Card {...folder}>
      <CardHeader title="S3 Properties" />
      <Divider />
      <CardContent>
        <Typography color="textSecondary" variant="subtitle2">
          S3 URI
        </Typography>
        <Typography color="textPrimary" variant="body2">
          {`s3://${folder.dataset.S3BucketName}/${folder.S3Prefix}/`}
        </Typography>
      </CardContent>
      <CardContent>
        <Typography color="textSecondary" variant="subtitle2">
          S3 ARN
        </Typography>
        <Typography color="textPrimary" variant="body2">
          {`arn:aws:s3:::${folder.dataset.S3BucketName}/${folder.S3Prefix}/`}
        </Typography>
      </CardContent>
      <CardContent>
        <Typography color="textSecondary" variant="subtitle2">
          Region
        </Typography>
        <Typography color="textPrimary" variant="body2">
          {folder.dataset.region}
        </Typography>
      </CardContent>
      <CardContent>
        <Typography color="textSecondary" variant="subtitle2">
          Account
        </Typography>
        <Typography color="textPrimary" variant="body2">
          {folder.dataset.AwsAccountId}
        </Typography>
      </CardContent>
    </Card>
  );
};

FolderS3Properties.propTypes = {
  folder: PropTypes.object.isRequired,
  isAdmin: PropTypes.bool.isRequired
};
