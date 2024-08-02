// import { LoadingButton } from '@mui/lab';
import {
  // Autocomplete,
  Button,
  // CardContent,
  // CardHeader,
  // Checkbox,
  Box,
  // Chip,
  // Divider,
  // FormControl,
  // FormGroup,
  // FormControlLabel,
  // FormLabel,
  // Grid,
  // InputLabel,
  // MenuItem,
  // Select,
  // Switch,
  // TextField,
  Typography
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
// import { Formik } from 'formik';
// import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
// import { useCallback, useEffect, useState } from 'react';

//import AutoModeIcon from '@mui/icons-material/AutoMode';
// import * as Yup from 'yup';
// import { ChipInput, Defaults } from 'design';
import { Scrollbar } from 'design';
//import { SET_ERROR, useDispatch } from 'globalErrors';
//import { useClient } from 'services';
/* eslint-disable no-console */
export const ReviewMetadataComponent = (props) => {
  const {
    // dataset,
    // targetType,
    targets
    // setTargets,
    // selectedMetadataTypes,
    // version,
    // setVersion
  } = props;
  // const { enqueueSnackbar } = useSnackbar();
  // const dispatch = useDispatch();
  // const client = useClient();

  return (
    <>
      {Array.isArray(targets) && targets.length > 0 ? (
        <Box>
          <Scrollbar>
            <Box sx={{ minWidth: 600 }}>
              <DataGrid
                autoHeight
                rows={targets} // Replace with your data array
                getRowId={(node) => node.targetUri}
                columns={[
                  // Define your columns here
                  { field: 'targetUri', hide: true },
                  { field: 'name', headerName: 'Name', flex: 2 },
                  { field: 'targetType', headerName: 'TargetType', flex: 1 },
                  { field: 'label', headerName: 'Label', flex: 1 },
                  { field: 'description', headerName: 'Description', flex: 3 },
                  { field: 'tags', headerName: 'Tags', flex: 2 },
                  { field: 'topics', headerName: 'Topics', flex: 2 }
                  // Add more columns as needed
                ]}
                pageSize={10} // Replace with your desired page size
                rowsPerPageOptions={[5, 10, 20]} // Customize row options
                pagination
                disableSelectionOnClick
                sx={{
                  wordWrap: 'break-word',
                  '& .MuiDataGrid-row': {
                    borderBottom: '1px solid rgba(145, 158, 171, 0.24)'
                  },
                  '& .MuiDataGrid-columnHeaders': {
                    borderBottom: 0.5
                  }
                }}
              />
            </Box>
          </Scrollbar>
        </Box>
      ) : (
        <Typography variant="body1">No metadata available</Typography>
      )}
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
