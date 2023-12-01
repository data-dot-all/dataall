import {
  Box,
  Card,
  CardHeader,
  Divider,
  Grid,
  CardContent,
  Typography,
  CircularProgress
} from '@mui/material';

import PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState } from 'react';
import { RefreshTableMenu, ObjectMetadata } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import { getEnvironmentMLStudioDomain } from '../services';

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
          title={<Box>ML Studio Domain</Box>}
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
              Environment: `{environment.label}`, edit the Environment and
              enable the ML Studio Environment Feature
            </Typography>
          </Box>
        ) : (
          <Grid container spacing={3}>
            <Grid item lg={8} xl={9} xs={12}>
              <Card>
                <CardHeader title="ML Studio Information" />
                <Divider />
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
                    arn:aws:s3:::
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
                {mlStudioDomain.vpcType === 'imported' && (
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
                        {mlStudioDomain.subnetIds}
                      </Typography>
                    </CardContent>
                  </>
                )}
              </Card>
            </Grid>
            <Grid item lg={4} xl={3} xs={12}>
              <ObjectMetadata
                accountId={environment.AwsAccountId}
                region={environment.region}
                environment={environment}
                owner={mlStudioDomain.owner}
                created={mlStudioDomain.created}
              />
            </Grid>
          </Grid>
        )}
        {/* <Scrollbar>
          <Box sx={{ minWidth: 600 }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Domain Name</TableCell>
                  <TableCell>VPC</TableCell>
                  <TableCell>Subnets</TableCell>
                </TableRow>
              </TableHead>
              {loading ? (
                <CircularProgress sx={{ mt: 1 }} />
              ) : (
                <TableBody>
                  {items.nodes.length > 0 ? (
                    items.nodes.map((domain) => (
                      <DomainRow
                        domain={domain}
                        environment={environment}
                        fetchItems={fetchItems}
                      />
                    ))
                  ) : (
                    <TableRow hover>
                      <TableCell>No SageMaker Studio Domain Found</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              )}
            </Table>
            {!loading && items.nodes.length > 0 && (
              <Pager
                mgTop={2}
                mgBottom={2}
                items={items}
                onChange={handlePageChange}
              />
            )}
          </Box>
        </Scrollbar> */}
      </Card>
    </Box>
  );
};

EnvironmentMLStudio.propTypes = {
  environment: PropTypes.object.isRequired
};
