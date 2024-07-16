import PropTypes from 'prop-types';
import {
  Button,
  Card,
  CardContent,
  CardHeader,
  Divider,
  Typography
} from '@mui/material';

import { useSnackbar } from 'notistack';
import React from 'react';
import { FaSync } from 'react-icons/fa';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';

import { DatashareStatus } from './DatashareStatus';
import { retryRedshiftDatashare } from '../services';

export const RedshiftDatasetAWSInfo = (props) => {
  const { dataset } = props;
  const dispatch = useDispatch();
  const client = useClient();
  const { enqueueSnackbar } = useSnackbar();
  const retryDataShare = async () => {
    const response = await client.mutate(
      retryRedshiftDatashare(dataset.datasetUri)
    );

    if (!response.errors) {
      enqueueSnackbar('Datashare retry triggered', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };

  return (
    <Card {...dataset}>
      <CardHeader title="AWS Information" />
      <Divider />
      <CardContent>
        <Typography color="textSecondary" variant="subtitle2">
          Datashare status
        </Typography>
        <Typography color="textPrimary" variant="body2">
          <DatashareStatus status={dataset.datashareStatus}></DatashareStatus>
          {!(dataset.datashareStatus === 'COMPLETED') ? (
            <Button
              startIcon={<FaSync size={15} />}
              color="error"
              type="submit"
              variant="text"
              onClick={() => {
                retryDataShare();
              }}
            >
              Retry/continue datashare
            </Button>
          ) : (
            ''
          )}
        </Typography>
      </CardContent>
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
              {dataset.connection.workgroup}
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
          DatashareArn
        </Typography>
        <Typography color="textPrimary" variant="body2">
          {dataset.datashareArn}
        </Typography>
      </CardContent>
    </Card>
  );
};

RedshiftDatasetAWSInfo.propTypes = {
  dataset: PropTypes.object.isRequired
};
