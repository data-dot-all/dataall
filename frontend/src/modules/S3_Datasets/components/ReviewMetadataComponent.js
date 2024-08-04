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
import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';

//import AutoModeIcon from '@mui/icons-material/AutoMode';
// import * as Yup from 'yup';
// import { ChipInput, Defaults } from 'design';
import { Scrollbar } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import { updateDataset } from '../services';
import { updateDatasetTable } from 'modules/Tables/services';
import { updateDatasetStorageLocation } from 'modules/Folders/services';
/* eslint-disable no-console */
export const ReviewMetadataComponent = (props) => {
  const {
    dataset,
    // targetType,
    targets,
    setTargets,
    selectedMetadataTypes
    // version,
    // setVersion
  } = props;
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const client = useClient();
  async function saveMetadata(targets) {
    try {
      console.log({ selectedMetadataTypes });
      const updatedTargets = targets.map(async (target) => {
        console.log({ v: target.targetType });
        const updatedMetadata = {};

        // Loop through selectedMetadataTypes and add the corresponding key-value pairs to updatedMetadata
        Object.entries(selectedMetadataTypes).forEach(
          ([metadataType, checked]) => {
            if (checked) {
              updatedMetadata[metadataType] = target[metadataType];
            }
          }
        );
        if (target.targetType === 'S3_Dataset') {
          updatedMetadata.KmsAlias = dataset.KmsAlias;
          const response = await client.mutate(
            updateDataset({
              datasetUri: target.targetUri, // Use target.targetUri instead of dataset.datasetUri
              input: updatedMetadata
            })
          );

          if (!response.errors) {
            return { ...target, success: true }; // Return the updated target with success flag
          } else {
            dispatch({ type: SET_ERROR, error: response.errors[0].message });
            return { ...target, success: false }; // Return the target with success flag set to false
          }
        } else if (target.targetType === 'Table') {
          const response = await client.mutate(
            updateDatasetTable({
              tableUri: target.targetUri, // Use target.targetUri instead of dataset.datasetUri
              input: updatedMetadata
            })
          );

          if (!response.errors) {
            return { ...target, success: true }; // Return the updated target with success flag
          } else {
            dispatch({ type: SET_ERROR, error: response.errors[0].message });
            return { ...target, success: false }; // Return the target with success flag set to false
          }
        } else if (target.targetType === 'Folder') {
          const response = await client.mutate(
            updateDatasetStorageLocation({
              locationUri: target.targetUri, // Use target.targetUri instead of dataset.datasetUri
              input: updatedMetadata
            })
          );

          if (!response.errors) {
            return { ...target, success: true }; // Return the updated target with success flag
          } else {
            dispatch({ type: SET_ERROR, error: response.errors[0].message });
            return { ...target, success: false }; // Return the target with success flag set to false
          }
        }
      });

      const updatedTargetsResolved = await Promise.all(updatedTargets);

      const successfulTargets = updatedTargetsResolved.filter(
        (target) => target.success
      );
      const failedTargets = updatedTargetsResolved.filter(
        (target) => !target.success
      );

      if (successfulTargets.length > 0) {
        enqueueSnackbar(
          `${successfulTargets.length} target(s) updated successfully`,
          {
            anchorOrigin: {
              horizontal: 'right',
              vertical: 'top'
            },
            variant: 'success'
          }
        );
      }

      if (failedTargets.length > 0) {
        enqueueSnackbar(`${failedTargets.length} target(s) failed to update`, {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'error'
        });
      }
    } catch (err) {
      console.error(err);
      dispatch({ type: SET_ERROR, error: err.message });
    }
  }
  return (
    <>
      {Array.isArray(targets) && targets.length > 0 ? (
        <Box>
          <Scrollbar>
            <Box sx={{ minWidth: 900 }}>
              <DataGrid
                autoHeight
                rows={targets}
                getRowId={(node) => node.targetUri}
                rowHeight={80}
                columns={[
                  { field: 'targetUri', hide: true },
                  {
                    field: 'name',
                    headerName: 'Name',
                    flex: 2,
                    editable: true
                  },
                  {
                    field: 'targetType',
                    headerName: 'Target Type',
                    flex: 1,
                    editable: true
                  },
                  {
                    field: 'label',
                    headerName: 'Label',
                    flex: 1,
                    editable: true
                  },
                  {
                    field: 'description',
                    headerName: 'Description',
                    flex: 3,
                    editable: true,
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
                    editable: true,
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
                    editable: true,
                    renderCell: (params) => (
                      <div style={{ whiteSpace: 'pre-wrap', padding: '8px' }}>
                        {params.value}
                      </div>
                    )
                  }
                ]}
                pageSize={10}
                rowsPerPageOptions={[5, 10, 20]}
                pagination
                disableSelectionOnClick
                onCellEditCommit={(params) => {
                  const { value, id, field } = params;
                  const updatedTargets = targets.map((target) => {
                    const newTarget = { ...target };
                    if (newTarget.targetUri === id) {
                      newTarget[field] = value;
                    }
                    return newTarget;
                  });
                  setTargets(updatedTargets);
                }}
                onProcessRowUpdateError={(error) => {
                  console.error('Error updating row:', error);
                }}
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
        onClick={() => saveMetadata(targets)}
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
