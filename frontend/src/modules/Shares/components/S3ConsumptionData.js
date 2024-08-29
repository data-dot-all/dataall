import {
  Box,
  Divider,
  Typography,
  Card,
  CardHeader,
  CardContent,
  IconButton
} from '@mui/material';
import PropTypes from 'prop-types';
import { useParams } from 'react-router-dom';
import React, { useCallback, useEffect, useState } from 'react';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import { getS3ConsumptionData } from '../services';
import { CopyToClipboard } from 'react-copy-to-clipboard/lib/Component';
import { CopyAllOutlined } from '@mui/icons-material';
import { useTheme } from '@mui/styles';
import { useSnackbar } from 'notistack';
import { isFeatureEnabled } from 'utils';

export const S3ConsumptionData = (props) => {
  const { share } = props;
  const theme = useTheme();
  const { enqueueSnackbar } = useSnackbar();
  const client = useClient();
  const dispatch = useDispatch();
  const params = useParams();
  const [consumptionData, setConsumptionData] = useState({});
  const fetchData = useCallback(async () => {
    const response_c = await client.query(
      getS3ConsumptionData({
        shareUri: params.uri
      })
    );
    if (!response_c.errors) {
      setConsumptionData({
        s3bucketName: response_c.data.getS3ConsumptionData.s3bucketName,
        s3AccessPointName:
          response_c.data.getS3ConsumptionData.s3AccessPointName,
        sharedGlueDatabase:
          response_c.data.getS3ConsumptionData.sharedGlueDatabase
      });
    } else {
      dispatch({ type: SET_ERROR, error: response_c.errors[0].message });
    }
  }, [client, dispatch, share]);

  useEffect(() => {
    if (client && share) {
      fetchData().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client, fetchData, dispatch, share]);

  const copyNotification = () => {
    enqueueSnackbar('Copied to clipboard', {
      anchorOrigin: {
        horizontal: 'right',
        vertical: 'top'
      },
      variant: 'success'
    });
  };

  return (
    <Box sx={{ mb: 3 }}>
      <Card {...share}>
        <Box>
          <CardHeader title="Data Consumption details" />
          <Divider />
        </Box>
        <CardContent>
          <Box>
            <Box>
              <Typography
                display="inline"
                color="textSecondary"
                variant="subtitle2"
              >
                S3 Bucket name (Bucket sharing):
              </Typography>
              <Typography
                display="inline"
                color="textPrimary"
                variant="subtitle2"
              >
                {` ${consumptionData.s3bucketName || '-'}`}
              </Typography>
              <Typography color="textPrimary" variant="subtitle2">
                <CopyToClipboard
                  onCopy={() => copyNotification()}
                  text={`aws s3 ls s3://${consumptionData.s3bucketName}`}
                >
                  <IconButton>
                    <CopyAllOutlined
                      sx={{
                        color:
                          theme.palette.mode === 'dark'
                            ? theme.palette.primary.contrastText
                            : theme.palette.primary.main
                      }}
                    />
                  </IconButton>
                </CopyToClipboard>
                {`aws s3 ls s3://${consumptionData.s3bucketName}`}
              </Typography>
            </Box>
            {isFeatureEnabled('s3_datasets', 'file_actions') && (
              <Box sx={{ mt: 3 }}>
                <Typography
                  display="inline"
                  color="textSecondary"
                  variant="subtitle2"
                >
                  S3 Access Point name (Folder sharing):
                </Typography>
                <Typography
                  display="inline"
                  color="textPrimary"
                  variant="subtitle2"
                >
                  {` ${consumptionData.s3AccessPointName || '-'}`}
                </Typography>
                <Typography color="textPrimary" variant="subtitle2">
                  <CopyToClipboard
                    onCopy={() => copyNotification()}
                    text={`aws s3 ls arn:aws:s3:${share.dataset.region}:${share.dataset.AwsAccountId}:accesspoint/${consumptionData.s3AccessPointName}/SHARED_FOLDER/`}
                  >
                    <IconButton>
                      <CopyAllOutlined
                        sx={{
                          color:
                            theme.palette.mode === 'dark'
                              ? theme.palette.primary.contrastText
                              : theme.palette.primary.main
                        }}
                      />
                    </IconButton>
                  </CopyToClipboard>
                  {`aws s3 ls arn:aws:s3:${share.dataset.region}:${share.dataset.AwsAccountId}:accesspoint/${consumptionData.s3AccessPointName}/SHARED_FOLDER/`}
                </Typography>
              </Box>
            )}
            <Box sx={{ mt: 3 }}>
              <Typography
                display="inline"
                color="textSecondary"
                variant="subtitle2"
              >
                Glue database name (Table sharing):
              </Typography>
              <Typography
                display="inline"
                color="textPrimary"
                variant="subtitle2"
              >
                {` ${consumptionData.sharedGlueDatabase || '-'}`}
              </Typography>
              <Typography color="textPrimary" variant="subtitle2">
                <CopyToClipboard
                  onCopy={() => copyNotification()}
                  text={`SELECT * FROM ${consumptionData.sharedGlueDatabase}.TABLENAME`}
                >
                  <IconButton>
                    <CopyAllOutlined
                      sx={{
                        color:
                          theme.palette.mode === 'dark'
                            ? theme.palette.primary.contrastText
                            : theme.palette.primary.main
                      }}
                    />
                  </IconButton>
                </CopyToClipboard>
                {`SELECT * FROM ${consumptionData.sharedGlueDatabase}.TABLENAME`}
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

S3ConsumptionData.propTypes = {
  share: PropTypes.object.isRequired
};
