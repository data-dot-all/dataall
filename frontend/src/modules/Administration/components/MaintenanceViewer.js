import {
    Box,
    Button,
    Card,
    CardHeader,
    CircularProgress,
    Dialog,
    Divider,
    Grid, IconButton,
    MenuItem,
    TextField,
    Typography
} from "@mui/material";
import React, {useCallback, useEffect, useState} from "react";
import {Article, CancelRounded, SystemUpdate} from "@mui/icons-material";
import {LoadingButton} from "@mui/lab";
import {Label} from "../../../design";
import {isMaintenanceMode} from "../../../services/graphql/MaintenanceWindow";
import {useClient} from "../../../services";
import {SET_ERROR, useDispatch} from "../../../globalErrors";
import {useSnackbar} from "notistack";

const maintenanceModes = [
    {value: "READ-ONLY", label: "Read-Only"},
    {value: "NO-ACCESS", label: "No-Access"}
]

export const MaintenanceConfirmationPopUp = ({popUp, setPopUp, mode, confirmedMode, setConfirmedMode, maintenanceButtonText, setMaintenanceButtonText, setDropDownStatus, refreshingTimer, startRefreshPolling}) => {

    const handlePopUpModal = () => {
        // Call the GrapQL API and then after the success is received change the UI
        if (maintenanceButtonText === 'Start Maintenance') {
            // Call the GraphQL to enable maintenance window
            setMaintenanceButtonText('End Maintenance')
            // Freeze the dropdown menu
            setDropDownStatus(true)
            // Start the Timer
            startRefreshPolling()
        }else if (maintenanceButtonText === 'End Maintenance'){
            // Call the GraphQL to disable maintenance window
            setMaintenanceButtonText('Start Maintenance')
            // Unfreeze the dropdown menu
            setDropDownStatus(false)
            // End the running timer as well
            clearInterval(refreshingTimer)
        }
        setConfirmedMode(mode)
        setPopUp(false)
    }

    return (
        <Dialog  maxWidth="md" fullWidth open={popUp}>
            <Box sx={{p : 2}}>
                <Card>
                    <CardHeader title={
                    <Box>
                        Are you sure you want to {maintenanceButtonText.toLowerCase()}?
                    </Box>
                  }/>
                    <Divider/>
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
                          onClick={() => {setPopUp(false)} }
                        >
                          No
                        </Button>
                    </Box>
                </Card>
            </Box>
        </Dialog>
    )
}

