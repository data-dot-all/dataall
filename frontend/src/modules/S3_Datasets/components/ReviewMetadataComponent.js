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
  // const getRowHeight = (description) => {
  //   const lineHeight = 20; // Adjust this value based on your font size and line height
  //   console.log(description.valueOf());
  //   const lines = description.split('\n').length; // Count the number of lines in the description
  //   const maxLines = 5; // Set the maximum number of lines to display
  //   const height = Math.min(lines, maxLines) * lineHeight + 16; // Calculate the height based on the number of lines
  //   return height;
  // };
  return (
    <>
      {Array.isArray(targets) && targets.length > 0 ? (
        <Box>
          <Scrollbar>
            <Box sx={{ minWidth: 900 }}>
              <DataGrid
                autoHeight
                rows={targets} // Replace with your data array
                getRowId={(node) => node.targetUri}
                rowHeight={80}
                columns={[
                  // Define your columns here
                  { field: 'targetUri', hide: true },
                  { field: 'name', headerName: 'Name', flex: 2 },
                  { field: 'targetType', headerName: 'Target Type', flex: 1 },
                  { field: 'label', headerName: 'Label', flex: 1 },
                  {
                    field: 'description',
                    headerName: 'Description',
                    flex: 3,
                    //rowHeight: (params) => getRowHeight(params.value),
                    renderCell: (params) => (
                      <div style={{ whiteSpace: 'pre-wrap', padding: '8px' }}>
                        {params.value}
                      </div>
                    )
                  },
                  {
                    field: 'tags',
                    headerName: 'Tags',
                    flex: 2,
                    renderCell: (params) => (
                      <div style={{ whiteSpace: 'pre-wrap', padding: '8px' }}>
                        {params.value}
                      </div>
                    )
                  },
                  {
                    field: 'topic',
                    headerName: 'Topics',
                    flex: 2,
                    renderCell: (params) => (
                      <div style={{ whiteSpace: 'pre-wrap', padding: '8px' }}>
                        {params.value}
                      </div>
                    )
                  }
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
