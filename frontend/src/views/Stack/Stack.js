import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import {
  Box,
  Button,
  Card,
  CardHeader,
  CircularProgress,
  Divider,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography
} from '@material-ui/core';
import { Article, RefreshRounded, SystemUpdate } from '@material-ui/icons';
import { useSnackbar } from 'notistack';
import { LoadingButton } from '@material-ui/lab';
import useClient from '../../hooks/useClient';
import { useDispatch } from '../../store';
import getStack from '../../api/Stack/getStack';
import { SET_ERROR } from '../../store/errorReducer';
import StackStatus from '../../components/StackStatus';
import Scrollbar from '../../components/Scrollbar';
import StackLogs from './StackLogs';
import updateStack from '../../api/Stack/updateStack';

const Stack = (props) => {
  const { environmentUri, stackUri, targetUri, targetType } = props;
  const client = useClient();
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const [stack, setStack] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [resources, setResources] = useState([]);
  const [stackName, setStackName] = useState(null);
  const [openLogsModal, setOpenLogsModal] = useState(null);
  const handleOpenLogsModal = () => {
    setOpenLogsModal(true);
  };
  const handleCloseOpenLogs = () => {
    setOpenLogsModal(false);
  };

  const fetchStack = async (isFetching = false, isRefreshing = false) => {
    if (isFetching) setLoading(true);
    if (isRefreshing) setRefreshing(true);
    try {
      const response = await client.query(getStack(environmentUri, stackUri));
      if (response && !response.errors) {
        setStack({ ...response.data.getStack });
        setStackName(`${response.data.getStack.name}`);
        setResources(JSON.parse(response.data.getStack.resources).resources);
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    }
  };

  const updateTargetStack = async () => {
    setUpdating(true);
    const response = await client.mutate(updateStack(targetUri, targetType));
    if (!response.errors) {
      enqueueSnackbar('CloudFormation stack update started', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      fetchStack().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setUpdating(false);
  };

  const fetchItem = async () => {
    fetchStack(true, false).then(() => setLoading(false)).catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
  };

  const refreshItem = async () => {
    fetchStack(false, true).then(() => setRefreshing(false)).catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
  };

  useEffect(() => {
    if (client) {
      fetchItem().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client]);

  if (loading) {
    return <CircularProgress />;
  }

  return (
    <Box sx={{ mt: 3 }}>
      {stack && (
      <Box>
        <Box
          display="flex"
          justifyContent="flex-end"
          sx={{ p: 1 }}
        >
          <Button
            color="primary"
            startIcon={<RefreshRounded fontSize="small" />}
            sx={{ m: 1 }}
            variant="outlined"
            onClick={refreshItem}
          >
            Refresh
          </Button>
          <Button
            color="primary"
            startIcon={<Article fontSize="small" />}
            sx={{ m: 1 }}
            variant="outlined"
            onClick={handleOpenLogsModal}
          >
            Logs
          </Button>
          <LoadingButton
            color="primary"
            pending={updating}
            onClick={updateTargetStack}
            startIcon={<SystemUpdate fontSize="small" />}
            sx={{ m: 1 }}
            variant="contained"
          >
            Update
          </LoadingButton>
        </Box>
        {refreshing ? <CircularProgress /> : (
          <Box>
            <Card>
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
                    <Typography
                      color="textSecondary"
                      variant="overline"
                    >
                      Name
                    </Typography>
                    <Typography
                      color="textPrimary"
                      variant="subtitle2"
                    >
                      {stackName || '-'}
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
                    <Typography
                      color="textSecondary"
                      variant="overline"
                    >
                      ARN
                    </Typography>
                    <Typography
                      color="textPrimary"
                      variant="subtitle2"
                    >
                      {stack.stackid}
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
                    <Typography
                      color="textSecondary"
                      variant="overline"
                    >
                      Status
                    </Typography>
                    <Typography
                      color="textPrimary"
                      variant="h5"
                    >
                      <StackStatus status={stack?.status} />

                    </Typography>
                  </div>
                </Grid>
              </Grid>
            </Card>
            {resources && (
            <Card sx={{ mt: 3 }}>
              <CardHeader
                title={<Box>CloudFormation Resources</Box>}
              />
              <Divider />
              <Scrollbar>
                <Box sx={{ minWidth: 600 }}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>
                          Physical ID
                        </TableCell>
                        <TableCell>
                          Resource Type
                        </TableCell>
                        <TableCell>
                          Resource Status
                        </TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {resources.map((node) => (
                        <TableRow>
                          <TableCell>
                            {node.PhysicalResourceId || '-'}
                          </TableCell>
                          <TableCell>
                            {node.ResourceType || '-'}
                          </TableCell>
                          <TableCell>
                            {node.ResourceStatus || '-'}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </Box>
              </Scrollbar>
            </Card>
            )}
          </Box>
        )}
        <StackLogs
          environmentUri={environmentUri}
          stack={stack}
          onClose={handleCloseOpenLogs}
          open={openLogsModal}
        />
      </Box>
      )}
    </Box>
  );
};

Stack.propTypes = {
  environmentUri: PropTypes.string.isRequired,
  stackUri: PropTypes.string.isRequired,
  targetUri: PropTypes.string.isRequired,
  targetType: PropTypes.string.isRequired
};
export default Stack;
