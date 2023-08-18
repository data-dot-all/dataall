import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Divider,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow
} from '@mui/material';
import PropTypes from 'prop-types';
import React, { useEffect, useState } from 'react';
import { useClient } from 'services';

export const PipelineEnvironments = (props) => {
  const { pipeline } = props;
  const client = useClient();
  const [environments, setEnvironments] = useState([]);

  useEffect(() => {
    if (client && pipeline) {
      const environmentsSorted = pipeline.developmentEnvironments.nodes.sort(
        (a, b) => {
          return a.order - b.order;
        }
      );
      setEnvironments(environmentsSorted);
    }
  }, [client, pipeline]);

  return (
    <>
      <Grid container spacing={3}>
        <Grid item lg={12} xl={12} xs={12}>
          <Box>
            <Card>
              <CardHeader title="Development environments" />
              <Divider />
              <CardContent>
                <Box>
                  <Table size="small">
                    <colgroup>
                      <col width="5%" />
                      <col width="10%" />
                      <col width="35%" />
                      <col width="35%" />
                      <col width="15%" />
                    </colgroup>
                    {environments > 0 && (
                      <TableHead>
                        <TableRow>
                          <TableCell>Order</TableCell>
                          <TableCell>Development Stage</TableCell>
                          <TableCell>Environment</TableCell>
                          <TableCell>Team</TableCell>
                          <TableCell>AWS Account</TableCell>
                        </TableRow>
                      </TableHead>
                    )}
                    <TableBody>
                      {environments &&
                        environments.map((e) => (
                          <>
                            <TableRow id="addr0" key={e.envPipelineUri}>
                              <TableCell>{e.order}</TableCell>
                              <TableCell>{e.stage}</TableCell>
                              <TableCell>{e.environmentLabel}</TableCell>
                              <TableCell>{e.samlGroupName}</TableCell>
                              <TableCell>{e.AwsAccountId}</TableCell>
                            </TableRow>
                          </>
                        ))}
                    </TableBody>
                  </Table>
                </Box>
              </CardContent>
            </Card>
          </Box>
        </Grid>
      </Grid>
    </>
  );
};
PipelineEnvironments.propTypes = {
  pipeline: PropTypes.object.isRequired
};
