// import { LoadingButton } from '@mui/lab';
import {
  // Autocomplete,
  Avatar,
  Button,
  // CardContent,
  // CardHeader,
  // Checkbox,
  Chip,
  // Divider,
  // FormControl,
  // FormGroup,
  // FormControlLabel,
  // FormLabel,
  Grid
  // InputLabel,
  // MenuItem,
  // Select,
  // Switch,
  // TextField,
  //Typography
} from '@mui/material';
// import { DataGrid } from '@mui/x-data-grid';
// import { Formik } from 'formik';
// import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
// import { useCallback, useEffect, useState } from 'react';

//import AutoModeIcon from '@mui/icons-material/AutoMode';
// import * as Yup from 'yup';
// import { ChipInput, Defaults } from 'design';
//import { Scrollbar } from 'design';
//import { SET_ERROR, useDispatch } from 'globalErrors';
//import { useClient } from 'services';
/* eslint-disable no-console */
export const ReviewMetadataComponent = (props) => {
  const {
    dataset,
    targetType,
    targets,
    setTargets,
    selectedMetadataTypes,
    version,
    setVersion,
    ...other
  } = props;
  // const { enqueueSnackbar } = useSnackbar();
  // const dispatch = useDispatch();
  // const client = useClient();

  return (
    <>
      <Grid
        container
        sx={{ m: 1 }}
        spacing={3}
        justifyContent="flex-start"
        {...other}
      >
        <Grid item lg={2} xl={2} md={2} sm={2} xs={2}>
          <Chip
            avatar={<Avatar>1</Avatar>}
            label="HOLA"
            color="primary"
            variant="outlined"
          />
        </Grid>
      </Grid>
      <Button
        color="primary"
        size="small"
        //startIcon={<AutoModeIcon size={15} />}
        sx={{ m: 2 }}
        //onClick={saveMetadata}
        type="button"
        variant="contained"
      >
        Save
      </Button>
    </>
  );
};

ReviewMetadataComponent.propTypes = {
  dataset: PropTypes.object.isRequired,
  targetType: PropTypes.string.isRequired,
  targets: PropTypes.array.isRequired,
  setTargets: PropTypes.func.isRequired,
  selectedMetadataTypes: PropTypes.object.isRequired,
  version: PropTypes.number.isRequired,
  setVersion: PropTypes.func.isRequired
};
