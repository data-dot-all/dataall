import {
  Box,
  Button,
  Card,
  CardHeader,
  CardContent,
  CircularProgress,
  Dialog,
  Divider,
  Grid,
  IconButton,
  MenuItem,
  TextField,
  Switch,
  Typography,
  FormControlLabel,
  FormGroup,
  Alert
} from '@mui/material';
import { Article, CancelRounded, SystemUpdate } from '@mui/icons-material';
import React, { useCallback, useEffect, useState } from 'react';
import { LoadingButton } from '@mui/lab';
import { Label } from 'design';
import {
  getMaintenanceStatus,
  stopMaintenanceWindow,
  startMaintenanceWindow,
  startReindexCatalog
} from '../services';
import { useClient, fetchEnums } from 'services';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useSnackbar } from 'notistack';
import { ModuleNames, isModuleEnabled } from 'utils';

const START_MAINTENANCE = 'Start Maintenance';
const END_MAINTENANCE = 'End Maintenance';
export const PENDING_STATUS = 'PENDING';
export const ACTIVE_STATUS = 'ACTIVE';
export const INACTIVE_STATUS = 'INACTIVE';

export const MaintenanceConfirmationPopUp = (props) => {
  const {
    popUp,
    setPopUp,
    confirmedMode,
    setConfirmedMode,
    maintenanceButtonText,
    setMaintenanceButtonText,
    setDropDownStatus,
    setMaintenanceWindowStatus
  } = props;
  const client = useClient();
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();

  const handlePopUpModal = async () => {
    if (maintenanceButtonText === START_MAINTENANCE) {
      if (!client) {
        dispatch({
          type: SET_ERROR,
          error: 'Client not initialized for starting maintenance window'
        });
      }
      const response = await client.mutate(
        startMaintenanceWindow({ mode: confirmedMode })
      );
      if (!response.errors && response.data.startMaintenanceWindow != null) {
        const respData = response.data.startMaintenanceWindow;
        if (respData === true) {
          setMaintenanceButtonText(END_MAINTENANCE);
          setMaintenanceWindowStatus(PENDING_STATUS);
          setDropDownStatus(false);
          enqueueSnackbar(
            'Maintenance Window Started. Please check the status',
            {
              anchorOrigin: {
                horizontal: 'right',
                vertical: 'top'
              },
              variant: 'success'
            }
          );
        } else {
          enqueueSnackbar('Could not start maintenance window', {
            anchorOrigin: {
              horizontal: 'right',
              vertical: 'top'
            },
            variant: 'success'
          });
        }
      } else {
        const error = response.errors
          ? response.errors[0].message
          : 'Something went wrong while starting maintenance window. Please check gql logs';
        dispatch({ type: SET_ERROR, error });
      }
    } else if (maintenanceButtonText === END_MAINTENANCE) {
      const response = await client.mutate(stopMaintenanceWindow());
      if (
        !response.errors &&
        response.data.stopMaintenanceWindow != null &&
        response.data.stopMaintenanceWindow === true
      ) {
        setMaintenanceButtonText(START_MAINTENANCE);
        // Unfreeze the dropdown menu
        setDropDownStatus(true);
        setConfirmedMode('');
        setMaintenanceWindowStatus(INACTIVE_STATUS);
        enqueueSnackbar('Maintenance Window Stopped', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
      } else {
        const error = response.errors
          ? response.errors[0].message
          : 'Something went wrong while stopping maintenance window. Please check gql logs';
        dispatch({ type: SET_ERROR, error });
      }
    }
    setPopUp(false);
  };

  return (
    <Dialog maxWidth="md" fullWidth open={popUp}>
      <Box sx={{ p: 2 }}>
        <Card>
          <CardHeader
            title={
              <Box>
                Are you sure you want to {maintenanceButtonText.toLowerCase()}?
              </Box>
            }
          />
          <Divider />
          <Box display="flex" sx={{ p: 1 }}>
            <Button
              color="primary"
              startIcon={<Article fontSize="small" />}
              sx={{ m: 1 }}
              variant="outlined"
              onClick={handlePopUpModal}
            >
              Yes
            </Button>
            <Button
              color="primary"
              startIcon={<Article fontSize="small" />}
              sx={{ m: 1 }}
              variant="outlined"
              onClick={() => {
                setPopUp(false);
              }}
            >
              No
            </Button>
          </Box>
        </Card>
      </Box>
    </Dialog>
  );
};

export const ReIndexConfirmationPopUp = (props) => {
  const { popUpReIndex, setPopUpReIndex, setUpdatingReIndex } = props;
  const client = useClient();
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const [withDelete, setWithDelete] = useState(false);

  const handleReindexStart = async () => {
    setUpdatingReIndex(true);
    if (!client) {
      dispatch({
        type: SET_ERROR,
        error: 'Client not initialized for re-indexing catalog task'
      });
    }
    const response = await client.mutate(
      startReindexCatalog({ handleDeletes: withDelete })
    );
    if (!response.errors && response.data.startReindexCatalog != null) {
      const respData = response.data.startReindexCatalog;
      if (respData === true) {
        enqueueSnackbar('Re Index Task has Started. Please check the status', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
      } else {
        enqueueSnackbar('Could not start re index task', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
      }
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Something went wrong while starting re index task. Please check gql logs';
      dispatch({ type: SET_ERROR, error });
    }
    setPopUpReIndex(false);
    setUpdatingReIndex(false);
  };

  return (
    <Dialog maxWidth="sm" fullWidth open={popUpReIndex}>
      <Box sx={{ p: 3 }}>
        <Typography
          align="center"
          color="textPrimary"
          gutterBottom
          variant="h5"
        >
          Start Data.all Catalog Reindexing Task?
        </Typography>
        <Divider />
        <Box>
          <CardContent>
            <Alert severity="warning" sx={{ mr: 1 }}>
              Starting a reindexing job will update all catalog objects in
              data.all with the latest information found in RDS.
            </Alert>
          </CardContent>
        </Box>
        <Box
          display="flex"
          alignItems="center"
          justifyContent="center"
          sx={{ mb: 3 }}
        >
          <FormGroup>
            <FormControlLabel
              control={
                <Switch
                  color="primary"
                  checked={withDelete}
                  onChange={() => {
                    setWithDelete(!withDelete);
                  }}
                  edge="start"
                  name="withDelete"
                />
              }
              label={
                <div>
                  With Deletes
                  <Alert severity="error" sx={{ mr: 1 }}>
                    Specifying <b>withDeletes</b> will identify catalog objects
                    no longer in data.all's DB (if any) and attempt to delete /
                    clean up the catalog
                  </Alert>
                </div>
              }
            />
          </FormGroup>
        </Box>
        <Divider />
        <Box display="flex" sx={{ mt: 1 }}>
          <CardContent>
            <Typography color="textPrimary">
              Please confirm if you want to start the reindexing task:
            </Typography>
            <Button
              color="primary"
              startIcon={<Article fontSize="small" />}
              sx={{ m: 1 }}
              variant="outlined"
              onClick={handleReindexStart}
            >
              Start
            </Button>
            <Button
              color="primary"
              startIcon={<Article fontSize="small" />}
              sx={{ m: 1 }}
              variant="outlined"
              onClick={() => {
                setPopUpReIndex(false);
              }}
            >
              Cancel
            </Button>
          </CardContent>
        </Box>
      </Box>
    </Dialog>
  );
};

export const MaintenanceViewer = () => {
  const client = useClient();
  const [refreshing, setRefreshing] = useState(true);
  const refreshingReIndex = false;
  const [updatingReIndex, setUpdatingReIndex] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [mode, setMode] = useState('');
  const [popUp, setPopUp] = useState(false);
  const [popUpReIndex, setPopUpReIndex] = useState(false);
  const [confirmedMode, setConfirmedMode] = useState('');
  const [maintenanceButtonText, setMaintenanceButtonText] =
    useState(START_MAINTENANCE);
  const [maintenanceWindowStatus, setMaintenanceWindowStatus] =
    useState(INACTIVE_STATUS);
  const [maintenanceModes, setMaintenanceModes] = useState([]);
  const [dropDownStatus, setDropDownStatus] = useState(false);
  const [refreshingTimer, setRefreshingTimer] = useState('');
  const { enqueueSnackbar, closeSnackbar } = useSnackbar();
  const dispatch = useDispatch();

  const fetchMaintenanceModes = async () => {
    const maintenanceModesEnum = await fetchEnums(client, ['MaintenanceModes']);
    if (maintenanceModesEnum['MaintenanceModes'].length > 0) {
      setMaintenanceModes(
        maintenanceModesEnum['MaintenanceModes'].map((elem) => {
          return { label: elem.value, value: elem.value };
        })
      );
    } else {
      dispatch({ type: SET_ERROR, error: 'Could not fetch maintenance modes' });
    }
  };

  const refreshMaintenanceView = async () => {
    setUpdating(true);
    setRefreshing(true);
    _getMaintenanceWindowStatus()
      .then((data) => {
        setMaintenanceWindowStatus(data.status);
        if (data.status === INACTIVE_STATUS) {
          setMaintenanceButtonText(START_MAINTENANCE);
          setConfirmedMode('');
          setDropDownStatus(true);
          clearInterval(refreshingTimer);
        } else {
          setMaintenanceButtonText(END_MAINTENANCE);
          setConfirmedMode(
            maintenanceModes.find((obj) => obj.value === data.mode).label
          );
          setDropDownStatus(false);
        }
        setUpdating(false);
        setRefreshing(false);
      })
      .catch((e) => dispatch({ type: SET_ERROR, e }));
  };

  const _getMaintenanceWindowStatus = async () => {
    if (client) {
      const response = await client.query(getMaintenanceStatus());
      if (
        !response.errors &&
        response.data.getMaintenanceWindowStatus !== null
      ) {
        return response.data.getMaintenanceWindowStatus;
      } else {
        const error = response.errors
          ? response.errors[0].message
          : 'Could not fetch status of maintenance window';
        dispatch({ type: SET_ERROR, error });
      }
    }
  };

  const startMaintenanceWindow = () => {
    // Check if proper maintenance mode is selected
    if (
      !maintenanceModes.map((obj) => obj.value).includes(mode) &&
      maintenanceButtonText === START_MAINTENANCE
    ) {
      dispatch({
        type: SET_ERROR,
        error: 'Please select correct maintenance mode'
      });
    }
    setConfirmedMode(mode);
    setPopUp(true);
  };

  const refreshStatus = async () => {
    closeSnackbar();
    const response = await client.query(getMaintenanceStatus());
    if (!response.errors && response.data.getMaintenanceWindowStatus !== null) {
      const maintenanceStatusData = response.data.getMaintenanceWindowStatus;
      setMaintenanceWindowStatus(maintenanceStatusData.status);
      if (
        maintenanceStatusData.status === INACTIVE_STATUS ||
        maintenanceStatusData.status === ACTIVE_STATUS
      ) {
        clearInterval(refreshingTimer);
      } else {
        enqueueSnackbar(
          <Box>
            <Grid container spacing={2}>
              <Grid item sx={1}>
                <CircularProgress sx={{ color: '#fff' }} size={15} />
              </Grid>
              <Grid item sx={11}>
                <Typography
                  color="textPrimary"
                  sx={{ color: '#fff' }}
                  variant="subtitle2"
                >
                  Maintenance Window Status is being updated
                </Typography>
              </Grid>
            </Grid>
          </Box>,
          {
            key: new Date().getTime() + Math.random(),
            anchorOrigin: {
              horizontal: 'right',
              vertical: 'top'
            },
            variant: 'info',
            persist: true,
            action: (key) => (
              <IconButton
                onClick={() => {
                  closeSnackbar(key);
                }}
              >
                <CancelRounded sx={{ color: '#fff' }} />
              </IconButton>
            )
          }
        );
      }
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Maintenance Status not found. Something went wrong';
      dispatch({ type: SET_ERROR, error });
    }
  };

  const initializeMaintenanceView = useCallback(async () => {
    const response = await client.query(getMaintenanceStatus());
    if (!response.errors && response.data.getMaintenanceWindowStatus !== null) {
      const maintenanceStatusData = response.data.getMaintenanceWindowStatus;
      if (
        maintenanceStatusData.status === PENDING_STATUS ||
        maintenanceStatusData.status === ACTIVE_STATUS
      ) {
        setMaintenanceButtonText(END_MAINTENANCE);
        setMaintenanceWindowStatus(maintenanceStatusData.status);
        setConfirmedMode(
          maintenanceModes.find(
            (obj) => obj.value === maintenanceStatusData.mode
          ).label
        );
        setDropDownStatus(false);
      } else if (maintenanceStatusData.status === INACTIVE_STATUS) {
        setMaintenanceButtonText(START_MAINTENANCE);
        setConfirmedMode('');
        setDropDownStatus(true);
      }
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Maintenance Status not found. Something went wrong';
      dispatch({ type: SET_ERROR, error });
    }
    setRefreshing(false);
  }, [client, maintenanceModes]);

  useEffect(() => {
    if (client) {
      fetchMaintenanceModes().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
      const setTimer = setInterval(() => {
        refreshStatus().catch((e) =>
          dispatch({ type: SET_ERROR, error: e.message })
        );
      }, [10000]);
      setRefreshingTimer(setTimer);
      return () => clearInterval(setTimer);
    }
  }, [client]);

  useEffect(() => {
    if (maintenanceModes.length > 0) {
      initializeMaintenanceView().catch((e) =>
        dispatch({ type: SET_ERROR, e })
      );
    }
  }, [maintenanceModes]);

  return (
    <Box>
      {refreshingReIndex ? (
        <CircularProgress />
      ) : (
        <div>
          {isModuleEnabled(ModuleNames.CATALOG) && (
            <Box display="flex" paddingBottom={3} width="25%">
              <Card>
                <CardHeader title={<Box>Re-Index Data.all Catalog</Box>} />
                <Divider />
                <Box>
                  <LoadingButton
                    color="primary"
                    loading={updatingReIndex}
                    onClick={() => setPopUpReIndex(true)}
                    startIcon={<SystemUpdate fontSize="small" />}
                    sx={{ m: 1 }}
                    variant="contained"
                  >
                    Start Re-Index Catalog Task
                  </LoadingButton>
                </Box>
              </Card>
              <ReIndexConfirmationPopUp
                popUpReIndex={popUpReIndex}
                setPopUpReIndex={setPopUpReIndex}
                setUpdatingReIndex={setUpdatingReIndex}
              />
            </Box>
          )}
        </div>
      )}
      {refreshing ? (
        <CircularProgress />
      ) : (
        <Box>
          <Card>
            <CardHeader title={<Box>Create a Maintenance Window</Box>} />
            <Divider />
            <Box>
              <Box display="flex" sx={{ p: 1 }}>
                <Box sx={{ flexGrow: 1 }}>
                  <TextField
                    style={{ width: 500 }}
                    label="Mode"
                    name="MaintenanceMode"
                    onChange={(event) => {
                      setMode(event.target.value);
                    }}
                    select
                    value={mode}
                    variant="outlined"
                    disabled={!dropDownStatus}
                  >
                    {maintenanceModes.map((group) => (
                      <MenuItem key={group.value} value={group.value}>
                        {group.label}
                      </MenuItem>
                    ))}
                  </TextField>
                </Box>
                <Button
                  color="primary"
                  startIcon={<Article fontSize="small" />}
                  sx={{ m: 1 }}
                  variant="outlined"
                  onClick={startMaintenanceWindow}
                  value={'Start Maintenance'}
                >
                  <div>{maintenanceButtonText}</div>
                </Button>

                <LoadingButton
                  color="primary"
                  loading={updating}
                  onClick={refreshMaintenanceView}
                  startIcon={<SystemUpdate fontSize="small" />}
                  sx={{ m: 1 }}
                  variant="contained"
                >
                  Refresh
                </LoadingButton>
              </Box>
            </Box>
            <Divider />
            <Box display="flex" sx={{ p: 3 }}>
              <Typography variant="subtitle2" fontSize={'15px'} sx={{ p: 2 }}>
                Maintenance window status :{' '}
                {maintenanceWindowStatus === ACTIVE_STATUS ? (
                  <Label color={'success'}>ACTIVE</Label>
                ) : maintenanceWindowStatus === PENDING_STATUS ? (
                  <Label color={'warning'}>PENDING</Label>
                ) : maintenanceWindowStatus === INACTIVE_STATUS ? (
                  <Label color={'error'}>INACTIVE</Label>
                ) : (
                  <> - </>
                )}
              </Typography>
              <Typography variant="subtitle2" fontSize={'15px'} sx={{ p: 2 }}>
                |
              </Typography>
              <Typography variant="subtitle2" fontSize={'15px'} sx={{ p: 2 }}>
                Current maintenance mode : {confirmedMode}
              </Typography>
            </Box>
            <Divider />
            <Box>
              <Typography variant="subtitle2" fontSize={'15px'} sx={{ p: 3 }}>
                Note - For safe deployments, please deploy when the status is{' '}
                <Label color={'success'}>ACTIVE</Label>
              </Typography>
            </Box>
          </Card>
          <MaintenanceConfirmationPopUp
            popUp={popUp}
            setPopUp={setPopUp}
            confirmedMode={confirmedMode}
            setConfirmedMode={setConfirmedMode}
            maintenanceButtonText={maintenanceButtonText}
            setMaintenanceButtonText={setMaintenanceButtonText}
            setDropDownStatus={setDropDownStatus}
            refreshingTimer={refreshingTimer}
            setMaintenanceWindowStatus={setMaintenanceWindowStatus}
          />
        </Box>
      )}
    </Box>
  );
};
