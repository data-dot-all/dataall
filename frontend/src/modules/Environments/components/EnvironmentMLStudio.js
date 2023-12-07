import {
  Box,
  Card,
  CardHeader,
  Divider,
  Grid,
  CardContent,
  Typography,
  CircularProgress,
  Chip
} from '@mui/material';

import PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState } from 'react';
import { RefreshTableMenu } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { getEnvironmentMLStudioDomain, useClient } from 'services';

export const EnvironmentMLStudio = ({ environment }) => {
  const client = useClient();
  const dispatch = useDispatch();
  const [mlStudioDomain, setMLStudioDomain] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchMLStudioDomain = useCallback(async () => {
    try {
      setLoading(true);
      const response = await client.query(
        getEnvironmentMLStudioDomain({
          environmentUri: environment.environmentUri
        })
      );
      if (!response.errors) {
        if (response.data.getEnvironmentMLStudioDomain) {
          setMLStudioDomain(response.data.getEnvironmentMLStudioDomain);
        }
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    } finally {
      setLoading(false);
    }
  }, [client, dispatch, environment.environmentUri]);

  useEffect(() => {
    if (client) {
      fetchMLStudioDomain().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, fetchMLStudioDomain, dispatch]);

  if (loading) {
    return <CircularProgress />;
  }

  return (
    <Box>
      <Card>
        <CardHeader
          action={<RefreshTableMenu refresh={fetchMLStudioDomain} />}
          title={<Box>ML Studio Domain Information</Box>}
        />
        <Divider />
        <Box
          sx={{
            alignItems: 'center',
            display: 'flex',
            flexWrap: 'wrap',
            m: -1,
            p: 2
          }}
        >
          <Grid item md={2} sm={6} xs={12}></Grid>
        </Box>
        {mlStudioDomain === null ? (
          <Box sx={{ p: 3 }}>
            <Typography
              align="center"
              color="textSecondary"
              variant="subtitle2"
            >
              No ML Studio Domain - To Create a ML Studio Domain for this
              Environment: {environment.label}, edit the Environment and enable
              the ML Studio Environment Feature
            </Typography>
          </Box>
        ) : (
          <Grid container spacing={3}>
            <Grid item lg={8} xl={9} xs={12}>
              <CardContent>
                <Typography color="textSecondary" variant="subtitle2">
                  SageMaker ML Studio Domain Name
                </Typography>
                <Typography color="textPrimary" variant="body2">
                  {mlStudioDomain.sagemakerStudioDomainName}
                </Typography>
              </CardContent>
              <CardContent>
                <Typography color="textSecondary" variant="subtitle2">
                  SageMaker ML Studio Default Execution Role
                </Typography>
                <Typography color="textPrimary" variant="body2">
                  arn:aws:iam::{environment.AwsAccountId}:role/
                  {mlStudioDomain.DefaultDomainRoleName}
                </Typography>
              </CardContent>
              <CardContent>
                <Typography color="textSecondary" variant="subtitle2">
                  Domain VPC Type
                </Typography>
                <Typography color="textPrimary" variant="body2">
                  {mlStudioDomain.vpcType}
                </Typography>
              </CardContent>
              {(mlStudioDomain.vpcType === 'imported' ||
                mlStudioDomain.vpcType === 'default') && (
                <>
                  <CardContent>
                    <Typography color="textSecondary" variant="subtitle2">
                      Domain VPC Id
                    </Typography>
                    <Typography color="textPrimary" variant="body2">
                      {mlStudioDomain.vpcId}
                    </Typography>
                  </CardContent>
                  <CardContent>
                    <Typography color="textSecondary" variant="subtitle2">
                      Domain Subnet Ids
                    </Typography>
                    <Typography color="textPrimary" variant="body2">
                      {mlStudioDomain.subnetIds?.map((subnet) => (
                        <Chip
                          sx={{ mr: 0.5, mb: 0.5 }}
                          key={subnet}
                          label={subnet}
                          variant="outlined"
                        />
                      ))}
                    </Typography>
                  </CardContent>
                </>
              )}
            </Grid>
          </Grid>
        )}
      </Card>
    </Box>
  );
};

EnvironmentMLStudio.propTypes = {
  environment: PropTypes.object.isRequired
};
