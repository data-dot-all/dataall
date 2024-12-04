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
          {`s3://${folder.restricted?.S3BucketName || 'UNAUTHORIZED_INFO'}/${
            folder.S3Prefix
          }/`}
        </Typography>
      </CardContent>
      <CardContent>
        <Typography color="textSecondary" variant="subtitle2">
          S3 ARN
        </Typography>
        <Typography color="textPrimary" variant="body2">
          {`arn:aws:s3:::${
            folder.restricted?.S3BucketName || 'UNAUTHORIZED_INFO'
          }/${folder.S3Prefix}/`}
        </Typography>
      </CardContent>
      <CardContent>
        <Typography color="textSecondary" variant="subtitle2">
          Region
        </Typography>
        <Typography color="textPrimary" variant="body2">
          {folder.restricted?.region || 'UNAUTHORIZED_INFO'}
        </Typography>
      </CardContent>
      <CardContent>
        <Typography color="textSecondary" variant="subtitle2">
          Account
        </Typography>
        <Typography color="textPrimary" variant="body2">
          {folder.restricted?.AwsAccountId || 'UNAUTHORIZED_INFO'}
        </Typography>
      </CardContent>
    </Card>
  );
};

FolderS3Properties.propTypes = {
  folder: PropTypes.object.isRequired,
  isAdmin: PropTypes.bool.isRequired
};
