import PropTypes from 'prop-types';
import {
  Card,
  CardContent,
  CardHeader,
  Divider,
  Typography
} from '@mui/material';

export const RedshiftDatasetAWSInfo = (props) => {
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
          {dataset.AwsAccountId}
        </Typography>
      </CardContent>
      <CardContent>
        <Typography color="textSecondary" variant="subtitle2">
          Redshift Connection
        </Typography>
        <Typography color="textPrimary" variant="body2">
          {dataset.connection.label}
        </Typography>
      </CardContent>
      <CardContent>
        <Typography color="textSecondary" variant="subtitle2">
          Redshift type
        </Typography>
        <Typography color="textPrimary" variant="body2">
          {dataset.connection.redshiftType === 'cluster'
            ? 'Provisioned cluster'
            : dataset.connection.redshiftType === 'serverless'
            ? 'Redshift Serverless'
            : 'Unknown'}
        </Typography>
      </CardContent>
      {dataset.connection.redshiftType === 'serverless' ? (
        <div>
          <CardContent>
            <Typography color="textSecondary" variant="subtitle2">
              Namespace Id
            </Typography>
            <Typography color="textPrimary" variant="body2">
              {dataset.connection.nameSpaceId}
            </Typography>
          </CardContent>
          <CardContent>
            <Typography color="textSecondary" variant="subtitle2">
              Workgroup Id
            </Typography>
            <Typography color="textPrimary" variant="body2">
              {dataset.connection.workgroupId}
            </Typography>
          </CardContent>
        </div>
      ) : (
        <CardContent>
          <Typography color="textSecondary" variant="subtitle2">
            Cluster Id
          </Typography>
          <Typography color="textPrimary" variant="body2">
            {dataset.connection.clusterId}
          </Typography>
        </CardContent>
      )}
      <CardContent>
        <Typography color="textSecondary" variant="subtitle2">
          Include Pattern
        </Typography>
        <Typography color="textPrimary" variant="body2">
          {dataset.includePattern
            ? dataset.includePattern
            : 'No include pattern'}
        </Typography>
      </CardContent>
      <CardContent>
        <Typography color="textSecondary" variant="subtitle2">
          Exclude Pattern
        </Typography>
        <Typography color="textPrimary" variant="body2">
          {dataset.excludePattern
            ? dataset.excludePattern
            : 'No exclude pattern'}
        </Typography>
      </CardContent>
    </Card>
  );
};

RedshiftDatasetAWSInfo.propTypes = {
  dataset: PropTypes.object.isRequired
};
