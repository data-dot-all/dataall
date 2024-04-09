import {Box, Button, Card, CardHeader, Dialog, Divider, MenuItem, TextField, Typography} from "@mui/material";
import React, {useState} from "react";
import {Article, SystemUpdate} from "@mui/icons-material";
import {LoadingButton} from "@mui/lab";
import {Label} from "../../../design";

const maintenanceModes = [
    {value: "READ-ONLY", label: "Read-Only"},
    {value: "NO-ACCESS", label: "No-Access"}
]

export const MaintenanceConfirmationPopUp = ({popUp, setPopUp}) => {

    return (
        <Dialog  maxWidth="md" fullWidth open={popUp}>
            <Box sx={{p : 2}}>
                <Card>
                    <CardHeader title={
                    <Box>
                        Are you sure ?
                    </Box>
                  }/>
                    <Divider/>
                    <Button
                          color="primary"
                          startIcon={<Article fontSize="small" />}
                          sx={{ m: 1 }}
                          variant="outlined"
                          onClick={() => {setPopUp(false)} }
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
                </Card>
            </Box>
        </Dialog>
    )
}

export const MaintenanceViewer = () => {

    const [updating, setUpdating] = useState(false);
    const [mode, setMode] = useState('')
    const [popUp, setPopUp] = useState(false)
    const [confirmedMode, setConfirmedMode] = useState('')

    const refreshMaintenanceView = () =>{
        console.log("Refreshing the maintenance view now!!!")
        return true
    }

    const startMaintenanceWindow = () => {
        setConfirmedMode(mode)
        setPopUp(true)
        return true;
    }

    const refreshWindow = () =>{
        setUpdating(true)
        console.log("Refreshing the page")
        setTimeout(() =>{
            setUpdating(false)
        }, 2000)

    }

    return (
        <Box>
            <Card>
                <CardHeader
                    actions = {refreshMaintenanceView()}
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
                          >
                            {maintenanceModes.map((group) => (
                              <MenuItem key={group.value} value={group.value}>
                                {group.label}
                              </MenuItem>
                            ))}
                          </TextField></Box>


                     {/*<Box display="flex" justifyContent="flex-end" sx={{ p: 1 }}>*/}
                         <Button
                          color="primary"
                          startIcon={<Article fontSize="small" />}
                          sx={{ m: 1 }}
                          variant="outlined"
                          onClick={startMaintenanceWindow}
                        >
                          Start Maintenance
                        </Button>

                         <LoadingButton
                          color="primary"
                          loading={updating}
                          onClick={refreshWindow}
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
                        Status : <Label color={'success'}>READY-FOR-DEPLOYMENT</Label>
                    </Typography>
                     <Typography variant="subtitle2" fontSize={'15px'} sx={{ p: 2 }}>
                        |
                    </Typography>
                    <Typography variant="subtitle2" fontSize={'15px'} sx={{ p: 2 }}>
                        Maintenance Mode : {confirmedMode}
                    </Typography>
                </Box>
                <Divider/>
                <Box>
                </Box>
            </Card>
            <MaintenanceConfirmationPopUp popUp={popUp} setPopUp={setPopUp} />
        </Box>
    )
}