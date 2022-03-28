import PropTypes from 'prop-types';
import { useCallback, useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardHeader,
  Divider,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography
} from '@mui/material';
import CircularProgress from '@mui/material/CircularProgress';
import { useSnackbar } from 'notistack';
import { PlayCircle } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import useClient from '../../hooks/useClient';
import * as Defaults from '../../components/defaults';
import Scrollbar from '../../components/Scrollbar';
import RefreshTableMenu from '../../components/RefreshTableMenu';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import listSqlPipelineExecutions from '../../api/SqlPipeline/listSqlPipelineExecutions';
import Label from '../../components/Label';
import startDataProcessingPipeline from '../../api/SqlPipeline/startPipeline';

const PipelineRuns = ({ pipeline }) => {
  const client = useClient();
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const [items, setItems] = useState(Defaults.PagedResponseDefault);
  const [filter] = useState(Defaults.DefaultFilter);
  const [running, setRunning] = useState(false);
  const [loading, setLoading] = useState(null);
  const [outputs] = useState(JSON.parse(pipeline?.stack?.outputs));
  const fetchItems = useCallback(async () => {
    setLoading(true);
    const response = await client.query(
      listSqlPipelineExecutions({
        sqlPipelineUri: pipeline.sqlPipelineUri,
        stage: 'prod'
      })
    );
    if (!response.errors) {
      setItems(response.data.listSqlPipelineExecutions);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [client, dispatch, pipeline.sqlPipelineUri]);

  const runPipeline = async () => {
    setRunning(true);
    const response = await client.mutate(
      startDataProcessingPipeline(pipeline.sqlPipelineUri)
    );
    if (!response.errors) {
      enqueueSnackbar('Pipeline started successfully', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setRunning(false);
  };

  useEffect(() => {
    if (client) {
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, filter.page, dispatch, fetchItems]);

  return (
    <Box>
      <Card sx={{ mb: 3 }}>
        <Grid container>
          <Grid
            item
            md={4}
            xs={12}
            sx={{
              alignItems: 'center',
              borderRight: (theme) => ({
                md: `1px solid ${theme.palette.divider}`
              }),
              borderBottom: (theme) => ({
                md: 'none',
                xs: `1px solid ${theme.palette.divider}`
              }),
              display: 'flex',
              justifyContent: 'space-between',
              p: 3
            }}
          >
            <div>
              <Typography color="textSecondary" variant="overline">
                State Machine
              </Typography>
              <Typography color="textPrimary" variant="subtitle2">
                {outputs.PipelineNameOutput || '-'}
              </Typography>
            </div>
          </Grid>
          <Grid
            item
            md={4}
            xs={12}
            sx={{
              alignItems: 'center',
              borderRight: (theme) => ({
                md: `1px solid ${theme.palette.divider}`
              }),
              borderBottom: (theme) => ({
                xs: `1px solid ${theme.palette.divider}`,
                md: 'none'
              }),
              display: 'flex',
              justifyContent: 'space-between',
              p: 3
            }}
          >
            <div>
              <Typography color="textSecondary" variant="overline">
                CodeCommit
              </Typography>
              <Typography color="textPrimary" variant="subtitle2">
                {pipeline.cloneUrlHttp}
              </Typography>
            </div>
          </Grid>
          <Grid
            item
            md={4}
            xs={12}
            sx={{
              alignItems: 'center',
              display: 'flex',
              justifyContent: 'space-between',
              p: 3
            }}
          >
            <div>
              <Typography color="textSecondary" variant="overline">
                Status
              </Typography>
              <Typography color="textPrimary" variant="h5">
                <Label
                  color={
                    items?.nodes[0]?.status !== 'FAILED' ? 'success' : 'error'
                  }
                >
                  {items?.nodes[0]?.status}
                </Label>
              </Typography>
            </div>
          </Grid>
        </Grid>
      </Card>
      <Card>
        <CardHeader
          action={<RefreshTableMenu refresh={fetchItems} />}
          title={<Box>Execution History</Box>}
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
          <Grid item md={10} sm={6} xs={12} />
          <Grid item md={2} sm={6} xs={12}>
            <LoadingButton
              loading={running}
              color="primary"
              onClick={runPipeline}
              startIcon={<PlayCircle fontSize="small" />}
              sx={{ m: 1 }}
              variant="outlined"
            >
              Run Pipeline
            </LoadingButton>
          </Grid>
        </Box>
        <Scrollbar>
          <Box sx={{ minWidth: 600 }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Execution ID</TableCell>
                  <TableCell>Start Date</TableCell>
                  <TableCell>End Date</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              {loading ? (
                <CircularProgress sx={{ mt: 1 }} />
              ) : (
                <TableBody>
                  {items.nodes.length > 0 ? (
                    items.nodes.map((item) => (
                      <TableRow hover key={item.name}>
                        <TableCell>{item.name}</TableCell>
                        <TableCell>{item.startDate}</TableCell>
                        <TableCell>{item.stopDate}</TableCell>
                        <TableCell>
                          <Label
                            color={
                              item.status !== 'FAILED' ? 'success' : 'error'
                            }
                          >
                            {item.status}
                          </Label>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow hover>
                      <TableCell>No pipeline executions found</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              )}
            </Table>
          </Box>
        </Scrollbar>
      </Card>
    </Box>
  );
};

PipelineRuns.propTypes = {
  pipeline: PropTypes.object.isRequired
};

export default PipelineRuns;