export const MaintenanceViewer = () => {
    const client = useClient();
    const [updating, setUpdating] = useState(false);
    const [mode, setMode] = useState('')
    const [popUp, setPopUp] = useState(false)
    const [confirmedMode, setConfirmedMode] = useState('')
    const [maintenanceButtonText, setMaintenanceButtonText] = useState('Start Maintenance')
    const [maintenanceWindowStatus, setMaintenanceWindowStatus] = useState('NOT-IN-MAINTENANCE')
    const [dropDownStatus, setDropDownStatus] = useState(false)
    const [refreshingTimer, setRefreshingTimer] = useState('')
    const { enqueueSnackbar, closeSnackbar } = useSnackbar();
    const dispatch = useDispatch();

    const refreshMaintenanceView = async () =>{
        console.log("Refreshing the maintenance view now!!!")
        // Call the que
        setUpdating(true)
        setTimeout(() =>{
            setUpdating(false)
        }, 2000)

        refreshStatus().catch((e) => dispatch({ type: SET_ERROR, error: e.message }))
        return true
    }

    const startMaintenanceWindow = () => {
        // Check if proper maintenance mode is selected
        // Use Formik forms for this in the future
        console.log(`value of the mode is ${mode}`)
        if (!['READ-ONLY', 'NO-ACCESS'].includes(mode) && maintenanceButtonText === 'Start Maintenance'){
            dispatch({ type: SET_ERROR, error: 'Please select correct maintenance mode' })
            return false;
        }
        setPopUp(true)
        return true;
    }

    const startRefreshPolling = useCallback(
        async () => {
            console.log("I am here in the refresh polling ")
            if (client){
                    const setTimer = setInterval(() => {
                    refreshStatus().catch((e) => dispatch({ type: SET_ERROR, error: e.message }))}
                    , [10000])
                    setRefreshingTimer(setTimer)
            }
        }
        , [client])

    const refreshStatus = async () => {
        closeSnackbar();
        await console.log("gsdlfjslf")
        console.log("Refreshing the status of the maintenance window")
        // Call the query to get the status of the maintenance window
        // Update the status of the maintenance window
        // Enqueue Snack bar to show that the maintenance window status is being polled
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
                    Maintenance Window Status is being updated !!
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

    useEffect(() => {
        if (client) {
            // For the first time
            // Check if the maintenance mode is ON
            if (isMaintenanceMode()){
                 // If ON, then
                // Fetch the value of the maintenance mode and paste it on the text field, disable the text field
                // Make the button say "End Maintenance" mode
                // Fetch the Status of the maintenance mode
                // Also, edit the Maintenance mode value
                const maintenanceMode = 'READ-ONLY' // GET THIS FROM GRAPHQL ENDPOINT
                setMaintenanceButtonText('End Maintenance')
                setMaintenanceWindowStatus('IN-PROGRESS') // GET THIS FROM GRAPHQL ENDPOINT
                setConfirmedMode(maintenanceMode)
                setDropDownStatus(true)

                const setTimer = setInterval(() => {
                    refreshStatus().catch((e) => dispatch({ type: SET_ERROR, error: e.message }))}
                    , [10000])
                setRefreshingTimer(setTimer)
                return () => clearInterval(setTimer)

            }else{
                // If OFF, then
                // Make the button say "Start Maintenance"
                // Clear the status and maintenance mode values
                setMaintenanceButtonText('Start Maintenance')
                setConfirmedMode('')
            }
        }
    }, [client]);


    return (
        <Box>
            <Card>
                <CardHeader
                    title={
                    <Box>
                        Create a Maintenance Window
                    </Box>
                  } />
                <Divider />
                <Box>
                    <Box display="flex"  sx={{ p: 1 }} >
                        <Box sx={{ flexGrow: 1 }}>
                            <TextField
                            style={{width:500}}
                            label="Mode"
                            name="MaintenanceMode"
                            onChange={(event)=>{setMode(event.target.value)}}
                            select
                            value={mode}
                            variant="outlined"
                            disabled={dropDownStatus}
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
                          value={"Start Maintenance"}
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
                <Divider/>
                <Box display="flex"  sx={{ p: 3 }}>
                    <Typography variant="subtitle2" fontSize={'15px'} sx={{ p: 2 }}>
                        Status : {maintenanceWindowStatus === 'READY-FOR-DEPLOYMENT' ? (<Label color={'success'}>READY-FOR-DEPLOYMENT</Label>) : maintenanceWindowStatus === 'IN-PROGRESS' ? (<Label color={'warning'}>IN-PROGRESS</Label>) : maintenanceWindowStatus === 'NOT-IN-MAINTENANCE' ? (<Label color={'secondary'}>NOT-IN-MAINTENANCE</Label>) : <> - </> }
                    </Typography>
                     <Typography variant="subtitle2" fontSize={'15px'} sx={{ p: 2 }}>
                        |
                    </Typography>
                    <Typography variant="subtitle2" fontSize={'15px'} sx={{ p: 2 }}>
                        Current Maintenance Mode : {confirmedMode}
                    </Typography>
                </Box>
                <Divider/>
                <Box>
                     <Typography variant="subtitle2" fontSize={'15px'} sx={{ p: 3 }}>
                        Note - To get updates on the maintenance window status please be on this tab or keep visiting maintenance tab. For safe deployments, please deploy when the status is READY-FOR-DEPLOYMENT
                    </Typography>
                </Box>
            </Card>
            <MaintenanceConfirmationPopUp popUp={popUp} setPopUp={setPopUp} mode={mode} confirmedMode={confirmedMode} setConfirmedMode={setConfirmedMode} maintenanceButtonText={maintenanceButtonText} setMaintenanceButtonText={setMaintenanceButtonText} setDropDownStatus={setDropDownStatus} refreshingTimer={refreshingTimer} startRefreshPolling={startRefreshPolling}/>
        </Box>
    )
}