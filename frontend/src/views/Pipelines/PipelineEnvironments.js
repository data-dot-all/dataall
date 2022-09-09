import React, {useCallback, useEffect, useState} from 'react';
import { useSnackbar } from 'notistack';
import {
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  Divider,
  Grid,
  IconButton,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField
} from '@mui/material';
import { DeleteOutlined } from '@mui/icons-material';
import PropTypes from 'prop-types';
import { LoadingButton } from '@mui/lab';
import useClient from '../../hooks/useClient';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import * as Defaults from '../../components/defaults';

const PipelineEnvironments = (props) => {
  const { pipeline } = props;
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const client = useClient();
  const [environments, setEnvironments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
      if (client && pipeline) {
        console.log("useeffect")
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
                        <col width="15%" />
                        <col width="40%" />
                        <col width="40%" />
                    </colgroup>
                    {pipeline.developmentEnvironments > 0 && (
                      <TableHead>
                        <TableRow>
                          <TableCell>Order</TableCell>
                          <TableCell>Development Stage</TableCell>
                          <TableCell>Environment</TableCell>
                          <TableCell>Team</TableCell>
                        </TableRow>
                      </TableHead>
                    )}
                    <TableBody>
                      {pipeline.developmentEnvironments && (pipeline.developmentEnvironments.nodes.map((e) => (
                        <>
                          <TableRow id="addr0" key={e.envPipelineUri}>
                            <TableCell>
                              <TextField
                                fullWidth
                                name="idx"
                                value={e.order.toString()}
                                variant="outlined"
                              />
                            </TableCell>
                            <TableCell>
                              <TextField
                                fullWidth
                                name="stage"
                                value={e.stage}
                                variant="outlined"
                              />
                            </TableCell>
                            <TableCell>
                              <TextField
                                fullWidth
                                name="env"
                                value={e.environmentLabel}
                                variant="outlined"
                              />
                            </TableCell>
                            <TableCell>
                              <TextField
                                fullWidth
                                name="team"
                                value={e.samlGroupName}
                                variant="outlined"
                              />
                            </TableCell>
                          </TableRow>
                        </>
                      )))}
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
export default PipelineEnvironments;
